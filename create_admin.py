"""
Securely create (or promote) an admin account.

This deliberately does NOT hard-code any admin email/password —
you enter them interactively so no credentials ever land in source
control.

Run with:
    python create_admin.py
"""
import getpass
from app import create_app
from extensions import db
from models import User, Cart, Wishlist


def run():
    app = create_app()
    with app.app_context():
        email = input("Admin email: ").strip().lower()
        existing = User.query.filter_by(email=email).first()

        if existing:
            existing.role = "admin"
            existing.is_active = True
            db.session.commit()
            print(f"Existing user '{email}' has been promoted to admin.")
            return

        name = input("Admin name: ").strip()
        password = getpass.getpass("Admin password (min 6 chars, hidden input): ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("Passwords do not match. Aborted.")
            return
        if len(password) < 6:
            print("Password must be at least 6 characters. Aborted.")
            return

        admin = User(name=name, email=email, role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.flush()
        db.session.add(Cart(user_id=admin.id))
        db.session.add(Wishlist(user_id=admin.id))
        db.session.commit()
        print(f"Admin account '{email}' created successfully.")


if __name__ == "__main__":
    run()
