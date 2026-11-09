# app/tests/use_cases/test_list_user_groups_use_case.py

from types import SimpleNamespace
from uuid import uuid4

from app.application.use_cases.list_user_groups_use_case import ListUserGroupsUseCase


class FakeUserGroupsRepo:
    def __init__(self, group_ids):
        self._group_ids = group_ids

    def list_group_ids(self, user_id):
        return self._group_ids


class FakeGroupsRepo:
    def __init__(self, groups_by_id):
        self._groups_by_id = groups_by_id

    def get(self, group_id):
        return self._groups_by_id.get(group_id)


class FakeUoW:
    def __init__(self, group_ids, groups_by_id):
        self.user_groups = FakeUserGroupsRepo(group_ids)
        self.groups = FakeGroupsRepo(groups_by_id)


def test_list_user_groups_success():
    gid1 = uuid4()
    gid2 = uuid4()
    user_id = str(uuid4())
    groups_by_id = {
        gid1: SimpleNamespace(id=gid1, name="Engenharia", description=None),
        gid2: SimpleNamespace(id=gid2, name="RH", description="x"),
    }

    uow = FakeUoW([gid1, gid2], groups_by_id)
    use_case = ListUserGroupsUseCase(uow)

    result = use_case.execute(user_id)

    assert result == [
        {"id": str(gid1), "name": "Engenharia", "description": None},
        {"id": str(gid2), "name": "RH", "description": "x"},
    ]
