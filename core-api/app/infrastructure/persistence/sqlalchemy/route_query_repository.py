# app/infrastructure/persistence/sqlalchemy/route_query_repository.py

from sqlalchemy.orm import joinedload

from app.domain.ports.route_query_port import RouteQueryPort
from app.infrastructure.db.models import AppRoute
from app.infrastructure.db.models import App


class SqlAlchemyRouteQueryRepository(RouteQueryPort):

    def __init__(self, session):
        self.session = session

    def list_active_menu_routes(self):

        return (
            self.session.query(AppRoute)
            .join(AppRoute.app)
            .options(
                joinedload(AppRoute.app),
                joinedload(AppRoute.permission),
            )
            .filter(
                AppRoute.active == True,
                AppRoute.show_in_menu == True,
                App.active == True, 
            )
            .order_by(AppRoute.app_id.asc(), AppRoute.order.asc())
            .all()
        )