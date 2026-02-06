"""
Encryption and security utility functions
"""

import os
import hashlib
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_encryption_key() -> bytes:
    """
    Generate a new encryption key

    Returns:
        Generated encryption key
    """
    return Fernet.generate_key()


def encrypt_data(data: str, key: bytes) -> str:
    """
    Encrypt data using Fernet symmetric encryption

    Args:
        data: Data to encrypt (must be string)
        key: Encryption key

    Returns:
        Encrypted data as base64 string
    """
    try:
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
    except Exception as e:
        raise Exception(f"Encryption failed: {e}")


def decrypt_data(encrypted_data: str, key: bytes) -> str:
    """
    Decrypt data using Fernet symmetric encryption

    Args:
        encrypted_data: Encrypted data as base64 string
        key: Encryption key

    Returns:
        Decrypted data
    """
    try:
        fernet = Fernet(key)
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted_data = fernet.decrypt(decoded_data)
        return decrypted_data.decode('utf-8')
    except Exception as e:
        raise Exception(f"Decryption failed: {e}")


def generate_hash(data: str, algorithm: str = 'sha256') -> str:
    """
    Generate hash of data

    Args:
        data: Data to hash
        algorithm: Hash algorithm (sha256, sha1, md5)

    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data.encode('utf-8'))
    return hash_obj.hexdigest()


def verify_hash(data: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """
    Verify data matches expected hash

    Args:
        data: Data to verify
        expected_hash: Expected hash
        algorithm: Hash algorithm

    Returns:
        True if hash matches, False otherwise
    """
    return generate_hash(data, algorithm) == expected_hash


def generate_salt(size: int = 16) -> bytes:
    """
    Generate a random salt

    Args:
        size: Size of salt in bytes

    Returns:
        Random salt
    """
    return os.urandom(size)


def derive_key(password: str, salt: bytes, key_length: int = 32, iterations: int = 100000) -> bytes:
    """
    Derive a key from password using PBKDF2

    Args:
        password: Password to derive key from
        salt: Salt value
        key_length: Length of derived key
        iterations: Number of iterations

    Returns:
        Derived key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_length,
        salt=salt,
        iterations=iterations
    )
    return kdf.derive(password.encode('utf-8'))


def secure_random_string(length: int = 32) -> str:
    """
    Generate a secure random string

    Args:
        length: Length of string

    Returns:
        Secure random string
    """
    return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8')[:length]


def is_strong_password(password: str, min_length: int = 8, require_special: bool = True) -> bool:
    """
    Check if password is strong

    Args:
        password: Password to check
        min_length: Minimum length
        require_special: Whether to require special characters

    Returns:
        True if password is strong, False otherwise
    """
    if len(password) < min_length:
        return False

    # Check for at least one uppercase letter
    if not any(c.isupper() for c in password):
        return False

    # Check for at least one lowercase letter
    if not any(c.islower() for c in password):
        return False

    # Check for at least one digit
    if not any(c.isdigit() for c in password):
        return False

    if require_special:
        import re
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False

    return True


def sanitize_input(input_str: str, allowed_chars: str = None) -> str:
    """
    Sanitize input to prevent injection attacks

    Args:
        input_str: Input string to sanitize
        allowed_chars: Optional regex pattern of allowed characters

    Returns:
        Sanitized string
    """
    if allowed_chars:
        import re
        return re.sub(f'[^\\{allowed_chars}]', '', input_str)
    else:
        return input_str.strip()


def validate_password_strength(password: str, min_length: int = 8) -> list:
    """
    Validate password strength and provide feedback

    Args:
        password: Password to validate
        min_length: Minimum required length

    Returns:
        List of validation errors
    """
    errors = []

    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    import re
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    return errors


def generate_api_key(prefix: str = "dai", length: int = 32) -> str:
    """
    Generate a secure API key

    Args:
        prefix: Optional prefix
        length: Length of random part

    Returns:
        API key string
    """
    random_part = secure_random_string(length)
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def mask_secret(secret: str, show_chars: int = 4) -> str:
    """
    Mask a secret string for display

    Args:
        secret: Secret to mask
        show_chars: Number of characters to show at beginning and end

    Returns:
        Masked secret
    """
    if len(secret) <= show_chars * 2:
        return '*' * len(secret)

    start = secret[:show_chars]
    end = secret[-show_chars:]
    mask = '*' * (len(secret) - show_chars * 2)
    return f"{start}{mask}{end}"


def obfuscate_email(email: str) -> str:
    """
    Obfuscate email address for display

    Args:
        email: Email address to obfuscate

    Returns:
        Obfuscated email
    """
    try:
        username, domain = email.split('@', 1)
        if len(username) <= 2:
            return f"{username}@***"
        return f"{username[:2]}***@{domain}"
    except Exception:
        return email
