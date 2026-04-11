"""
In-house ChaCha20 cipher implementation.
"""

import base64
import os
import struct

from daie.utils.encryption.hashes import constant_time_compare, hmac_sha256


def _rotate_left(v: int, c: int) -> int:
    """Rotate left v by c bits for ChaCha20"""
    return ((v << c) & 0xFFFFFFFF) | (v >> (32 - c))


def _chacha20_quarter_round(x: list, a: int, b: int, c: int, d: int):
    """ChaCha20 quarter round"""
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = _rotate_left(x[d] ^ x[a], 16)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = _rotate_left(x[b] ^ x[c], 12)
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = _rotate_left(x[d] ^ x[a], 8)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = _rotate_left(x[b] ^ x[c], 7)


def _chacha20_block(key: bytes, counter: int, nonce: bytes) -> bytes:
    """Generate a single ChaCha20 block (64 bytes)"""
    constants = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]
    ctx = list(constants)
    ctx.extend(struct.unpack("<8L", key))
    ctx.append(counter & 0xFFFFFFFF)
    ctx.extend(struct.unpack("<3L", nonce))

    original = list(ctx)

    for _ in range(10):  # 20 rounds
        _chacha20_quarter_round(ctx, 0, 4, 8, 12)
        _chacha20_quarter_round(ctx, 1, 5, 9, 13)
        _chacha20_quarter_round(ctx, 2, 6, 10, 14)
        _chacha20_quarter_round(ctx, 3, 7, 11, 15)
        _chacha20_quarter_round(ctx, 0, 5, 10, 15)
        _chacha20_quarter_round(ctx, 1, 6, 11, 12)
        _chacha20_quarter_round(ctx, 2, 7, 8, 13)
        _chacha20_quarter_round(ctx, 3, 4, 9, 14)

    res = [(ctx[i] + original[i]) & 0xFFFFFFFF for i in range(16)]
    return struct.pack("<16L", *res)


def chacha20_crypt(data: bytes, key: bytes, nonce: bytes, counter: int = 0) -> bytes:
    """Encrypt/Decrypt data using ChaCha20"""
    res = bytearray()
    for i in range(0, len(data), 64):
        keystream = _chacha20_block(key, counter + (i // 64), nonce)
        block = data[i: i + 64]
        for j in range(len(block)):
            res.append(block[j] ^ keystream[j])
    return bytes(res)


def generate_encryption_key() -> bytes:
    """Generate a new encryption key (32 bytes)"""
    return os.urandom(32)


def encrypt_data(data: str, key: bytes) -> str:
    """
    Encrypt data using authenticated ChaCha20
    Format: base64(nonce + hmac + encrypted_data)
    """
    nonce = os.urandom(12)
    data_bytes = data.encode("utf-8")
    encrypted_data = chacha20_crypt(data_bytes, key, nonce)

    # Calculate HMAC for authentication
    mac = hmac_sha256(key, nonce + encrypted_data)

    combined = nonce + mac + encrypted_data
    return base64.urlsafe_b64encode(combined).decode("utf-8")


def decrypt_data(encrypted_data: str, key: bytes) -> str:
    """Decrypt data using authenticated ChaCha20"""
    try:
        combined = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
        if len(combined) < 12 + 32:
            raise ValueError("Data too short")

        nonce = combined[:12]
        mac = combined[12:44]
        actual_encrypted_data = combined[44:]

        # Verify HMAC
        expected_mac = hmac_sha256(key, nonce + actual_encrypted_data)

        if not constant_time_compare(mac, expected_mac):
            raise Exception("Authentication failed: data modified")

        decrypted_data = chacha20_crypt(actual_encrypted_data, key, nonce)
        return decrypted_data.decode("utf-8")
    except Exception as e:
        raise Exception(f"Decryption failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# X25519 Key Exchange (RFC 7748)
# ─────────────────────────────────────────────────────────────────────────────


P = 2**255 - 19


def _fe_unserialize(bs: bytes) -> int:
    return (
        struct.unpack("<32B", bs)[0]
        if len(bs) == 1
        else int.from_bytes(bs, "little") & ((1 << 255) - 1)
    )


def _fe_serialize(n: int) -> bytes:
    return (n % P).to_bytes(32, "little")


def x25519_scalar_mult(scalar: bytes, u_coord: bytes) -> bytes:
    """X25519 scalar multiplication as defined in RFC 7748"""
    u = int.from_bytes(u_coord, "little") & ((1 << 255) - 1)
    k = int.from_bytes(scalar, "little")

    # Montgomery ladder
    x_1 = u
    x_2, z_2 = 1, 0
    x_3, z_3 = u, 1
    swap = 0

    for t in reversed(range(255)):
        k_t = (k >> t) & 1
        swap ^= k_t
        if swap:
            x_2, x_3 = x_3, x_2
            z_2, z_3 = z_3, z_2
        swap = k_t

        A = (x_2 + z_2) % P
        AA = (A * A) % P
        B = (x_2 - z_2) % P
        BB = (B * B) % P
        E = (AA - BB) % P
        C = (x_3 + z_3) % P
        D = (x_3 - z_3) % P
        DA = (D * A) % P
        CB = (C * B) % P
        x_3 = ((DA + CB) ** 2) % P
        z_3 = (x_1 * (DA - CB) ** 2) % P
        x_2 = (AA * BB) % P
        z_2 = (E * (AA + 121665 * E)) % P

    if swap:
        x_2, x_3 = x_3, x_2
        z_2, z_3 = z_3, z_2

    return _fe_serialize((x_2 * pow(z_2, P - 2, P)) % P)


def generate_x25519_keypair() -> tuple[bytes, bytes]:
    """Generate X25519 private and public keys"""
    priv = os.urandom(32)
    # Clamp the private key
    priv_list = list(priv)
    priv_list[0] &= 248
    priv_list[31] &= 127
    priv_list[31] |= 64
    clamped_priv = bytes(priv_list)

    # Base point is 9
    base_point = b"\x09" + b"\x00" * 31
    pub = x25519_scalar_mult(clamped_priv, base_point)
    return clamped_priv, pub


def derive_shared_secret(private_key: bytes, remote_public_key: bytes) -> bytes:
    """Derive SHA256 hashed shared secret using X25519"""
    secret = x25519_scalar_mult(private_key, remote_public_key)
    # Use SHA256 to derive the actual symmetric key from the shared secret
    from daie.utils.encryption.hashes import hmac_sha256

    return hmac_sha256(b"daie_secret_salt", secret)
