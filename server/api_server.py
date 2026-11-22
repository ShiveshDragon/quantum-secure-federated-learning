import os
import sys
import json
import time
import math
import random
import traceback
import numpy as np
from flask import Flask, request, jsonify, send_from_directory

# Ensure backend root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Import backend modules
try:
    from quantum.e91 import (
        generate_sifted_key,
        run_chsh,
        simulate_correlation,
        calculate_chsh,
        singlet_statevector,
        theoretical_correlation
    )
    from quantum.noise import build_depolarizing_noise
    from crypto.key_manager import derive_session_key
    from crypto.aes_crypto import encrypt_json, decrypt_json
    from crypto.hmac_auth import canonical_bytes, create_message_mac, verify_hmac
    from federated.dataset import (
        create_dataset, 
        split_clients, 
        get_dataset_summary, 
        load_csv_dataset, 
        DEFAULT_HOSPITAL_DATA_PATH
    )
    from federated.client import Client
    from federated.model import SimpleLogisticModel, classification_metrics
    from federated.server import FLServer
    from experiments.common import run_fl, secure_update, make_clients
    from federated.robust_aggregation import coordinate_median, coordinate_trimmed_mean
    from experiments.robust_aggregation_experiment import (
        run_robust_aggregation_comparison,
        run_multi_seed_evaluation,
        run_malicious_fraction_sweep,
        run_non_iid_comparison
    )
except Exception as e:
    print(f"Error importing backend modules: {e}")
    traceback.print_exc()

app = Flask(__name__, static_folder=FRONTEND_DIR)

# Enable CORS for local development
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Serve frontend static files
@app.route("/")
def serve_index():
    if os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({
        "status": "Quantum FL-IoT API Server Online",
        "endpoints": [
            "/api/status",
            "/api/quantum/e91",
            "/api/quantum/chsh",
            "/api/quantum/sweep/eavesdropping",
            "/api/quantum/sweep/noise",
            "/api/fl/run",
            "/api/fl/compare",
            "/api/crypto/demonstrate",
            "/api/results/all"
        ]
    })

@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/api/status", methods=["GET"])
def api_status():
    import qiskit
    return jsonify({
        "status": "online",
        "paper_title": "Integrating quantum computing with federated learning for enhanced security and privacy in IoT networks",
        "journal": "Results in Engineering (Elsevier)",
        "doi": "10.1016/j.rineng.2025.108500",
        "qiskit_version": getattr(qiskit, "__version__", "unknown"),
        "python_version": sys.version,
        "capabilities": [
            "E91 Quantum Key Distribution Simulation",
            "CHSH Bell-Inequality Aer Circuit Simulation",
            "Eve Eavesdropping Intercept/Resend Attack Model",
            "Depolarizing Noise Channel Simulation",
            "AES-256-GCM + HMAC-SHA256 Cryptography",
            "Multi-client Federated Learning (FedAvg)",
            "IID and Non-IID Label-Skew Partitioning",
            "Quantum-Secured Federated Learning Orchestration",
            "Robust Aggregation (Coordinate-Wise Median & Trimmed Mean)",
            "Model-Poisoning & Byzantine Adversary Defense",
            "Cryptographic Replay Attack Protection"
        ]
    })

