"""TV Custom GPT Actions — OpenAPI, security, digest, commit gates."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tv_app.application.gpt_actions import CUSTOM_GPT_CORS_ORIGINS, GPT_ACTIONS_OPERATION_IDS
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
    count_operations,
    resolve_gpt_actions_server_url,
)
from tv_app.application.gpt_actions.plan_digest import compute_plan_digest, digests_match
from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.services.data.tv_copilot_content_service import TvCopilotContentService
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    InMemoryIdempotencyRepository,
)
from tv_app.main import ALLOWED_ORIGINS, app, build_allowed_origins
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


def test_openapi_contract_limits_and_consequential():
    doc = build_gpt_actions_openapi(
        server_url="https://example.com/apps/tv-dashboard-api"
    )
    assert doc["openapi"].startswith("3.1")
    assert doc["servers"][0]["url"].startswith("https://")
    assert count_operations(doc) == 8
    assert "/gpt-actions/v1/openapi.json" not in (doc.get("paths") or {})
    ids = []
    for path, methods in doc["paths"].items():
        for method, op in methods.items():
            if not isinstance(op, dict):
                continue
            oid = op.get("operationId")
            assert oid and oid.startswith("gpt_")
            assert len(op.get("description") or "") <= 300
            for param in op.get("parameters") or []:
                assert len(param.get("description") or "") <= 700
            ids.append(oid)
            assert op.get("security") == [{"BearerAuth": []}]
            if oid == "gpt_commit_change":
                assert op.get("x-openai-isConsequential") is True
            else:
                assert not op.get("x-openai-isConsequential")
    assert ids == list(GPT_ACTIONS_OPERATION_IDS)
    assert "BearerAuth" in doc["components"]["securitySchemes"]


def test_resolve_server_url_uses_public_base_and_root():
    url = resolve_gpt_actions_server_url(
        public_base_url="https://minhadelpi.com.br",
        root_path="/apps/tv-dashboard-api",
    )
    assert url == "https://minhadelpi.com.br/apps/tv-dashboard-api"


def test_public_schema_exact_path_not_prefix():
    assert "/gpt-actions/v1/openapi.json" in PUBLIC_EXACT
    assert _is_public("/gpt-actions/v1/openapi.json")
    assert not _is_public("/gpt-actions/v1/catalog")
    assert not _is_public("/gpt-actions/v1/changes/commit")


def test_openapi_json_accessible_without_jwt():
    client = TestClient(app)
    response = client.get("/gpt-actions/v1/openapi.json")
    assert response.status_code == 200
    body = response.json()
    assert body["openapi"].startswith("3.1")
    assert count_operations(body) == 8


def test_catalog_requires_auth_when_middleware_active():
    client = TestClient(app)
    # Sem bypass: middleware exige JWT → 401
    response = client.get("/gpt-actions/v1/catalog")
    assert response.status_code in {401, 403}


def test_cors_includes_chatgpt_origins_and_keeps_existing():
    origins = set(build_allowed_origins())
    assert "https://chatgpt.com" in origins
    assert "https://chat.openai.com" in origins
    for origin in CUSTOM_GPT_CORS_ORIGINS:
        assert origin in set(ALLOWED_ORIGINS) or origin in origins


def test_plan_digest_deterministic_and_sensitive_to_actor_ops_revision():
    base = dict(
        actor_id="a1",
        target={"playlistId": "p1"},
        ops=[{"op": "add_blank_slide", "title": "X"}],
        catalog_version="2026.08.05.1",
        base_revision=3,
    )
    d1 = compute_plan_digest(**base)
    d2 = compute_plan_digest(**base)
    assert d1 == d2
    assert digests_match(d1, d2)
    assert compute_plan_digest(**{**base, "actor_id": "a2"}) != d1
    assert compute_plan_digest(**{**base, "base_revision": 4}) != d1
    assert (
        compute_plan_digest(
            **{**base, "ops": [{"op": "add_blank_slide", "title": "Y"}]}
        )
        != d1
    )


def test_catalog_projection_uses_authority_not_duplicate():
    user = _superadmin()
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.gpt_actions_routes.resolve_user",
            return_value=user,
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
    ):
        response = client.get("/gpt-actions/v1/catalog")
    assert response.status_code == 200
    data = response.json()["data"]
    authority = TvCopilotContentService.capability_catalog_document()
    assert data["catalogVersion"] == authority["catalogVersion"]
    assert data["allowedOps"] == authority["allowedOps"]
    assert isinstance(data["operations"], dict) and data["operations"]


def test_viewer_forbidden_on_commit():
    user = _viewer()
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.gpt_actions_routes.resolve_user",
            return_value=user,
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
    body = response.json()
    assert body.get("ok") is False
    assert body["error"]["code"] == "PERMISSION_DENIED"


def test_commit_stale_catalog_no_write():
    writes = MagicMock(spec=["create_playlist", "add_slide"])
    patch_svc = MagicMock()
    access = MagicMock()
    access.actor_id.return_value = "actor-1"
    service = TvGptCommitService(
        writes=writes,
        patch=patch_svc,
        access=access,
        idempotency=InMemoryIdempotencyRepository(),
    )
    with pytest.raises(GptActionsError) as caught:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={"playlistId": str(uuid4())},
            ops=[{"op": "add_blank_slide"}],
            catalog_version="stale-version",
            expected_revision=1,
            plan_digest="x",
            idempotency_key="idem-1",
        )
    assert caught.value.code == "CATALOG_VERSION_STALE"
    writes.create_playlist.assert_not_called()
    writes.add_slide.assert_not_called()


def test_commit_revision_conflict_no_write():
    from tv_app.application.services.tv_presentation_write_service import (
        RevisionConflictError,
    )

    playlist_id = uuid4()
    writes = MagicMock(spec=["assert_expected_revision", "add_slide", "create_playlist"])
    writes.assert_expected_revision.side_effect = RevisionConflictError(
        expected_revision=1,
        current_revision=9,
    )
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True)
    service = TvGptCommitService(
        writes=writes,
        patch=MagicMock(),
        access=access,
        idempotency=InMemoryIdempotencyRepository(),
    )
    with pytest.raises(GptActionsError) as caught:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={"playlistId": str(playlist_id)},
            ops=[{"op": "add_blank_slide", "title": "A"}],
            catalog_version=TvCopilotContentService.catalog_version(),
            expected_revision=1,
            plan_digest="x",
            idempotency_key="idem-rev",
        )
    assert caught.value.code == "REVISION_CONFLICT"
    writes.add_slide.assert_not_called()


def test_commit_partial_not_verified_integral():
    from tv_app.application.services.tv_presentation_write_service import (
        PresentationWriteError,
    )

    playlist_id = uuid4()
    slide_a = uuid4()
    writes = MagicMock(
        spec=[
            "assert_expected_revision",
            "get_revision",
            "add_slide",
            "list_slides",
            "list_sections",
            "get_playlist",
        ]
    )
    writes.assert_expected_revision.return_value = 1
    writes.get_revision.return_value = 2
    writes.add_slide.side_effect = [
        {"id": str(slide_a)},
        PresentationWriteError("boom", status_code=422),
    ]
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True)
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {"confirmationPolicy": "direct"}
    catalog = TvCopilotContentService.catalog_version()
    ops = [
        {"op": "add_blank_slide", "title": "A"},
        {"op": "add_blank_slide", "title": "B"},
    ]
    digest = compute_plan_digest(
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops,
        catalog_version=catalog,
        base_revision=1,
    )
    service = TvGptCommitService(
        writes=writes,
        patch=patch_svc,
        access=access,
        idempotency=InMemoryIdempotencyRepository(),
    )
    with pytest.raises(GptActionsError) as caught:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={"playlistId": str(playlist_id)},
            ops=ops,
            catalog_version=catalog,
            expected_revision=1,
            plan_digest=digest,
            idempotency_key="partial-key",
        )
    assert caught.value.code == "PARTIAL_COMMIT"
    assert caught.value.details.get("appliedOps")
    assert writes.add_slide.call_count == 2


def test_commit_plan_mismatch_no_write():
    playlist_id = uuid4()
    writes = MagicMock(spec=["assert_expected_revision", "get_revision", "add_slide", "create_playlist"])
    writes.assert_expected_revision.return_value = 2
    writes.get_revision.return_value = 2
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True)
    patch_svc = MagicMock()
    service = TvGptCommitService(
        writes=writes,
        patch=patch_svc,
        access=access,
        idempotency=InMemoryIdempotencyRepository(),
    )
    with pytest.raises(GptActionsError) as caught:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={"playlistId": str(playlist_id)},
            ops=[{"op": "add_blank_slide", "title": "A"}],
            catalog_version=TvCopilotContentService.catalog_version(),
            expected_revision=2,
            plan_digest="not-the-digest",
            idempotency_key="idem-2",
        )
    assert caught.value.code == "PLAN_MISMATCH"
    patch_svc.preview.assert_not_called()
    writes.add_slide.assert_not_called()


def test_commit_idempotent_replay_single_write():
    playlist_id = uuid4()
    slide_id = uuid4()
    writes = MagicMock(
        spec=[
            "assert_expected_revision",
            "get_revision",
            "add_slide",
            "list_slides",
            "list_sections",
            "get_playlist",
            "create_playlist",
        ]
    )
    writes.assert_expected_revision.return_value = 1
    writes.get_revision.side_effect = [1, 2, 2, 2]
    writes.add_slide.return_value = {"id": str(slide_id)}
    writes.list_slides.return_value = [{"id": str(slide_id), "nativeConfig": {}}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": str(playlist_id)}
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True)
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {
        "nativeConfig": None,
        "confirmationPolicy": "direct",
        "appliedOps": [{"op": "add_blank_slide"}],
    }
    ops = [{"op": "add_blank_slide", "title": "Hello"}]
    catalog = TvCopilotContentService.catalog_version()
    digest = compute_plan_digest(
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops,
        catalog_version=catalog,
        base_revision=1,
    )
    service = TvGptCommitService(
        writes=writes,
        patch=patch_svc,
        access=access,
        idempotency=InMemoryIdempotencyRepository(),
    )
    kwargs = dict(
        user=_superadmin(),
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops,
        catalog_version=catalog,
        expected_revision=1,
        plan_digest=digest,
        idempotency_key="replay-key",
    )
    first = service.commit(**kwargs)
    second = service.commit(**kwargs)
    assert first["status"] == "VERIFIED"
    assert second == first
    assert writes.add_slide.call_count == 1


def test_commit_idempotency_conflict_different_payload():
    playlist_id = uuid4()
    created = {"id": str(uuid4())}
    writes = MagicMock(
        spec=[
            "assert_expected_revision",
            "get_revision",
            "add_slide",
            "list_slides",
            "list_sections",
            "get_playlist",
            "create_playlist",
        ]
    )
    writes.assert_expected_revision.return_value = 1
    writes.get_revision.side_effect = [1, 2, 2]
    writes.add_slide.return_value = created
    writes.list_slides.return_value = [created]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": str(playlist_id)}

    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(can_edit=True)
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {"confirmationPolicy": "direct", "appliedOps": []}
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
    service = TvGptCommitService(
        writes=writes,
        patch=patch_svc,
        access=access,
        idempotency=InMemoryIdempotencyRepository(),
    )
    service.commit(
        user=_superadmin(),
        actor_id="actor-1",
        target={"playlistId": str(playlist_id)},
        ops=ops_a,
        catalog_version=catalog,
        expected_revision=1,
        plan_digest=digest_a,
        idempotency_key="same-key",
    )
    with pytest.raises(GptActionsError) as caught:
        service.commit(
            user=_superadmin(),
            actor_id="actor-1",
            target={"playlistId": str(playlist_id)},
            ops=ops_b,
            catalog_version=catalog,
            expected_revision=1,
            plan_digest=digest_b,
            idempotency_key="same-key",
        )
    assert caught.value.code == "IDEMPOTENCY_CONFLICT"


def test_preview_change_strips_http_commands():
    user = _superadmin()
    client = TestClient(app)
    fake_preview = {
        "appliedOps": [{"op": "add_blank_slide"}],
        "baseRevision": 5,
        "risk": "low",
        "confirmationPolicy": "direct",
        "sideEffectHints": [],
        "diff": {"ops": 1},
        "fingerprint": "fp",
        "httpCommands": [{"method": "POST", "path": "/playlists/x/slides"}],
        "message": "ok",
        "nativeConfig": {},
    }
    with (
        patch(
            "tv_app.interface.http.routes.gpt_actions_routes.resolve_user",
            return_value=user,
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.TvCopilotPatchService.preview",
            return_value=fake_preview,
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.PlaylistAccessService.actor_id",
            return_value="actor-1",
        ),
    ):
        response = client.post(
            "/gpt-actions/v1/changes/preview",
            json={
                "target": {"playlistId": str(uuid4())},
                "ops": [{"op": "add_blank_slide", "title": "T"}],
                "catalogVersion": TvCopilotContentService.catalog_version(),
            },
        )
    # May 404 if playlist access checked — mock access as editable
    # Re-run with access mock:
    with (
        patch(
            "tv_app.interface.http.routes.gpt_actions_routes.resolve_user",
            return_value=user,
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.TvCopilotPatchService.preview",
            return_value=fake_preview,
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.PlaylistAccessService.actor_id",
            return_value="actor-1",
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.PlaylistAccessService.resolve",
            return_value=SimpleNamespace(can_edit=True, can_read=True, level="owner"),
        ),
    ):
        response = client.post(
            "/gpt-actions/v1/changes/preview",
            json={
                "target": {"playlistId": str(uuid4())},
                "ops": [{"op": "add_blank_slide", "title": "T"}],
                "catalogVersion": TvCopilotContentService.catalog_version(),
            },
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "httpCommands" not in data
    assert data["persisted"] is False
    assert data["planDigest"]
    assert data["canCommit"] is True


def test_write_service_shared_by_slide_routes_module():
    from tv_app.interface.http.routes import slide_routes
    from tv_app.application.services.tv_presentation_write_service import (
        TvPresentationWriteService,
    )

    assert isinstance(slide_routes._writes, TvPresentationWriteService)
