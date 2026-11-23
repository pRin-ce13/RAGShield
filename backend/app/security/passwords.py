"""Cryptographic Password Hashing and Verification for RAGShield.

Uses native bcrypt for secure, salted password hashing adhering to NIST SP 800-63B.
"""

import bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Computes a secure bcrypt hash with a cryptographically random salt.
    
    Truncates input to 72 bytes in conformance with the bcrypt specification.
    """
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")