@app.route("/api/quantum/e91", methods=["POST"])
def api_quantum_e91():
    data = request.get_json() or {}
    rounds = int(data.get("rounds", 1000))
    key_angle = float(data.get("key_angle", 0.0))
    eve_probability = float(data.get("eve_probability", 0.0))
    seed = int(data.get("seed", random.randint(1, 100000)))

    # Run protocol-level simulation
    res = generate_sifted_key(
        rounds=rounds,
        key_angle=key_angle,
        seed=seed,
        eve_probability=eve_probability
    )

    # Detailed per-event tracking for frontend visualizer (first 30 events)
    rng = random.Random(seed)
    events = []
    for i in range(min(rounds, 30)):
        a_basis = key_angle if rng.random() < 0.5 else 45.0
        b_basis = key_angle if rng.random() < 0.5 else 45.0
        same = math.isclose(a_basis, b_basis, abs_tol=1e-12)
        a_bit = rng.randint(0, 1)
        b_bit = 1 - a_bit if same else rng.randint(0, 1)
        intercepted = False
        if eve_probability and rng.random() < eve_probability:
            intercepted = True
            b_bit = rng.randint(0, 1)
        
        b_key_bit = 1 - b_bit if same else None
        error = (same and a_bit != b_key_bit)

        events.append({
            "pair_index": i + 1,
            "alice_basis": a_basis,
            "bob_basis": b_basis,
            "matched_basis": same,
            "alice_bit": a_bit,
            "bob_raw_bit": b_bit,
            "bob_sifted_bit": b_key_bit,
            "intercepted": intercepted,
            "error": error
        })

    # Derive session key if QBER is tolerable (< 0.11)
    session_key_hex = None
    if res.qber <= 0.11 and len(res.alice_bits) > 0:
        session_key_hex = derive_session_key(res.alice_bits).hex()

    return jsonify({
        "rounds": rounds,
        "key_angle": key_angle,
        "eve_probability": eve_probability,
        "seed": seed,
        "total_pairs": rounds,
        "sifted_bits_count": len(res.alice_bits),
        "sifting_efficiency": round(len(res.alice_bits) / rounds, 4) if rounds else 0,
        "qber": round(res.qber, 4),
        "qber_percentage": round(res.qber * 100, 2),
        "eve_detected": res.qber > 0.11,
        "security_threshold": 0.11,
        "alice_key_preview": res.alice_bits[:64],
        "bob_key_preview": res.bob_bits[:64],
        "session_key_hex": session_key_hex,
        "sample_events": events
    })

@app.route("/api/quantum/chsh", methods=["POST"])
def api_quantum_chsh():
    data = request.get_json() or {}
    shots = int(data.get("shots", 2048))
    noise_prob = float(data.get("noise", 0.0))
    eve_probability = float(data.get("eve_probability", 0.0))
    seed = int(data.get("seed", 1234))

    if shots <= 0:
        return jsonify({"error": "shots must be a positive integer"}), 400
    if not 0.0 <= noise_prob <= 1.0:
        return jsonify({"error": "noise must be between 0 and 1"}), 400
    if not 0.0 <= eve_probability <= 1.0:
        return jsonify({"error": "eve_probability must be between 0 and 1"}), 400

    noise_model = None
    if noise_prob > 0.0 or eve_probability > 0.0:
        noise_model = build_depolarizing_noise(noise_prob, eve_probability)

    start = time.perf_counter()
    res = run_chsh(shots=shots, seed=seed, noise_model=noise_model,
                   eve_probability=eve_probability)
    sim_time = time.perf_counter() - start

    chsh_val = res["CHSH"]
    ideal_chsh = res["ideal_CHSH"]
    classical_bound = 2.0
    quantum_bound = 2.0 * math.sqrt(2)

    return jsonify({
        "shots": shots,
        "noise": noise_prob,
        "eve_probability": eve_probability,
        "seed": seed,
        "execution_time_sec": round(sim_time, 3),
        "correlations": {
            "E_a1_b1": round(res["E(a1,b1)"], 4),
            "E_a1_b2": round(res["E(a1,b2)"], 4),
            "E_a2_b1": round(res["E(a2,b1)"], 4),
            "E_a2_b2": round(res["E(a2,b2)"], 4)
        },
        "settings": {
            "alice_bases": [0.0, 45.0],
            "bob_bases": [22.5, -22.5]
        },
        "chsh": round(chsh_val, 4),
        "ideal_chsh": round(ideal_chsh, 4),
        "classical_bound": classical_bound,
        "quantum_bound": round(quantum_bound, 4),
        "violation": chsh_val > classical_bound,
        "entanglement_verified": chsh_val > classical_bound
    })

