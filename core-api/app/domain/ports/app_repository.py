# app/domain/ports/app_repository.py

from typing import Protocol, Optional, List
from app.infrastructure.db.models.app_module import App


class AppRepository(Protocol):

    def get(self, app_id: str) -> Optional[App]:
        ...

    def list_active(self) -> List[App]:
        ...

    def add(self, app: App) -> None:
        ...

    def delete(self, app_id: str) -> None:
        ...