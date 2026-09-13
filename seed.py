"""
Development seed script.

Populates categories and sample products so the frontend has real
data to work against. Safe to re-run — it skips anything that
already exists instead of creating duplicates.

Run with:
    python seed.py
"""
from app import create_app
from extensions import db
from models import Category, Product

CATEGORIES = [
    ("Scrunchies", "Soft fabric scrunchies for everyday and special occasions."),
    ("Bows", "Cute and elegant hair bows for every look."),
    ("Clips", "Trendy hair clips to keep your style in place."),
    ("Hair Bands", "Comfortable hair bands for all hair types."),
    ("Accessories", "Other fashion hair accessories."),
]

# (name, description, category_name, price, discount_price, stock, image_url, featured)
PRODUCTS = [
    ("Velvet Scrunchie - Blush Pink", "A soft velvet scrunchie in a delicate blush pink.", "Scrunchies", 199, 149, 40, None, True),
    ("Silk Scrunchie - Ivory", "Gentle on hair, reduces breakage and creasing.", "Scrunchies", 249, None, 25, None, False),
    ("Oversized Satin Bow Clip", "A statement satin bow clip for a polished look.", "Bows", 299, 229, 15, None, True),
    ("Mini Bow Set (Pack of 4)", "Four mini bows in pastel shades.", "Bows", 349, None, 30, None, False),
    ("Pearl Hair Clip", "Elegant pearl-studded hair clip.", "Clips", 179, 129, 50, None, True),
    ("Claw Clip - Tortoise Shell", "Strong-grip claw clip in a classic tortoise pattern.", "Clips", 229, None, 35, None, False),
    ("Braided Hair Band", "A stretchy braided hair band for everyday wear.", "Hair Bands", 149, 99, 60, None, False),
    ("Knotted Headband", "A cozy knotted headband, one size fits most.", "Hair Bands", 199, None, 20, None, True),
    ("Rhinestone Hair Pin Set", "Sparkly hair pins, great for special occasions.", "Accessories", 279, 199, 18, None, False),
    ("Everyday Hair Tie Pack (10 pcs)", "No-crease, gentle hold hair ties for daily use.", "Accessories", 129, None, 80, None, False),
]


def run():
    app = create_app()
    with app.app_context():
        name_to_category = {}
        for name, description in CATEGORIES:
            existing = Category.query.filter_by(name=name).first()
            if existing:
                name_to_category[name] = existing
                continue
            cat = Category(name=name, description=description)
            db.session.add(cat)
            db.session.flush()
            name_to_category[name] = cat
        db.session.commit()
        print(f"Categories ready: {len(name_to_category)}")

        created = 0
        for name, description, cat_name, price, discount_price, stock, image_url, featured in PRODUCTS:
            if Product.query.filter_by(name=name).first():
                continue
            product = Product(
                name=name,
                description=description,
                category_id=name_to_category[cat_name].id,
                price=price,
                discount_price=discount_price,
                stock_quantity=stock,
                image_url=image_url,
                featured=featured,
                is_active=True,
            )
            db.session.add(product)
            created += 1
        db.session.commit()
        print(f"Products created: {created}")
        print("Seed complete.")


if __name__ == "__main__":
    run()
