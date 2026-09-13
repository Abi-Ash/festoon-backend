import random
import string
from datetime import datetime
from flask import Blueprint, request, g, current_app
from extensions import db
from models import Cart, Order, OrderItem, Product
from utils.responses import success, error
from utils.validators import require_fields, is_valid_phone, is_valid_pincode
from middleware.auth_middleware import token_required

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")


def _generate_order_number():
    stamp = datetime.utcnow().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=6))
    return f"FES-{stamp}-{suffix}"


@orders_bp.post("")
@token_required
def create_order():
    """
    Creates an order from the user's current cart.
    Prices and stock are recalculated from the database - the frontend's
    numbers are only used for display, never trusted for the actual charge.
    """
    data = request.get_json(silent=True) or {}
    required = ["shipping_name", "shipping_phone", "shipping_address", "shipping_city", "shipping_state", "shipping_pincode"]
    missing = require_fields(data, required)
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 400)
    if not is_valid_phone(data["shipping_phone"]):
        return error("Please enter a valid phone number.", 400)
    if not is_valid_pincode(data["shipping_pincode"]):
        return error("Please enter a valid pincode.", 400)

    cart = Cart.query.filter_by(user_id=g.current_user.id).first()
    if not cart or not cart.items:
        return error("Your cart is empty.", 400)

    subtotal = 0.0
    order_items = []
    for cart_item in cart.items:
        product = Product.query.filter_by(id=cart_item.product_id, is_active=True).first()
        if not product:
            return error(f"A product in your cart is no longer available.", 400)
        if cart_item.quantity > product.stock_quantity:
            return error(
                f"Only {product.stock_quantity} unit(s) of '{product.name}' are in stock.", 400
            )
        price = product.effective_price()
        line_subtotal = round(price * cart_item.quantity, 2)
        subtotal += line_subtotal
        order_items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                price=price,
                quantity=cart_item.quantity,
                subtotal=line_subtotal,
            )
        )

    subtotal = round(subtotal, 2)
    threshold = current_app.config["FREE_DELIVERY_THRESHOLD"]
    delivery_charge = 0.0 if subtotal >= threshold else current_app.config["DELIVERY_CHARGE"]
    total_amount = round(subtotal + delivery_charge, 2)

    order = Order(
        user_id=g.current_user.id,
        order_number=_generate_order_number(),
        subtotal=subtotal,
        delivery_charge=delivery_charge,
        total_amount=total_amount,
        status="Pending",
        payment_status="Pending",
        shipping_name=data["shipping_name"].strip(),
        shipping_phone=data["shipping_phone"].strip(),
        shipping_address=data["shipping_address"].strip(),
        shipping_city=data["shipping_city"].strip(),
        shipping_state=data["shipping_state"].strip(),
        shipping_pincode=data["shipping_pincode"].strip(),
    )
    order.items = order_items
    db.session.add(order)
    db.session.commit()

    return success("Order created. Proceed to payment.", order.to_dict(), 201)


@orders_bp.get("")
@token_required
def list_orders():
    orders = (
        Order.query.filter_by(user_id=g.current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return success("Orders fetched.", [o.to_dict(include_items=False) for o in orders])


@orders_bp.get("/<int:order_id>")
@token_required
def get_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=g.current_user.id).first()
    if not order:
        return error("Order not found.", 404)
    return success("Order fetched.", order.to_dict())
