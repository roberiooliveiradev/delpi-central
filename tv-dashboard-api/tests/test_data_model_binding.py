"""DM2 — binding formal de visuais a DataModel (``modelId``).

Contrato: ``visual.modelId`` com precedência determinística sobre o legado
``visual.dataSourceId``. Mutações normalizam para um único target ativo;
campos continuam selecionados pelas projeções existentes. Nenhuma mudança de
canvas/frontend nesta etapa.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from test_data_model_foundation import (
    SLIDE_ID,
    _enrichment,
    _patch_service,
    _preview_envelope,
    _rol_model,
    _rol_payload,
    _user,
    _gateway_by_preset,
)
from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchError,
)


# ---------------------------------------------------------------------------
# Fixtures locais
# ---------------------------------------------------------------------------


def _visual(block_id: str = "kpi1", **extra) -> dict:
    block = {
        "id": block_id,
        "type": "kpi_view",
        "kpiProjection": {"metrics": [{"field": "value", "label": "Var %"}]},
    }
    block.update(extra)
    return block


def _source_block(block_id: str = "ds1", **extra) -> dict:
    block = {
        "id": block_id,
        "type": "data_source",
        "queryName": block_id,
        "dataBinding": {
            "operationId": "get_commercial_rol_summary",
            "params": {"branch": "01", "dateRangePreset": "this_year"},
        },
    }
    block.update(extra)
    return block


def _gateway_uniform(payload: dict):
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = payload
    return gateway


def _enrich_slide(blocks: list[dict], models: list[dict], gateway) -> list[dict]:
    cfg = {"version": 5, "blocks": blocks, "dataModels": models}
    return _enrichment(gateway).enrich_blocks(
        blocks,
        cfg=cfg,
        authorization=None,
        playlist_defaults={},
    )


# ---------------------------------------------------------------------------
# Binding contract — read precedence
# ---------------------------------------------------------------------------


class TestBindingContract:
    def test_model_id_only_resolves(self):
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(4399153.22), "current": _rol_payload(4516461.10)}
        )
        visual = _visual(modelId="mdl_rol_delta")
        enriched = _enrich_slide([visual], [_rol_model()], gateway)
        resolved = enriched[0].get("resolved")
        assert isinstance(resolved, dict)
        assert resolved.get("dataModelId") == "mdl_rol_delta"

    def test_data_source_id_only_still_resolves_legacy(self):
        gateway = _gateway_uniform(_rol_payload(10.0))
        visual = _visual(dataSourceId="ds1")
        enriched = _enrich_slide([visual, _source_block()], [], gateway)
        kpi = next(b for b in enriched if b["id"] == "kpi1")
        assert isinstance(kpi.get("resolved"), dict)

    def test_both_ids_model_wins(self):
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(4399153.22), "current": _rol_payload(4516461.10)}
        )
        visual = _visual(modelId="mdl_rol_delta", dataSourceId="ds1")
        enriched = _enrich_slide([visual, _source_block()], [_rol_model()], gateway)
        resolved = enriched[0].get("resolved") or {}
        # modelId vence: resolved vem do modelo (stamp dataModelId), não do ds1.
        assert resolved.get("dataModelId") == "mdl_rol_delta"


# ---------------------------------------------------------------------------
# bind_visual op — mutual exclusivity
# ---------------------------------------------------------------------------


class TestBindVisualOp:
    def _slide_with_visual(self, **visual_extra) -> dict:
        return {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [_visual(**visual_extra)],
                "dataModels": [_rol_model()],
            },
        }

    def test_bind_visual_to_model(self):
        slide = self._slide_with_visual()
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            ),
            slide=slide,
        )
        result = svc.preview(
            _preview_envelope(
                [{"op": "bind_visual", "visualId": "kpi1", "modelId": "mdl_rol_delta"}]
            ),
            user=_user(),
        )
        visual = result["nativeConfig"]["blocks"][0]
        assert visual["modelId"] == "mdl_rol_delta"
        assert "dataSourceId" not in visual

    def test_bind_visual_to_model_clears_legacy_target(self):
        slide = self._slide_with_visual(dataSourceId="ds_legacy")
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            ),
            slide=slide,
        )
        result = svc.preview(
            _preview_envelope(
                [{"op": "bind_visual", "visualId": "kpi1", "modelId": "mdl_rol_delta"}]
            ),
            user=_user(),
        )
        visual = result["nativeConfig"]["blocks"][0]
        assert visual["modelId"] == "mdl_rol_delta"
        assert "dataSourceId" not in visual

    def test_bind_visual_back_to_legacy_clears_model(self):
        slide = self._slide_with_visual(modelId="mdl_rol_delta")
        slide["nativeConfig"]["blocks"].append(_source_block())
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            ),
            slide=slide,
        )
        result = svc.preview(
            _preview_envelope(
                [{"op": "bind_visual", "visualId": "kpi1", "dataSourceId": "ds1"}]
            ),
            user=_user(),
        )
        visual = next(
            b for b in result["nativeConfig"]["blocks"] if b["id"] == "kpi1"
        )
        assert visual["dataSourceId"] == "ds1"
        assert "modelId" not in visual

    def test_bind_visual_both_targets_rejected(self):
        slide = self._slide_with_visual()
        svc = _patch_service(_gateway_uniform(_rol_payload(1.0)), slide=slide)
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope(
                    [
                        {
                            "op": "bind_visual",
                            "visualId": "kpi1",
                            "modelId": "mdl_rol_delta",
                            "dataSourceId": "ds1",
                        }
                    ]
                ),
                user=_user(),
            )
        assert exc.value.code == "data_model.contract_invalid"

    def test_bind_visual_missing_model_typed_error(self):
        slide = self._slide_with_visual()
        svc = _patch_service(_gateway_uniform(_rol_payload(1.0)), slide=slide)
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope(
                    [{"op": "bind_visual", "visualId": "kpi1", "modelId": "mdl_ghost"}]
                ),
                user=_user(),
            )
        assert exc.value.code == "data_model.not_found"
        assert exc.value.details.get("modelId") == "mdl_ghost"
        assert exc.value.details.get("visualId") == "kpi1"


# ---------------------------------------------------------------------------
# Field validation against dynamic model output
# ---------------------------------------------------------------------------


class TestFieldValidation:
    def _slide(self, field: str = "value") -> dict:
        visual = _visual(modelId="mdl_rol_delta")
        visual["kpiProjection"] = {"metrics": [{"field": field, "label": "F"}]}
        return {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [visual],
                "dataModels": [_rol_model()],
            },
        }

    def test_existing_field_accepted(self):
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            ),
            slide=self._slide(field="value"),
        )
        updated = _rol_model()
        updated["label"] = "mesmo schema"
        result = svc.preview(
            _preview_envelope([{"op": "upsert_data_model", "model": updated}]),
            user=_user(),
        )
        assert result["nativeConfig"]["dataModels"][0]["label"] == "mesmo schema"

    def test_model_update_removing_field_rejected(self):
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            ),
            slide=self._slide(field="value"),
        )
        # Modelo sem o addColumn value → consumer de 'value' quebra.
        updated = _rol_model()
        updated["transform"] = {
            "version": 1,
            "steps": [
                {
                    "op": "merge",
                    "sourceId": "previous",
                    "leftKey": "join_key",
                    "rightKey": "join_key",
                    "columns": ["rol_prev"],
                }
            ],
        }
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope([{"op": "upsert_data_model", "model": updated}]),
                user=_user(),
            )
        assert exc.value.code == "DATA_BINDING_FIELD_MISSING"
        assert exc.value.details.get("modelId") == "mdl_rol_delta"
        assert "value" in (exc.value.details.get("consumers") or {}).get("kpi1", [])

    def test_bind_visual_then_invalid_field_rejected(self):
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            ),
            slide=self._slide(field="campo_inexistente"),
        )
        updated = _rol_model()
        updated["label"] = "rebind check"
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope([{"op": "upsert_data_model", "model": updated}]),
                user=_user(),
            )
        assert exc.value.code == "DATA_BINDING_FIELD_MISSING"


# ---------------------------------------------------------------------------
# Same-candidate model + visual
# ---------------------------------------------------------------------------


class TestSameCandidateModelAndVisual:
    def test_upsert_model_and_bind_in_same_candidate(self):
        slide = {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [_visual()],
                "dataModels": [],
            },
        }
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(4399153.22), "current": _rol_payload(4516461.10)}
            ),
            slide=slide,
        )
        result = svc.preview(
            _preview_envelope(
                [
                    {"op": "upsert_data_model", "model": _rol_model()},
                    {
                        "op": "bind_visual",
                        "visualId": "kpi1",
                        "modelId": "mdl_rol_delta",
                    },
                ]
            ),
            user=_user(),
        )
        cfg = result["nativeConfig"]
        visual = cfg["blocks"][0]
        assert visual["modelId"] == "mdl_rol_delta"
        assert len(cfg["dataModels"]) == 1

    def test_same_candidate_with_bad_field_fails_closed(self):
        slide = {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [_visual()],
                "dataModels": [],
            },
        }
        slide["nativeConfig"]["blocks"][0]["kpiProjection"] = {
            "metrics": [{"field": "nao_existe", "label": "X"}]
        }
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            ),
            slide=slide,
        )
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope(
                    [
                        {"op": "upsert_data_model", "model": _rol_model()},
                        {
                            "op": "bind_visual",
                            "visualId": "kpi1",
                            "modelId": "mdl_rol_delta",
                        },
                    ]
                ),
                user=_user(),
            )
        assert exc.value.code == "DATA_BINDING_FIELD_MISSING"


# ---------------------------------------------------------------------------
# Delete protection
# ---------------------------------------------------------------------------


class TestDeleteProtection:
    def test_delete_model_with_visual_consumer_rejected(self):
        slide = {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [_visual(modelId="mdl_rol_delta")],
                "dataModels": [_rol_model()],
            },
        }
        svc = _patch_service(_gateway_uniform(_rol_payload(1.0)), slide=slide)
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope(
                    [{"op": "delete_data_model", "modelId": "mdl_rol_delta"}]
                ),
                user=_user(),
            )
        assert exc.value.code == "data_model.in_use"

    def test_delete_model_after_rebind_to_legacy_allowed(self):
        slide = {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [_visual(modelId="mdl_rol_delta"), _source_block()],
                "dataModels": [_rol_model()],
            },
        }
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            ),
            slide=slide,
        )
        result = svc.preview(
            _preview_envelope(
                [
                    {"op": "bind_visual", "visualId": "kpi1", "dataSourceId": "ds1"},
                    {"op": "delete_data_model", "modelId": "mdl_rol_delta"},
                ]
            ),
            user=_user(),
        )
        cfg = result["nativeConfig"]
        assert cfg["dataModels"] == []
        visual = next(b for b in cfg["blocks"] if b["id"] == "kpi1")
        assert visual["dataSourceId"] == "ds1"


# ---------------------------------------------------------------------------
# Mixed slide + cell-level binding
# ---------------------------------------------------------------------------


class TestMixedAndCells:
    def test_mixed_slide_both_visuals_resolve(self):
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
        )
        blocks = [
            _visual("kpi_legacy", dataSourceId="ds1"),
            _visual("kpi_model", modelId="mdl_rol_delta"),
            _source_block(),
        ]
        enriched = _enrich_slide(blocks, [_rol_model()], gateway)
        by_id = {b["id"]: b for b in enriched}
        assert isinstance(by_id["kpi_legacy"].get("resolved"), dict)
        model_resolved = by_id["kpi_model"].get("resolved") or {}
        assert model_resolved.get("dataModelId") == "mdl_rol_delta"

    def test_canvas_table_cell_bound_to_model(self):
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
        )
        table = {
            "id": "tbl1",
            "type": "canvas_table",
            "cells": [
                [
                    {
                        "text": "",
                        "modelId": "mdl_rol_delta",
                        "dataRef": {"field": "value"},
                    }
                ]
            ],
        }
        enriched = _enrich_slide([table], [_rol_model()], gateway)
        resolved_by_source = enriched[0].get("resolvedBySourceId") or {}
        assert "mdl_rol_delta" in resolved_by_source

    def test_legacy_only_slide_unchanged(self):
        gateway = _gateway_uniform(_rol_payload(3.0))
        blocks = [_visual("kpi1", dataSourceId="ds1"), _source_block()]
        enriched = _enrich_slide(blocks, [], gateway)
        assert isinstance(enriched[0].get("resolved"), dict)


# ---------------------------------------------------------------------------
# Runtime acceptance — model value reaches the visual
# ---------------------------------------------------------------------------


class TestRuntimeAcceptance:
    def test_visual_receives_model_output_value(self):
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(4399153.22), "current": _rol_payload(4516461.10)}
        )
        visual = _visual(modelId="mdl_rol_delta")
        enriched = _enrich_slide([visual], [_rol_model()], gateway)
        resolved = enriched[0]["resolved"]
        table = resolved.get("table") or {}
        rows = table.get("rows") or []
        assert rows, "model output should materialize rows"
        assert rows[0].get("value") == pytest.approx(2.6667, abs=0.01)


# ---------------------------------------------------------------------------
# DM3 — model preview stamps linkedResolvedByBlockId (editor paint contract)
# ---------------------------------------------------------------------------


class TestModelPreviewLinkedResolved:
    def test_preview_data_model_attaches_linked_view_resolved(self):
        from tv_app.application.services.data.tv_data_preview_service import (
            TvDataPreviewService,
        )
        from tv_app.application.services.tv_data_route_catalog_service import (
            TvDataRouteCatalogService,
        )

        gateway = _gateway_by_preset(
            {"previous": _rol_payload(4399153.22), "current": _rol_payload(4516461.10)}
        )
        model = _rol_model()
        cfg = {
            "version": 5,
            "blocks": [_visual("kpi1", modelId="mdl_rol_delta")],
            "dataModels": [model],
        }
        service = TvDataPreviewService(TvDataRouteCatalogService())
        service._resolution = _enrichment(gateway)
        resolved = service.preview_data_model(
            model,
            native_config=cfg,
            authorization=None,
        )
        linked = resolved.get("linkedResolvedByBlockId") or {}
        assert "kpi1" in linked
        view_resolved = linked["kpi1"]
        rows = (view_resolved.get("table") or {}).get("rows") or []
        assert rows[0].get("value") == pytest.approx(2.6667, abs=0.01)
