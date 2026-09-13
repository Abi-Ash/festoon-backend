"""
Central application configuration.
All values are read from environment variables (see .env.example).
Never hard-code secrets here.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24"))
    )

    # MySQL / SQLAlchemy
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "festoon_db")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Hosted MySQL providers (Aiven, TiDB Cloud, etc.) require SSL. Set
    # MYSQL_SSL=true in production. If the provider gives you a specific CA
    # certificate, paste its content into MYSQL_SSL_CA_CONTENT. If not (TiDB
    # Cloud, for example, uses a publicly-trusted certificate rather than a
    # custom one), we fall back to the certifi package's trusted root bundle
    # - the same trust store your browser effectively relies on.
    _connect_args = {}
    if os.getenv("MYSQL_SSL", "false").lower() == "true":
        ca_content = os.getenv("MYSQL_SSL_CA_CONTENT")
        if ca_content:
            ca_path = "/tmp/mysql_ca.pem"
            with open(ca_path, "w") as f:
                f.write(ca_content.replace("\\n", "\n"))
            _connect_args["ssl_ca"] = ca_path
        else:
            import certifi
            _connect_args["ssl_ca"] = certifi.where()
        _connect_args["ssl_verify_cert"] = True

    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "connect_args": _connect_args}

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

    # Razorpay
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

    # CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Business rules
    DELIVERY_CHARGE = float(os.getenv("DELIVERY_CHARGE", "60"))
    FREE_DELIVERY_THRESHOLD = float(os.getenv("FREE_DELIVERY_THRESHOLD", "999"))
