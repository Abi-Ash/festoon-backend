from datetime import datetime
from extensions import db

ORDER_STATUSES = ["Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"]
PAYMENT_STATUSES = ["Pending", "Paid", "Failed", "Refunded"]


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    order_number = db.Column(db.String(40), nullable=False, unique=True, index=True)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_charge = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(db.String(20), nullable=False, default="Pending")
    payment_status = db.Column(db.String(20), nullable=False, default="Pending")

    shipping_name = db.Column(db.String(120), nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=False)
    shipping_address = db.Column(db.String(400), nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_state = db.Column(db.String(100), nullable=False)
    shipping_pincode = db.Column(db.String(10), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan", lazy=True)
    payment = db.relationship("Payment", backref="order", uselist=False, cascade="all, delete-orphan")

    def to_dict(self, include_items=True):
        data = {
            "id": self.id,
            "order_number": self.order_number,
            "user_id": self.user_id,
            "subtotal": float(self.subtotal),
            "delivery_charge": float(self.delivery_charge),
            "total_amount": float(self.total_amount),
            "status": self.status,
            "payment_status": self.payment_status,
            "shipping": {
                "name": self.shipping_name,
                "phone": self.shipping_phone,
                "address": self.shipping_address,
                "city": self.shipping_city,
                "state": self.shipping_state,
                "pincode": self.shipping_pincode,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "price": float(self.price),
            "quantity": self.quantity,
            "subtotal": float(self.subtotal),
        }
