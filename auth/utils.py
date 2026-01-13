"""Authentication utility functions."""

import re
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import config

def hash_password(password):
    """Hash a password using Werkzeug's PBKDF2."""
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password_hash, password):
    """Verify a password against its hash."""
    return check_password_hash(password_hash, password)

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Validate password strength.
    Requirements: Min 8 characters, 1 uppercase, 1 lowercase, 1 number
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"

    return True, "Password is valid"

def encrypt_credential(plaintext):
    """Encrypt portal credentials."""
    if not config.ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY not set in environment")

    key = config.ENCRYPTION_KEY.encode() if isinstance(config.ENCRYPTION_KEY, str) else config.ENCRYPTION_KEY
    f = Fernet(key)
    return f.encrypt(plaintext.encode()).decode()

def decrypt_credential(encrypted):
    """Decrypt portal credentials."""
    if not config.ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY not set in environment")

    key = config.ENCRYPTION_KEY.encode() if isinstance(config.ENCRYPTION_KEY, str) else config.ENCRYPTION_KEY
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()
