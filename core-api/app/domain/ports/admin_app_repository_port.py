# app/domain/ports/admin_app_repository_port.py

from datetime import datetime
from typing import Protocol, List, Tuple
from dataclasses import dataclass


@dataclass
class AdminAppDTO:
    id: str
    name: str
    description: str | None
    icon: str | None
    type: str
    version: str
    active: bool
    base_path: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_user_id: str | None = None
    created_by_email: str | None = None
    updated_by_user_id: str | None = None
    updated_by_email: str | None = None


class AdminAppRepositoryPort(Protocol):

    def list_paginated(
        self,
        page: int,
        page_size: int,
        q: str | None,
        sort: str,
        direction: str,
    ) -> Tuple[List[AdminAppDTO], int]:
        ...

    def get(self, app_id: str) -> AdminAppDTO | None:
        ...

    def update_metadata(
        self,
        app_id: str,
        name: str,
        description: str | None,
        icon: str | None,
    ) -> None:
        ...

    def set_active(self, app_id: str, active: bool) -> None:
        ...

    def delete(self, app_id: str) -> None:
        ...