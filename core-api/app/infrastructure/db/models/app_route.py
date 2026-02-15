# app/infrastructure/db/models/app_route.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin

class AppRoute(db.Model, TimestampMixin):
    __tablename__ = "app_routes"

    id = db.Column(db.Uuid, primary_key=True, server_default=db.text("gen_random_uuid()"))
    app_id = db.Column(db.String(50), db.ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True)

    path = db.Column(db.String(200), nullable=False)
    label = db.Column(db.String(150), nullable=True)
    icon = db.Column(db.String(100), nullable=True)

    permission_id = db.Column(db.Uuid, db.ForeignKey("permissions.id"), nullable=True)

    show_in_menu = db.Column(db.Boolean, default=True, nullable=False)
    order_index = db.Column(db.Integer, default=0, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
