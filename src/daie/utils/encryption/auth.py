"""
Authentication and security-related utility functions.
"""

import re
import os
from typing import Optional


def generate_salt(length: int = 16) -> bytes:
    """Generate a new secure random salt"""
    return os.urandom(length)


def is_strong_password(password: str) -> bool:
    """
    Check if a password meets strength requirements:
    - Min 12 chars
    - Uppercase, lowercase, numbers, special chars
    """
    if len(password) < 12:
        return False
    
    # Check for complexity
    patterns = [
        r"[A-Z]",      # Uppercase
        r"[a-z]",      # Lowercase
        r"[0-9]",      # Digit
        r"[!@#$%^&*(),.?\":{}|<>]"  # Special character
    ]
    
    return all(re.search(p, password) for p in patterns)


def sanitize_input(text: str) -> str:
    """Sanitize input string by removing common dangerous characters"""
    if not text:
        return ""
    # Basic XSS protection
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    # Basic SQL injection (very basic, use parameterized queries instead)
    text = text.replace("'", "''").replace(";", "")
    return text


def validate_password_strength(password: str) -> bool:
    """Validate password strength and log reason if weak (alias for is_strong_password)"""
    return is_strong_password(password)


def mask_secret(secret: str, show_last: int = 4) -> str:
    """Mask secret with '*' showing last n characters"""
    if not secret:
        return ""
    if len(secret) <= show_last:
        return "*" * len(secret)
    return "*" * (len(secret) - show_last) + secret[-show_last:]


def obfuscate_email(email: str) -> str:
    """Obfuscate email address for display"""
    if not email or "@" not in email:
        return email
    
    parts = email.split("@")
    name = parts[0]
    domain = parts[1]
    
    if len(name) <= 2:
        masked_name = "*" * len(name)
    else:
        masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
    
    return f"{masked_name}@{domain}"
