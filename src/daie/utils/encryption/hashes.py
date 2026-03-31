"""
In-house SHA-256, HMAC, and PBKDF2 hashing implementations.
"""

import struct
from typing import Dict, List, Optional, Union


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
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
        ]
        self._buf = b''
        self._len = 0
        if m:
            self.update(m)

    def update(self, m: Union[str, bytes]):
        if isinstance(m, str):
            m = m.encode('utf-8')
        self._buf += m
        self._len += len(m)
        while len(self._buf) >= 64:
            self._process(self._buf[:64])
            self._buf = self._buf[64:]

    def _process(self, chunk: bytes):
        w = list(struct.unpack('>16L', chunk)) + [0] * 48
        for i in range(16, 64):
            s0 = _rotr(w[i-15], 7) ^ _rotr(w[i-15], 18) ^ (w[i-15] >> 3)
            s1 = _rotr(w[i-2], 17) ^ _rotr(w[i-2], 19) ^ (w[i-2] >> 10)
            w[i] = (w[i-16] + s0 + w[i-7] + s1) & 0xFFFFFFFF
        
        a, b, c, d, e, f, g, h = self._h
        
        # Round constants
        k = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
            0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
            0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
            0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
            0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
            0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
            0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
            0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
            0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
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
        m = self._buf + b'\x80'
        while (len(m) + 8) % 64 != 0:
            m += b'\x00'
        m += struct.pack('>Q', self._len * 8)
        
        h_orig = list(self._h)
        for i in range(0, len(m), 64):
            self._process(m[i:i+64])
        
        res = struct.pack('>8L', *self._h)
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
        key = key + b'\x00' * (64 - len(key))
    
    o_key_pad = bytes(x ^ 0x5c for x in key)
    i_key_pad = bytes(x ^ 0x36 for x in key)
    
    inner = SHA256(i_key_pad + msg).digest()
    return SHA256(o_key_pad + inner).digest()


def pbkdf2_hmac_sha256(password: Union[str, bytes], salt: bytes, iterations: int, dklen: int) -> bytes:
    """Implement PBKDF2-HMAC-SHA256 (RFC 2898)"""
    password = password.encode('utf-8') if isinstance(password, str) else password
    
    def F(p, s, c, i):
        u = hmac_sha256(p, s + struct.pack('>I', i))
        res = bytearray(u)
        for _ in range(c - 1):
            u = hmac_sha256(p, u)
            for j in range(len(res)):
                res[j] ^= u[j]
        return bytes(res)
    
    t = b''
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
