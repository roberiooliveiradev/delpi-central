# app/tests/use_cases/test_create_role_use_case.py

import pytest
from app.application.use_cases.create_role_use_case import CreateRoleUseCase


class FakeRolesRepo:
    def __init__(self, exists=False):
        self._exists = exists
        self.created = False

    def exists_by_name(self, name):
        return self._exists

    def create(self, name, description):
        self.created = True
        return "role-id"


class FakeUoW:
    def __init__(self, exists=False):
        self.roles = FakeRolesRepo(exists)
        self.committed = False
        self.events = []

    def collect_event(self, event):
        self.events.append(event)

    def commit(self):
        self.committed = True


def test_create_role_success():
    uow = FakeUoW(exists=False)
    use_case = CreateRoleUseCase(uow)

    role_id = use_case.execute("admin", None)

    assert role_id == "role-id"
    assert uow.roles.created
    assert uow.events


def test_create_role_already_exists():
    uow = FakeUoW(exists=True)
    use_case = CreateRoleUseCase(uow)

    with pytest.raises(ValueError):
        use_case.execute("admin", None)
