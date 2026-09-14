# app/tests/domain/test_permission_resolver.py

from uuid import uuid4
from app.domain.services.permission_resolver import PermissionResolver


class FakeCache:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

    def invalidate(self, key):
        if key in self.store:
            del self.store[key]


class FakeQuery:
    def __init__(
        self,
        all_permissions=None,
        direct=None,
        group=None,
        overrides=None,
    ):
        self._all = all_permissions or []
        self._direct = direct or []
        self._group = group or []
        self._overrides = overrides or []

    def list_all_permission_codes(self):
        return self._all

    def list_direct_role_permissions(self, user_id):
        return self._direct

    def list_group_role_permissions(self, user_id):
        return self._group

    def list_user_overrides(self, user_id):
        return self._overrides


def test_superadmin_returns_all_permissions():
    uid = uuid4()
    query = FakeQuery(all_permissions=["a", "b", "c"])
    resolver = PermissionResolver(query, FakeCache())

    result = resolver.resolve(uid, is_superadmin=True)

    assert sorted(result) == ["a", "b", "c"]


def test_resolve_direct_role_permissions():
    uid = uuid4()
    resolver = PermissionResolver(FakeQuery(direct=["apps.manage"]), FakeCache())

    assert resolver.resolve(uid, is_superadmin=False) == ["apps.manage"]


def test_resolve_group_role_permissions():
    uid = uuid4()
    resolver = PermissionResolver(FakeQuery(group=["dashboard.view"]), FakeCache())

    assert resolver.resolve(uid, is_superadmin=False) == ["dashboard.view"]


def test_resolve_merges_direct_and_group_permissions():
    uid = uuid4()
    query = FakeQuery(
        direct=["apps.manage", "shared.view"],
        group=["dashboard.view", "shared.view"],
    )
    resolver = PermissionResolver(query, FakeCache())

    assert resolver.resolve(uid, is_superadmin=False) == [
        "apps.manage",
        "dashboard.view",
        "shared.view",
    ]


def test_resolve_allow_override_adds_permission():
    uid = uuid4()
    query = FakeQuery(direct=["a"], overrides=[("c", True)])
    resolver = PermissionResolver(query, FakeCache())

    assert resolver.resolve(uid, is_superadmin=False) == ["a", "c"]


def test_resolve_deny_override_removes_inherited_permission():
    uid = uuid4()
    query = FakeQuery(direct=["a", "b"], overrides=[("b", False)])
    resolver = PermissionResolver(query, FakeCache())

    assert resolver.resolve(uid, is_superadmin=False) == ["a"]


def test_cache_is_used():
    uid = uuid4()
    cache = FakeCache()
    cache.set(str(uid), ["cached"])

    query = FakeQuery(direct=["should_not_be_used"])
    resolver = PermissionResolver(query, cache)

    result = resolver.resolve(uid, is_superadmin=False)

    assert result == ["cached"]


def test_cache_is_invalidated():
    uid = uuid4()
    cache = FakeCache()
    query = FakeQuery(direct=["a"])
    resolver = PermissionResolver(query, cache)

    resolver.resolve(uid, is_superadmin=False)
    assert cache.get(str(uid)) is not None

    resolver.invalidate(uid)
    assert cache.get(str(uid)) is None
