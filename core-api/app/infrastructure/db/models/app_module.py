# app/infrastructure/db/models/app_module.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin

class App(db.Model, TimestampMixin):
    __tablename__ = "apps"

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    base_path = db.Column(db.String(150), nullable=False)
    icon = db.Column(db.String(100), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(20), nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
