# lib/auth.py
import os
import hmac
from typing import Optional

from passlib.context import CryptContext

# bcryptを使わない（MissingBackendError/72bytes問題を回避）
pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

_SECRET = os.getenv("APP_SECRET", "dev-secret-change-me")

def hash_password(p: str) -> str:
    # 長さ制限は実質不要だが、極端に長い入力はDoS対策で上限を置く
    p = (p or "").strip()
    if len(p) < 8:
        raise ValueError("パスワードは8文字以上にしてください。")
    if len(p) > 256:
        raise ValueError("パスワードが長すぎます（256文字以内）。")
    return pwd.hash(p)

def verify_password(p: str, hashed: str) -> bool:
    try:
        return pwd.verify(p, hashed)
    except Exception:
        return False

def sign_session(user_id: int) -> str:
    msg = str(user_id).encode("utf-8")
    sig = hmac.new(_SECRET.encode("utf-8"), msg, digestmod="sha256").hexdigest()
    return f"{user_id}.{sig}"

def verify_session(token: Optional[str]) -> Optional[int]:
    if not token or "." not in token:
        return None
    uid_str, sig = token.split(".", 1)
    if not uid_str.isdigit():
        return None
    msg = uid_str.encode("utf-8")
    expected = hmac.new(_SECRET.encode("utf-8"), msg, digestmod="sha256").hexdigest()
    if hmac.compare_digest(sig, expected):
        return int(uid_str)
    return None