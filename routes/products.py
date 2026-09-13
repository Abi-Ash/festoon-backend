from flask import Blueprint, request
from sqlalchemy import or_
from extensions import db
from models import Product, ProductImage, Category, OrderItem
from utils.responses import success, error
from middleware.auth_middleware import admin_required
from utils.cloudinary_utils import upload_product_image, upload_product_images

products_bp = Blueprint("products", __name__, url_prefix="/api/products")


@products_bp.get("")
def list_products():
    """
    Public product listing with search, category filter, sort and pagination.
    Query params: search, category_id, sort (price_asc|price_desc|newest), featured=1,
    page, per_page
    """
    query = Product.query.filter_by(is_active=True)

    search = request.args.get("search")
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(Product.name.ilike(like), Product.description.ilike(like)))

    category_id = request.args.get("category_id", type=int)
    if category_id:
        query = query.filter(Product.category_id == category_id)

    if request.args.get("featured") == "1":
        query = query.filter(Product.featured.is_(True))

    sort = request.args.get("sort", "newest")
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 12, type=int), 50)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success(
        "Products fetched.",
        {
            "products": [p.to_dict() for p in pagination.items],
            "page": pagination.page,
            "per_page": per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        },
    )


@products_bp.get("/<int:product_id>")
def get_product(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        return error("Product not found.", 404)
    return success("Product fetched.", product.to_dict())


def _validate_product_payload(data, partial=False):
    errors = []
    if not partial or "name" in data:
        if not (data.get("name") or "").strip():
            errors.append("name is required")
    if not partial or "category_id" in data:
        if not data.get("category_id"):
            errors.append("category_id is required")
        elif not Category.query.get(data.get("category_id")):
            errors.append("category_id does not exist")
    if not partial or "price" in data:
        try:
            if float(data.get("price")) <= 0:
                errors.append("price must be greater than 0")
        except (TypeError, ValueError):
            errors.append("price must be a valid number")
    if "discount_price" in data and data.get("discount_price") not in (None, ""):
        try:
            float(data["discount_price"])
        except (TypeError, ValueError):
            errors.append("discount_price must be a valid number")
    if "stock_quantity" in data:
        try:
            if int(data.get("stock_quantity")) < 0:
                errors.append("stock_quantity cannot be negative")
        except (TypeError, ValueError):
            errors.append("stock_quantity must be a valid integer")
    return errors


@products_bp.post("")
@admin_required
def create_product():
    """
    Accepts multipart/form-data so images can be uploaded in the same request.
    Fields: name, description, category_id, price, discount_price, stock_quantity,
    featured, is_active, images (one or more files - the first becomes the cover
    image shown on product cards; all of them make up the swipeable gallery).
    The older single "image" field is still accepted for backward compatibility.
    """
    data = request.form.to_dict()
    errors = _validate_product_payload(data)
    if errors:
        return error("; ".join(errors), 400)

    image_files = request.files.getlist("images")
    if not image_files:
        legacy_file = request.files.get("image")
        if legacy_file and legacy_file.filename:
            image_files = [legacy_file]

    try:
        gallery_urls = upload_product_images(image_files)
    except Exception as exc:
        return error(f"Image upload failed: {exc}", 502)

    product = Product(
        name=data["name"].strip(),
        description=(data.get("description") or "").strip(),
        category_id=int(data["category_id"]),
        price=float(data["price"]),
        discount_price=float(data["discount_price"]) if data.get("discount_price") else None,
        stock_quantity=int(data.get("stock_quantity", 0)),
        image_url=gallery_urls[0] if gallery_urls else None,
        featured=str(data.get("featured", "false")).lower() in ("1", "true", "on"),
        is_active=str(data.get("is_active", "true")).lower() in ("1", "true", "on"),
    )
    db.session.add(product)
    db.session.flush()  # assigns product.id so gallery rows can reference it

    for i, url in enumerate(gallery_urls):
        db.session.add(ProductImage(product_id=product.id, image_url=url, sort_order=i))

    db.session.commit()
    return success("Product created.", product.to_dict(), 201)


@products_bp.put("/<int:product_id>")
@admin_required
def update_product(product_id):
    """
    remove_image_ids: repeated form field of ProductImage ids to delete.
    images: new files to append to the gallery.
    After any gallery change, the cover (image_url) is recomputed as the
    first remaining image so product cards always match the gallery.
    """
    product = Product.query.get(product_id)
    if not product:
        return error("Product not found.", 404)

    data = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
    errors = _validate_product_payload(data, partial=True)
    if errors:
        return error("; ".join(errors), 400)

    remove_ids = {int(i) for i in request.form.getlist("remove_image_ids") if str(i).isdigit()}
    if remove_ids:
        ProductImage.query.filter(
            ProductImage.product_id == product.id, ProductImage.id.in_(remove_ids)
        ).delete(synchronize_session=False)
        db.session.flush()

    new_files = request.files.getlist("images")
    if not new_files:
        legacy_file = request.files.get("image")
        if legacy_file and legacy_file.filename:
            new_files = [legacy_file]

    try:
        new_urls = upload_product_images(new_files)
    except Exception as exc:
        return error(f"Image upload failed: {exc}", 502)

    if new_urls:
        existing_max = db.session.query(db.func.max(ProductImage.sort_order)).filter_by(product_id=product.id).scalar()
        next_order = (existing_max + 1) if existing_max is not None else 0
        for i, url in enumerate(new_urls):
            db.session.add(ProductImage(product_id=product.id, image_url=url, sort_order=next_order + i))
        db.session.flush()

    if remove_ids or new_urls:
        remaining = ProductImage.query.filter_by(product_id=product.id).order_by(ProductImage.sort_order).all()
        product.image_url = remaining[0].image_url if remaining else None

    if "name" in data:
        product.name = data["name"].strip()
    if "description" in data:
        product.description = data["description"]
    if "category_id" in data:
        product.category_id = int(data["category_id"])
    if "price" in data:
        product.price = float(data["price"])
    if "discount_price" in data:
        product.discount_price = float(data["discount_price"]) if data["discount_price"] else None
    if "stock_quantity" in data:
        product.stock_quantity = int(data["stock_quantity"])
    if "featured" in data:
        product.featured = str(data["featured"]).lower() in ("1", "true", "on")
    if "is_active" in data:
        product.is_active = str(data["is_active"]).lower() in ("1", "true", "on")

    db.session.commit()
    return success("Product updated.", product.to_dict())


@products_bp.delete("/<int:product_id>")
@admin_required
def delete_product(product_id):
    """
    Safe deletion: if a product already appears in historical order_items,
    we soft-delete it (is_active = False) so past orders keep showing correct
    product history. Only products that were never ordered are hard-deleted.
    """
    product = Product.query.get(product_id)
    if not product:
        return error("Product not found.", 404)

    has_orders = OrderItem.query.filter_by(product_id=product_id).first() is not None

    if has_orders:
        product.is_active = False
        db.session.commit()
        return success("Product has past orders, so it was deactivated instead of deleted.")

    db.session.delete(product)
    db.session.commit()
    return success("Product deleted.")
