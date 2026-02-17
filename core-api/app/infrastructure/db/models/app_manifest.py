# app/infrastructure/db/models/app_manifest.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin

class AppManifest(db.Model, TimestampMixin):
    __tablename__ = "app_manifests"

    app_id = db.Column(db.String(50), db.ForeignKey("apps.id", ondelete="CASCADE"), primary_key=True)
    manifest = db.Column(db.JSON, nullable=False)
    checksum = db.Column(db.String(100), nullable=True)
