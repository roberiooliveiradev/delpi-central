# app/tests/use_cases/test_update_route_use_case.py

from app.application.use_cases.update_route_use_case import UpdateRouteUseCase


class FakeUoW:
    def __init__(self, should_fail=False):
        self.admin_routes = type("", (), {
            "update": lambda *a, **k: (_ for _ in ()).throw(Exception("fail")) if should_fail else None
        })()
        self.committed = False
        self.rolled_back = False
        self._should_fail = should_fail

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_update_route_success():
    uow = FakeUoW()
    use_case = UpdateRouteUseCase(uow)

    result = use_case.execute("route1", {"label": "New"})

    assert result.success
    assert uow.committed


def test_update_route_failure():
    uow = FakeUoW(should_fail=True)
    use_case = UpdateRouteUseCase(uow)

    result = use_case.execute("route1", {"label": "New"})

    assert not result.success
    assert uow.rolled_back