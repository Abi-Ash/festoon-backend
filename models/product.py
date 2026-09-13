from datetime import datetime
from extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_price = db.Column(db.Numeric(10, 2), nullable=True)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(500), nullable=True)  # cover image - shown on product cards
    featured = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship(
        "ProductImage",
        backref="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
    )

    def effective_price(self):
        if self.discount_price is not None and float(self.discount_price) < float(self.price):
            return float(self.discount_price)
        return float(self.price)

    def to_dict(self):
        if self.images:
            gallery = [{"id": img.id, "image_url": img.image_url} for img in self.images]
        elif self.image_url:
            gallery = [{"id": None, "image_url": self.image_url}]
        else:
            gallery = []
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "price": float(self.price),
            "discount_price": float(self.discount_price) if self.discount_price is not None else None,
            "effective_price": self.effective_price(),
            "stock_quantity": self.stock_quantity,
            "in_stock": self.stock_quantity > 0,
            "image_url": self.image_url,
            "images": gallery,
            "featured": self.featured,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
