# app/tests/use_cases/test_bulk_delete_routes_use_case.py

from app.application.use_cases.bulk_delete_routes_use_case import BulkDeleteRoutesUseCase


class FakeAdminRoutes:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def bulk_delete(self, ids):
        if self.should_fail:
            raise Exception("boom")
        return len(ids)


class FakeUoW:
    def __init__(self, should_fail=False):
        self.admin_routes = FakeAdminRoutes(should_fail)
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_bulk_delete_success():
    uow = FakeUoW()
    use_case = BulkDeleteRoutesUseCase(uow)

    result = use_case.execute(["1", "2"])

    assert result.success
    assert result.deleted == 2
    assert uow.committed


def test_bulk_delete_failure():
    uow = FakeUoW(should_fail=True)
    use_case = BulkDeleteRoutesUseCase(uow)

    result = use_case.execute(["1"])

    assert not result.success
    assert uow.rolled_back