@app.route("/api/quantum/sweep/eavesdropping", methods=["POST"])
def api_sweep_eavesdropping():
    data = request.get_json() or {}
    rounds = int(data.get("rounds", 8000))
    seed = int(data.get("seed", 42))

    probs = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    results = []
    for p in probs:
        r = generate_sifted_key(rounds=rounds, seed=seed, eve_probability=p)
        results.append({
            "eve_probability": p,
            "qber": round(r.qber, 4),
            "qber_pct": round(r.qber * 100, 2),
            "sifted_bits": len(r.alice_bits),
            "detected": r.qber > 0.11
        })

    return jsonify({
        "rounds": rounds,
        "seed": seed,
        "sweep": results,
        "threshold": 0.11
    })

@app.route("/api/quantum/sweep/noise", methods=["POST"])
def api_sweep_noise():
    data = request.get_json() or {}
    shots = int(data.get("shots", 4096))
    seed = int(data.get("seed", 100))

    probs = [0.0, 0.002, 0.005, 0.01, 0.02, 0.035, 0.05]
    results = []
    for p in probs:
        noise = None if p == 0 else build_depolarizing_noise(p)
        chsh_res = run_chsh(shots=shots, seed=seed, noise_model=noise)
        same = simulate_correlation(0, 0, shots=shots, seed=seed, noise_model=noise)["correlation"]
        qber_est = (1 + same) / 2
        results.append({
            "depolarizing_noise": p,
            "chsh": round(chsh_res["CHSH"], 4),
            "qber_estimate": round(qber_est, 4),
            "violation": chsh_res["CHSH"] > 2.0
        })

    return jsonify({
        "shots": shots,
        "sweep": results,
        "classical_bound": 2.0,
        "quantum_bound": round(2 * math.sqrt(2), 4)
    })

@app.route("/api/data/info", methods=["GET"])
def api_data_info():
    """Return summary and preview of loaded clinical hospital dataset."""
    summary = get_dataset_summary()
    return jsonify(summary)

@app.route("/api/data/upload", methods=["POST"])
def api_data_upload():
    """Ingest custom hospital CSV dataset from web UI or API."""
    try:
        content = None
        filename = "hospital_data.csv"
        
        # Check if multipart form upload
        if "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400
            filename = file.filename
            content = file.read().decode("utf-8", errors="replace")
        elif request.is_json:
            data = request.get_json() or {}
            content = data.get("csv_text")
            filename = data.get("filename", "hospital_data.csv")
        else:
            content = request.get_data(as_text=True)

        if not content or len(content.strip()) == 0:
            return jsonify({"error": "Uploaded content is empty"}), 400

        # Validate CSV content
        import io
        import pandas as pd
        df = pd.read_csv(io.StringIO(content))
        
        if len(df) < 5:
            return jsonify({"error": f"Dataset has only {len(df)} rows. Minimum 5 rows required for federated learning across 5 clients."}), 400

        df_cols = [c.strip().lower() for c in df.columns]
        target_candidates = [c for c in df_cols if c in ("target", "label", "outcome", "diagnosis", "class")]
        if not target_candidates:
            return jsonify({
                "error": "No target/label column found. CSV must contain a 'target' column with 0 (normal) or 1 (risk).",
                "detected_columns": list(df.columns)
            }), 400

        # Save to DEFAULT_HOSPITAL_DATA_PATH
        os.makedirs(os.path.dirname(DEFAULT_HOSPITAL_DATA_PATH), exist_ok=True)
        with open(DEFAULT_HOSPITAL_DATA_PATH, "w", encoding="utf-8") as f:
            f.write(content)

        summary = get_dataset_summary(DEFAULT_HOSPITAL_DATA_PATH)
        return jsonify({
            "success": True,
            "message": f"Successfully loaded hospital dataset '{filename}' ({summary['total_rows']} patients, {summary['n_features']} clinical features).",
            "summary": summary
        })
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"Failed to parse CSV: {str(exc)}"}), 400

