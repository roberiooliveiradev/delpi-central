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
    policy = TvCopilotContentService.aggregate_ops_policy(ops)
    assert public["risk"] == policy["risk"]
    assert public["confirmationPolicy"] == policy["confirmationPolicy"]
    assert public["sideEffectHints"] == policy["sideEffectHints"]


def test_preview_policy_from_catalog_authority_not_patch_echo():
    """Blocker B — policy comes from TvCopilotContentService, not patch metadata."""
    repo = MagicMock()
    writes = _writes_mock()
    dispatch = GptActionsDispatchService(
        repo=repo,
        writes=writes,
        commit=TvGptCommitService(
            writes=writes, idempotency=InMemoryIdempotencyRepository()
        ),
    )
    playlist_id = str(uuid4())
    slide_id = str(uuid4())
    catalog = TvCopilotContentService.catalog_version()

    cases = [
        ([{"op": "update_slide", "title": "X"}], "mutation", "direct", "refreshFilmstrip"),
        ([{"op": "delete_slide"}], "destructive", "confirm", None),
        (
            [{"op": "update_slide", "title": "X"}, {"op": "delete_slide"}],
            "destructive",
            "confirm",
            None,
        ),
    ]
    for ops, risk, confirm, hint in cases:
        expected = TvCopilotContentService.aggregate_ops_policy(ops)
        assert expected["risk"] == risk
        assert expected["confirmationPolicy"] == confirm
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
                    "appliedOps": [str(op["op"]) for op in ops],
                    "baseRevision": 1,
                    # Deliberately wrong — must be ignored for public policy fields.
                    "risk": "additive",
                    "confirmationPolicy": None,
                    "sideEffectHints": ["should-not-leak"],
                    "diff": {},
                    "fingerprint": "fp",
                    "message": "ok",
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
        assert public["risk"] == expected["risk"]
        assert public["confirmationPolicy"] == expected["confirmationPolicy"]
        assert public["sideEffectHints"] == expected["sideEffectHints"]
        if hint:
            assert hint in public["sideEffectHints"]
        assert public["persisted"] is False


