from flask import Blueprint, request, g
from extensions import db
from models import Cart, CartItem, Product
from utils.responses import success, error
from middleware.auth_middleware import token_required

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")


def _get_or_create_cart(user_id):
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart


def _cart_summary(cart):
    items = [i.to_dict() for i in cart.items]
    subtotal = round(sum(i["line_subtotal"] for i in items), 2)
    return {"id": cart.id, "items": items, "subtotal": subtotal, "item_count": len(items)}


@cart_bp.get("")
@token_required
def get_cart():
    cart = _get_or_create_cart(g.current_user.id)
    return success("Cart fetched.", _cart_summary(cart))


@cart_bp.post("")
@token_required
def add_to_cart():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))

    if not product_id or quantity < 1:
        return error("product_id and a quantity of at least 1 are required.", 400)

    product = Product.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        return error("Product not found.", 404)

    cart = _get_or_create_cart(g.current_user.id)
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

    desired_qty = (item.quantity if item else 0) + quantity
    if desired_qty > product.stock_quantity:
        return error(
            f"Only {product.stock_quantity} unit(s) of '{product.name}' are in stock.", 400
        )

    if item:
        item.quantity = desired_qty
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.session.add(item)

    db.session.commit()
    return success("Item added to cart.", _cart_summary(cart), 201)


@cart_bp.put("/<int:item_id>")
@token_required
def update_cart_item(item_id):
    data = request.get_json(silent=True) or {}
    quantity = data.get("quantity")
    if quantity is None or int(quantity) < 1:
        return error("A valid quantity of at least 1 is required.", 400)
    quantity = int(quantity)

    cart = _get_or_create_cart(g.current_user.id)
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        return error("Cart item not found.", 404)

    if quantity > item.product.stock_quantity:
        return error(f"Only {item.product.stock_quantity} unit(s) available.", 400)

    item.quantity = quantity
    db.session.commit()
    return success("Cart updated.", _cart_summary(cart))


@cart_bp.delete("/<int:item_id>")
@token_required
def remove_cart_item(item_id):
    cart = _get_or_create_cart(g.current_user.id)
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        return error("Cart item not found.", 404)

    db.session.delete(item)
    db.session.commit()
    return success("Item removed from cart.", _cart_summary(cart))
