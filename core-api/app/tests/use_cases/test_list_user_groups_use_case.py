# app/tests/use_cases/test_list_user_groups_use_case.py

from uuid import uuid4
from app.application.use_cases.list_user_groups_use_case import ListUserGroupsUseCase


class FakeUserGroupsRepo:
    def __init__(self, group_ids):
        self._group_ids = group_ids

    def list_group_ids(self, user_id):
        return self._group_ids


class FakeUoW:
    def __init__(self, group_ids):
        self.user_groups = FakeUserGroupsRepo(group_ids)


def test_list_user_groups_success():
    gid1 = uuid4()
    gid2 = uuid4()
    user_id = str(uuid4())

    uow = FakeUoW([gid1, gid2])
    use_case = ListUserGroupsUseCase(uow)

    result = use_case.execute(user_id)

    assert result["userId"] == user_id
    assert result["groupIds"] == [str(gid1), str(gid2)]