def test_anonymous_gpt_actions_401_uses_error_envelope():
    client = TestClient(app)
    catalog = client.get("/gpt-actions/v1/catalog")
    assert catalog.status_code == 401
    body = catalog.json()
    assert body.get("ok") is False
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert body["error"]["retryable"] is False
    assert body["meta"]["correlationId"]

    commit = client.post(
        "/gpt-actions/v1/changes/commit",
        json={
            "ops": [{"op": "update_slide", "title": "nope"}],
            "catalogVersion": "x",
            "planDigest": "y",
        },
        headers={"Idempotency-Key": "anon-commit"},
    )
    assert commit.status_code == 401
    cbody = commit.json()
    assert cbody.get("ok") is False
    assert cbody["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert cbody["meta"]["correlationId"]

    schema = client.get("/gpt-actions/v1/openapi.json")
    assert schema.status_code == 200

    # Non-GPT TV paths keep shared middleware representation.
    playlists = client.get("/playlists")
    assert playlists.status_code == 401
    assert playlists.json() == {"detail": "Unauthorized"}
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


def _assert_object_schemas_have_properties(node: object, path: str = "") -> None:
    """type=object must be constructible: properties, typed map, or explicit opaque."""
    if isinstance(node, dict):
        if node.get("type") == "object" and "$ref" not in node:
            has_props = isinstance(node.get("properties"), dict) and bool(node.get("properties"))
            typed_map = isinstance(node.get("additionalProperties"), dict)
            opaque = node.get("x-delpi-gpt-opaque-object") is True
            empty_props = node.get("properties") == {}
            assert has_props or typed_map or (opaque and empty_props), path
        for key, value in node.items():
            if key == "example":
                continue
            _assert_object_schemas_have_properties(value, f"{path}/{key}")
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            _assert_object_schemas_have_properties(value, f"{path}[{idx}]")


def test_openapi_object_schemas_have_properties_for_gpt_builder():
    doc = build_gpt_actions_openapi(server_url="https://minhadelpi.com.br/apps/tv-dashboard-api")
    _assert_object_schemas_have_properties(doc)


def test_openapi_prepare_act_bodies_have_typed_examples_and_ops_oneof():
    doc = build_gpt_actions_openapi(server_url="https://minhadelpi.com.br/apps/tv-dashboard-api")
    body_ops = (
        "gpt_preview_data_block",
        "gpt_suggest_change",
        "gpt_preview_change",
        "gpt_commit_change",
    )
    found: dict[str, dict] = {}
    for path, methods in doc["paths"].items():
        for method, op in methods.items():
            if not isinstance(op, dict):
                continue
            oid = op.get("operationId")
            if oid in body_ops:
                found[oid] = op

    assert set(found) == set(body_ops)
    for oid, op in found.items():
        assert "requestBody" in op, oid
        content = op["requestBody"]["content"]["application/json"]
        assert "schema" in content
        assert "example" in content, oid
        example = content["example"]
        assert isinstance(example, dict)

    preview_ex = found["gpt_preview_change"]["requestBody"]["content"]["application/json"][
        "example"
    ]
    commit_ex = found["gpt_commit_change"]["requestBody"]["content"]["application/json"][
        "example"
    ]
    assert preview_ex["ops"][0]["op"] == "create_playlist"
    assert preview_ex["ops"][0]["name"] == "Testando a VISTA"
    assert commit_ex["ops"] == preview_ex["ops"]
    assert "expectedRevision" not in commit_ex
    assert "planDigest" in commit_ex
    assert commit_ex["catalogVersion"] == TvCopilotContentService.catalog_version()

    suggest_ex = found["gpt_suggest_change"]["requestBody"]["content"]["application/json"][
        "example"
    ]
    assert "Testando a VISTA" in suggest_ex["message"]

    ops_schema = found["gpt_preview_change"]["requestBody"]["content"]["application/json"][
        "schema"
    ]["properties"]["ops"]
    assert "oneOf" in ops_schema["items"]
    titles = {branch.get("title") for branch in ops_schema["items"]["oneOf"]}
    assert "create_playlist" in titles
    assert "update_slide" in titles
    assert "add_blank_slide" in titles

    # GET Actions must not invent empty bodies.
    for oid in ("gpt_get_catalog", "gpt_list_playlists", "gpt_get_playlist_context", "gpt_search_data_routes"):
        for path, methods in doc["paths"].items():
            get = methods.get("get")
            if isinstance(get, dict) and get.get("operationId") == oid:
                assert "requestBody" not in get, oid


def test_create_playlist_preview_then_commit_verified_family():
    """Incident family: create playlist 'Testando a VISTA' via preview → commit."""
    writes = _writes_mock()
    new_id = uuid4()
    writes.create_playlist.return_value = {
        "id": str(new_id),
        "name": "Testando a VISTA",
    }
    writes.get_revision.return_value = 1
    writes.list_slides.return_value = []
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {
        "id": str(new_id),
        "name": "Testando a VISTA",
    }
    ops = [{"op": "create_playlist", "name": "Testando a VISTA"}]
    catalog = TvCopilotContentService.catalog_version()
    repo = MagicMock()
    idem = InMemoryIdempotencyRepository()
    commit = TvGptCommitService(writes=writes, idempotency=idem)
    dispatch = GptActionsDispatchService(repo=repo, writes=writes, commit=commit)

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
                "appliedOps": ["create_playlist"],
                "baseRevision": None,
                "risk": "additive",
                "confirmationPolicy": "direct",
                "sideEffectHints": ["refreshFilmstrip"],
                "diff": {},
                "fingerprint": "fp",
                "httpCommands": [{"method": "POST", "path": "/playlists"}],
                "message": "ok",
                "nativeConfig": {},
            },
        ),
    ):
        preview = dispatch.preview_change(
            user=_superadmin(),
            target={},
            ops=ops,
            catalog_version=catalog,
            authorization=None,
        )

    assert preview["ops"] == ops
    assert "httpCommands" not in preview
    assert preview["planDigest"]
    assert preview.get("confirmationPolicy") == "direct"
    digest = preview["planDigest"]

    patch_svc = MagicMock()
    patch_svc.preview.return_value = {"confirmationPolicy": "direct"}
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
        idempotency_key="vista-create-playlist-1",
    )
    assert result["status"] == "VERIFIED"
    writes.create_playlist.assert_called_once()
    assert writes.create_playlist.call_args.kwargs["name"] == "Testando a VISTA"


def test_malformed_tool_payloads_return_gpt_error_envelope():
    client = TestClient(app)
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
        # Empty suggest message → 422 pydantic / validation envelope
        empty_msg = client.post(
            "/gpt-actions/v1/changes/suggest",
            json={"message": ""},
        )
        assert empty_msg.status_code in (400, 422)
        body = empty_msg.json()
        assert body.get("ok") is False or "error" in body or "detail" in body

        # Ops item missing op → application error envelope (not 500)
        bad_ops = client.post(
            "/gpt-actions/v1/changes/preview",
            json={
                "target": {},
                "ops": [{"name": "Testando a VISTA"}],
                "catalogVersion": TvCopilotContentService.catalog_version(),
            },
        )
        assert bad_ops.status_code < 500
        assert bad_ops.status_code >= 400

        # Ops as strings → rejected
        string_ops = client.post(
            "/gpt-actions/v1/changes/preview",
            json={
                "ops": ["create_playlist"],
                "catalogVersion": TvCopilotContentService.catalog_version(),
            },
        )
        assert string_ops.status_code < 500
        assert string_ops.status_code >= 400


