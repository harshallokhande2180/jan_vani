"""
Authentication and security module for Jan-Vani backend.
Implements password hashing with bcrypt, token generation, and
role-based access control as required in Section 5.4.
"""

import time
import secrets
from typing import Optional, Dict, Any
import bcrypt

# In-memory session store (simple & robust for demo)
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(officer_data: Dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    ACTIVE_SESSIONS[token] = {
        "email": officer_data["email"],
        "full_name": officer_data["full_name"],
        "role": officer_data["role"],
        "assigned_ward": officer_data["assigned_ward"],
        "created_at": time.time()
    }
    return token

def get_session(token: str) -> Optional[Dict[str, Any]]:
    return ACTIVE_SESSIONS.get(token)

def revoke_session(token: str) -> bool:
    if token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
        return True
    return False
