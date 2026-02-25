# app/infrastructure/persistence/sqlalchemy/plugin_route_repository.py

from __future__ import annotations

from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.domain.ports.plugin_route_repository_port import PluginRouteRepositoryPort
from app.infrastructure.db.models import AppRoute, Permission


class SqlAlchemyPluginRouteRepository(PluginRouteRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def bulk_create(self, routes: List[Dict[str, Any]]) -> None:
        """
        Espera cada route:
          {
            "app_id": str,
            "path": str,
            "label": str | None,
            "icon": str | None,
            "permission": str | None,   # permission code
            "order": int,
            "show_in_menu": bool
          }
        """
        objs: List[AppRoute] = []

        for r in routes:
            perm_id = None
            perm_code = r.get("permission")
            if perm_code:
                perm = self.session.query(Permission).filter_by(code=perm_code).first()
                perm_id = perm.id if perm else None

            objs.append(
                AppRoute(
                    app_id=r["app_id"],
                    path=r["path"],
                    label=r.get("label"),
                    icon=r.get("icon"),
                    permission_id=perm_id,
                    order=r.get("order", 0),
                    show_in_menu=r.get("show_in_menu", True),
                    active=True,
                )
            )

        if objs:
            self.session.add_all(objs)

    def delete_by_app(self, plugin_id: str) -> None:
        self.session.query(AppRoute).filter_by(app_id=plugin_id).delete(synchronize_session=False)

    def update_by_app_and_path(self, plugin_id: str, path: str, patch: Dict[str, Any]) -> None:
        """
        Atualiza rota existente do app pelo path.
        Não cria rota se não existir.
        patch pode conter:
          label, icon, order, show_in_menu
        """
        row = (
            self.session.query(AppRoute)
            .filter_by(app_id=plugin_id, path=path)
            .first()
        )
        if not row:
            return

        if "label" in patch:
            row.label = patch["label"]
        if "icon" in patch:
            row.icon = patch["icon"]
        if "order" in patch and patch["order"] is not None:
            row.order = patch["order"]
        if "show_in_menu" in patch and patch["show_in_menu"] is not None:
            row.show_in_menu = patch["show_in_menu"]