# app/infrastructure/persistence/sqlalchemy/admin_route_repository.py

from __future__ import annotations

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.domain.ports.admin_route_repository_port import AdminRouteRepositoryPort, AdminRouteDTO
from app.infrastructure.db.models import AppRoute, Permission


class SqlAlchemyAdminRouteRepository(AdminRouteRepositoryPort):

    def __init__(self, session: Session):
        self.session = session

    def _to_dto(self, r: AppRoute) -> AdminRouteDTO:
        perm_code = None
        if getattr(r, "permission_id", None):
            perm = self.session.get(Permission, r.permission_id)
            perm_code = perm.code if perm else None

        return AdminRouteDTO(
            id=str(r.id),
            app_id=str(r.app_id),
            path=r.path,
            label=r.label,
            icon=r.icon,
            permission_code=perm_code,
            order=int(r.order or 0),
            show_in_menu=bool(r.show_in_menu),
            active=bool(r.active),
        )

    def list_by_app(self, app_id: str) -> List[AdminRouteDTO]:
        rows = (
            self.session.query(AppRoute)
            .filter_by(app_id=app_id)
            .order_by(AppRoute.order.asc())
            .all()
        )
        return [self._to_dto(r) for r in rows]

    def get(self, route_id: str) -> Optional[AdminRouteDTO]:
        row = self.session.get(AppRoute, route_id)
        if not row:
            return None
        return self._to_dto(row)

    def create(self, data: Dict[str, Any]) -> AdminRouteDTO:
        permission_code = data.get("permission_code")
        permission_id = None
        if permission_code:
            perm = self.session.query(Permission).filter_by(code=permission_code).first()
            if perm:
                permission_id = perm.id

        row = AppRoute(
            app_id=data["app_id"],
            path=data["path"],
            label=data.get("label"),
            icon=data.get("icon"),
            permission_id=permission_id,
            order=data.get("order", 0),
            show_in_menu=data.get("show_in_menu", True),
            active=data.get("active", True),
        )
        self.session.add(row)
        self.session.flush()  # garante id
        return self._to_dto(row)

    def update(self, route_id: str, patch: Dict[str, Any]) -> None:
        row = self.session.get(AppRoute, route_id)
        if not row:
            raise ValueError("Route not found")

        if "path" in patch:
            row.path = patch["path"]
        if "label" in patch:
            row.label = patch["label"]
        if "icon" in patch:
            row.icon = patch["icon"]
        if "order" in patch:
            row.order = patch["order"]
        if "show_in_menu" in patch:
            row.show_in_menu = patch["show_in_menu"]
        if "active" in patch:
            row.active = patch["active"]

        if "permission_code" in patch:
            code = patch["permission_code"]
            if not code:
                row.permission_id = None
            else:
                perm = self.session.query(Permission).filter_by(code=code).first()
                row.permission_id = perm.id if perm else None

    def delete(self, route_id: str) -> None:
        row = self.session.get(AppRoute, route_id)
        if not row:
            raise ValueError("Route not found")
        self.session.delete(row)

    def bulk_delete(self, route_ids: List[str]) -> int:
        if not route_ids:
            return 0
        q = self.session.query(AppRoute).filter(AppRoute.id.in_(route_ids))
        count = q.count()
        q.delete(synchronize_session=False)
        return count