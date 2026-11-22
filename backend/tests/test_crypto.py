import pytest
from cryptography.exceptions import InvalidTag
from crypto.aes_crypto import decrypt_json, encrypt_json
from crypto.hmac_auth import canonical_bytes, create_message_mac, verify_hmac
from crypto.key_manager import bits_to_bytes, derive_session_key


def test_key_derivation_is_32_bytes(): assert len(derive_session_key([1,0]*128))==32

def test_aes_round_trip():
    key=derive_session_key([1,0]*128); payload={"client_id":"c1","round":1,"value":42}
    encrypted=encrypt_json(key,payload,b"c1:1")
    assert decrypt_json(key,encrypted,b"c1:1")==payload

def test_aes_associated_data_rejects_context_tampering():
    key=derive_session_key([1,0]*128); enc=encrypt_json(key,{"x":1},b"c1:1")
    with pytest.raises(InvalidTag): decrypt_json(key,enc,b"c1:2")

def test_hmac_accepts_and_rejects_tampering():
    key=derive_session_key([1,0]*128); m={"client_id":"c1","round":1}; tag=create_message_mac(key,m)
    assert verify_hmac(key,canonical_bytes(m),tag)
    assert not verify_hmac(key,canonical_bytes({"client_id":"c1","round":2}),tag)

def test_wrong_aes_key_fails():
    k1=derive_session_key([1,0]*128); k2=derive_session_key([0,1]*128)
    enc=encrypt_json(k1,{"value":1})
    with pytest.raises(InvalidTag): decrypt_json(k2,enc)

def test_bits_to_bytes_validation():
    assert bits_to_bytes([1,0,1,0,0,0,0,1])==b'\xa1'
    with pytest.raises(ValueError): bits_to_bytes([])
    with pytest.raises(ValueError): bits_to_bytes([2])


def test_replay_protection_rejects_duplicates_and_stale():
    from crypto.replay_detector import ReplayDetector
    detector = ReplayDetector(max_round_window=1, ttl_seconds=60.0)

    # Valid message
    ok, reason = detector.check_and_record("client1", round_number=1, message_id="m1")
    assert ok and reason == "OK"

    # Replay of exact message_id
    ok, reason = detector.check_and_record("client1", round_number=1, message_id="m1")
    assert not ok and "Replay detected" in reason

    # Stale round
    ok, reason = detector.check_and_record("client1", round_number=1, message_id="m2", current_server_round=3)
    assert not ok and "Stale round" in reason

    # Out of window future round
    ok, reason = detector.check_and_record("client1", round_number=10, message_id="m3", current_server_round=1)
    assert not ok and "Future round" in reason

