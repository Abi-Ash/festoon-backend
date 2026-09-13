"""
Shared extension instances. Imported by app.py and by models/routes
to avoid circular imports.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
