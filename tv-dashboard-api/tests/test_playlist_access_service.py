from types import SimpleNamespace
from uuid import uuid4

from tv_app.application.services.playlist_access_service import PlaylistAccessService


class _FakeRepo:
    def __init__(
        self,
        playlist: dict | None,
        share_role: str | None = None,
        *,
        claim_result: dict | None = None,
    ):
        self._playlist = playlist
        self._share_role = share_role
        self._claim_result = claim_result
        self.claim_calls: list[tuple] = []

    def get_by_id(self, playlist_id):
        return self._playlist

    def get_share_role(self, playlist_id, target_user_id):
        return self._share_role

    def try_claim_owner(self, playlist_id, user_id):
        self.claim_calls.append((playlist_id, user_id))
        if self._claim_result is not None:
            self._playlist = self._claim_result
            return self._claim_result
        return None


def _user(user_id: str, *, permissions: list[str] | None = None, is_superadmin: bool = False):
    return SimpleNamespace(
        id=user_id,
        permissions=permissions or [],
        is_superadmin=is_superadmin,
    )


def test_actor_id_prefers_user_id_from_delpi_auth():
    assert PlaylistAccessService.actor_id(_user("kc-sub-1")) == "kc-sub-1"
    assert PlaylistAccessService.actor_id(SimpleNamespace(sub="legacy-sub")) == "legacy-sub"
    assert PlaylistAccessService.actor_id(SimpleNamespace()) is None


def test_owner_has_manage_access():
    pid = uuid4()
    repo = _FakeRepo({"id": str(pid), "ownerUserId": "user-a", "createdBy": "user-a"})
    access = PlaylistAccessService(repo).resolve(pid, _user("user-a"))
    assert access.level == "owner"
    assert access.can_manage is True


def test_other_user_without_share_has_no_access():
    pid = uuid4()
    repo = _FakeRepo({"id": str(pid), "ownerUserId": "user-a", "createdBy": "user-a"})
    access = PlaylistAccessService(repo).resolve(pid, _user("user-b"))
    assert access.level == "none"
    assert access.can_read is False


def test_shared_editor_can_edit_but_not_manage():
    pid = uuid4()
    repo = _FakeRepo(
        {"id": str(pid), "ownerUserId": "user-a", "createdBy": "user-a"},
        share_role="editor",
    )
    access = PlaylistAccessService(repo).resolve(pid, _user("user-b"))
    assert access.level == "editor"
    assert access.can_edit is True
    assert access.can_manage is False


def test_shared_viewer_read_only():
    pid = uuid4()
    repo = _FakeRepo(
        {"id": str(pid), "ownerUserId": "user-a"},
        share_role="viewer",
    )
    access = PlaylistAccessService(repo).resolve(pid, _user("user-b"))
    assert access.level == "viewer"
    assert access.can_read is True
    assert access.can_edit is False


def test_orphan_not_claimable_by_regular_writer():
    pid = uuid4()
    repo = _FakeRepo({"id": str(pid), "ownerUserId": None, "createdBy": None})
    access = PlaylistAccessService(repo).resolve(
        pid,
        _user("user-a", permissions=["tv-dashboard.write"]),
    )
    assert access.level == "none"
    assert repo.claim_calls == []


def test_orphan_claimed_by_superadmin_on_open():
    pid = uuid4()
    claimed = {"id": str(pid), "ownerUserId": "admin-1", "createdBy": "admin-1"}
    repo = _FakeRepo(
        {"id": str(pid), "ownerUserId": None, "createdBy": None},
        claim_result=claimed,
    )
    access = PlaylistAccessService(repo).resolve(pid, _user("admin-1", is_superadmin=True))
    assert access.level == "owner"
    assert len(repo.claim_calls) == 1
