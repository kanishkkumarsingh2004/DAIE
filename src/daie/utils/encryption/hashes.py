"""
In-house SHA-256, HMAC, and PBKDF2 hashing implementations.
"""

import struct
from typing import Optional, Union


def _rotr(x: int, n: int) -> int:
    """Rotate right x by n bits for SHA-256"""
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


class SHA256:
    """
    Pure-Python implementation of SHA-256 hash algorithm (FIPS 180-4)
    """

    digest_size = 32
    block_size = 64

    def __init__(self, m: Optional[Union[str, bytes]] = None):
        # Initial hash values
        self._h = [
            0x6A09E667,
            0xBB67AE85,
            0x3C6EF372,
            0xA54FF53A,
            0x510E527F,
            0x9B05688C,
            0x1F83D9AB,
            0x5BE0CD19,
        ]
        self._buf = b""
        self._len = 0
        if m:
            self.update(m)

    def update(self, m: Union[str, bytes]):
        if isinstance(m, str):
            m = m.encode("utf-8")
        self._buf += m
        self._len += len(m)
        while len(self._buf) >= 64:
            self._process(self._buf[:64])
            self._buf = self._buf[64:]

    def _process(self, chunk: bytes):
        w = list(struct.unpack(">16L", chunk)) + [0] * 48
        for i in range(16, 64):
            s0 = _rotr(w[i - 15], 7) ^ _rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
            s1 = _rotr(w[i - 2], 17) ^ _rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
            w[i] = (w[i - 16] + s0 + w[i - 7] + s1) & 0xFFFFFFFF

        a, b, c, d, e, f, g, h = self._h

        # Round constants
        k = [
            0x428A2F98,
            0x71374491,
            0xB5C0FBCF,
            0xE9B5DBA5,
            0x3956C25B,
            0x59F111F1,
            0x923F82A4,
            0xAB1C5ED5,
            0xD807AA98,
            0x12835B01,
            0x243185BE,
            0x550C7DC3,
            0x72BE5D74,
            0x80DEB1FE,
            0x9BDC06A7,
            0xC19BF174,
            0xE49B69C1,
            0xEFBE4786,
            0x0FC19DC6,
            0x240CA1CC,
            0x2DE92C6F,
            0x4A7484AA,
            0x5CB0A9DC,
            0x76F988DA,
            0x983E5152,
            0xA831C66D,
            0xB00327C8,
            0xBF597FC7,
            0xC6E00BF3,
            0xD5A79147,
            0x06CA6351,
            0x14292967,
            0x27B70A85,
            0x2E1B2138,
            0x4D2C6DFC,
            0x53380D13,
            0x650A7354,
            0x766A0ABB,
            0x81C2C92E,
            0x92722C85,
            0xA2BFE8A1,
            0xA81A664B,
            0xC24B8B70,
            0xC76C51A3,
            0xD192E819,
            0xD6990624,
            0xF40E3585,
            0x106AA070,
            0x19A4C116,
            0x1E376C08,
            0x2748774C,
            0x34B0BCB5,
            0x391C0CB3,
            0x4ED8AA4A,
            0x5B9CCA4F,
            0x682E6FF3,
            0x748F82EE,
            0x78A5636F,
            0x84C87814,
            0x8CC70208,
            0x90BEFFFA,
            0xA4506CEB,
            0xBEF9A3F7,
            0xC67178F2,
        ]

        for i in range(64):
            s1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
            ch = (e & f) ^ ((~e) & g)
            t1 = (h + s1 + ch + k[i] + w[i]) & 0xFFFFFFFF
            s0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            t2 = (s0 + maj) & 0xFFFFFFFF
            h = g
            g = f
            f = e
            e = (d + t1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (t1 + t2) & 0xFFFFFFFF

        self._h = [(x + y) & 0xFFFFFFFF for x, y in zip(self._h, [a, b, c, d, e, f, g, h])]

    def digest(self) -> bytes:
        m = self._buf + b"\x80"
        while (len(m) + 8) % 64 != 0:
            m += b"\x00"
        m += struct.pack(">Q", self._len * 8)

        h_orig = list(self._h)
        for i in range(0, len(m), 64):
            self._process(m[i: i + 64])

        res = struct.pack(">8L", *self._h)
        self._h = h_orig
        return res

    def hexdigest(self) -> str:
        return self.digest().hex()


def sha256_hash(m: Union[str, bytes]) -> str:
    """Calculate SHA-256 hash of the given message."""
    return SHA256(m).hexdigest()


def hmac_sha256(key: bytes, msg: bytes) -> bytes:
    """Implement HMAC-SHA256 (RFC 2104)"""
    if len(key) > 64:
        key = SHA256(key).digest()
    if len(key) < 64:
        key = key + b"\x00" * (64 - len(key))

    o_key_pad = bytes(x ^ 0x5C for x in key)
    i_key_pad = bytes(x ^ 0x36 for x in key)

    inner = SHA256(i_key_pad + msg).digest()
    return SHA256(o_key_pad + inner).digest()


def pbkdf2_hmac_sha256(
    password: Union[str, bytes], salt: bytes, iterations: int, dklen: int
) -> bytes:
    """Implement PBKDF2-HMAC-SHA256 (RFC 2898)"""
    password = password.encode("utf-8") if isinstance(password, str) else password

    def F(p, s, c, i):
        u = hmac_sha256(p, s + struct.pack(">I", i))
        res = bytearray(u)
        for _ in range(c - 1):
            u = hmac_sha256(p, u)
            for j in range(len(res)):
                res[j] ^= u[j]
        return bytes(res)

    t = b""
    for i in range(1, (dklen + 31) // 32 + 1):
        t += F(password, salt, iterations, i)
    return t[:dklen]


def constant_time_compare(val1: bytes, val2: bytes) -> bool:
    """Constant-time comparison to avoid timing attacks."""
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= x ^ y
    return result == 0


def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """Generate hash of data. Currently only supports sha256 in-house."""
    return sha256_hash(data)


def verify_hash(data: str, expected_hash: str, algorithm: str = "sha256") -> bool:
    """Verify data matches expected hash"""
    return generate_hash(data, algorithm) == expected_hash