def _ops_oneof_branches() -> list[dict]:
    doc = build_gpt_actions_openapi(server_url="https://minhadelpi.com.br/apps/tv-dashboard-api")
    preview = None
    for methods in doc["paths"].values():
        post = methods.get("post") if isinstance(methods, dict) else None
        if isinstance(post, dict) and post.get("operationId") == "gpt_preview_change":
            preview = post
            break
    assert preview is not None
    schema = preview["requestBody"]["content"]["application/json"]["schema"]
    return schema["properties"]["ops"]["items"]["oneOf"]


def _branch(name: str) -> dict:
    for item in _ops_oneof_branches():
        if item.get("title") == name:
            return item
    raise AssertionError(name)


def test_canonical_complex_ops_are_fully_typed_and_projected():
    canonical = TvCopilotContentService.operations()
    for name in (
        "patch_native_config",
        "reorder_slides",
        "set_data_transform",
        "upsert_block",
        "upsert_data_source",
        "create_playlist",
    ):
        schema = canonical[name]["inputSchema"]
        assert schema["type"] == "object"
        assert schema["properties"]
        branch = _branch(name)
        assert branch["properties"]
        assert branch.get("example")

    patch = _branch("patch_native_config")["properties"]["patch"]
    assert set(patch["properties"]) == {
        "background",
        "dataFilters",
        "speakerNotes",
        "groupTransforms",
    }
    assert patch.get("additionalProperties") is False

    items = _branch("reorder_slides")["properties"]["items"]
    assert items["items"]["required"] == ["id", "sortOrder"]
    assert items["items"]["properties"]["sortOrder"]["type"] == "integer"

    steps = _branch("set_data_transform")["properties"]["steps"]
    variants = {item["properties"]["op"]["const"] for item in steps["items"]["oneOf"]}
    assert "keepRows" in variants
    assert "select" in variants
    assert "filter" in variants

    labels = _branch("upsert_data_source")["properties"]["fieldLabels"]
    assert labels["additionalProperties"] == {"type": "string"}
    params = _branch("upsert_data_source")["properties"]["params"]
    assert isinstance(params["additionalProperties"], dict)

    block = _branch("upsert_block")["properties"]["block"]
    assert "text" in block["properties"]["type"]["enum"]
    assert block["properties"]["frame"]["properties"]


def test_gpt_request_opaque_objects_are_explicit():
    doc = build_gpt_actions_openapi(server_url="https://minhadelpi.com.br/apps/tv-dashboard-api")
    preview_data = None
    for methods in doc["paths"].values():
        post = methods.get("post") if isinstance(methods, dict) else None
        if isinstance(post, dict) and post.get("operationId") == "gpt_preview_data_block":
            preview_data = post
            break
    assert preview_data is not None
    props = preview_data["requestBody"]["content"]["application/json"]["schema"]["properties"]
    for key in ("block", "nativeConfig", "playlistDefaults", "previewOptions"):
        schema = props[key]
        assert schema["x-delpi-gpt-opaque-object"] is True
        assert schema["description"]

    details = doc["components"]["schemas"]["GptErrorEnvelope"]["properties"]["error"][
        "properties"
    ]["details"]
    assert details["x-delpi-gpt-opaque-object"] is True


def test_openapi_has_exactly_eight_stable_operation_ids():
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == 8
    found = []
    for methods in doc["paths"].values():
        for method, op in methods.items():
            if isinstance(op, dict) and op.get("operationId"):
                found.append(op["operationId"])
    assert found == list(GPT_ACTIONS_OPERATION_IDS)


def test_openapi_artifact_matches_builder():
    from pathlib import Path
    import json

    artifact = Path("docs/gpt-actions/openapi-gpt-actions.json")
    doc = build_gpt_actions_openapi()
    assert artifact.exists()
    on_disk = json.loads(artifact.read_text(encoding="utf-8"))
    assert on_disk == doc
    assert count_operations(on_disk) == 8


def test_dispatch_maps_nested_contract_error_to_invalid_change():
    from tv_app.application.services.data.tv_copilot_patch_service import TvCopilotPatchError

    repo = MagicMock()
    writes = _writes_mock()
    commit = TvGptCommitService(writes=writes, idempotency=InMemoryIdempotencyRepository())
    dispatch = GptActionsDispatchService(repo=repo, writes=writes, commit=commit)
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
            side_effect=TvCopilotPatchError("fieldLabels deve ser um mapa string→string."),
        ),
    ):
        with pytest.raises(GptActionsError) as exc:
            dispatch.preview_change(
                user=_superadmin(),
                target={"playlistId": str(uuid4()), "slideId": str(uuid4())},
                ops=[
                    {
                        "op": "upsert_data_source",
                        "operationId": "op.demo",
                        "fieldLabels": {"value": 10},
                    }
                ],
                catalog_version=TvCopilotContentService.catalog_version(),
                authorization=None,
            )
    assert exc.value.code == "INVALID_CHANGE"
    assert exc.value.status_code == 422
