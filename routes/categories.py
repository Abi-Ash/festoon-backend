from flask import Blueprint, request
from extensions import db
from models import Category
from utils.responses import success, error
from middleware.auth_middleware import admin_required

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@categories_bp.get("")
def list_categories():
    categories = Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()
    return success("Categories fetched.", [c.to_dict() for c in categories])


@categories_bp.post("")
@admin_required
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return error("Category name is required.", 400)
    if Category.query.filter_by(name=name).first():
        return error("A category with this name already exists.", 409)

    category = Category(name=name, description=(data.get("description") or "").strip())
    db.session.add(category)
    db.session.commit()
    return success("Category created.", category.to_dict(), 201)


@categories_bp.put("/<int:category_id>")
@admin_required
def update_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return error("Category not found.", 404)

    data = request.get_json(silent=True) or {}
    if "name" in data and data["name"].strip():
        category.name = data["name"].strip()
    if "description" in data:
        category.description = data["description"]
    if "is_active" in data:
        category.is_active = bool(data["is_active"])

    db.session.commit()
    return success("Category updated.", category.to_dict())
