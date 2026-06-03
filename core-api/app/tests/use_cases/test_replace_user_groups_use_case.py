# app/tests/use_cases/test_replace_user_groups_use_case.py

from uuid import uuid4

from app.application.use_cases.replace_user_groups_use_case import ReplaceUserGroupsUseCase


class FakeUserGroups:
    def __init__(self, existing=None):
        self.existing = list(existing or [])

    def list_group_ids(self, user_id):
        return list(self.existing)

    def replace_groups(self, user_id, group_ids):
        self.existing = list(group_ids)


class FakeUser:
    def __init__(self, user_id):
        self.id = user_id
        self.is_superadmin = False


class FakeUsers:
    def __init__(self, user):
        self._user = user

    def get_by_id(self, user_id):
        return self._user


class FakePermissionQueries:
    def list_direct_role_permissions(self, user_id):
        return []

    def list_group_role_permissions(self, user_id):
        return []

    def list_user_overrides(self, user_id):
        return []

    def list_all_permission_codes(self):
        return []


class FakeUoW:
    def __init__(self, existing_groups=None, user_id=None):
        self.user_groups = FakeUserGroups(existing_groups)
        self._events = []
        uid = user_id or uuid4()
        self.users = FakeUsers(FakeUser(uid))
        self.permission_queries = FakePermissionQueries()

    def collect_event(self, event):
        self._events.append(event)


def test_replace_user_groups_emits_event_on_removal_only():
    user_id = uuid4()
    uow = FakeUoW(user_id=user_id)
    use_case = ReplaceUserGroupsUseCase(uow)

    removed = uuid4()
    uow.user_groups.existing = [removed]

    use_case.execute(str(user_id), [])

    assert len(uow._events) == 1
    assert uow._events[0].action == "groups_replaced"
    assert uow._events[0].target_user_id == str(user_id)
    assert uow._events[0].payload["removedGroupIds"] == [str(removed)]
    assert "addedGroupIds" not in uow._events[0].payload


def test_replace_user_groups_emits_event_on_add_with_snapshot():
    user_id = uuid4()
    uow = FakeUoW(user_id=user_id)
    use_case = ReplaceUserGroupsUseCase(uow)

    new_group = uuid4()

    use_case.execute(str(user_id), [str(new_group)])

    assert len(uow._events) == 1
    assert uow._events[0].payload["addedGroupIds"] == [str(new_group)]
    assert "previousPermissionCodes" in uow._events[0].payload


def test_replace_user_groups_no_event_when_unchanged():
    user_id = uuid4()
    existing = uuid4()
    uow = FakeUoW(existing_groups=[existing], user_id=user_id)
    use_case = ReplaceUserGroupsUseCase(uow)

    use_case.execute(str(user_id), [str(existing)])

    assert uow._events == []
