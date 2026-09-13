from flask import Blueprint, request, g
from extensions import db
from models import User, Cart, Wishlist
from utils.responses import success, error
from utils.validators import is_valid_email, require_fields
from utils.jwt_utils import generate_token
from middleware.auth_middleware import token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    missing = require_fields(data, ["name", "email", "password"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)

    name = data["name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]
    phone = (data.get("phone") or "").strip() or None

    if not is_valid_email(email):
        return error("Please enter a valid email address.", 400)
    if len(password) < 6:
        return error("Password must be at least 6 characters long.", 400)

    if User.query.filter_by(email=email).first():
        return error("An account with this email already exists.", 409)

    user = User(name=name, email=email, phone=phone, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # get user.id before commit

    # Every user gets an empty cart and wishlist created up front.
    db.session.add(Cart(user_id=user.id))
    db.session.add(Wishlist(user_id=user.id))
    db.session.commit()

    token = generate_token(user.id, user.role)
    return success(
        "Account created successfully.",
        {"token": token, "user": user.to_dict()},
        201,
    )


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["email", "password"])
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)

    email = data["email"].strip().lower()
    password = data["password"]

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return error("Invalid email or password.", 401)
    if not user.is_active:
        return error("This account has been deactivated. Contact support.", 403)

    token = generate_token(user.id, user.role)
    return success("Login successful.", {"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@token_required
def me():
    return success("Current user fetched.", {"user": g.current_user.to_dict()})
