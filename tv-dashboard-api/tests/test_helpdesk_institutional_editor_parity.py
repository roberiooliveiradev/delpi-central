"""Editor de fonte institucional usa a mesma identidade da apresentação."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import Request

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.data.institutional_presentation_sources import (
    INSTITUTIONAL_PRESENTATION_OPERATIONS,
    institutional_operations_from_configs,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.interface.http.routes import data_api_routes

HELPDESK = "get_helpdesk_dashboard_summary"
OTHER = "get_health"
PARAMS = {"start_date": "2026-10-01", "end_date": "2026-10-22"}


class _Gateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None, dict]] = []

    def fetch_by_operation_id(self, operation_id, *, params=None, authorization=None):
        self.calls.append((operation_id, authorization, dict(params or {})))
        overdue = None if authorization else 143
        counts = {
            "total_created_in_period": 166,
            "open": 107,
            "in_progress": 49,
            "resolved": 127,
            "pending": 0,
            "overdue": overdue,
            "pending_overdue": overdue,
        }
        return {
            "operationId": operation_id,
            "data": counts if operation_id == HELPDESK else {"status": "ok"},
            "meta": {"operationId": operation_id, "shape": "scalar", "fields": {}},
            "route": {
                "valueFields": list(counts) if operation_id == HELPDESK else ["status"],
                "valueFieldLabels": {},
                "valueFieldTypes": {},
            },
        }


def _block(operation_id: str, block_id: str) -> dict:
    return {
        "id": block_id,
        "type": "data_source",
        "dataBinding": {
            "operationId": operation_id,
            "displayMode": "kpi",
            "params": PARAMS if operation_id == HELPDESK else {},
        },
    }


def _service(gateway: _Gateway) -> ComunicadoDataEnrichmentService:
    return ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )


def _user():
    return SimpleNamespace(sub="editor-1", permissions=["tv.read"], is_superadmin=False)


def _overdue(block: dict):
    data = _data(block)
    if isinstance(data, dict) and "overdue" in data:
        return data["overdue"]
    return None


def _data(block: dict) -> dict | None:
    resolved = block.get("resolved") if isinstance(block, dict) else None
    data = resolved.get("data") if isinstance(resolved, dict) else None
    return data if isinstance(data, dict) else None


def setup_function() -> None:
    reset_comunicado_data_block_cache()


def test_missing_or_invalid_playlist_does_not_authorize_institutional_fetch():
    assert data_api_routes._persisted_institutional_operations(None) == frozenset()
    assert data_api_routes._persisted_institutional_operations("not-a-uuid") == frozenset()


def test_persisted_reader_uses_saved_slide_not_an_arbitrary_operation():
    from tv_app.application.services.data.institutional_presentation_sources import (
        persisted_institutional_operations,
    )

    class _Repo:
        def list_slides(self, playlist_id):
            assert playlist_id
            return [
                {
                    "nativeConfig": {
                        "blocks": [
                            {"dataBinding": {"operationId": OTHER}},
                            {"dataBinding": {"operationId": HELPDESK}},
                        ]
                    }
                }
            ]

    assert persisted_institutional_operations(uuid4(), repository=_Repo()) == frozenset({HELPDESK})


def test_only_persisted_helpdesk_source_is_institutional():
    found = institutional_operations_from_configs(
        [
            {
                "blocks": [
                    {"dataBinding": {"operationId": HELPDESK}},
                    {"dataBinding": {"operationId": OTHER}},
                ]
            }
        ]
    )
    assert found == INSTITUTIONAL_PRESENTATION_OPERATIONS
    assert institutional_operations_from_configs(
        [{"blocks": [{"dataBinding": {"operationId": OTHER}}]}]
    ) == frozenset()


def test_editor_bound_source_matches_presentation_and_keeps_other_routes_personal():
    gateway = _Gateway()
    service = _service(gateway)
    user = _user()
    blocks = [_block(HELPDESK, "helpdesk"), _block(OTHER, "health")]
    cfg = {"blocks": blocks}
    editor = service.enrich_blocks(
        blocks,
        cfg=cfg,
        authorization="Bearer person",
        user=user,
        institutional_operation_ids=frozenset({HELPDESK}),
    )
    presented = service.enrich_blocks(
        [_block(HELPDESK, "helpdesk")],
        cfg={"blocks": [_block(HELPDESK, "helpdesk")]},
        authorization=None,
        user=None,
    )
    by_op = {operation: auth for operation, auth, _params in gateway.calls}
    assert by_op[HELPDESK] is None
    assert by_op[OTHER] == "Bearer person"
    helpdesk_calls = [item for item in gateway.calls if item[0] == HELPDESK]
    assert helpdesk_calls == [(HELPDESK, None, PARAMS)]
    editor_data = _data(editor[0])
    presented_data = _data(presented[0])
    assert editor_data == presented_data
    assert editor_data == {
        "total_created_in_period": 166,
        "open": 107,
        "in_progress": 49,
        "resolved": 127,
        "pending": 0,
        "overdue": 143,
        "pending_overdue": 143,
    }


def test_unbound_helpdesk_preview_stays_personal_and_null_is_not_zero():
    gateway = _Gateway()
    service = _service(gateway)
    enriched = service.enrich_blocks(
        [_block(HELPDESK, "helpdesk")],
        cfg={"blocks": [_block(HELPDESK, "helpdesk")]},
        authorization="Bearer person",
        user=_user(),
        institutional_operation_ids=frozenset(),
    )
    assert gateway.calls == [(HELPDESK, "Bearer person", PARAMS)]
    assert _overdue(enriched[0]) is None


def test_personal_cache_does_not_satisfy_institutional_fetch():
    gateway = _Gateway()
    service = _service(gateway)
    user = _user()
    block = [_block(HELPDESK, "helpdesk")]
    cfg = {"blocks": block}
    personal = service.enrich_blocks(
        block,
        cfg=cfg,
        authorization="Bearer person",
        user=user,
    )
    institutional = service.enrich_blocks(
        block,
        cfg=cfg,
        authorization="Bearer person",
        user=user,
        institutional_operation_ids=frozenset({HELPDESK}),
    )
    assert _overdue(personal[0]) is None
    assert _overdue(institutional[0]) == 143
    assert gateway.calls == [
        (HELPDESK, "Bearer person", PARAMS),
        (HELPDESK, None, PARAMS),
    ]


def test_preview_block_denies_playlist_without_calling_the_resolver():
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer person"}
    body = data_api_routes.PreviewDataBlockBody(
        block=_block(HELPDESK, "helpdesk"),
        nativeConfig={"blocks": [_block(HELPDESK, "helpdesk")]},
        playlistId=str(uuid4()),
    )
    denied = MagicMock()
    with (
        patch.object(data_api_routes, "resolve_user", return_value=_user()),
        patch.object(data_api_routes, "assert_permission"),
        patch.object(data_api_routes, "require_playlist_access", return_value=denied),
        patch.object(data_api_routes, "_preview") as preview,
    ):
        result = data_api_routes.preview_data_block_v2(request, body)
    assert result is denied
    preview.preview_block.assert_not_called()


def test_preview_block_institutional_set_comes_from_persisted_playlist():
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer person"}
    playlist_id = str(uuid4())
    body = data_api_routes.PreviewDataBlockBody(
        block=_block(HELPDESK, "helpdesk"),
        nativeConfig={"blocks": [_block(OTHER, "health")]},
        playlistId=playlist_id,
    )
    user = _user()
    with (
        patch.object(data_api_routes, "resolve_user", return_value=user),
        patch.object(data_api_routes, "assert_permission"),
        patch.object(
            data_api_routes,
            "require_playlist_access",
            return_value=(user, MagicMock()),
        ),
        patch.object(
            data_api_routes,
            "persisted_institutional_operations",
            return_value=frozenset({HELPDESK}),
        ) as persisted,
        patch.object(data_api_routes, "_preview") as preview,
        patch.object(data_api_routes, "ok", side_effect=lambda payload: payload),
    ):
        preview.preview_block.return_value = {"id": "helpdesk", "resolved": {}}
        data_api_routes.preview_data_block_v2(request, body)
    persisted.assert_called_once()
    assert preview.preview_block.call_args.kwargs["institutional_operation_ids"] == frozenset(
        {HELPDESK}
    )
    assert preview.preview_block.call_args.kwargs["authorization"] == "Bearer person"


def test_unapproved_operation_stays_personal_even_if_caller_names_it():
    gateway = _Gateway()
    service = _service(gateway)
    service.enrich_blocks(
        [_block(OTHER, "health"), _block(HELPDESK, "helpdesk")],
        cfg={"blocks": [_block(OTHER, "health"), _block(HELPDESK, "helpdesk")]},
        authorization="Bearer person",
        user=_user(),
        institutional_operation_ids=frozenset({OTHER, HELPDESK}),
    )
    by_op = {operation: auth for operation, auth, _params in gateway.calls}
    assert by_op[OTHER] == "Bearer person"
    assert by_op[HELPDESK] is None


def test_missing_route_permission_does_not_resolve_the_source():
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer person"}
    body = data_api_routes.PreviewDataBlockBody(
        block=_block(HELPDESK, "helpdesk"),
        playlistId=str(uuid4()),
    )
    with (
        patch.object(data_api_routes, "resolve_user", return_value=_user()),
        patch.object(data_api_routes, "assert_permission", side_effect=PermissionError("denied")),
        patch.object(data_api_routes, "_preview") as preview,
        patch.object(data_api_routes, "persisted_institutional_operations") as persisted,
    ):
        result = data_api_routes.preview_data_block_v2(request, body)
    assert getattr(result, "status_code", None) == 403
    preview.preview_block.assert_not_called()
    persisted.assert_not_called()


def test_body_operation_without_persisted_binding_does_not_authorize_institutional_fetch():
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer person"}
    body = data_api_routes.PreviewDataBlockBody(
        block=_block(HELPDESK, "helpdesk"),
        nativeConfig={"blocks": [_block(HELPDESK, "helpdesk")]},
        playlistId=str(uuid4()),
    )
    user = _user()
    with (
        patch.object(data_api_routes, "resolve_user", return_value=user),
        patch.object(data_api_routes, "assert_permission"),
        patch.object(data_api_routes, "require_playlist_access", return_value=(user, MagicMock())),
        patch.object(
            data_api_routes,
            "persisted_institutional_operations",
            return_value=frozenset(),
        ),
        patch.object(data_api_routes, "_preview") as preview,
        patch.object(data_api_routes, "ok", side_effect=lambda payload: payload),
    ):
        preview.preview_block.return_value = {"id": "helpdesk", "resolved": {}}
        data_api_routes.preview_data_block_v2(request, body)
    assert preview.preview_block.call_args.kwargs["institutional_operation_ids"] == frozenset()


def test_preview_cache_key_changes_when_institutional_set_changes():
    from tv_app.application.services.data.m_query.m_phase7_quality_service import (
        preview_cache_key,
    )

    block = _block(HELPDESK, "helpdesk")
    common = {
        "block": block,
        "native_config": {"blocks": [block]},
        "playlist_defaults": {},
        "target_step_name": None,
        "preview_options": None,
        "user": _user(),
        "authorization": "Bearer person",
    }
    personal, _ = preview_cache_key(**common)
    institutional, _ = preview_cache_key(
        **common,
        institutional_operation_ids=frozenset({HELPDESK}),
    )
    assert personal != institutional


def test_editor_preview_and_public_presentation_share_persisted_institutional_source():
    from tv_app.application.services.presentation_payload_service import (
        PresentationPayloadService,
    )

    playlist_id = uuid4()
    native_config = {"blocks": [_block(HELPDESK, "blk_d0e9932a0a")]}
    playlist = {
        "id": str(playlist_id),
        "name": "Helpdesk",
        "publicToken": "public-token",
        "isActive": True,
        "defaultDurationSec": 30,
        "transitionStyle": "fade",
        "globalRefreshSec": 300,
        "viewportProfile": "1080p",
    }
    slide = {
        "id": "07ecd52e-5a35-4086-8478-01ff0a119899",
        "sortOrder": 1,
        "slideType": "native",
        "nativeScreenKey": "custom_message",
        "nativeConfig": native_config,
        "title": "Helpdesk",
        "isActive": True,
        "durationSec": 30,
    }
    repo = MagicMock()
    repo.get_by_id.return_value = playlist
    repo.get_by_token.return_value = playlist
    repo.list_sections.return_value = []
    repo.list_slides.return_value = [slide]
    native = MagicMock()
    native.resolve.return_value = {"blocks": []}
    comunicado = MagicMock()
    comunicado.enrich_master_config.return_value = {}
    service = PresentationPayloadService(
        repository=repo,
        native_data=native,
        comunicado_enrichment=comunicado,
    )
    user = _user()
    service.build_by_id(playlist_id, authorization="Bearer person", user=user)
    service.build_by_token("public-token", authorization=None, user=None)
    assert native.resolve.call_count == 2
    editor_call, public_call = native.resolve.call_args_list
    assert editor_call.kwargs["authorization"] == "Bearer person"
    assert editor_call.kwargs["institutional_operation_ids"] == frozenset({HELPDESK})
    assert public_call.kwargs["authorization"] is None
    assert public_call.kwargs["institutional_operation_ids"] == frozenset({HELPDESK})
    assert editor_call.kwargs["config"] == public_call.kwargs["config"]
