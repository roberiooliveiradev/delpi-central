# app/domain/ports/app_query_port.py

from typing import Protocol, List
from dataclasses import dataclass


@dataclass
class RouteDTO:
    path: str
    label: str | None
    icon: str | None
    permission_code: str | None
    show_in_menu: bool
    order: int | None
    entry: str | None
    open_in_new_tab: bool = False
    # Quando preenchido (len>=2), autorização da rota é ANY-OF esses códigos.
    # ``permission_code`` permanece o código primário (exibição/compat).
    any_of_permission_codes: tuple[str, ...] | None = None

@dataclass
class AppDTO:
    id: str
    name: str
    base_path: str
    icon: str | None
    type: str
    entry_url: str | None
    render_mode: str | None
    routes: List[RouteDTO]


class AppQueryPort(Protocol):
    def list_active_apps_with_routes(self) -> List[AppDTO]:
        ...