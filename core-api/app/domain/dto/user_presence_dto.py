# app/domain/dto/user_presence_dto.py

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserPresenceSessionDTO:
    user_id: str
    session_id: str
    connected_at: datetime
    last_seen_at: datetime


@dataclass(frozen=True)
class UserPresenceSummaryDTO:
    user_id: str
    connection_count: int
    connected_at: datetime
    last_seen_at: datetime
