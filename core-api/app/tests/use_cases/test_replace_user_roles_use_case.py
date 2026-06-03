# app/tests/use_cases/test_replace_user_roles_use_case.py

from uuid import uuid4

from app.application.use_cases.replace_user_roles_use_case import ReplaceUserRolesUseCase


class FakeUserRoles:
    def __init__(self, existing=None):
        self.existing = list(existing or [])
        self.replaced_with = None
        self.events = []

    def list_role_ids(self, user_id):
        return list(self.existing)

    def replace_roles(self, user_id, role_ids):
        self.replaced_with = role_ids
        self.existing = list(role_ids)


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
    def __init__(self, existing_roles=None, user_id=None):
        self.user_roles = FakeUserRoles(existing_roles)
        self._events = []
        uid = user_id or __import__("uuid").uuid4()
        self.users = FakeUsers(FakeUser(uid))
        self.permission_queries = FakePermissionQueries()

    def collect_event(self, event):
        self._events.append(event)


def test_replace_user_roles_success():
    uid = uuid4()
    uow = FakeUoW(user_id=uid)
    use_case = ReplaceUserRolesUseCase(uow)

    roles = [str(uuid4())]

    result = use_case.execute(str(uid), roles)

    assert result["ok"] is True
    assert len(uow._events) == 1
    assert uow._events[0].action == "roles_replaced"
    assert uow._events[0].payload["addedRoleIds"] == roles


def test_replace_user_roles_no_event_when_unchanged():
    uow = FakeUoW()
    use_case = ReplaceUserRolesUseCase(uow)

    uid = str(uuid4())
    existing = uuid4()
    uow.user_roles.existing = [existing]

    use_case.execute(uid, [str(existing)])

    assert uow._events == []


def test_replace_user_roles_emits_event_on_removal_only():
    user_id = uuid4()
    uow = FakeUoW(user_id=user_id)
    use_case = ReplaceUserRolesUseCase(uow)

    removed = uuid4()
    uow.user_roles.existing = [removed]

    use_case.execute(str(user_id), [])

    assert len(uow._events) == 1
    assert uow._events[0].action == "roles_replaced"
    assert uow._events[0].payload["removedRoleIds"] == [str(removed)]
    assert "addedRoleIds" not in uow._events[0].payload


def test_replace_user_roles_swap_includes_permission_snapshot():
    user_id = uuid4()
    uow = FakeUoW(user_id=user_id)
    use_case = ReplaceUserRolesUseCase(uow)

    old_role = uuid4()
    new_role = uuid4()
    uow.user_roles.existing = [old_role]

    use_case.execute(str(user_id), [str(new_role)])

    assert len(uow._events) == 1
    payload = uow._events[0].payload
    assert payload["addedRoleIds"] == [str(new_role)]
    assert "previousPermissionCodes" in payload
    assert payload["removedRoleIds"] == [str(old_role)]