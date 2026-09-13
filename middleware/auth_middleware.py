from functools import wraps
import jwt
from flask import request, g
from utils.jwt_utils import decode_token
from utils.responses import error
from models import User


def _extract_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


def token_required(f):
    """Requires a valid JWT. Sets g.current_user for the route to use."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return error("Authentication token is missing.", 401)
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error("Session expired. Please log in again.", 401)
        except jwt.InvalidTokenError:
            return error("Invalid authentication token.", 401)

        user = User.query.get(int(payload["sub"]))
        if not user or not user.is_active:
            return error("Account not found or deactivated.", 401)

        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Must be used AFTER token_required (or combined) - checks role == admin."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return error("Authentication token is missing.", 401)
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error("Session expired. Please log in again.", 401)
        except jwt.InvalidTokenError:
            return error("Invalid authentication token.", 401)

        user = User.query.get(int(payload["sub"]))
        if not user or not user.is_active:
            return error("Account not found or deactivated.", 401)
        if user.role != "admin":
            return error("Admin access required.", 403)

        g.current_user = user
        return f(*args, **kwargs)

    return decorated
