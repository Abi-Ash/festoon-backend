"""
Festoon Threads e-commerce backend entry point.

Run locally with:
    python app.py

This creates all DB tables on first run (via db.create_all()) if they
don't already exist. For schema changes later, consider adding
Flask-Migrate — kept out for now to stay simple for a beginner project.
"""
from flask import Flask
from flask_cors import CORS

from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from utils.cloudinary_utils import init_cloudinary
    init_cloudinary(app)

    CORS(
        app,
        resources={r"/api/*": {"origins": [o.strip() for o in app.config["FRONTEND_URL"].split(",")]}},
        supports_credentials=True,
    )

    # Import models so they are registered with SQLAlchemy before create_all()
    import models  # noqa: F401

    # Register blueprints
    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.categories import categories_bp
    from routes.cart import cart_bp
    from routes.wishlist import wishlist_bp
    from routes.orders import orders_bp
    from routes.payments import payments_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(admin_bp)

    @app.get("/api/health")
    def health():
        return {"success": True, "message": "Festoon Threads API is running."}

    # @app.get("/api/debug-cors")
    # def debug_cors():
    #     raw = app.config["FRONTEND_URL"]
    #     origins = [o.strip() for o in raw.split(",")]
    #     return {
    #         "raw_value": f"[{raw}]",
    #         "raw_length": len(raw),
    #         "parsed_origins": [f"[{o}]" for o in origins],
    #     }

    @app.errorhandler(404)
    def not_found(e):
        return {"success": False, "message": "Resource not found."}, 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return {"success": False, "message": "Method not allowed."}, 405

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return {"success": False, "message": "Internal server error."}, 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
