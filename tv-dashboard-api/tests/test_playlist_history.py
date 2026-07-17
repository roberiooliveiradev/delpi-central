import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.application.services.playlist_history_change_service import (
    PlaylistHistoryChangeService,
)
from tv_app.infrastructure.persistence.repositories.playlist_history_repository import (
    HISTORY_LIMIT_PER_PLAYLIST,
    PlaylistHistoryRepository,
    PlaylistRevisionConflictError,
    _history_change,
    _history_summary,
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


def test_v009_adds_nullable_actor_snapshot_without_changing_v008():
    migrations = Path(playlist_history_routes.__file__).resolve().parents[4] / "migrations"
    v008 = (migrations / "V008__playlist_persistent_history.sql").read_text(
        encoding="utf-8"
    )
    v009 = (migrations / "V009__playlist_history_actor_snapshot.sql").read_text(
        encoding="utf-8"
    )

    assert "actor_name" not in v008
    assert "actor_email" not in v008
    assert "ADD COLUMN IF NOT EXISTS actor_name TEXT" in v009
    assert "ADD COLUMN IF NOT EXISTS actor_email TEXT" in v009
    assert "NOT NULL" not in v009


def test_capture_records_actor_reason_and_prunes_after_500():
    cursor = MagicMock()
    cursor.rowcount = 1
    playlist_id = uuid4()

    with patch(
        "tv_app.infrastructure.persistence.repositories.playlist_history_repository.get_current_user",
        return_value=SimpleNamespace(
            id="user-1", name="Robério Oliveira", email="roberio@delpi.com.br"
        ),
    ):
        PlaylistHistoryRepository.capture_before_mutation(
            cursor,
            playlist_id,
            actor_user_id="user-1",
            reason="slide_updated",
        )

    assert cursor.execute.call_count == 2
    capture_args = cursor.execute.call_args_list[0].args[1]
    prune_args = cursor.execute.call_args_list[1].args[1]
    assert capture_args == (
        "user-1",
        "Robério Oliveira",
        "roberio@delpi.com.br",
        "slide_updated",
        str(playlist_id),
    )
    assert prune_args[-1] == 500


def test_actor_snapshot_is_ignored_when_request_user_id_differs():
    with patch(
        "tv_app.infrastructure.persistence.repositories.playlist_history_repository.get_current_user",
        return_value=SimpleNamespace(
            id="other-user", name="Outro", email="outro@delpi.com.br"
        ),
    ):
        snapshot = PlaylistHistoryRepository._resolve_actor_snapshot("user-1")

    assert snapshot == {"name": None, "email": None}


def test_history_summary_exposes_immutable_actor_name_and_email():
    summary = _history_summary(
        {
            "id": uuid4(),
            "playlist_id": uuid4(),
            "revision": 4,
            "actor_user_id": "user-1",
            "actor_name": "Robério Oliveira",
            "actor_email": "roberio@delpi.com.br",
            "reason": "slide_updated",
            "created_at": datetime(2026, 7, 16, tzinfo=timezone.utc),
            "slide_count": 0,
            "playlist_name": "TV",
            "slide_titles": [],
        }
    )

    assert summary["authorName"] == "Robério Oliveira"
    assert summary["authorEmail"] == "roberio@delpi.com.br"


def test_change_compares_deep_values_and_summarizes_slide_changes():
    previous = {
        "playlist": {"id": "playlist-1", "name": "Antes", "dataDefaults": {"branch": "01"}},
        "slides": [
            {
                "id": "slide-1",
                "playlistId": "playlist-1",
                "sortOrder": 0,
                "title": "Primeiro",
                "nativeConfig": {"filters": {"branch": "01"}},
                "updatedAt": "old",
            },
            {"id": "slide-2", "sortOrder": 1, "title": "Removido"},
            {"id": "slide-3", "sortOrder": 2, "title": "Terceiro"},
        ],
    }
    next_state = {
        "playlist": {"id": "playlist-1", "name": "Depois", "dataDefaults": {"branch": "01"}},
        "slides": [
            {"id": "slide-3", "sortOrder": 0, "title": "Terceiro"},
            {
                "id": "slide-1",
                "playlistId": "ignored",
                "sortOrder": 1,
                "title": "Primeiro editado",
                "nativeConfig": {"filters": {"branch": "02"}},
                "updatedAt": "new",
            },
            {"id": "slide-4", "sortOrder": 2, "title": "Adicionado"},
        ],
    }

    change = PlaylistHistoryChangeService.compare(
        previous, next_state, compared_to_revision=5
    )

    assert change == {
        "available": True,
        "comparedToRevision": 5,
        "playlistFields": ["name"],
        "slides": {
            "added": [{"id": "slide-4", "title": "Adicionado"}],
            "removed": [{"id": "slide-2", "title": "Removido"}],
            "updated": [
                {
                    "id": "slide-1",
                    "title": "Primeiro editado",
                    "fields": ["nativeConfig", "title"],
                }
            ],
            "reordered": True,
        },
        "totals": {"added": 1, "removed": 1, "updated": 1},
    }


def test_change_is_unavailable_for_legacy_snapshot():
    change = PlaylistHistoryChangeService.compare(
        {"playlist": {"name": "Legado"}},
        {"playlist": {"name": "Atual"}, "slides": []},
        compared_to_revision=2,
    )

    assert change["available"] is False
    assert change["comparedToRevision"] is None


def test_history_change_uses_exact_next_revision_or_latest_live_state():
    revision_3 = {"playlist": {"name": "R3"}, "slides": []}
    revision_4 = {"playlist": {"name": "R4"}, "slides": []}
    live_revision_5 = {"playlist": {"name": "R5"}, "slides": []}

    from_next_snapshot = _history_change(
        {"revision": 3, "snapshot": revision_3, "next_snapshot": revision_4},
        current_revision=5,
        live_snapshot=live_revision_5,
    )
    from_live_state = _history_change(
        {"revision": 4, "snapshot": revision_4, "next_snapshot": None},
        current_revision=5,
        live_snapshot=live_revision_5,
    )

    assert from_next_snapshot["available"] is True
    assert from_next_snapshot["comparedToRevision"] == 4
    assert from_live_state["available"] is True
    assert from_live_state["comparedToRevision"] == 5


def test_history_change_marks_revision_gap_unavailable():
    change = _history_change(
        {
            "revision": 2,
            "snapshot": {"playlist": {"name": "R2"}, "slides": []},
            "next_snapshot": None,
        },
        current_revision=5,
        live_snapshot={"playlist": {"name": "R5"}, "slides": []},
    )

    assert change["available"] is False
    assert change["comparedToRevision"] is None


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
