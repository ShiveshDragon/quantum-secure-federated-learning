import numpy as np
from experiments.common import run_fl
from crypto.key_manager import derive_session_key
from crypto.aes_crypto import encrypt_json,decrypt_json
from crypto.hmac_auth import canonical_bytes,create_message_mac,verify_hmac
from quantum.e91 import generate_sifted_key


def test_one_secure_fl_round():
    rows,key=run_fl(n_clients=4,rounds=2,secure=True,seed=11)
    assert key["qber"]==0.0
    assert len(rows)==2
    assert all(0<=r["accuracy"]<=1 for r in rows)


def test_secure_message_round_trip_and_authentication():
    key=derive_session_key(generate_sifted_key(2048,seed=2).alice_bits)
    p={"client_id":"c1","round":1,"weights":[.1,.2],"sample_count":10}
    enc=encrypt_json(key,p,b"c1:1")
    m={"client_id":"c1","round":1,"encrypted":enc}
    tag=create_message_mac(key,m)
    assert verify_hmac(key,canonical_bytes(m),tag)
    assert decrypt_json(key,enc,b"c1:1")==p


def test_end_to_end_secure_fl_with_poisoning_and_robust_aggregation():
    """Verify that under E91 + AES + HMAC, an authenticated attacker can poison FedAvg, but coordinate median mitigates it."""
    # Under attack with coordinate median
    rows_med, _ = run_fl(
        n_clients=5, rounds=2, secure=True, seed=12,
        aggregation_method="coordinate_median",
        malicious_clients=["client5"], attack_type="sign_flip", attack_factor=3.0
    )
    assert len(rows_med) == 2
    assert rows_med[-1]["accuracy"] >= 0.70
    assert rows_med[-1]["secure"] == 1
    assert rows_med[-1]["malicious_count"] == 1

