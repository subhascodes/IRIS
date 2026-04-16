"""
Admin Authentication Module
=============================
Simple login interface for admin access control.

Credentials are stored in a simple JSON file (for demo).
For production, replace with proper auth service (OAuth, LDAP, etc).
"""

import json
import hashlib
from pathlib import Path


CREDENTIALS_FILE = Path("data/credentials.json")


def _hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def _load_credentials() -> dict:
    """Load admin credentials from file."""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_credentials(credentials: dict) -> None:
    """Save admin credentials to file."""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials, f, indent=2)


def initialize_default_admin() -> None:
    """Initialize default admin credentials if none exist."""
    creds = _load_credentials()
    
    if not creds:
        # Default: username=admin, password=admin
        default_admin = {
            "admin": _hash_password("admin")
        }
        _save_credentials(default_admin)


def verify_credentials(username: str, password: str) -> bool:
    """Verify username and password."""
    creds = _load_credentials()
    
    if username not in creds:
        return False
    
    return creds[username] == _hash_password(password)


def get_admin_list() -> list:
    """Get list of admin usernames."""
    return list(_load_credentials().keys())


def create_admin(username: str, password: str) -> bool:
    """Create a new admin user (existing user won't be overwritten)."""
    creds = _load_credentials()
    
    if username in creds:
        return False  # User already exists
    
    creds[username] = _hash_password(password)
    _save_credentials(creds)
    return True


def delete_admin(username: str) -> bool:
    """Delete an admin user."""
    creds = _load_credentials()
    
    if username not in creds:
        return False
    
    del creds[username]
    _save_credentials(creds)
    return True


def change_password(username: str, old_password: str, new_password: str) -> bool:
    """Change password for an admin user."""
    if not verify_credentials(username, old_password):
        return False
    
    creds = _load_credentials()
    creds[username] = _hash_password(new_password)
    _save_credentials(creds)
    return True
