# app/domain/events/notification_events.py

from dataclasses import dataclass


@dataclass
class UserNotifiedEvent:
    notification_id: str
    user_id: str
    title: str | None
    message: str
    type: str

@dataclass
class NotificationMarkedReadEvent:
    notification_id: str
    user_id: str

@dataclass
class AllNotificationsMarkedReadEvent:
    user_id: str