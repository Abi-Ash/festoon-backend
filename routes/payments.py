from flask import Blueprint, request, g, current_app
from extensions import db
from models import Order, Payment, Product, Cart
from utils.responses import success, error
from middleware.auth_middleware import token_required
from utils.razorpay_utils import create_razorpay_order, verify_payment_signature

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payment")


@payments_bp.post("/create-order")
@token_required
def create_order_payment():
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    if not order_id:
        return error("order_id is required.", 400)

    order = Order.query.filter_by(id=order_id, user_id=g.current_user.id).first()
    if not order:
        return error("Order not found.", 404)
    if order.payment_status == "Paid":
        return error("This order has already been paid for.", 400)

    try:
        rp_order = create_razorpay_order(float(order.total_amount), receipt=order.order_number)
    except RuntimeError as exc:
        return error(str(exc), 503)
    except Exception as exc:
        return error(f"Could not create payment order: {exc}", 502)

    payment = Payment.query.filter_by(order_id=order.id).first()
    if not payment:
        payment = Payment(order_id=order.id, amount=order.total_amount)
        db.session.add(payment)
    payment.razorpay_order_id = rp_order["id"]
    payment.status = "Pending"
    db.session.commit()

    return success(
        "Razorpay order created.",
        {
            "razorpay_order_id": rp_order["id"],
            "amount": rp_order["amount"],  # in paise
            "currency": rp_order["currency"],
            "key_id": current_app.config["RAZORPAY_KEY_ID"],  # public key, safe to expose
            "order_id": order.id,
            "order_number": order.order_number,
        },
    )


@payments_bp.post("/verify")
@token_required
def verify_payment():
    """
    Verifies the Razorpay signature on the backend before trusting that a
    payment succeeded. Only after verification do we mark the order paid,
    reduce stock and clear the cart.
    """
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not all([order_id, razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return error("Missing payment verification fields.", 400)

    order = Order.query.filter_by(id=order_id, user_id=g.current_user.id).first()
    if not order:
        return error("Order not found.", 404)

    payment = Payment.query.filter_by(order_id=order.id).first()
    if not payment or payment.razorpay_order_id != razorpay_order_id:
        return error("Payment record mismatch.", 400)

    is_valid = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    if not is_valid:
        payment.status = "Failed"
        order.payment_status = "Failed"
        db.session.commit()
        return error("Payment signature verification failed.", 400)

    # Re-check stock at the moment of confirmation (it may have changed since order creation).
    for item in order.items:
        if item.product_id:
            product = Product.query.get(item.product_id)
            if product and product.stock_quantity < item.quantity:
                payment.status = "Failed"
                order.payment_status = "Failed"
                db.session.commit()
                return error(
                    f"'{item.product_name}' no longer has enough stock. "
                    "Please contact support - your payment will be refunded.",
                    409,
                )

    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = "Paid"

    order.payment_status = "Paid"
    order.status = "Confirmed"

    for item in order.items:
        if item.product_id:
            product = Product.query.get(item.product_id)
            if product:
                product.stock_quantity = max(0, product.stock_quantity - item.quantity)

    cart = Cart.query.filter_by(user_id=g.current_user.id).first()
    if cart:
        for cart_item in list(cart.items):
            db.session.delete(cart_item)

    db.session.commit()
    return success("Payment verified. Order confirmed.", order.to_dict())
