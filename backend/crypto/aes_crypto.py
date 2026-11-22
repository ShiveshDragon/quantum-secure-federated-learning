import base64
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def normalize_key(key: bytes) -> bytes:
    if not isinstance(key, bytes) or not key:
        raise ValueError("key must be non-empty bytes")
    if len(key) == 32:
        return key
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=b"quantum-fl-iot-aes256").derive(key)


def encrypt_bytes(key: bytes, plaintext: bytes, associated_data: bytes = b""):
    nonce = os.urandom(12)
    return nonce, AESGCM(normalize_key(key)).encrypt(nonce, plaintext, associated_data)


def decrypt_bytes(key, nonce, ciphertext, associated_data=b""):
    return AESGCM(normalize_key(key)).decrypt(nonce, ciphertext, associated_data)


def encrypt_json(key, payload, associated_data=b""):
    plaintext = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    nonce, ciphertext = encrypt_bytes(key, plaintext, associated_data)
    return {"nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode()}


def decrypt_json(key, encrypted, associated_data=b""):
    nonce = base64.b64decode(encrypted["nonce"])
    ciphertext = base64.b64decode(encrypted["ciphertext"])
    return json.loads(decrypt_bytes(key, nonce, ciphertext, associated_data).decode())
