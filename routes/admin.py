from flask import Blueprint, request
from sqlalchemy import func, or_
from extensions import db
from models import User, Product, Order, ORDER_STATUSES
from utils.responses import success, error
from middleware.auth_middleware import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/products")
@admin_required
def list_all_products():
    """
    Admin product listing - unlike the public /api/products endpoint this
    includes inactive (soft-deleted/deactivated) products too, so admins
    can find and reactivate them.
    """
    query = Product.query

    search = request.args.get("search")
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(Product.name.ilike(like), Product.description.ilike(like)))

    category_id = request.args.get("category_id", type=int)
    if category_id:
        query = query.filter(Product.category_id == category_id)

    status = request.args.get("status")  # "active" | "inactive"
    if status == "active":
        query = query.filter(Product.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(Product.is_active.is_(False))

    products = query.order_by(Product.created_at.desc()).all()
    return success("Products fetched.", [p.to_dict() for p in products])


@admin_bp.get("/dashboard")
@admin_required
def dashboard():
    total_products = Product.query.filter_by(is_active=True).count()
    total_users = User.query.filter_by(role="user").count()
    total_orders = Order.query.count()
    total_revenue = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.payment_status == "Paid")
        .scalar()
    )
    low_stock = (
        Product.query.filter(Product.is_active.is_(True), Product.stock_quantity <= 5)
        .order_by(Product.stock_quantity.asc())
        .limit(10)
        .all()
    )
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    return success(
        "Dashboard stats fetched.",
        {
            "total_products": total_products,
            "total_users": total_users,
            "total_orders": total_orders,
            "total_revenue": float(total_revenue or 0),
            "low_stock_products": [p.to_dict() for p in low_stock],
            "recent_orders": [o.to_dict(include_items=False) for o in recent_orders],
        },
    )


@admin_bp.get("/users")
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return success("Users fetched.", [u.to_dict() for u in users])


@admin_bp.put("/users/<int:user_id>/status")
@admin_required
def toggle_user_status(user_id):
    user = User.query.get(user_id)
    if not user:
        return error("User not found.", 404)
    if user.role == "admin":
        return error("Admin accounts cannot be deactivated from here.", 400)

    data = request.get_json(silent=True) or {}
    if "is_active" not in data:
        return error("is_active is required.", 400)

    user.is_active = bool(data["is_active"])
    db.session.commit()
    return success("User status updated.", user.to_dict())


@admin_bp.get("/orders")
@admin_required
def list_orders():
    query = Order.query
    status = request.args.get("status")
    if status:
        query = query.filter(Order.status == status)
    search = request.args.get("search")
    if search:
        query = query.filter(Order.order_number.ilike(f"%{search.strip()}%"))

    orders = query.order_by(Order.created_at.desc()).all()
    return success("Orders fetched.", [o.to_dict(include_items=False) for o in orders])


@admin_bp.get("/orders/<int:order_id>")
@admin_required
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return error("Order not found.", 404)
    return success("Order fetched.", order.to_dict())


@admin_bp.put("/orders/<int:order_id>/status")
@admin_required
def update_order_status(order_id):
    order = Order.query.get(order_id)
    if not order:
        return error("Order not found.", 404)

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in ORDER_STATUSES:
        return error(f"status must be one of: {', '.join(ORDER_STATUSES)}", 400)

    order.status = new_status
    db.session.commit()
    return success("Order status updated.", order.to_dict())
