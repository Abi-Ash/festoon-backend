import jwt
from datetime import datetime, timezone
from flask import current_app


def generate_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token: str):
    """Returns the decoded payload dict, or raises jwt exceptions on failure."""
    return jwt.decode(
        token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
    )
