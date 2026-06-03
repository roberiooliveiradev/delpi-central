# app/tests/use_cases/test_replace_role_permissions_use_case.py

from uuid import uuid4

from app.application.use_cases.replace_role_permissions_use_case import (
    ReplaceRolePermissionsUseCase,
)


class FakeRolePermissions:
    def __init__(self, existing=None):
        self.existing = list(existing or [])

    def list_permission_ids(self, role_id):
        return list(self.existing)

    def replace_permissions_by_ids(self, role_id, permission_ids):
        self.existing = [uuid4() if isinstance(pid, str) else pid for pid in permission_ids]


class FakeUoW:
    def __init__(self, existing=None):
        self.role_permissions = FakeRolePermissions(existing)
        self._events = []

    def collect_event(self, event):
        self._events.append(event)


def test_replace_role_permissions_emits_added_ids():
    uow = FakeUoW()
    use_case = ReplaceRolePermissionsUseCase(uow)

    role_id = str(uuid4())
    existing = uuid4()
    new_perm = str(uuid4())
    uow.role_permissions.existing = [existing]

    use_case.execute(role_id, [str(existing), new_perm])

    assert uow._events[0].action == "role_permissions_replaced"
    assert str(existing) not in (uow._events[0].payload.get("addedPermissionIds") or [])
    assert new_perm in uow._events[0].payload["addedPermissionIds"]
