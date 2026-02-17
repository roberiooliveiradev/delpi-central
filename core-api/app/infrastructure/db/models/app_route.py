# app/infrastructure/db/models/app_route.py

import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class AppRoute(db.Model, TimestampMixin):
    __tablename__ = "app_routes"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    app_id = db.Column(
        db.String(50),
        db.ForeignKey("apps.id"),
        nullable=False
    )

    path = db.Column(db.String(255), nullable=False)

    label = db.Column(db.String(150), nullable=True)
    icon = db.Column(db.String(100), nullable=True)

    order = db.Column(db.Integer, nullable=True)

    show_in_menu = db.Column(db.Boolean, default=True)
    active = db.Column(db.Boolean, default=True)

    permission_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("permissions.id"),
        nullable=True
    )
    
    app = db.relationship("App", back_populates="routes")
    permission = db.relationship("Permission")