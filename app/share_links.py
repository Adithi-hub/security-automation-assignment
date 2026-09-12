import secrets
from datetime import datetime, timedelta, timezone

from auth import get_password_hash, verify_password


def generate_share_token() -> str:
    return secrets.token_urlsafe(32)


def get_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=24)


def hash_share_password(password: str) -> str:
    return get_password_hash(password)


def check_share_password(password: str, password_hash: str) -> bool:
    return verify_password(password, password_hash)