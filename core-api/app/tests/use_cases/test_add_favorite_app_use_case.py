# app/tests/use_cases/test_add_favorite_app_use_case.py

import pytest
from types import SimpleNamespace
from app.application.use_cases.add_favorite_app_use_case import AddFavoriteAppUseCase


class FakeFavoriteRepo:
    def __init__(self, exists=False):
        self._exists = exists
        self.add_called = False

    def exists(self, user_id, app_id):
        return self._exists

    def add(self, user_id, app_id):
        self.add_called = True


class FakeAppQueries:
    def __init__(self, apps):
        self._apps = apps

    def list_active_apps_with_routes(self):
        return self._apps


class FakeUoW:
    def __init__(self, apps, exists=False):
        self.favorite = FakeFavoriteRepo(exists)
        self.app_queries = FakeAppQueries(apps)
        self.committed = False

    def commit(self):
        self.committed = True


def test_add_favorite_success():
    app = SimpleNamespace(id="crm")
    uow = FakeUoW([app], exists=False)

    use_case = AddFavoriteAppUseCase(uow)
    use_case.execute("user1", "crm")

    assert uow.favorite.add_called
    assert uow.committed


def test_add_favorite_app_not_found():
    uow = FakeUoW([], exists=False)
    use_case = AddFavoriteAppUseCase(uow)

    with pytest.raises(ValueError):
        use_case.execute("user1", "crm")


def test_add_favorite_idempotent():
    app = SimpleNamespace(id="crm")
    uow = FakeUoW([app], exists=True)

    use_case = AddFavoriteAppUseCase(uow)
    use_case.execute("user1", "crm")

    assert not uow.favorite.add_called