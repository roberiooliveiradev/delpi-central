# app/tests/use_cases/test_reorder_favorite_apps_use_case.py

import pytest
from app.application.use_cases.reorder_favorite_apps_use_case import (
    ReorderFavoriteAppsUseCase,
)
from app.domain.ports.app_query_port import AppDTO, RouteDTO


class FakeFavoriteRepo:
    def __init__(self, favorites):
        self._favorites = favorites
        self.reorder_called_with = None

    def list_user_favorites(self, user_id):
        return self._favorites

    def reorder(self, user_id, app_ids):
        self.reorder_called_with = (user_id, app_ids)


class FakeAppQueries:
    def __init__(self, apps):
        self._apps = apps

    def list_active_apps_with_routes(self):
        return self._apps


class FakeUoW:
    def __init__(self, favorites, apps=None):
        self.favorites = FakeFavoriteRepo(favorites)
        self.app_queries = FakeAppQueries(apps or [])


def _app(app_id: str, permission_code: str | None = None) -> AppDTO:
    return AppDTO(
        id=app_id,
        name=app_id,
        base_path=f"/{app_id}",
        icon=None,
        type="microfrontend",
        entry_url=None,
        render_mode=None,
        routes=[
            RouteDTO(
                path=f"/{app_id}",
                label=app_id,
                icon=None,
                permission_code=permission_code,
                show_in_menu=True,
                order=0,
                entry=None,
            )
        ],
    )


def test_reorder_favorites_success():
    favorites = [
        {"id": "crm", "order_index": 0},
        {"id": "dash", "order_index": 1},
    ]
    uow = FakeUoW(
        favorites,
        apps=[_app("crm"), _app("dash")],
    )
    use_case = ReorderFavoriteAppsUseCase(uow)

    use_case.execute(
        "user1",
        ["dash", "crm"],
        permissions=[],
        is_superadmin=True,
    )

    assert uow.favorites.reorder_called_with == ("user1", ["dash", "crm"])


def test_reorder_favorites_invalid_list():
    favorites = [{"id": "crm", "order_index": 0}]
    uow = FakeUoW(favorites, apps=[_app("crm")])
    use_case = ReorderFavoriteAppsUseCase(uow)

    with pytest.raises(ValueError):
        use_case.execute(
            "user1",
            ["crm", "missing"],
            permissions=[],
            is_superadmin=True,
        )


def test_reorder_favorites_duplicate_ids():
    favorites = [{"id": "crm", "order_index": 0}]
    uow = FakeUoW(favorites, apps=[_app("crm")])
    use_case = ReorderFavoriteAppsUseCase(uow)

    with pytest.raises(ValueError):
        use_case.execute(
            "user1",
            ["crm", "crm"],
            permissions=[],
            is_superadmin=True,
        )


def test_reorder_favorites_merges_hidden_unauthorized_favorites():
    favorites = [
        {"id": "chat", "order_index": 0},
        {"id": "hidden", "order_index": 1},
        {"id": "crm", "order_index": 2},
    ]
    uow = FakeUoW(
        favorites,
        apps=[
            _app("chat"),
            _app("hidden", permission_code="secret.access"),
            _app("crm"),
        ],
    )
    use_case = ReorderFavoriteAppsUseCase(uow)

    use_case.execute(
        "user1",
        ["crm", "chat"],
        permissions=[],
        is_superadmin=False,
    )

    assert uow.favorites.reorder_called_with == (
        "user1",
        ["crm", "hidden", "chat"],
    )
