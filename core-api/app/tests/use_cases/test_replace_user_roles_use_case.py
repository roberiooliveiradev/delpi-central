# app/tests/use_cases/test_replace_user_roles_use_case.py

from uuid import uuid4
from app.application.use_cases.replace_user_roles_use_case import ReplaceUserRolesUseCase


class FakeUoW:
    def __init__(self):
        self.user_roles = type("", (), {"replace_roles": lambda *a, **k: None})()
        self.cache = type("", (), {"invalidate": lambda *a, **k: None})()
        self.committed = False

    def commit(self):
        self.committed = True


def test_replace_user_roles_success():
    uow = FakeUoW()
    use_case = ReplaceUserRolesUseCase(uow)

    uid = str(uuid4())
    roles = [str(uuid4())]

    result = use_case.execute(uid, roles)

    assert result["ok"] is True
    assert uow.committed