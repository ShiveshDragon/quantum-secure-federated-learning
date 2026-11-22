import hashlib


def bits_to_bytes(bits):
    bits = [int(x) for x in bits]
    if not bits:
        raise ValueError("empty bit sequence")
    if any(x not in (0, 1) for x in bits):
        raise ValueError("bits must contain only 0 or 1")
    padded = bits + [0] * ((8 - len(bits) % 8) % 8)
    return bytes(sum(padded[i + j] << (7 - j) for j in range(8))
                 for i in range(0, len(padded), 8))


def derive_session_key(raw_key_bits):
    """Prototype privacy-amplification placeholder using SHA-256.

    A production E91 deployment needs authenticated reconciliation and
    finite-key privacy amplification. Here SHA-256 acts as a deterministic
    compression/KDF step for the simulation.
    """
    return hashlib.sha256(bits_to_bytes(raw_key_bits)).digest()
