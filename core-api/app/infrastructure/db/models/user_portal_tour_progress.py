# app/infrastructure/db/models/user_portal_tour_progress.py

from datetime import datetime
import uuid

from app.extensions.db import db


class UserPortalTourProgress(db.Model):
    __tablename__ = "user_portal_tour_progress"

    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tour_version = db.Column(db.String(80), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="exploring", index=True)
    completed_quest_ids = db.Column(db.JSON, nullable=False, default=list)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_activity_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class PortalTourQuestEvent(db.Model):
    __tablename__ = "portal_tour_quest_events"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tour_version = db.Column(db.String(80), nullable=False, index=True)
    quest_id = db.Column(db.String(80), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "tour_version",
            "quest_id",
            name="uq_portal_tour_quest_events_user_version_quest",
        ),
    )
