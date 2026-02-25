# app/domain/ports/admin_app_repository_port.py

from typing import Protocol, List
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


class AdminAppRepositoryPort(Protocol):

    def list_all(self) -> List[AdminAppDTO]:
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