from flask import Blueprint, request, g
from extensions import db
from models import Wishlist, WishlistItem, Product, Cart, CartItem
from utils.responses import success, error
from middleware.auth_middleware import token_required

wishlist_bp = Blueprint("wishlist", __name__, url_prefix="/api/wishlist")


def _get_or_create_wishlist(user_id):
    wishlist = Wishlist.query.filter_by(user_id=user_id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        db.session.add(wishlist)
        db.session.commit()
    return wishlist


@wishlist_bp.get("")
@token_required
def get_wishlist():
    wishlist = _get_or_create_wishlist(g.current_user.id)
    return success("Wishlist fetched.", [i.to_dict() for i in wishlist.items])


@wishlist_bp.post("")
@token_required
def add_to_wishlist():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    if not product_id:
        return error("product_id is required.", 400)

    product = Product.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        return error("Product not found.", 404)

    wishlist = _get_or_create_wishlist(g.current_user.id)
    existing = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
    if existing:
        return success("Product already in wishlist.", existing.to_dict())

    item = WishlistItem(wishlist_id=wishlist.id, product_id=product_id)
    db.session.add(item)
    db.session.commit()
    return success("Added to wishlist.", item.to_dict(), 201)


@wishlist_bp.delete("/<int:item_id>")
@token_required
def remove_from_wishlist(item_id):
    wishlist = _get_or_create_wishlist(g.current_user.id)
    item = WishlistItem.query.filter_by(id=item_id, wishlist_id=wishlist.id).first()
    if not item:
        return error("Wishlist item not found.", 404)

    db.session.delete(item)
    db.session.commit()
    return success("Removed from wishlist.")


@wishlist_bp.post("/<int:item_id>/move-to-cart")
@token_required
def move_to_cart(item_id):
    wishlist = _get_or_create_wishlist(g.current_user.id)
    item = WishlistItem.query.filter_by(id=item_id, wishlist_id=wishlist.id).first()
    if not item:
        return error("Wishlist item not found.", 404)

    product = Product.query.filter_by(id=item.product_id, is_active=True).first()
    if not product or product.stock_quantity < 1:
        return error("This product is currently out of stock.", 400)

    cart = Cart.query.filter_by(user_id=g.current_user.id).first()
    if not cart:
        cart = Cart(user_id=g.current_user.id)
        db.session.add(cart)
        db.session.flush()

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity = min(cart_item.quantity + 1, product.stock_quantity)
    else:
        db.session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=1))

    db.session.delete(item)
    db.session.commit()
    return success("Moved to cart.")
