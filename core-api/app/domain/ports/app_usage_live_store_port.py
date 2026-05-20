# app/domain/ports/app_usage_live_store_port.py

from typing import Protocol

from app.domain.dto.app_usage_dto import AppUsageLiveAppDTO, AppUsageLiveSessionDTO


class AppUsageLiveStorePort(Protocol):

    def bind_session(self, *, user_id: str, session_id: str) -> None:
        ...

    def unbind_session(self, session_id: str) -> None:
        ...

    def set_active_app(
        self,
        session_id: str,
        *,
        app_id: str,
        route_path: str | None = None,
    ) -> None:
        ...

    def touch(self, session_id: str, *, app_id: str | None = None) -> None:
        ...

    def get_user_id(self, session_id: str) -> str | None:
        ...

    def list_live_apps(self) -> list[AppUsageLiveAppDTO]:
        ...

    def list_live_sessions(self) -> list[AppUsageLiveSessionDTO]:
        ...
