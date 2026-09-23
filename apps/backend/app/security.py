from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from secrets import compare_digest, token_hex
import jwt
from app.config import settings


def hash_password(password: str) -> str:
    salt = token_hex(16)
    digest = pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    actual = pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return compare_digest(actual, digest)


def make_token(user_id: str, kind: str, days: int = 0, minutes: int = 0) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": user_id, "typ": kind, "exp": now + timedelta(days=days, minutes=minutes)}, settings.secret_key, algorithm="HS256")


def tokens(user_id: str) -> dict[str, str]:
    return {"access_token": make_token(user_id, "access", minutes=120), "refresh_token": make_token(user_id, "refresh", days=30), "token_type": "bearer"}


def decode(token: str, kind: str) -> str:
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    if payload.get("typ") != kind:
        raise jwt.InvalidTokenError()
    return str(payload["sub"])

