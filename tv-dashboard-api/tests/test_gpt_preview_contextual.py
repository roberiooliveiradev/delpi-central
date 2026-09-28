"""GPT Actions — preview contextual de data_source e gate executável de dados.

Reproduz o caso real pct2_weg_sc_y25 + pct2_weg_sc_y26: uma fonte compõe o
resultado de outra via merge; o preview por Action deve usar o contexto do
slide (persistido ou candidate) em vez de um nativeConfig de um único bloco.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.data.slide_data_resolution_service import (
    SlideDataResolutionService,
)
from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService
from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService

_OP = "get_commercial_rol_summary"


@pytest.fixture(autouse=True)
def _clear_data_cache():
    reset_comunicado_data_block_cache()
    yield
    reset_comunicado_data_block_cache()


def _user():
    return SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1")


def _gateway(payload_by_sid: dict[str, dict], fails: dict[str, Exception] | None = None):
    """Mock keyed por `branch` real: y25 → branch "02", y26 → branch "01"."""
    gateway = MagicMock()

    def _fetch(operation_id, params=None, **kw):
        sid = {"02": "prev", "01": "cur"}.get(str((params or {}).get("branch")))
        if fails and sid in fails:
            raise fails[sid]
        return payload_by_sid[sid]

    gateway.fetch_by_operation_id.side_effect = _fetch
    return gateway


def _rol_payload(value: float) -> dict:
    """Shape fiel de get_commercial_rol_summary com meta SI anexada.

    goal é um objeto aninhado — a presença dele não pode rebaixar os
    campos autoritativos para a tabela de apresentação campo/valor.
    """
    return {
        "meta": {"shape": "scalar", "entity": "commercial_rol_summary"},
        "data": {
            "branch": "01",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "rol": value,
            "comparable_goal": 1000000.0,
            "rol_target_pct": 88.0,
            "goal_value": 1000000.0,
            "reference_goal": 950000.0,
            "goal": {
                "goal_label": "Meta anual",
                "comparable_goal": 1000000.0,
                "goal_periodicity": "monthly",
                "goal_scope": {"branch": "01"},
            },
        },
        "route": {"label": "ROL", "valueFields": ["rol"]},
    }


def _source(
    block_id: str,
    sid: str,
    steps: list[dict] | None = None,
    frame: dict | None = None,
) -> dict:
    block = {
        "id": block_id,
        "type": "data_source",
        "frame": frame
        or {"x": 4, "y": 4 if sid == "prev" else 16, "w": 20, "h": 8},
        "dataBinding": {
            "operationId": _OP,
            "params": {
                "branch": "02" if sid == "prev" else "01",
                "customer_segment": "weg",
                "dateRangePreset": "this_year",
            },
        },
    }
    if steps:
        block["dataTransform"] = {"steps": steps}
    return block


def _prev_source() -> dict:
    return _source(
        "pct2_weg_sc_y25",
        "prev",
        steps=[
            {"op": "rename", "from": "rol", "to": "rol_prev"},
            {"op": "addColumn", "name": "join_key", "expr": "1"},
        ],
    )


def _cur_source() -> dict:
    return _source(
        "pct2_weg_sc_y26",
        "cur",
        steps=[
            {"op": "addColumn", "name": "join_key", "expr": "1"},
            {
                "op": "merge",
                "sourceId": "pct2_weg_sc_y25",
                "leftKey": "join_key",
                "rightKey": "join_key",
                "columns": ["rol_prev"],
            },
            {
                "op": "addColumn",
                "name": "value",
                "expr": "(rol / rol_prev - 1) * 100",
            },
        ],
    )


def _dispatch_for(
    *,
    payloads: dict[str, dict],
    fails: dict[str, Exception] | None = None,
    slide: dict | None = None,
    playlist: dict | None = None,
) -> GptActionsDispatchService:
    gateway = _gateway(payloads, fails)
    catalog = TvDataRouteCatalogService()
    enrichment = ComunicadoDataEnrichmentService(catalog=catalog, gateway=gateway)
    preview = TvDataPreviewService(
        catalog=catalog,
        enrichment=enrichment,
        resolution=SlideDataResolutionService(catalog=catalog, enrichment=enrichment),
    )
    writes = MagicMock()
    writes.get_slide.side_effect = lambda slide_id, playlist_id=None: (
        slide
        if slide is not None and str(slide.get("id")) == str(slide_id)
        else (_ for _ in ()).throw(Exception("slide not found"))
    )
    writes.list_slides.return_value = [slide] if slide else []
    access = MagicMock()
    access.resolve.return_value = PlaylistAccess(
        level="owner", playlist=playlist or {"id": "pl", "dataDefaults": {}}
    )
    access.actor_id.return_value = "actor-1"
    return GptActionsDispatchService(
        repo=MagicMock(),
        writes=writes,
        commit=MagicMock(),
        access=access,
        preview=preview,
    )


_SLIDE_ID = "00000000-0000-0000-0000-000000000002"
_PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"


def _slide() -> dict:
    return {
        "id": _SLIDE_ID,
        "nativeConfig": {
            "version": 5,
            "blocks": [_prev_source(), _cur_source()],
        },
    }


class TestContextualPreviewRepro:
    def test_engine_direct_two_sources_pass(self):
        """Prova: engine canônico resolve o merge quando ambas as fontes existem."""
        payloads = {"prev": _rol_payload(4399153.22), "cur": _rol_payload(4516461.10)}
        enrichment = ComunicadoDataEnrichmentService(
            catalog=TvDataRouteCatalogService(), gateway=_gateway(payloads)
        )
        enriched = enrichment.enrich_blocks(
            [_prev_source(), _cur_source()],
            cfg={"version": 5, "blocks": [_prev_source(), _cur_source()]},
            authorization=None,
        )
        resolved = next(
            b["resolved"] for b in enriched if b.get("id") == "pct2_weg_sc_y26"
        )
        row = (resolved["_queryTable"]["rows"] or [])[0]
        assert row["value"] == pytest.approx(2.6667, abs=0.01)

    def test_action_block_only_fails_without_context(self):
        """Action com block isolado (sem slide/nativeConfig): sibling ausente."""
        payloads = {"prev": _rol_payload(4399153.22), "cur": _rol_payload(4516461.10)}
        dispatch = _dispatch_for(payloads=payloads)
        result = dispatch.preview_data_block(
            user=_user(),
            body={"block": _cur_source()},
            authorization=None,
        )
        resolved = self._resolved_of(result)
        assert resolved.get("transformError", {}).get("code") == (
            "m.merge_source_unavailable"
        )

    def test_action_candidate_nativeconfig_context_passes(self):
        """Candidate state: block+nativeConfig fornecidos pela Action."""
        payloads = {"prev": _rol_payload(4399153.22), "cur": _rol_payload(4516461.10)}
        dispatch = _dispatch_for(payloads=payloads)
        result = dispatch.preview_data_block(
            user=_user(),
            body={
                "block": _cur_source(),
                "nativeConfig": {
                    "version": 5,
                    "blocks": [_prev_source(), _cur_source()],
                },
            },
            authorization=None,
        )
        resolved = self._resolved_of(result)
        assert not resolved.get("error")
        row = (resolved["_queryTable"]["rows"] or [])[0]
        assert row["value"] == pytest.approx(2.6667, abs=0.01)

    def test_action_slide_context_resolves_sibling(self):
        """playlistId+slideId+blockId: preview usa o nativeConfig persistido."""
        payloads = {"prev": _rol_payload(4399153.22), "cur": _rol_payload(4516461.10)}
        dispatch = _dispatch_for(payloads=payloads, slide=_slide())
        result = dispatch.preview_data_block(
            user=_user(),
            body={
                "playlistId": _PLAYLIST_ID,
                "slideId": _SLIDE_ID,
                "blockId": "pct2_weg_sc_y26",
            },
            authorization=None,
        )
        resolved = self._resolved_of(result)
        assert not resolved.get("error")
        row = (resolved["_queryTable"]["rows"] or [])[0]
        assert row["value"] == pytest.approx(2.6667, abs=0.01)

    def _resolved_of(self, result: dict) -> dict:
        block = result.get("block") if isinstance(result.get("block"), dict) else {}
        return block.get("resolved") or result.get("resolved") or {}




# ---------------------------------------------------------------------------
# gpt_preview_change — gate executável de dados no candidate state
# ---------------------------------------------------------------------------


class _GateRepo:
    """Repo mínimo para o patch service no fluxo de preview/commit_now."""

    def __init__(self, slide: dict | None = None) -> None:
        self._slide = slide or {
            "id": _SLIDE_ID,
            "nativeConfig": {"version": 5, "blocks": []},
        }
        self.updated: list[dict] = []

    def get_by_id(self, playlist_id):
        return {
            "id": str(playlist_id),
            "dataDefaults": {"branch": "01"},
            "revision": 7,
        }

    def get_slide(self, slide_id, *, playlist_id=None):
        from tv_app.infrastructure.persistence.repositories.playlist_repository import (
            SlideNotFoundError,
        )

        if str(slide_id) != self._slide["id"]:
            raise SlideNotFoundError(str(slide_id))
        return dict(self._slide)


def _patch_service(payloads, fails=None, *, slide=None):
    from tv_app.application.services.data.presentation_mutation.patch_service import (
        PresentationPatchService,
    )

    catalog = TvDataRouteCatalogService()
    enrichment = ComunicadoDataEnrichmentService(
        catalog=catalog,
        gateway=_gateway(payloads, fails),
    )
    return PresentationPatchService(
        catalog=catalog,
        repo=_GateRepo(slide),
        resolution=SlideDataResolutionService(catalog=catalog, enrichment=enrichment),
    )


def _upsert_prev_op() -> dict:
    return {
        "op": "upsert_data_source",
        "operationId": _OP,
        "blockId": "pct2_weg_sc_y25",
        "params": {
            "branch": "02",
            "customer_segment": "weg",
            "dateRangePreset": "same_period_previous_year",
        },
        "dataTransform": {
            "steps": [
                {"op": "rename", "from": "rol", "to": "rol_prev"},
                {"op": "addColumn", "name": "join_key", "expr": "1"},
            ]
        },
    }


def _upsert_cur_op(*, merge_source: str = "pct2_weg_sc_y25") -> dict:
    return {
        "op": "upsert_data_source",
        "operationId": _OP,
        "blockId": "pct2_weg_sc_y26",
        "params": {
            "branch": "01",
            "customer_segment": "weg",
            "dateRangePreset": "this_year",
        },
        "dataTransform": {
            "steps": [
                {"op": "addColumn", "name": "join_key", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": merge_source,
                    "leftKey": "join_key",
                    "rightKey": "join_key",
                    "columns": ["rol_prev"],
                },
                {
                    "op": "addColumn",
                    "name": "value",
                    "expr": "(rol / rol_prev - 1) * 100",
                },
            ]
        },
    }


def _preview_envelope(ops: list[dict]) -> dict:
    return {
        "target": {"playlistId": _PLAYLIST_ID, "slideId": _SLIDE_ID},
        "ops": ops,
    }


class TestPreviewChangeDataExecutionGate:
    def test_valid_candidate_can_commit(self):
        svc = _patch_service(
            {"prev": _rol_payload(4399153.22), "cur": _rol_payload(4516461.10)}
        )
        result = svc.preview(
            _preview_envelope([_upsert_prev_op(), _upsert_cur_op()]),
            user=_user(),
        )
        assert result["nativeConfig"]
        assert result["fingerprint"]

    def test_invalid_candidate_rejected_with_typed_error(self):
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchError,
        )

        svc = _patch_service({"cur": _rol_payload(4516461.10)})
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope([_upsert_cur_op()]),
                user=_user(),
            )
        assert exc.value.code == "m.merge_source_unavailable"
        assert exc.value.details["blockId"] == "pct2_weg_sc_y26"
        assert exc.value.details["dependencySourceId"] == "pct2_weg_sc_y25"
        assert exc.value.details["stage"] == "data_execution"

    def test_failed_dependency_propagates(self):
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchError,
        )

        svc = _patch_service(
            {"cur": _rol_payload(4516461.10), "prev": _rol_payload(4399153.22)},
            fails={"prev": Exception("upstream down")},
        )
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope([_upsert_prev_op(), _upsert_cur_op()]),
                user=_user(),
            )
        assert exc.value.code in {"m.merge_source_failed", "m.merge_source_unavailable"}

    def test_set_data_transform_breaking_existing_source_rejected(self):
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchError,
        )

        slide = {
            "id": _SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [_prev_source(), _cur_source()],
            },
        }
        svc = _patch_service(
            {"cur": _rol_payload(4516461.10), "prev": _rol_payload(4399153.22)},
            slide=slide,
        )
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope(
                    [
                        {
                            "op": "set_data_transform",
                            "blockId": "pct2_weg_sc_y26",
                            "steps": [
                                {
                                    "op": "merge",
                                    "sourceId": "ghost_src",
                                    "leftKey": "join_key",
                                    "rightKey": "join_key",
                                    "columns": ["rol_prev"],
                                }
                            ],
                        }
                    ]
                ),
                user=_user(),
            )
        assert exc.value.code == "m.merge_source_unavailable"

    def test_visual_only_op_skips_data_execution(self):
        svc = _patch_service({"cur": _rol_payload(4516461.10)})
        svc._resolution = MagicMock()
        svc._resolution.resolve_blocks = MagicMock(
            side_effect=AssertionError("resolve_blocks should not run")
        )
        result = svc.preview(
            _preview_envelope(
                [{"op": "update_slide", "slideId": _SLIDE_ID, "title": "Novo título"}]
            ),
            user=_user(),
        )
        assert result
        svc._resolution.resolve_blocks.assert_not_called()

    def _dispatch_with_gate(self, payloads, fails=None, *, slide=None):
        from tv_app.application.gpt_actions.commit_service import TvGptCommitService
        from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
            InMemoryIdempotencyRepository,
        )
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchService,
        )

        catalog = TvDataRouteCatalogService()
        enrichment = ComunicadoDataEnrichmentService(
            catalog=catalog,
            gateway=_gateway(payloads, fails),
        )
        writes = MagicMock()
        writes.assert_expected_revision = Mock(return_value=None)
        persisted = slide or {
            "id": _SLIDE_ID,
            "nativeConfig": {"version": 5, "blocks": []},
        }

        def _update_slide(playlist_id, slide_id, payload, **kw):
            if "nativeConfig" in payload:
                persisted["nativeConfig"] = payload["nativeConfig"]
            return dict(persisted)

        writes.update_slide.side_effect = _update_slide
        writes.list_slides.side_effect = lambda *a, **kw: [persisted]
        writes.list_sections.return_value = []
        writes.get_playlist.return_value = {"id": _PLAYLIST_ID}
        writes.get_revision.return_value = 8
        access = MagicMock()
        access.resolve.return_value = PlaylistAccess(
            level="owner", playlist={"id": _PLAYLIST_ID, "dataDefaults": {}}
        )
        access.actor_id.return_value = "actor-1"
        patch_svc = PresentationPatchService(
            catalog=catalog,
            repo=_GateRepo(slide),
            resolution=SlideDataResolutionService(
                catalog=catalog, enrichment=enrichment
            ),
        )
        dispatch = GptActionsDispatchService(
            repo=MagicMock(),
            writes=writes,
            commit=TvGptCommitService(
                writes=writes,
                idempotency=InMemoryIdempotencyRepository(),
                patch=patch_svc,
                access=access,
            ),
            access=access,
            patch=patch_svc,
        )
        return dispatch, writes

    def test_commit_now_valid_candidate_persists(self):
        from tv_app.application.services.data.presentation_ops_content_service import (
            PresentationOpsContentService,
        )

        slide = {
            "id": _SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [_prev_source(), _cur_source()],
            },
        }
        dispatch, writes = self._dispatch_with_gate(
            {"prev": _rol_payload(4399153.22), "cur": _rol_payload(4516461.10)},
            slide=slide,
        )
        result = dispatch.preview_change(
            user=_user(),
            target={"playlistId": _PLAYLIST_ID, "slideId": _SLIDE_ID},
            ops=[
                {
                    "op": "set_data_transform",
                    "blockId": "pct2_weg_sc_y26",
                    "steps": _cur_source()["dataTransform"]["steps"],
                }
            ],
            commit_now=True,
            confirmation={"confirmed": True},
            idempotency_key="gate-valid-1",
            catalog_version=PresentationOpsContentService.catalog_version(),
            authorization=None,
        )
        assert result["commit_now_applied"] is True
        assert result["persisted"] is True
        writes.update_slide.assert_called_once()

    def test_commit_now_invalid_candidate_does_not_persist(self):
        from tv_app.application.services.data.presentation_ops_content_service import (
            PresentationOpsContentService,
        )

        dispatch, writes = self._dispatch_with_gate(
            {"cur": _rol_payload(4516461.10)}
        )
        with pytest.raises(GptActionsError) as exc:
            dispatch.preview_change(
                user=_user(),
                target={"playlistId": _PLAYLIST_ID, "slideId": _SLIDE_ID},
                ops=[_upsert_cur_op()],
                commit_now=True,
                catalog_version=PresentationOpsContentService.catalog_version(),
                authorization=None,
            )
        assert exc.value.code == "m.merge_source_unavailable"
        writes.update_slide.assert_not_called()


# ---------------------------------------------------------------------------
# Caso real VISTA: mesma branch=01 nas duas fontes — o mock distingue pelos
# params de período materializados (start_date), como o runtime faz.
# ---------------------------------------------------------------------------


def _vista_prev_block() -> dict:
    block = _prev_source()
    block["dataBinding"]["params"] = {
        "branch": "01",
        "customer_segment": "weg",
        "dateRangePreset": "same_period_previous_year",
    }
    return block


def _vista_cur_block() -> dict:
    block = _cur_source()
    block["dataBinding"]["params"] = {
        "branch": "01",
        "customer_segment": "weg",
        "dateRangePreset": "this_year",
    }
    return block


def _vista_gateway(prev_value: float, cur_value: float):
    """Gateway que discrimina pelo param de período real, não pela branch.

    Ambas as fontes usam branch=01; a única diferença nos params enviados ao
    gateway é  — a materialização para datas concretas
    acontece dentro do gateway/camada HTTP, igual ao runtime real.
    """
    gateway = MagicMock()
    calls: list[dict] = []

    def _fetch(operation_id, params=None, **kw):
        params = dict(params or {})
        calls.append(params)
        preset = str(params.get("dateRangePreset") or "")
        return _rol_payload(prev_value if "previous" in preset else cur_value)

    gateway.fetch_by_operation_id.side_effect = _fetch
    gateway.calls = calls
    return gateway


class TestVistaRealCaseSameBranch:
    """Reprodução exata: y25/y26 com branch=01 e só o preset distinguindo."""

    def _blocks(self) -> tuple[dict, dict]:
        return _vista_prev_block(), _vista_cur_block()

    def _slide(self, prev: dict, cur: dict) -> dict:
        return {
            "id": _SLIDE_ID,
            "nativeConfig": {"version": 5, "blocks": [prev, cur]},
        }

    def _dispatch(self, gateway, slide: dict) -> GptActionsDispatchService:
        catalog = TvDataRouteCatalogService()
        enrichment = ComunicadoDataEnrichmentService(
            catalog=catalog, gateway=gateway
        )
        preview = TvDataPreviewService(
            catalog=catalog,
            enrichment=enrichment,
            resolution=SlideDataResolutionService(
                catalog=catalog, enrichment=enrichment
            ),
        )
        writes = MagicMock()
        writes.get_slide.side_effect = lambda slide_id, playlist_id=None: slide
        writes.list_slides.return_value = [slide]
        access = MagicMock()
        access.resolve.return_value = PlaylistAccess(
            level="owner", playlist={"id": _PLAYLIST_ID, "dataDefaults": {}}
        )
        access.actor_id.return_value = "actor-1"
        return GptActionsDispatchService(
            repo=MagicMock(),
            writes=writes,
            commit=MagicMock(),
            access=access,
            preview=preview,
        )

    def test_contextual_preview_same_branch_both_periods(self):
        prev, cur = self._blocks()
        gateway = _vista_gateway(4399153.22, 4516461.10)
        dispatch = self._dispatch(gateway, self._slide(prev, cur))
        result = dispatch.preview_data_block(
            user=_user(),
            body={
                "playlistId": _PLAYLIST_ID,
                "slideId": _SLIDE_ID,
                "blockId": "pct2_weg_sc_y26",
            },
            authorization=None,
        )
        block = result.get("block") or {}
        resolved = block.get("resolved") or result.get("resolved") or {}
        assert not resolved.get("error")
        assert not resolved.get("transformError")
        rows = (resolved.get("_queryTable") or {}).get("rows") or []
        row = rows[0]
        assert row["rol"] == pytest.approx(4516461.10)
        assert row["rol_prev"] == pytest.approx(4399153.22)
        assert row["value"] == pytest.approx(2.6667, abs=0.01)
        # Duas execuções separadas, períodos distintos, sem confusão de cache.
        presets = sorted(
            str(p.get("dateRangePreset") or "") for p in gateway.calls
        )
        assert len(presets) == 2
        assert presets == ["same_period_previous_year", "this_year"]

    def test_preview_change_candidate_same_branch_passes_gate(self):
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchService,
        )

        gateway = _vista_gateway(4399153.22, 4516461.10)
        catalog = TvDataRouteCatalogService()
        enrichment = ComunicadoDataEnrichmentService(
            catalog=catalog, gateway=gateway
        )
        svc = PresentationPatchService(
            catalog=catalog,
            repo=_GateRepo(self._slide(*self._blocks())),
            resolution=SlideDataResolutionService(
                catalog=catalog, enrichment=enrichment
            ),
        )
        ops = [
            {
                "op": "set_data_transform",
                "blockId": "pct2_weg_sc_y26",
                "steps": _vista_cur_block()["dataTransform"]["steps"],
            }
        ]
        result = svc.preview(
            {
                "target": {"playlistId": _PLAYLIST_ID, "slideId": _SLIDE_ID},
                "ops": ops,
            },
            user=_user(),
        )
        assert result["fingerprint"]
        assert len(gateway.calls) >= 2
        presets = {str(p.get("dateRangePreset") or "") for p in gateway.calls}
        assert "same_period_previous_year" in presets
        assert "this_year" in presets


# ---------------------------------------------------------------------------
# Scalar multi-field payloads com metadata aninhada + precedência de preset
# ---------------------------------------------------------------------------


class TestScalarCompositionSourceTable:
    """Dict escalar + objetos aninhados de metadata deve virar linha larga."""

    def test_scalar_payload_with_nested_metadata_keeps_fields(self):
        """Genérico: metric_a/metric_b + objeto aninhado → rename funciona."""
        from tv_app.application.services.data.tv_data_transform_service import (
            apply_data_transform_to_payload_result,
        )

        payload = {
            "metric_a": 100,
            "metric_b": 80,
            "details": {"unit": "BRL", "scope": {"branch": "01"}},
        }
        result = apply_data_transform_to_payload_result(
            payload,
            {"steps": [{"op": "rename", "from": "metric_a", "to": "metric_prev"}]},
        )
        assert result["applied"] is True
        table = result["table"]
        assert "metric_prev" in table["columns"]
        assert "metric_b" in table["columns"]
        assert table["rows"][0]["metric_prev"] == 100

    def test_list_payload_still_uses_tabular_path(self):
        """Dict com lista continua indo para coerce (rotas tabulares)."""
        from tv_app.application.services.data.tv_data_transform_service import (
            apply_data_transform_to_payload_result,
        )

        payload = {"items": [{"sku": "A", "qty": 3}], "total": 1}
        result = apply_data_transform_to_payload_result(
            payload,
            {"steps": [{"op": "rename", "from": "qty", "to": "qty_prev"}]},
        )
        assert result["applied"] is True
        assert "qty_prev" in result["table"]["columns"]

    def test_unknown_column_error_lists_available_columns(self):
        """m.unknown_column deve carregar column + availableColumns."""
        from tv_app.application.services.data.tv_data_transform_service import (
            apply_data_transform_to_payload_result,
        )

        result = apply_data_transform_to_payload_result(
            {"metric_a": 100, "metric_b": 80},
            {"steps": [{"op": "rename", "from": "ghost", "to": "x"}]},
        )
        assert result["failed"] is True
        sample = (result.get("runtimeErrors") or {}).get("sample") or []
        err = sample[0]
        assert err["code"] == "m.unknown_column"
        assert err["column"] == "ghost"
        assert "metric_a" in err["availableColumns"]
        assert "metric_b" in err["availableColumns"]


class TestExplicitPresetPrecedence:
    """Preset explícito no bloco vence default de playlist."""

    def test_explicit_preset_beats_playlist_default(self):
        """dateRangePreset explícito não pode ser rebaixado pelo default."""
        gateway = MagicMock()
        calls: list[dict] = []

        def _fetch(operation_id, params=None, **kw):
            calls.append(dict(params or {}))
            return _rol_payload(4399153.22)

        gateway.fetch_by_operation_id.side_effect = _fetch
        catalog = TvDataRouteCatalogService()
        enrichment = ComunicadoDataEnrichmentService(
            catalog=catalog, gateway=gateway
        )
        block = {
            "id": "src-preset",
            "type": "data_source",
            "frame": {"x": 4, "y": 4, "w": 20, "h": 8},
            "dataBinding": {
                "operationId": _OP,
                "params": {
                    "branch": "01",
                    "customer_segment": "weg",
                    "dateRangePreset": "same_period_previous_year",
                },
            },
        }
        cfg = {"version": 5, "blocks": [block]}
        enriched = enrichment.enrich_blocks(
            [block],
            cfg=cfg,
            authorization=None,
            playlist_defaults={"dateRangePreset": "this_month_full"},
        )
        assert calls, "fetch deveria ter sido chamado"
        sent = calls[0]
        assert sent.get("dateRangePreset") == "same_period_previous_year"
        resolved = enriched[0].get("resolved") or {}
        assert resolved.get("error") in (None, "")
