"""TV-GPI-002A — acceptance fixes for Custom GPT Actions."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS
from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
    count_operations,
)
from tv_app.application.gpt_actions.plan_digest import compute_plan_digest
from tv_app.application.services.data.tv_copilot_content_service import TvCopilotContentService
from tv_app.application.services.data.tv_copilot_patch_service import TvCopilotPatchService
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
    TvPresentationWriteService,
)
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    InMemoryIdempotencyRepository,
)
from tv_app.main import app
from tv_app.middleware.auth_middleware import PUBLIC_EXACT, _is_public


async def _bypass_auth_middleware(request, call_next):
    return await call_next(request)


def _superadmin():
    return SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1")


def _viewer():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.read"],
        id="viewer-1",
    )


def _writes_mock(spec_extra: list[str] | None = None):
    base = [
        "assert_expected_revision",
        "get_revision",
        "add_slide",
        "add_slide_from_preset",
        "update_slide",
        "delete_slide",
        "reorder_slides",
        "add_section",
        "update_section",
        "delete_section",
        "reorder_sections",
        "list_slides",
        "list_sections",
        "get_playlist",
        "create_playlist",
    ]
    return MagicMock(spec=base + (spec_extra or []))


def test_openapi_error_envelope_and_success_schemas():
    doc = build_gpt_actions_openapi(server_url="https://example.com/apps/tv-dashboard-api")
    schemas = doc["components"]["schemas"]
    assert "GptSuccessEnvelope" in schemas
    assert "GptErrorEnvelope" in schemas
    commit = doc["paths"]["/gpt-actions/v1/changes/commit"]["post"]
    assert commit["responses"]["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/GptErrorEnvelope"
    }
    assert commit["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/GptSuccessEnvelope"
    }
    assert count_operations(doc) == 8
    assert list(GPT_ACTIONS_OPERATION_IDS)


def test_public_schema_exact_only():
    assert "/gpt-actions/v1/openapi.json" in PUBLIC_EXACT
    assert _is_public("/gpt-actions/v1/openapi.json")
    assert not _is_public("/gpt-actions/v1/catalog")


def test_preview_returns_typed_ops_not_string_applied_ops():
    """Real patch service returns appliedOps as list[str]; preview must expose typed ops."""
    repo = MagicMock()
    writes = TvPresentationWriteService(repo=repo)
    idem = InMemoryIdempotencyRepository()
    commit = TvGptCommitService(writes=writes, idempotency=idem)
    dispatch = GptActionsDispatchService(repo=repo, writes=writes, commit=commit)

    playlist_id = str(uuid4())
    slide_id = str(uuid4())
    ops = [{"op": "add_blank_slide", "title": "Hello GPT"}]
    catalog = TvCopilotContentService.catalog_version()

    with (
        patch.object(
            dispatch._access,
            "resolve",
            return_value=SimpleNamespace(can_edit=True, can_read=True, level="owner"),
        ),
        patch.object(dispatch._access, "actor_id", return_value="actor-1"),
        patch.object(
            TvCopilotPatchService,
            "preview",
            return_value={
                # Canonical shape: names only
                "appliedOps": ["add_blank_slide"],
                "baseRevision": 7,
                "risk": "low",
                "confirmationPolicy": "direct",
                "sideEffectHints": [],
                "diff": {},
                "fingerprint": "fp",
                "httpCommands": [{"method": "POST", "path": "/playlists/x/slides"}],
                "message": "ok",
                "nativeConfig": {},
            },
        ),
    ):
        public = dispatch.preview_change(
            user=_superadmin(),
            target={"playlistId": playlist_id, "slideId": slide_id},
            ops=ops,
            catalog_version=catalog,
            authorization=None,
        )

    assert public["ops"] == ops
    assert all(isinstance(item, dict) for item in public["ops"])
    assert public["operationNames"] == ["add_blank_slide"]
    assert "httpCommands" not in public
    expected_digest = compute_plan_digest(
        actor_id="actor-1",
        target={"playlistId": playlist_id, "slideId": slide_id},
        ops=ops,
        catalog_version=catalog,
        base_revision=7,
    )
    assert public["planDigest"] == expected_digest


def test_preview_ops_feed_commit_digest_match():
    repo = MagicMock()
    writes = _writes_mock()
    writes.assert_expected_revision.return_value = 3
    writes.get_revision.return_value = 4
    slide_id = uuid4()
    playlist_id = uuid4()
    writes.add_slide.return_value = {"id": str(slide_id), "title": "T"}
    writes.list_slides.return_value = [{"id": str(slide_id), "title": "T", "nativeConfig": {}}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": str(playlist_id)}
    idem = InMemoryIdempotencyRepository()
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {"confirmationPolicy": "direct", "nativeConfig": None}
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True)
    service = TvGptCommitService(
        writes=writes, idempotency=idem, patch=patch_svc, access=access
    )
    ops = [{"op": "add_blank_slide", "title": "T"}]
    catalog = TvCopilotContentService.catalog_version()
    digest = compute_plan_digest(
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops,
        catalog_version=catalog,
        base_revision=3,
    )
    result = service.commit(
        user=_superadmin(),
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops,
        catalog_version=catalog,
        expected_revision=3,
        plan_digest=digest,
        idempotency_key="feed-1",
    )
    assert result["status"] == "VERIFIED"


def test_expected_revision_required_for_existing_playlist():
    writes = _writes_mock()
    service = TvGptCommitService(
        writes=writes,
        idempotency=InMemoryIdempotencyRepository(),
        access=MagicMock(resolve=MagicMock(return_value=SimpleNamespace(can_edit=True))),
    )
    with pytest.raises(GptActionsError) as caught:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={"playlistId": str(uuid4())},
            ops=[{"op": "add_blank_slide", "title": "A"}],
            catalog_version=TvCopilotContentService.catalog_version(),
            expected_revision=None,
            plan_digest="x",
            idempotency_key="rev-missing",
        )
    assert caught.value.code == "INVALID_CHANGE"
    assert caught.value.status_code == 422
    writes.add_slide.assert_not_called()
    writes.create_playlist.assert_not_called()


def test_create_playlist_may_omit_expected_revision():
    writes = _writes_mock()
    new_id = uuid4()
    writes.create_playlist.return_value = {"id": str(new_id), "name": "Nova"}
    writes.get_revision.return_value = 1
    writes.list_slides.return_value = []
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": str(new_id), "name": "Nova"}
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {"confirmationPolicy": "direct"}
    ops = [{"op": "create_playlist", "name": "Nova"}]
    catalog = TvCopilotContentService.catalog_version()
    digest = compute_plan_digest(
        actor_id="actor-1",
        target={},
        ops=ops,
        catalog_version=catalog,
        base_revision=None,
    )
    service = TvGptCommitService(
        writes=writes,
        idempotency=InMemoryIdempotencyRepository(),
        patch=patch_svc,
        access=MagicMock(),
    )
    result = service.commit(
        user=_superadmin(),
        actor_id="actor-1",
        target={},
        ops=ops,
        catalog_version=catalog,
        expected_revision=None,
        plan_digest=digest,
        idempotency_key="create-ok",
    )
    assert result["status"] == "VERIFIED"
    writes.create_playlist.assert_called_once()


def test_idempotency_in_progress_does_not_execute_second_write():
    from tv_app.application.gpt_actions.plan_digest import compute_request_fingerprint

    playlist_id = str(uuid4())
    ops = [{"op": "add_blank_slide", "title": "A"}]
    catalog = TvCopilotContentService.catalog_version()
    digest = "x"
    fingerprint = compute_request_fingerprint(
        {
            "target": {"playlistId": playlist_id},
            "ops": ops,
            "catalogVersion": catalog,
            "expectedRevision": 1,
            "planDigest": digest,
        }
    )
    idem = InMemoryIdempotencyRepository()
    first = idem.acquire(
        key="k-ip",
        actor_user_id="actor-1",
        request_fingerprint=fingerprint,
    )
    assert first.status == "ACQUIRED"
    second = idem.acquire(
        key="k-ip",
        actor_user_id="actor-1",
        request_fingerprint=fingerprint,
    )
    assert second.status == "IN_PROGRESS"

    writes = _writes_mock()
    service = TvGptCommitService(
        writes=writes,
        idempotency=idem,
        patch=MagicMock(),
        access=MagicMock(resolve=MagicMock(return_value=SimpleNamespace(can_edit=True))),
    )
    with pytest.raises(GptActionsError) as caught:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={"playlistId": playlist_id},
            ops=ops,
            catalog_version=catalog,
            expected_revision=1,
            plan_digest=digest,
            idempotency_key="k-ip",
        )
    assert caught.value.code == "IDEMPOTENCY_IN_PROGRESS"
    assert caught.value.retryable is True
    writes.add_slide.assert_not_called()


def test_idempotency_replay_and_conflict():
    writes = _writes_mock()
    playlist_id = uuid4()
    slide_id = uuid4()
    writes.assert_expected_revision.return_value = 1
    writes.get_revision.return_value = 2
    writes.add_slide.return_value = {"id": str(slide_id), "title": "A"}
    writes.list_slides.return_value = [{"id": str(slide_id), "title": "A"}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": str(playlist_id)}
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {"confirmationPolicy": "direct"}
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True)
    service = TvGptCommitService(
        writes=writes,
        idempotency=InMemoryIdempotencyRepository(),
        patch=patch_svc,
        access=access,
    )
    catalog = TvCopilotContentService.catalog_version()
    ops_a = [{"op": "add_blank_slide", "title": "A"}]
    ops_b = [{"op": "add_blank_slide", "title": "B"}]
    digest_a = compute_plan_digest(
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops_a,
        catalog_version=catalog,
        base_revision=1,
    )
    digest_b = compute_plan_digest(
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops_b,
        catalog_version=catalog,
        base_revision=1,
    )
    first = service.commit(
        user=_superadmin(),
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops_a,
        catalog_version=catalog,
        expected_revision=1,
        plan_digest=digest_a,
        idempotency_key="same",
    )
    second = service.commit(
        user=_superadmin(),
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops_a,
        catalog_version=catalog,
        expected_revision=1,
        plan_digest=digest_a,
        idempotency_key="same",
    )
    assert first == second
    assert writes.add_slide.call_count == 1
    with pytest.raises(GptActionsError) as caught:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={"playlistId": str(playlist_id)},
            ops=ops_b,
            catalog_version=catalog,
            expected_revision=1,
            plan_digest=digest_b,
            idempotency_key="same",
        )
    assert caught.value.code == "IDEMPOTENCY_CONFLICT"


def test_partial_commit_replay_does_not_reexecute():
    writes = _writes_mock()
    playlist_id = uuid4()
    created = uuid4()
    writes.create_playlist.return_value = {"id": str(created), "name": "P"}
    writes.get_revision.return_value = 1
    writes.add_slide.side_effect = PresentationWriteError("boom", status_code=422)
    writes.list_slides.return_value = []
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": str(created), "name": "P"}
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {"confirmationPolicy": "direct"}
    service = TvGptCommitService(
        writes=writes,
        idempotency=InMemoryIdempotencyRepository(),
        patch=patch_svc,
        access=MagicMock(),
    )
    ops = [
        {"op": "create_playlist", "name": "P"},
        {"op": "add_blank_slide", "title": "X"},
    ]
    catalog = TvCopilotContentService.catalog_version()
    digest = compute_plan_digest(
        actor_id="actor-1",
        target={},
        ops=ops,
        catalog_version=catalog,
        base_revision=None,
    )
    with pytest.raises(GptActionsError) as first:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={},
            ops=ops,
            catalog_version=catalog,
            expected_revision=None,
            plan_digest=digest,
            idempotency_key="partial-1",
        )
    assert first.value.code == "PARTIAL_COMMIT"
    assert writes.create_playlist.call_count == 1
    with pytest.raises(GptActionsError) as second:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={},
            ops=ops,
            catalog_version=catalog,
            expected_revision=None,
            plan_digest=digest,
            idempotency_key="partial-1",
        )
    assert second.value.code == "PARTIAL_COMMIT"
    assert writes.create_playlist.call_count == 1
    assert writes.add_slide.call_count == 1


def test_postcondition_update_move_reorder_section_native():
    writes = _writes_mock()
    playlist_id = uuid4()
    slide_id = uuid4()
    section_id = uuid4()
    writes.assert_expected_revision.return_value = 1
    writes.get_revision.return_value = 2
    writes.update_slide.return_value = {"id": str(slide_id)}
    writes.reorder_slides.return_value = []
    writes.update_section.return_value = {"id": str(section_id), "name": "S2"}
    writes.reorder_sections.return_value = []
    writes.list_slides.return_value = [
        {
            "id": str(slide_id),
            "title": "New",
            "durationSec": 40,
            "isActive": True,
            "sectionId": str(section_id),
            "sortOrder": 1,
            "nativeConfig": {"version": 5, "blocks": [{"id": "b1", "type": "text", "text": "Hi"}]},
        }
    ]
    writes.list_sections.return_value = [
        {"id": str(section_id), "name": "S2", "isCollapsed": False, "sortOrder": 0}
    ]
    writes.get_playlist.return_value = {"id": str(playlist_id)}
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {
        "confirmationPolicy": "direct",
        "nativeConfig": {
            "version": 5,
            "blocks": [{"id": "b1", "type": "text", "text": "Hi"}],
            "resolved": {"ignore": True},
        },
    }
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True)
    service = TvGptCommitService(
        writes=writes,
        idempotency=InMemoryIdempotencyRepository(),
        patch=patch_svc,
        access=access,
    )
    ops = [
        {"op": "update_slide", "title": "New", "durationSec": 40, "isActive": True},
        {"op": "move_slide_to_section", "sectionId": str(section_id)},
        {
            "op": "reorder_slides",
            "items": [{"id": str(slide_id), "sortOrder": 1}],
        },
        {"op": "upsert_section", "sectionId": str(section_id), "name": "S2"},
        {
            "op": "reorder_sections",
            "items": [{"id": str(section_id), "sortOrder": 0}],
        },
        {"op": "upsert_block", "block": {"id": "b1"}},
    ]
    catalog = TvCopilotContentService.catalog_version()
    digest = compute_plan_digest(
        actor_id="actor-1",
        target={"playlistId": str(playlist_id), "slideId": str(slide_id)},
        ops=ops,
        catalog_version=catalog,
        base_revision=1,
    )
    result = service.commit(
        user=_superadmin(),
        actor_id="actor-1",
        target={"playlistId": str(playlist_id), "slideId": str(slide_id)},
        ops=ops,
        catalog_version=catalog,
        expected_revision=1,
        plan_digest=digest,
        idempotency_key="post-1",
    )
    assert result["status"] == "VERIFIED"
    assert result["verified"] is True


def test_postcondition_negative_update_mismatch_not_verified():
    writes = _writes_mock()
    playlist_id = uuid4()
    slide_id = uuid4()
    writes.assert_expected_revision.return_value = 1
    writes.get_revision.return_value = 2
    writes.update_slide.return_value = {"id": str(slide_id)}
    # Persisted title differs from requested
    writes.list_slides.return_value = [{"id": str(slide_id), "title": "OTHER"}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": str(playlist_id)}
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {"confirmationPolicy": "direct"}
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True)
    service = TvGptCommitService(
        writes=writes,
        idempotency=InMemoryIdempotencyRepository(),
        patch=patch_svc,
        access=access,
    )
    ops = [{"op": "update_slide", "title": "Expected"}]
    catalog = TvCopilotContentService.catalog_version()
    digest = compute_plan_digest(
        actor_id="actor-1",
        target={"playlistId": str(playlist_id), "slideId": str(slide_id)},
        ops=ops,
        catalog_version=catalog,
        base_revision=1,
    )
    with pytest.raises(GptActionsError) as caught:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={"playlistId": str(playlist_id), "slideId": str(slide_id)},
            ops=ops,
            catalog_version=catalog,
            expected_revision=1,
            plan_digest=digest,
            idempotency_key="post-neg",
        )
    assert caught.value.code == "OUTCOME_NOT_VERIFIED"


def test_gpt_pydantic_422_uses_error_envelope():
    client = TestClient(app)
    with patch(
        "tv_app.middleware.auth_middleware._base_jwt_middleware",
        side_effect=_bypass_auth_middleware,
    ), patch(
        "tv_app.interface.http.routes.gpt_actions_routes.resolve_user",
        return_value=_superadmin(),
    ):
        response = client.post("/gpt-actions/v1/changes/commit", json={"ops": []})
    assert response.status_code == 422
    body = response.json()
    assert body.get("ok") is False
    assert "error" in body and body["error"]["code"] == "INVALID_CHANGE"
    assert "meta" in body and "correlationId" in body["meta"]


def test_application_layer_ports_no_concrete_postgres():
    from pathlib import Path
    import re

    app_root = Path(__file__).resolve().parents[1] / "tv_app" / "application"
    gpt_files = list((app_root / "gpt_actions").glob("*.py"))
    write_file = app_root / "services" / "tv_presentation_write_service.py"
    ports_dir = app_root / "ports"
    ports_files = list(ports_dir.glob("*.py")) if ports_dir.is_dir() else []
    boundary = gpt_files + [write_file] + ports_files
    infra_import = re.compile(
        r"(?:from|import)\s+tv_app\.infrastructure\b|"
        r"import\s+tv_app\.infrastructure\b"
    )
    for path in boundary:
        text = path.read_text(encoding="utf-8")
        assert "PostgresIdempotencyRepository" not in text
        assert "plugins_postgres_connection" not in text
        assert "PlaylistRepository()" not in text
        assert not infra_import.search(text), (
            f"{path.relative_to(app_root.parent.parent)} must not import tv_app.infrastructure"
        )
    write_src = write_file.read_text(encoding="utf-8")
    assert "PresentationRepositoryPort" in write_src
    assert "from tv_app.application.errors" in write_src or "playlist_persistence" in write_src


def test_invalid_playlist_uuid_completes_idempotency_and_replays():
    writes = _writes_mock()
    idem = InMemoryIdempotencyRepository()
    service = TvGptCommitService(
        writes=writes,
        idempotency=idem,
        patch=MagicMock(),
        access=MagicMock(),
    )
    catalog = TvCopilotContentService.catalog_version()
    target = {"playlistId": "not-a-uuid"}
    ops = [{"op": "add_blank_slide", "title": "A"}]
    digest = compute_plan_digest(
        actor_id="actor-1",
        target=target,
        ops=ops,
        catalog_version=catalog,
        base_revision=1,
    )
    with pytest.raises(GptActionsError) as first:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target=target,
            ops=ops,
            catalog_version=catalog,
            expected_revision=1,
            plan_digest=digest,
            idempotency_key="bad-uuid-key",
        )
    assert first.value.code == "INVALID_CHANGE"
    assert first.value.status_code == 422
    writes.assert_expected_revision.assert_not_called()
    writes.add_slide.assert_not_called()
    writes.create_playlist.assert_not_called()

    with pytest.raises(GptActionsError) as replay:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target=target,
            ops=ops,
            catalog_version=catalog,
            expected_revision=1,
            plan_digest=digest,
            idempotency_key="bad-uuid-key",
        )
    assert replay.value.code == "INVALID_CHANGE"
    assert replay.value.status_code == 422
    assert replay.value.code != "IDEMPOTENCY_IN_PROGRESS"

    ops_other = [{"op": "add_blank_slide", "title": "B"}]
    digest_other = compute_plan_digest(
        actor_id="actor-1",
        target=target,
        ops=ops_other,
        catalog_version=catalog,
        base_revision=1,
    )
    with pytest.raises(GptActionsError) as conflict:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target=target,
            ops=ops_other,
            catalog_version=catalog,
            expected_revision=1,
            plan_digest=digest_other,
            idempotency_key="bad-uuid-key",
        )
    assert conflict.value.code == "IDEMPOTENCY_CONFLICT"


def test_viewer_forbidden_on_commit_http():
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.gpt_actions_routes.resolve_user",
            return_value=_viewer(),
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
    ):
        response = client.post(
            "/gpt-actions/v1/changes/commit",
            json={
                "target": {"playlistId": str(uuid4())},
                "ops": [{"op": "add_blank_slide", "title": "A"}],
                "catalogVersion": TvCopilotContentService.catalog_version(),
                "expectedRevision": 1,
                "planDigest": "deadbeef",
            },
            headers={"Idempotency-Key": "k1"},
        )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_catalog_and_openapi_http_smoke():
    client = TestClient(app)
    assert client.get("/gpt-actions/v1/openapi.json").status_code == 200
    with (
        patch(
            "tv_app.interface.http.routes.gpt_actions_routes.resolve_user",
            return_value=_superadmin(),
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
    ):
        response = client.get("/gpt-actions/v1/catalog")
    assert response.status_code == 200
    assert response.json()["data"]["catalogVersion"] == TvCopilotContentService.catalog_version()
