"""
Authentication utilities for simple username/password auth
"""
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional
from ..config import Settings

settings = Settings()

# Simple password hashing (you can upgrade to bcrypt later)
def hash_password(password: str) -> str:
    """Hash a password with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{pwd_hash.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, pwd_hash = hashed.split(':')
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex() == pwd_hash
    except:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)  # Default 24 hours
    
    to_encode.update({"exp": expire})
    
    # Use a simple secret key (you can make this more secure later)
    secret_key = getattr(settings, 'SECRET_KEY', 'your-secret-key-change-this')
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        secret_key = getattr(settings, 'SECRET_KEY', 'your-secret-key-change-this')
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None
