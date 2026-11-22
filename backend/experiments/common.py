import json
import os
import time
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from quantum.e91 import generate_sifted_key, run_chsh
from crypto.key_manager import derive_session_key
from crypto.aes_crypto import encrypt_json, decrypt_json
from crypto.hmac_auth import canonical_bytes, create_message_mac, verify_hmac
from federated.client import Client
from federated.dataset import create_dataset, split_clients
from federated.server import FLServer

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def save_json(name: str, data: Any) -> str:
    path = os.path.join(RESULTS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def make_clients(
    n_clients: int = 5, 
    non_iid: bool = False, 
    seed: int = 42,
    dataset_source: str = "synthetic",
    csv_path: Optional[str] = None
):
    xtr, xte, ytr, yte = create_dataset(600, 8, seed, source=dataset_source, csv_path=csv_path)
    parts = split_clients(xtr, ytr, n_clients, non_iid=non_iid)
    return [Client(cid, x, y) for cid, x, y in parts], xte, yte, xtr.shape[1]


def secure_update(
    session_key: bytes, 
    client: Client, 
    global_state: Dict[str, Any], 
    round_number: int, 
    epochs: int = 8, 
    lr: float = 0.05,
    is_malicious: bool = False,
    attack_type: str = "sign_flip",
    attack_factor: float = 3.0,
    server: Optional[FLServer] = None
) -> Tuple[Dict[str, np.ndarray], int, Dict[str, Any]]:
    """Encrypt, sign, transmit, authenticate, and decrypt client model update with replay protection."""
    start = time.perf_counter()
    if is_malicious:
        state, count = client.train_poisoned(
            global_state, attack_type=attack_type, factor=attack_factor, epochs=epochs, lr=lr
        )
    else:
        state, count = client.train(global_state, epochs=epochs, lr=lr)
    train_time = time.perf_counter() - start

    timestamp = time.time()
    message_id = f"msg_{client.client_id}_r{round_number}_{int(timestamp*1000)}"

    payload = {
        "client_id": client.client_id, 
        "round": round_number,
        "sample_count": count, 
        "weights": state["weights"].tolist(),
        "bias": state["bias"].tolist(),
        "timestamp": timestamp,
        "message_id": message_id
    }
    associated = f"{client.client_id}:{round_number}".encode()
    
    start = time.perf_counter()
    encrypted = encrypt_json(session_key, payload, associated)
    enc_time = time.perf_counter() - start
    
    message = {
        "client_id": client.client_id, 
        "round": round_number,
        "encrypted": encrypted,
        "timestamp": timestamp,
        "message_id": message_id
    }
    mac = create_message_mac(session_key, message)
    message["hmac"] = mac
    wire = canonical_bytes(message)
    
    # Server-side verification and decryption
    start = time.perf_counter()
    ok = verify_hmac(session_key, canonical_bytes({k: message[k] for k in message if k != "hmac"}), mac)
    if not ok:
        raise RuntimeError(f"HMAC verification failed for client {client.client_id}")
        
    recovered = decrypt_json(session_key, encrypted, associated)
    sec_time = time.perf_counter() - start

    recovered_state = {
        "weights": np.asarray(recovered["weights"], dtype=float),
        "bias": np.asarray(recovered["bias"], dtype=float)
    }

    # Verify server replay protection if server instance supplied
    if server is not None:
        server.validate_client_update(
            recovered_state,
            client_id=client.client_id,
            round_number=round_number,
            message_id=message_id,
            timestamp=timestamp
        )

    return recovered_state, count, {
        "train_time": train_time, 
        "encrypt_time": enc_time,
        "security_verify_decrypt_time": sec_time,
        "payload_bytes": len(wire)
    }


def run_fl(
    n_clients: int = 5, 
    rounds: int = 5, 
    secure: bool = False, 
    non_iid: bool = False, 
    seed: int = 42,
    aggregation_method: str = "fedavg",
    trim_ratio: float = 0.2,
    malicious_clients: Optional[List[str]] = None,
    attack_type: str = "sign_flip",
    attack_factor: float = 3.0,
    dataset_source: str = "synthetic",
    csv_path: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Execute federated learning simulation across clients with optional security and robust aggregation.
    
    Args:
        n_clients: Number of simulated IoT devices (4 or 5)
        rounds: Number of global communication rounds
        secure: Enable E91 QKD + AES-256-GCM + HMAC-SHA256
        non_iid: Enable label-skew partition
        seed: Random seed for dataset and model reproducibility
        aggregation_method: 'fedavg', 'coordinate_median', or 'trimmed_mean'
        trim_ratio: Trimming ratio for trimmed_mean
        malicious_clients: List of client IDs simulating poisoning attacks (e.g. ['client5'])
        attack_type: 'sign_flip', 'random_noise', or 'constant_offset'
        attack_factor: Scaling factor for poisoning attack
        dataset_source: 'synthetic' or 'hospital'/'csv'
        csv_path: Optional path to custom CSV dataset
    """
    clients, xte, yte, n_features = make_clients(n_clients, non_iid, seed, dataset_source=dataset_source, csv_path=csv_path)
    server = FLServer(n_features)
    key_info = None
    session_key = None
    malicious_set = set(malicious_clients or [])

    if secure:
        e91 = generate_sifted_key(rounds=4096, seed=seed)
        if e91.qber > 0.02:
            raise RuntimeError(f"QBER too high for session key: {e91.qber}")
        session_key = derive_session_key(e91.alice_bits)
        key_info = {"sifted_bits": len(e91.alice_bits), "qber": e91.qber}

    rows = []
    for r in range(1, rounds + 1):
        states, counts, timings = [], [], []
        round_start = time.perf_counter()
        
        for client in clients:
            is_mal = client.client_id in malicious_set
            if secure:
                state, count, timing = secure_update(
                    session_key=session_key, 
                    client=client, 
                    global_state=server.get_global_state(), 
                    round_number=r,
                    is_malicious=is_mal,
                    attack_type=attack_type,
                    attack_factor=attack_factor,
                    server=server
                )
            else:
                start = time.perf_counter()
                if is_mal:
                    state, count = client.train_poisoned(
                        server.get_global_state(), attack_type=attack_type, factor=attack_factor, epochs=8, lr=0.05
                    )
                else:
                    state, count = client.train(server.get_global_state(), epochs=8, lr=0.05)
                train_dur = time.perf_counter() - start
                timing = {
                    "train_time": train_dur, 
                    "encrypt_time": 0.0,
                    "security_verify_decrypt_time": 0.0, 
                    "payload_bytes": 0
                }
            states.append(state)
            counts.append(count)
            timings.append(timing)
            
        agg_start = time.perf_counter()
        server.aggregate(
            states=states, 
            counts=counts, 
            method=aggregation_method, 
            trim_ratio=trim_ratio
        )
        agg_time = time.perf_counter() - agg_start
        
        metrics = server.evaluate_metrics(xte, yte)
        metrics.update({
            "round": r, 
            "total_round_time": time.perf_counter() - round_start,
            "aggregation_time": agg_time,
            "aggregation_method": aggregation_method,
            "secure": int(secure), 
            "clients": n_clients,
            "malicious_count": len(malicious_set),
            "malicious_clients": list(malicious_set),
            "non_iid": int(non_iid)
        })
        metrics["mean_train_time"] = float(np.mean([t["train_time"] for t in timings]))
        metrics["mean_encrypt_time"] = float(np.mean([t["encrypt_time"] for t in timings]))
        metrics["mean_security_time"] = float(np.mean([t["security_verify_decrypt_time"] for t in timings]))
        metrics["total_payload_bytes"] = int(sum(t["payload_bytes"] for t in timings))
        rows.append(metrics)
        
    return rows, key_info
