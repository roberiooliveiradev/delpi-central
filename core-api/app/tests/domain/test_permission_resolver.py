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
        self.direct_calls = 0
        self.group_calls = 0

    def list_all_permission_codes(self):
        return self._all

    def list_direct_role_permissions(self, user_id):
        self.direct_calls += 1
        return self._direct

    def list_group_role_permissions(self, user_id):
        self.group_calls += 1
        return self._group

    def list_user_overrides(self, user_id):
        return self._overrides


# ---------------------------------------------------------
# TESTS
# ---------------------------------------------------------

def test_direct_role_permissions_only():
    uid = uuid4()
    query = FakeQuery(direct=["permission.a", "permission.b"], group=[])
    resolver = PermissionResolver(query, FakeCache())

    result = resolver.resolve(uid, is_superadmin=False)

    assert sorted(result) == ["permission.a", "permission.b"]


def test_group_role_permissions_only():
    uid = uuid4()
    query = FakeQuery(direct=[], group=["permission.c"])
    resolver = PermissionResolver(query, FakeCache())

    result = resolver.resolve(uid, is_superadmin=False)

    assert sorted(result) == ["permission.c"]


def test_resolve_merges_direct_and_group_permissions():
    uid = uuid4()

    query = FakeQuery(
        direct=["apps.manage"],
        group=["dashboard.view"],
    )

    resolver = PermissionResolver(query, FakeCache())
    result = resolver.resolve(uid, is_superadmin=False)

    assert sorted(result) == ["apps.manage", "dashboard.view"]


def test_allow_override_adds_permission():
    uid = uuid4()
    query = FakeQuery(
        direct=["permission.a"],
        group=[],
        overrides=[("permission.d", True)],
    )
    resolver = PermissionResolver(query, FakeCache())

    result = resolver.resolve(uid, is_superadmin=False)

    assert sorted(result) == ["permission.a", "permission.d"]


def test_deny_override_removes_permission():
    uid = uuid4()
    query = FakeQuery(
        direct=["permission.a", "permission.b"],
        group=["permission.c"],
        overrides=[("permission.b", False)],
    )
    resolver = PermissionResolver(query, FakeCache())

    result = resolver.resolve(uid, is_superadmin=False)

    assert sorted(result) == ["permission.a", "permission.c"]


def test_resolve_applies_allow_and_deny_overrides_together():
    uid = uuid4()

    query = FakeQuery(
        direct=["permission.a", "permission.b"],
        group=["permission.c"],
        overrides=[("permission.b", False), ("permission.d", True)],
    )

    resolver = PermissionResolver(query, FakeCache())
    result = resolver.resolve(uid, is_superadmin=False)

    assert sorted(result) == ["permission.a", "permission.c", "permission.d"]


def test_superadmin_returns_all_permissions():
    uid = uuid4()

    query = FakeQuery(all_permissions=["a", "b", "c"])
    resolver = PermissionResolver(query, FakeCache())

    result = resolver.resolve(uid, is_superadmin=True)

    assert sorted(result) == ["a", "b", "c"]


def test_cache_is_used():
    uid = uuid4()
    cache = FakeCache()
    cache.set(str(uid), ["cached"])

    query = FakeQuery(direct=["should_not_be_used"])
    resolver = PermissionResolver(query, cache)

    result = resolver.resolve(uid, is_superadmin=False)

    assert result == ["cached"]
    assert query.direct_calls == 0


def test_cache_is_populated_on_resolve():
    uid = uuid4()
    cache = FakeCache()
    query = FakeQuery(direct=["permission.a"])
    resolver = PermissionResolver(query, cache)

    result = resolver.resolve(uid, is_superadmin=False)

    assert result == ["permission.a"]
    assert cache.get(str(uid)) == ["permission.a"]


def test_cache_is_invalidated():
    uid = uuid4()
    cache = FakeCache()

    query = FakeQuery(direct=["a"])
    resolver = PermissionResolver(query, cache)

    resolver.resolve(uid, is_superadmin=False)
    assert cache.get(str(uid)) is not None

    resolver.invalidate(uid)
    assert cache.get(str(uid)) is None


def test_resolve_after_invalidation_recalculates():
    uid = uuid4()
    cache = FakeCache()
    query = FakeQuery(direct=["permission.a"])
    resolver = PermissionResolver(query, cache)

    first = resolver.resolve(uid, is_superadmin=False)
    assert first == ["permission.a"]
    assert cache.get(str(uid)) == ["permission.a"]

    resolver.invalidate(uid)
    assert cache.get(str(uid)) is None

    query._direct = ["permission.a", "permission.z"]
    second = resolver.resolve(uid, is_superadmin=False)

    assert sorted(second) == ["permission.a", "permission.z"]
    assert cache.get(str(uid)) == ["permission.a", "permission.z"]
