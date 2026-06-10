# app/tests/use_cases/test_reorder_favorite_apps_use_case.py

import pytest
from app.application.use_cases.reorder_favorite_apps_use_case import (
    ReorderFavoriteAppsUseCase,
)


class FakeFavoriteRepo:
    def __init__(self, favorites):
        self._favorites = favorites
        self.reorder_called_with = None

    def list_user_favorites(self, user_id):
        return self._favorites

    def reorder(self, user_id, app_ids):
        self.reorder_called_with = (user_id, app_ids)


class FakeUoW:
    def __init__(self, favorites):
        self.favorites = FakeFavoriteRepo(favorites)


def test_reorder_favorites_success():
    favorites = [
        {"id": "crm", "order_index": 0},
        {"id": "dash", "order_index": 1},
    ]
    uow = FakeUoW(favorites)
    use_case = ReorderFavoriteAppsUseCase(uow)

    use_case.execute("user1", ["dash", "crm"])

    assert uow.favorites.reorder_called_with == ("user1", ["dash", "crm"])


def test_reorder_favorites_invalid_list():
    favorites = [{"id": "crm", "order_index": 0}]
    uow = FakeUoW(favorites)
    use_case = ReorderFavoriteAppsUseCase(uow)

    with pytest.raises(ValueError):
        use_case.execute("user1", ["crm", "missing"])


def test_reorder_favorites_duplicate_ids():
    favorites = [{"id": "crm", "order_index": 0}]
    uow = FakeUoW(favorites)
    use_case = ReorderFavoriteAppsUseCase(uow)

    with pytest.raises(ValueError):
        use_case.execute("user1", ["crm", "crm"])
