import hashlib
import hmac
import json


def canonical_bytes(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def create_hmac(key: bytes, data: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def verify_hmac(key: bytes, data: bytes, tag: str) -> bool:
    return hmac.compare_digest(create_hmac(key, data), tag)


def create_message_mac(key: bytes, message_without_hmac: dict) -> str:
    return create_hmac(key, canonical_bytes(message_without_hmac))
