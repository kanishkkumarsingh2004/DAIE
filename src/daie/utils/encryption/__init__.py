"""
Encryption and security utilities for the Decentralized AI Library.
"""

from daie.utils.encryption.auth import (generate_salt, is_strong_password,
                                       mask_secret, obfuscate_email,
                                       sanitize_input,
                                       validate_password_strength)
from daie.utils.encryption.ciphers import (decrypt_data, encrypt_data,
                                          generate_encryption_key,
                                          chacha20_crypt)
from daie.utils.encryption.hashes import (SHA256, constant_time_compare,
                                         generate_hash, hmac_sha256,
                                         pbkdf2_hmac_sha256, sha256_hash,
                                         verify_hash)
from daie.utils.encryption.ids import (generate_api_key, generate_id,
                                      secure_random_string, uuid7)

__all__ = [
    "SHA256",
    "sha256_hash",
    "hmac_sha256",
    "pbkdf2_hmac_sha256",
    "constant_time_compare",
    "generate_hash",
    "verify_hash",
    "encrypt_data",
    "decrypt_data",
    "generate_encryption_key",
    "chacha20_crypt",
    "uuid7",
    "generate_id",
    "secure_random_string",
    "generate_api_key",
    "generate_salt",
    "is_strong_password",
    "validate_password_strength",
    "sanitize_input",
    "mask_secret",
    "obfuscate_email",
]
