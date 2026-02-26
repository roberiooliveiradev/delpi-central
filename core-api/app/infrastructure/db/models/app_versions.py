# app/infrastructure/db/models/app_versions.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class AppVersion(db.Model, TimestampMixin):
    __tablename__ = "app_versions"

    id = db.Column(db.BigInteger, primary_key=True)

    app_id = db.Column(
        db.String(50),
        db.ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
    )

    version = db.Column(db.String(20), nullable=False)
    manifest = db.Column(db.JSON, nullable=False)
    checksum = db.Column(db.String(100), nullable=False)

    # 🔒 Garante que não exista versão duplicada por app
    __table_args__ = (
        db.UniqueConstraint("app_id", "version", name="uq_app_version"),
        db.Index("ix_app_versions_app_id", "app_id"),
    )

    app = db.relationship(
        "App",
        back_populates="versions",
    )