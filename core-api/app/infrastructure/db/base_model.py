# app/infrastructure/db/base_model.py

from sqlalchemy.sql import func
from app.extensions import db

class TimestampMixin:
    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

