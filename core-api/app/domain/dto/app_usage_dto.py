# app/domain/dto/app_usage_dto.py

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AppUsageLiveSessionDTO:
    user_id: str
    app_id: str
    route_path: str | None
    connected_at: datetime
    last_seen_at: datetime


@dataclass(frozen=True)
class AppUsageLiveAppDTO:
    app_id: str
    user_count: int
    session_count: int
    last_seen_at: datetime


@dataclass(frozen=True)
class AppUsageRankDTO:
    app_id: str
    app_name: str
    count: int
