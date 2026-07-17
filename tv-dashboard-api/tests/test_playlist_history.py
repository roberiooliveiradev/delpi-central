import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.infrastructure.persistence.repositories.playlist_history_repository import (
    HISTORY_LIMIT_PER_PLAYLIST,
    PlaylistHistoryRepository,
    PlaylistRevisionConflictError,
)
from tv_app.interface.http.routes import playlist_history_routes, slide_routes


def _response_body(response):
    return json.loads(response.body.decode("utf-8"))


def _request(user_id: str = "user-1"):
    request = MagicMock()
    request.state.user = SimpleNamespace(id=user_id)
    return request


def _access(playlist_id, *, level="editor", revision=4):
    return (
        SimpleNamespace(id="user-1"),
        PlaylistAccess(
            level=level,
            playlist={"id": str(playlist_id), "revision": revision},
        ),
    )


def test_migration_defines_jsonb_revision_and_logical_limit():
    migration = Path(playlist_history_routes.__file__).resolve().parents[4] / (
        "migrations/V008__playlist_persistent_history.sql"
    )
    sql = migration.read_text(encoding="utf-8")
    assert "snapshot       JSONB NOT NULL" in sql
    assert "revision BIGINT NOT NULL DEFAULT 0" in sql
    assert HISTORY_LIMIT_PER_PLAYLIST == 500


def test_capture_records_actor_reason_and_prunes_after_500():
    cursor = MagicMock()
    cursor.rowcount = 1
    playlist_id = uuid4()

    PlaylistHistoryRepository.capture_before_mutation(
        cursor,
        playlist_id,
        actor_user_id="user-1",
        reason="slide_updated",
    )

    assert cursor.execute.call_count == 2
    capture_args = cursor.execute.call_args_list[0].args[1]
    prune_args = cursor.execute.call_args_list[1].args[1]
    assert capture_args == ("user-1", "slide_updated", str(playlist_id))
    assert prune_args[-1] == 500


def test_restore_returns_409_with_current_revision():
    playlist_id = uuid4()
    history_id = uuid4()
    history_repo = MagicMock()
    history_repo.restore.side_effect = PlaylistRevisionConflictError(8)

    with (
        patch.object(playlist_history_routes, "_history_repo", history_repo),
        patch(
            "tv_app.interface.http.routes.playlist_history_routes.require_playlist_access",
            return_value=_access(playlist_id),
        ),
    ):
        response = playlist_history_routes.restore_playlist_history(
            _request(),
            playlist_id,
            history_id,
            playlist_history_routes.RestorePlaylistBody(expectedRevision=4),
        )

    assert response.status_code == 409
    assert _response_body(response)["data"]["currentRevision"] == 8


def test_list_history_uses_paginated_frontend_contract():
    playlist_id = uuid4()
    history_repo = MagicMock()
    history_repo.list_history.return_value = {
        "items": [],
        "page": 2,
        "pageSize": 10,
        "total": 0,
        "totalPages": 0,
        "currentRevision": 4,
        "currentSnapshotId": None,
    }

    with (
        patch.object(playlist_history_routes, "_history_repo", history_repo),
        patch(
            "tv_app.interface.http.routes.playlist_history_routes.require_playlist_access",
            return_value=_access(playlist_id, level="viewer"),
        ),
    ):
        response = playlist_history_routes.list_playlist_history(
            _request(),
            playlist_id,
            page=2,
            page_size=10,
        )

    assert response.status_code == 200
    assert _response_body(response)["data"]["pageSize"] == 10
    history_repo.list_history.assert_called_once_with(playlist_id, page=2, page_size=10)


def test_restore_notifies_websocket_only_after_repository_commit():
    playlist_id = uuid4()
    history_id = uuid4()
    events = []
    history_repo = MagicMock()
    history_repo.restore.side_effect = lambda *args, **kwargs: events.append("commit") or 5
    playlist_repo = MagicMock()
    playlist_repo.get_by_id.return_value = {"id": str(playlist_id), "revision": 5}
    playlist_repo.list_slides.return_value = []

    with (
        patch.object(playlist_history_routes, "_history_repo", history_repo),
        patch.object(playlist_history_routes, "_playlist_repo", playlist_repo),
        patch(
            "tv_app.interface.http.routes.playlist_history_routes.require_playlist_access",
            return_value=_access(playlist_id),
        ),
        patch.object(
            playlist_history_routes,
            "notify_presentation_changed",
            side_effect=lambda **kwargs: events.append("websocket"),
        ),
    ):
        response = playlist_history_routes.restore_playlist_history(
            _request(),
            playlist_id,
            history_id,
            playlist_history_routes.RestorePlaylistBody(
                expectedRevision=4,
                reason="Correção editorial",
            ),
        )

    assert response.status_code == 200
    assert events == ["commit", "websocket"]
    body = _response_body(response)["data"]
    assert body["playlist"]["revision"] == 5
    assert body["snapshotId"] == str(history_id)
    assert body["restoredFromSnapshotId"] == str(history_id)
    assert history_repo.restore.call_args.kwargs == {
        "expected_revision": 4,
        "actor_user_id": "user-1",
        "reason": "Correção editorial",
    }


def test_update_and_delete_slide_scope_mutation_by_playlist():
    playlist_id = uuid4()
    slide_id = uuid4()
    repo = MagicMock()
    repo.update_slide.return_value = {"id": str(slide_id)}

    with (
        patch.object(slide_routes, "_repo", repo),
        patch(
            "tv_app.interface.http.routes.slide_routes.require_playlist_access",
            return_value=_access(playlist_id),
        ),
        patch.object(slide_routes, "notify_presentation_changed"),
    ):
        update_response = slide_routes.update_slide(
            _request(),
            playlist_id,
            slide_id,
            slide_routes.UpdateSlideBody(title="Título"),
        )
        delete_response = slide_routes.delete_slide(_request(), playlist_id, slide_id)

    assert update_response.status_code == 200
    repo.update_slide.assert_called_once_with(
        playlist_id,
        slide_id,
        {"title": "Título"},
        actor_user_id="user-1",
        reason="slide_updated",
    )
    assert delete_response.status_code == 200
    repo.delete_slide.assert_called_once_with(
        playlist_id,
        slide_id,
        actor_user_id="user-1",
        reason="slide_deleted",
    )
