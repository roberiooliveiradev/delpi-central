# app/infrastructure/db/models/user_favorite_app.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin

class UserFavoriteApp(db.Model, TimestampMixin):
    __tablename__ = "user_favorite_apps"

    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    app_id = db.Column(
        db.String(50),
        db.ForeignKey("apps.id", ondelete="CASCADE"),
        primary_key=True
    )

    order_index = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship("User", backref="favorite_app_links")
    app = db.relationship("App")