@app.route("/api/fl/run", methods=["POST"])
def api_fl_run():
    data = request.get_json() or {}
    n_clients = int(data.get("n_clients", 5))
    if n_clients not in (4, 5):
        n_clients = 5
    rounds = int(data.get("rounds", 5))
    secure = bool(data.get("secure", True))
    non_iid = bool(data.get("non_iid", False))
    seed = int(data.get("seed", 42))
    dataset_source = data.get("dataset_source", "hospital" if os.path.exists(DEFAULT_HOSPITAL_DATA_PATH) else "synthetic")

    t0 = time.perf_counter()
    try:
        rows, key_info = run_fl(
            n_clients=n_clients,
            rounds=rounds,
            secure=secure,
            non_iid=non_iid,
            seed=seed,
            dataset_source=dataset_source
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    total_duration = time.perf_counter() - t0

    # Also extract client dataset breakdown
    clients, xte, yte, n_features = make_clients(n_clients, non_iid, seed, dataset_source=dataset_source)
    clients_meta = []
    for c in clients:
        pos_samples = int(np.sum(c.y == 1))
        neg_samples = int(np.sum(c.y == 0))
        clients_meta.append({
            "client_id": c.client_id,
            "total_samples": len(c.y),
            "pos_samples": pos_samples,
            "neg_samples": neg_samples,
            "label_ratio": round(pos_samples / len(c.y), 3) if len(c.y) else 0
        })

    return jsonify({
        "configuration": {
            "n_clients": n_clients,
            "rounds": rounds,
            "secure": secure,
            "non_iid": non_iid,
            "seed": seed,
            "dataset_source": dataset_source
        },
        "total_duration_sec": round(total_duration, 4),
        "key_info": key_info,
        "clients": clients_meta,
        "rounds": rows
    })

@app.route("/api/fl/compare", methods=["GET"])
def api_fl_compare():
    seed = int(request.args.get("seed", 42))
    n_clients = int(request.args.get("n_clients", 5))
    rounds = int(request.args.get("rounds", 5))
    dataset_source = request.args.get("dataset_source", "hospital" if os.path.exists(DEFAULT_HOSPITAL_DATA_PATH) else "synthetic")

    # 1. Centralized ML baseline
    xtr, xte, ytr, yte = create_dataset(600, 8, seed, source=dataset_source)
    t0 = time.perf_counter()
    cent_model = SimpleLogisticModel(xtr.shape[1]).fit(xtr, ytr, epochs=rounds * 8, lr=0.05)
    cent_time = time.perf_counter() - t0
    cent_metrics = classification_metrics(yte, cent_model.predict(xte))
    cent_metrics["train_time_sec"] = round(cent_time, 4)
    cent_metrics["total_payload_bytes"] = 0
    cent_metrics["privacy_level"] = "None (Centralized Data Warehouse)"
    cent_metrics["security_level"] = "Standard Server Boundary"

    # 2. Standard Federated Learning
    fl_rows, _ = run_fl(n_clients, rounds, secure=False, seed=seed, dataset_source=dataset_source)
    fl_final = fl_rows[-1]
    fl_final["privacy_level"] = "Decentralized Data (Vulnerable In-Transit Model Gradients)"
    fl_final["security_level"] = "Plaintext FL Transport"

    # 3. Quantum-Secured Federated Learning
    sec_rows, key_info = run_fl(n_clients, rounds, secure=True, seed=seed, dataset_source=dataset_source)
    sec_final = sec_rows[-1]
    sec_final["privacy_level"] = "Decentralized Data + AES-256-GCM Payload Confidentiality"
    sec_final["security_level"] = "E91 QKD Key Exchange + HMAC-SHA256 Integrity Verification"

    return jsonify({
        "dataset_source": dataset_source,
        "centralized": cent_metrics,
        "standard_fl": {
            "metrics": fl_final,
            "rounds": fl_rows
        },
        "quantum_secured_fl": {
            "metrics": sec_final,
            "key_info": key_info,
            "rounds": sec_rows
        }
    })

@app.route("/api/crypto/demonstrate", methods=["POST"])
def api_crypto_demo():
    data = request.get_json() or {}
    client_id = data.get("client_id", "client1")
    round_no = int(data.get("round", 1))
    tamper_ciphertext = bool(data.get("tamper_ciphertext", False))
    tamper_hmac = bool(data.get("tamper_hmac", False))

    # Generate a quantum key bitstring and derive session key
    e91 = generate_sifted_key(rounds=1024, seed=123)
    session_key = derive_session_key(e91.alice_bits)

    payload = {
        "client_id": client_id,
        "round": round_no,
        "sample_count": 96,
        "weights": [0.124, -0.453, 0.891, -0.045, 0.632, -0.312, 0.089, 0.441],
        "bias": [0.015]
    }
    associated_data = f"{client_id}:{round_no}".encode("utf-8")

    # Encrypt
    t0 = time.perf_counter()
    enc_data = encrypt_json(session_key, payload, associated_data)
    enc_time = (time.perf_counter() - t0) * 1000

    # HMAC
    message = {
        "client_id": client_id,
        "round": round_no,
        "encrypted": enc_data
    }
    mac = create_message_mac(session_key, message)
    message["hmac"] = mac

    # Optional tampering
    tampered_msg = None
    if tamper_ciphertext:
        # Flip a byte in ciphertext base64
        ct = enc_data["ciphertext"]
        tampered_ct = ct[:-2] + ("AA" if ct[-2:] != "AA" else "BB")
        enc_data["ciphertext"] = tampered_ct
        tampered_msg = "Ciphertext bits altered by an eavesdropper / man-in-the-middle!"
    elif tamper_hmac:
        # Flip a hex char in HMAC
        mac = ("0" if mac[0] != "0" else "1") + mac[1:]
        message["hmac"] = mac
        tampered_msg = "HMAC authentication tag altered!"

    # Verification and Decryption
    t1 = time.perf_counter()
    body_for_verify = canonical_bytes({k: message[k] for k in message if k != "hmac"})
    hmac_valid = verify_hmac(session_key, body_for_verify, message["hmac"])
    
    decrypted_payload = None
    gcm_tag_valid = False
    error_msg = None

    if hmac_valid:
        try:
            decrypted_payload = decrypt_json(session_key, enc_data, associated_data)
            gcm_tag_valid = True
        except Exception as exc:
            error_msg = f"AES-GCM Authentication Failed: {str(exc)}"
    else:
        error_msg = "HMAC Verification Failed: Message was tampered or corrupted in-transit!"

    dec_time = (time.perf_counter() - t1) * 1000
    wire_bytes = canonical_bytes(message)

    return jsonify({
        "quantum_sifted_bits_used": len(e91.alice_bits),
        "derived_session_key_hex": session_key.hex(),
        "associated_data": associated_data.decode("utf-8"),
        "payload_plain": payload,
        "iv_b64": enc_data.get("nonce", ""),
        "ciphertext_b64": enc_data["ciphertext"],
        "hmac_tag_hex": message["hmac"],
        "total_wire_bytes": len(wire_bytes),
        "encryption_time_ms": round(enc_time, 4),
        "decryption_time_ms": round(dec_time, 4),
        "hmac_valid": hmac_valid,
        "gcm_tag_valid": gcm_tag_valid,
        "tampered_msg": tampered_msg,
        "error_msg": error_msg,
        "decrypted_payload": decrypted_payload
    })

@app.route("/api/fl/robust", methods=["POST"])
def api_fl_robust():
    data = request.get_json() or {}
    method = data.get("aggregation_method", "coordinate_median")
    trim_ratio = float(data.get("trim_ratio", 0.2))
    attack_type = data.get("attack_type", "sign_flip")
    attack_factor = float(data.get("attack_factor", 3.0))
    malicious_clients = data.get("malicious_clients", ["client5"])
    rounds = int(data.get("rounds", 5))
    n_clients = int(data.get("n_clients", 5))
    non_iid = bool(data.get("non_iid", False))
    secure = bool(data.get("secure", False))
    seed = int(data.get("seed", 42))
    dataset_source = data.get("dataset_source", "hospital" if os.path.exists(DEFAULT_HOSPITAL_DATA_PATH) else "synthetic")

    t0 = time.perf_counter()
    target_rows, key_info = run_fl(
        n_clients=n_clients,
        rounds=rounds,
        secure=secure,
        non_iid=non_iid,
        seed=seed,
        aggregation_method=method,
        trim_ratio=trim_ratio,
        malicious_clients=malicious_clients,
        attack_type=attack_type,
        attack_factor=attack_factor,
        dataset_source=dataset_source
    )
    target_dur = time.perf_counter() - t0

    clean_rows, _ = run_fl(
        n_clients=n_clients,
        rounds=rounds,
        secure=False,
        non_iid=non_iid,
        seed=seed,
        aggregation_method="fedavg",
        malicious_clients=[],
        dataset_source=dataset_source
    )

    att_fedavg_final_acc = None
    if method != "fedavg" and malicious_clients:
        att_fedavg_rows, _ = run_fl(
            n_clients=n_clients,
            rounds=rounds,
            secure=False,
            non_iid=non_iid,
            seed=seed,
            aggregation_method="fedavg",
            malicious_clients=malicious_clients,
            attack_type=attack_type,
            attack_factor=attack_factor,
            dataset_source=dataset_source
        )
        att_fedavg_final_acc = att_fedavg_rows[-1]["accuracy"]

    final_target = target_rows[-1]
    final_clean = clean_rows[-1]
    
    degradation = round(final_clean["accuracy"] - final_target["accuracy"], 4)
    improvement = round(final_target["accuracy"] - att_fedavg_final_acc, 4) if att_fedavg_final_acc is not None else 0.0

    return jsonify({
        "configuration": {
            "aggregation_method": method,
            "trim_ratio": trim_ratio,
            "attack_type": attack_type,
            "attack_factor": attack_factor,
            "malicious_clients": malicious_clients,
            "malicious_count": len(malicious_clients),
            "rounds": rounds,
            "n_clients": n_clients,
            "non_iid": non_iid,
            "secure": secure,
            "seed": seed
        },
        "total_duration_sec": round(target_dur, 4),
        "key_info": key_info,
        "rounds": target_rows,
        "clean_baseline_rounds": clean_rows,
        "summary": {
            "final_accuracy": final_target["accuracy"],
            "final_f1": final_target["f1"],
            "final_precision": final_target["precision"],
            "final_recall": final_target["recall"],
            "clean_accuracy": final_clean["accuracy"],
            "clean_f1": final_clean["f1"],
            "attacked_fedavg_accuracy": att_fedavg_final_acc,
            "accuracy_degradation": degradation,
            "robustness_improvement": improvement,
            "mean_aggregation_time_sec": round(float(np.mean([r.get("aggregation_time", 0.0) for r in target_rows])), 6),
            "confusion_matrix": {
                "tp": final_target["tp"],
                "tn": final_target["tn"],
                "fp": final_target["fp"],
                "fn": final_target["fn"]
            }
        }
    })

@app.route("/api/experiments/robust-aggregation/results", methods=["GET"])
@app.route("/api/robust-aggregation/results", methods=["GET"])
def api_robust_aggregation_results():
    results_path = os.path.join(BACKEND_DIR, "results", "robust_aggregation_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "robust_aggregation_results.json not found", "status": "pending"}), 404

@app.route("/api/results/all", methods=["GET"])
def api_results_all():
    results_dir = os.path.join(BACKEND_DIR, "results")
    summary = {}
    if os.path.exists(results_dir):
        for fname in os.listdir(results_dir):
            fpath = os.path.join(results_dir, fname)
            if fname.endswith(".json") and os.path.isfile(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        summary[fname] = json.load(f)
                except Exception:
                    pass
            elif fname.endswith(".csv") and os.path.isfile(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        summary[fname] = f.read()
                except Exception:
                    pass
    return jsonify(summary)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting Quantum FL-IoT Server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
