"""
Auth Service — password hashing and JWT token management.

Copy this file into your project's backend/ directory.
"""

import secrets
from datetime import datetime, timedelta
from pathlib import Path

import bcrypt
import jwt

# JWT secret stored in a file so it survives restarts but isn't committed
_SECRET_PATH = Path(__file__).parent / ".jwt_secret"
_JWT_ALGORITHM = "HS256"
_TOKEN_EXPIRY_HOURS = 24


def get_or_create_secret() -> str:
    """Read JWT secret from file, or generate and save a new one."""
    if _SECRET_PATH.exists():
        return _SECRET_PATH.read_text(encoding="utf-8").strip()
    secret = secrets.token_hex(32)
    _SECRET_PATH.write_text(secret, encoding="utf-8")
    return secret


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_id: int, expires_hours: int = _TOKEN_EXPIRY_HOURS) -> str:
    """Create a JWT token for a user."""
    secret = get_or_create_secret()
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=expires_hours),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify a JWT token. Returns the payload or raises jwt.InvalidTokenError."""
    secret = get_or_create_secret()
    return jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
