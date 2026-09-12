"""
Cryptographic and Security Utilities.
Provides:
- JWT authentication
- Password hashing (PBKDF2-HMAC-SHA256)
- Field-level encryption (Fernet / AES)
- Biometric template hashing
- Tamper-evident audit chain hashing
"""

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from cryptography.fernet import Fernet
from app.core.config import settings

# Fernet cipher for sensitive demographic field encryption
def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY.encode()
    # Ensure key is valid 32-byte base64
    if len(key) != 44:
        # Generate deterministic key from SECRET_KEY if invalid
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_field(plain_text: str) -> str:
    """Encrypts a sensitive string field using Fernet AES."""
    if not plain_text:
        return ""
    cipher = _get_fernet()
    return cipher.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_field(cipher_text: str) -> str:
    """Decrypts an encrypted string field."""
    if not cipher_text:
        return ""
    try:
        cipher = _get_fernet()
        return cipher.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return "[Decryption Failed]"


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a secure salt."""
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verifies a password against the stored salt$hash."""
    try:
        salt_hex, hash_hex = hashed.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and verifies a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None


def hash_biometric_template(embedding_bytes: bytes) -> str:
    """
    Computes an irreversible cryptographic HMAC-SHA256 hash of the voice template.
    Ensures that raw biometric embeddings cannot be reversed to vocal features.
    """
    return hmac.new(settings.SECRET_KEY.encode(), embedding_bytes, hashlib.sha256).hexdigest()


def compute_audit_hash(prev_hash: str, timestamp_iso: str, details_str: str) -> str:
    """
    Generates a tamper-evident blockchain-style hash for audit log chaining.
    """
    record = f"{prev_hash}|{timestamp_iso}|{details_str}"
    return hashlib.sha256(record.encode("utf-8")).hexdigest()
