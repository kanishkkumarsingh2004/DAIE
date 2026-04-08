"""
In-house ID generation utilities, including UUIDv7.
"""

import os
import time
import random
import string
import secrets
from typing import Optional


def uuid7() -> str:
    """
    Generate a UUID v7 (time-ordered UUID) as a string.

    UUID v7 format:
    - 48 bits: timestamp in milliseconds
    - 4 bits: version (0111 for v7)
    - 12 bits: random
    - 2 bits: variant (10)
    - 62 bits: random

    Returns:
    - 36-character hyphenated UUID string (e.g., 018c65f2-9a3d-7b2e-a1b2-c3d4e5f6a7b8)
    """
    # Get current timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)

    # Generate random bytes using os.urandom for cryptographic randomness
    # We need 10 random bytes (80 bits)
    random_bytes = os.urandom(10)

    # Convert timestamp to 6 bytes (48 bits)
    timestamp_bytes = timestamp_ms.to_bytes(6, byteorder="big")

    # Combine with random bytes
    # total 16 bytes (128 bits)
    uuid_bytes = bytearray(timestamp_bytes + random_bytes)

    # Set version bits (bits 4-7 of byte 6 to 0111)
    # Byte 6: TTTT VVVV (T = timestamp, V = version)
    uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x70  # Version 7

    # Set variant bits (bits 6-7 of byte 8 to 10)
    # Byte 8: VV RRRRRR (V = variant, R = random)
    uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80  # Variant 10

    # Convert to hex string with hyphens
    h = uuid_bytes.hex()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


def generate_id() -> str:
    """
    Generate a unique ID using UUID v7.
    """
    return uuid7()


def secure_random_string(length: int = 32) -> str:
    """Generate a cryptographically secure random string"""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_api_key(prefix: str = "daie_") -> str:
    """Generate a new API key with prefix"""
    return f"{prefix}{secure_random_string(32)}"
