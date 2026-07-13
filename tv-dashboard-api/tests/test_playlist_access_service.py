from types import SimpleNamespace
from uuid import uuid4

from tv_app.application.services.playlist_access_service import PlaylistAccessService


class _FakeRepo:
    def __init__(self, playlist: dict | None, share_role: str | None = None):
        self._playlist = playlist
        self._share_role = share_role

    def get_by_id(self, playlist_id):
        return self._playlist

    def get_share_role(self, playlist_id, target_user_id):
        return self._share_role


def test_owner_has_manage_access():
    pid = uuid4()
    repo = _FakeRepo({"id": str(pid), "ownerUserId": "user-a", "createdBy": "user-a"})
    access = PlaylistAccessService(repo).resolve(pid, SimpleNamespace(sub="user-a", is_superadmin=False))
    assert access.level == "owner"
    assert access.can_manage is True


def test_other_user_without_share_has_no_access():
    pid = uuid4()
    repo = _FakeRepo({"id": str(pid), "ownerUserId": "user-a", "createdBy": "user-a"})
    access = PlaylistAccessService(repo).resolve(pid, SimpleNamespace(sub="user-b", is_superadmin=False))
    assert access.level == "none"
    assert access.can_read is False


def test_shared_editor_can_edit_but_not_manage():
    pid = uuid4()
    repo = _FakeRepo(
        {"id": str(pid), "ownerUserId": "user-a", "createdBy": "user-a"},
        share_role="editor",
    )
    access = PlaylistAccessService(repo).resolve(pid, SimpleNamespace(sub="user-b", is_superadmin=False))
    assert access.level == "editor"
    assert access.can_edit is True
    assert access.can_manage is False


def test_shared_viewer_read_only():
    pid = uuid4()
    repo = _FakeRepo(
        {"id": str(pid), "ownerUserId": "user-a"},
        share_role="viewer",
    )
    access = PlaylistAccessService(repo).resolve(pid, SimpleNamespace(sub="user-b", is_superadmin=False))
    assert access.level == "viewer"
    assert access.can_read is True
    assert access.can_edit is False
