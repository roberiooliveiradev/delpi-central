# app/infrastructure/persistence/sqlalchemy/app_query_repository.py

from typing import List
from sqlalchemy.orm import Session

from app.domain.ports.app_query_port import AppQueryPort, AppDTO, RouteDTO
from app.infrastructure.db.models import App, AppRoute, Permission
from app.infrastructure.db.models.app_manifest import AppManifest

class SqlAlchemyAppQueryRepository(AppQueryPort):

    def __init__(self, session: Session):
        self.session = session

    def list_active_apps_with_routes(self) -> List[AppDTO]:

        apps = (
            self.session.query(App)
            .filter_by(active=True)
            .all()
        )

        result: List[AppDTO] = []

        for app in apps:

            # Buscar manifesto
            manifest_row = (
                self.session.query(AppManifest)
                .filter_by(app_id=app.id)
                .first()
            )

            entry_url = None
            render_mode = "embedded"

            if manifest_row and manifest_row.manifest:
                manifest = manifest_row.manifest

                entry_url = manifest.get("entry")

                render_mode = manifest.get("ui", {}).get("renderMode", "embedded")

                if app.type == "iframe":
                    allowed = {"embedded", "external"}
                elif app.type == "microfrontend":
                    allowed = {"embedded", "federated"}
                else:
                    allowed = set()

                if render_mode not in allowed:
                    render_mode = "embedded"

            if app.type == "backend-only":
                entry_url = None
                render_mode = None

            routes = (
                self.session.query(AppRoute)
                .filter_by(app_id=app.id, active=True)
                .all()
            )

            route_dtos = []

            for r in routes:
                permission_code = None
                if r.permission:
                    permission_code = r.permission.code

                route_dtos.append(
                    RouteDTO(
                        path=r.path,
                        label=r.label,
                        icon=r.icon,
                        permission_code=permission_code,
                        show_in_menu=bool(r.show_in_menu),
                        order=r.order,
                    )
                )

            result.append(
                AppDTO(
                    id=app.id,
                    name=app.name,
                    base_path=app.base_path,
                    icon=app.icon,
                    type=app.type,
                    entry_url=entry_url,
                    render_mode=render_mode,  
                    routes=route_dtos,
                )
            )

        return result