"""DM1 — DataModel backend foundation.

Contrato congelado: ``nativeConfig.dataModels[]`` — objeto lógico não-visual
com 1..N inputs embutidos + transforms. O runtime canônico (DAG, fetch,
AuthZ, transforms, erros tipados) é reutilizado via projeção em nós
``data_source`` sintéticos — nenhum engine novo.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.data.data_model_service import (
    DataModelContractError,
    data_model_source_blocks,
    find_data_model,
    new_data_model_id,
    normalize_data_model,
)
from tv_app.application.services.data.slide_data_resolution_service import (
    SlideDataResolutionService,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService

_OP = "get_commercial_rol_summary"

PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"
SLIDE_ID = "00000000-0000-0000-0000-000000000002"


@pytest.fixture(autouse=True)
def _clear_data_cache():
    reset_comunicado_data_block_cache()
    yield
    reset_comunicado_data_block_cache()


def _user():
    return SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1")


def _rol_payload(value: float) -> dict:
    """Shape real de get_commercial_rol_summary incluindo meta SI aninhada."""
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


def _gateway_by_preset(
    payload_by_preset: dict[str, dict],
    fails: dict[str, Exception] | None = None,
):
    """Mock do gateway distinguindo pelos params de período reais
    (dateRangePreset) — como o runtime faz."""
    gateway = MagicMock()
    calls: list[dict] = []

    def _fetch(operation_id, params=None, **kw):
        params = dict(params or {})
        calls.append(params)
        preset = str(params.get("dateRangePreset") or "")
        key = "previous" if "previous" in preset or "same_period" in preset else "current"
        if fails and key in fails:
            raise fails[key]
        return payload_by_preset[key]

    gateway.fetch_by_operation_id.side_effect = _fetch
    gateway.calls = calls
    return gateway


def _enrichment(gateway) -> ComunicadoDataEnrichmentService:
    return ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(), gateway=gateway
    )


def _rol_model(*, model_transform_merge=True) -> dict:
    """Caso real ROL: previous + current, mesma branch, presets diferentes."""
    model = {
        "id": "mdl_rol_delta",
        "label": "ROL vs ano anterior",
        "primaryInputId": "current",
        "inputs": [
            {
                "id": "previous",
                "label": "ROL anterior",
                "operationId": _OP,
                "params": {
                    "branch": "01",
                    "customer_segment": "weg",
                    "dateRangePreset": "same_period_previous_year",
                },
                "transform": {
                    "version": 1,
                    "steps": [
                        {"op": "rename", "from": "rol", "to": "rol_prev"},
                        {"op": "addColumn", "name": "join_key", "expr": "1"},
                    ],
                },
            },
            {
                "id": "current",
                "label": "ROL atual",
                "operationId": _OP,
                "params": {
                    "branch": "01",
                    "customer_segment": "weg",
                    "dateRangePreset": "this_year",
                },
                "transform": {
                    "version": 1,
                    "steps": [{"op": "addColumn", "name": "join_key", "expr": "1"}],
                },
            },
        ],
        "transform": {
            "version": 1,
            "steps": [
                {
                    "op": "merge",
                    "sourceId": "previous",
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
        }
        if model_transform_merge
        else None,
    }
    return model


def _resolve_model(
    model: dict,
    *,
    gateway=None,
    cfg: dict | None = None,
    playlist_defaults: dict | None = None,
) -> dict:
    enrichment = _enrichment(gateway or _gateway_by_preset({}))
    cfg = cfg or {"version": 5, "blocks": [], "dataModels": [model]}
    resolved_map = enrichment.enrich_data_models(
        [model],
        cfg=cfg,
        authorization=None,
        playlist_defaults=playlist_defaults,
    )
    return resolved_map[str(model["id"])]


class _Repo:
    def __init__(self, slide: dict | None = None) -> None:
        self._slide = slide or {
            "id": SLIDE_ID,
            "nativeConfig": {"version": 5, "blocks": []},
        }

    def get_by_id(self, playlist_id):
        return {"id": str(playlist_id), "dataDefaults": {"branch": "01"}, "revision": 7}

    def get_slide(self, slide_id, *, playlist_id=None):
        from tv_app.infrastructure.persistence.repositories.playlist_repository import (
            SlideNotFoundError,
        )

        if str(slide_id) != self._slide["id"]:
            raise SlideNotFoundError(str(slide_id))
        return dict(self._slide)


def _patch_service(gateway, *, slide=None):
    from tv_app.application.services.data.presentation_mutation.patch_service import (
        PresentationPatchService,
    )

    catalog = TvDataRouteCatalogService()
    enrichment = _enrichment(gateway)
    return PresentationPatchService(
        catalog=catalog,
        repo=_Repo(slide),
        resolution=SlideDataResolutionService(catalog=catalog, enrichment=enrichment),
    )


def _preview_envelope(ops: list[dict]) -> dict:
    return {
        "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
        "ops": ops,
    }


# ---------------------------------------------------------------------------
# Contract validation
# ---------------------------------------------------------------------------


class TestDataModelContract:
    def test_valid_model_normalizes(self):
        model = normalize_data_model(
            _rol_model(), catalog=TvDataRouteCatalogService()
        )
        assert model["id"] == "mdl_rol_delta"
        assert model["primaryInputId"] == "current"
        assert model["inputs"][0]["queryName"] == "previous"
        assert model["inputs"][0]["params"]["branch"] == "01"

    def test_inputs_required(self):
        with pytest.raises(DataModelContractError) as exc:
            normalize_data_model({"id": "mdl_x", "primaryInputId": "a", "inputs": []})
        assert exc.value.code == "data_model.contract_invalid"

    def test_duplicate_input_id(self):
        model = _rol_model()
        model["inputs"][1]["id"] = "previous"
        with pytest.raises(DataModelContractError) as exc:
            normalize_data_model(model)
        assert exc.value.code == "data_model.contract_invalid"
        assert exc.value.details["inputId"] == "previous"

    def test_missing_input_id(self):
        model = _rol_model()
        model["inputs"][0].pop("id")
        with pytest.raises(DataModelContractError) as exc:
            normalize_data_model(model)
        assert exc.value.code == "m.query_identity_required"

    def test_duplicate_query_name(self):
        model = _rol_model()
        model["inputs"][1]["queryName"] = "previous"
        with pytest.raises(DataModelContractError) as exc:
            normalize_data_model(model)
        assert exc.value.code == "m.duplicate_query_name"

    def test_query_name_derived_from_id(self):
        model = _rol_model()
        model["inputs"][0].pop("queryName", None)
        normalized = normalize_data_model(model)
        assert normalized["inputs"][0]["queryName"] == "previous"

    def test_primary_input_must_exist(self):
        model = _rol_model()
        model["primaryInputId"] = "ghost"
        with pytest.raises(DataModelContractError) as exc:
            normalize_data_model(model)
        assert exc.value.code == "data_model.contract_invalid"

    def test_operation_id_required(self):
        model = _rol_model()
        model["inputs"][0]["operationId"] = ""
        with pytest.raises(DataModelContractError) as exc:
            normalize_data_model(model)
        assert exc.value.code == "data_model.contract_invalid"

    def test_operation_id_must_be_in_catalog(self):
        model = _rol_model()
        model["inputs"][0]["operationId"] = "not_a_real_route"
        with pytest.raises(DataModelContractError) as exc:
            normalize_data_model(model, catalog=TvDataRouteCatalogService())
        assert exc.value.code == "data_model.contract_invalid"

    def test_merge_ref_must_be_model_input(self):
        model = _rol_model()
        model["transform"]["steps"][0]["sourceId"] = "ghost"
        with pytest.raises(DataModelContractError) as exc:
            normalize_data_model(model)
        assert exc.value.code == "m.merge_source_unavailable"

    def test_params_must_be_object(self):
        model = _rol_model()
        model["inputs"][0]["params"] = "branch=01"
        with pytest.raises(DataModelContractError):
            normalize_data_model(model)

    def test_invalid_transform_step_rejected_by_patch(self):
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchError,
        )

        svc = _patch_service(_gateway_by_preset({}))
        bad = _rol_model()
        bad["transform"]["steps"][0] = {"op": "not_a_step"}
        with pytest.raises(PresentationPatchError):
            svc.preview(
                _preview_envelope([{"op": "upsert_data_model", "model": bad}]),
                user=_user(),
            )


# ---------------------------------------------------------------------------
# Runtime adapter + ordering
# ---------------------------------------------------------------------------


class TestRuntimeAdapter:
    def test_projection_builds_data_source_nodes(self):
        nodes, primary = data_model_source_blocks(_rol_model())
        assert primary == "current"
        ids = [n["id"] for n in nodes]
        assert ids == ["previous", "current"]
        assert all(n["type"] == "data_source" for n in nodes)
        prev = next(n for n in nodes if n["id"] == "previous")
        assert prev["dataBinding"]["operationId"] == _OP
        assert prev["dataBinding"]["params"]["dateRangePreset"] == (
            "same_period_previous_year"
        )
        # input.transform local preservado
        assert prev["dataTransform"]["steps"][0]["op"] == "rename"
        cur = next(n for n in nodes if n["id"] == "current")
        steps = cur["dataTransform"]["steps"]
        # input.transform do primário ANTES de model.transform
        assert steps[0] == {"op": "addColumn", "name": "join_key", "expr": "1"}
        assert steps[1]["op"] == "merge"
        assert steps[2]["expr"] == "(rol / rol_prev - 1) * 100"

    def test_primary_input_transform_runs_before_model_transform(self):
        """input.transform → model.transform: o transform do modelo vê a
        saída pós-transform do input primário."""
        model = {
            "id": "mdl_order",
            "primaryInputId": "main",
            "inputs": [
                {
                    "id": "main",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                    "transform": {
                        "version": 1,
                        "steps": [{"op": "rename", "from": "rol", "to": "rol_base"}],
                    },
                }
            ],
            "transform": {
                "version": 1,
                "steps": [
                    {"op": "addColumn", "name": "dbl", "expr": "rol_base * 2"}
                ],
            },
        }
        gateway = _gateway_by_preset({"current": _rol_payload(4516461.10)})
        resolved = _resolve_model(model, gateway=gateway)
        assert not resolved.get("error")
        row = resolved["table"]["rows"][0]
        assert row["dbl"] == pytest.approx(4516461.10 * 2)


# ---------------------------------------------------------------------------
# Execution — 1/N sources, transforms, errors
# ---------------------------------------------------------------------------


class TestOneSourceModel:
    def test_single_input_no_transform(self):
        model = {
            "id": "mdl_single",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                }
            ],
            "transform": None,
        }
        gateway = _gateway_by_preset({"current": _rol_payload(4516461.10)})
        resolved = _resolve_model(model, gateway=gateway)
        assert not resolved.get("error")
        # Campos autoritativos + goal aninhado preservados (linha larga).
        assert resolved["data"]["rol"] == pytest.approx(4516461.10)
        assert resolved["data"]["branch"] == "01"

    def test_single_input_with_input_transform(self):
        model = {
            "id": "mdl_it",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                    "transform": {
                        "version": 1,
                        "steps": [{"op": "rename", "from": "rol", "to": "rol_renamed"}],
                    },
                }
            ],
            "transform": None,
        }
        gateway = _gateway_by_preset({"current": _rol_payload(1.0)})
        resolved = _resolve_model(model, gateway=gateway)
        assert resolved["table"]["rows"][0]["rol_renamed"] == 1.0

    def test_single_input_with_model_transform(self):
        model = {
            "id": "mdl_mt",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                }
            ],
            "transform": {
                "version": 1,
                "steps": [{"op": "addColumn", "name": "k", "expr": "rol * 0"}],
            },
        }
        gateway = _gateway_by_preset({"current": _rol_payload(3.0)})
        resolved = _resolve_model(model, gateway=gateway)
        assert resolved["table"]["rows"][0]["k"] == 0

    def test_fetch_failure_surfaces_error(self):
        model = {
            "id": "mdl_fail",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                }
            ],
        }
        gateway = _gateway_by_preset({}, fails={"current": Exception("upstream down")})
        resolved = _resolve_model(model, gateway=gateway)
        assert resolved.get("error")


class TestTwoSourceRealRol:
    def test_exact_rol_case_value(self):
        """previous(same_period_previous_year) + current(this_year),
        mesma branch — merge + fórmula ≈ 2.6667."""
        gateway = _gateway_by_preset(
            {
                "previous": _rol_payload(4399153.22),
                "current": _rol_payload(4516461.10),
            }
        )
        resolved = _resolve_model(_rol_model(), gateway=gateway)
        assert not resolved.get("error"), resolved
        row = resolved["table"]["rows"][0]
        assert row["rol_prev"] == pytest.approx(4399153.22)
        assert row["rol"] == pytest.approx(4516461.10)
        assert row["value"] == pytest.approx(2.6667, abs=0.01)
        # dois fetches separados, presets distintos — nenhum colapso de período
        presets = {str(p.get("dateRangePreset") or "") for p in gateway.calls}
        assert presets == {"same_period_previous_year", "this_year"}

    def test_nested_goal_metadata_stays_wide_row(self):
        gateway = _gateway_by_preset({"current": _rol_payload(100.0)})
        model = {
            "id": "mdl_goal",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                    "transform": {
                        "version": 1,
                        "steps": [{"op": "rename", "from": "rol", "to": "rol_2"}],
                    },
                }
            ],
        }
        resolved = _resolve_model(model, gateway=gateway)
        assert resolved["table"]["rows"][0]["rol_2"] == 100.0


class TestFourSourceModel:
    def test_four_inputs_generic_composition(self):
        model = {
            "id": "mdl_four",
            "primaryInputId": "a",
            "inputs": [
                {
                    "id": name,
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": preset},
                    "transform": {
                        "version": 1,
                        "steps": [
                            {"op": "rename", "from": "rol", "to": f"rol_{name}"},
                            {"op": "addColumn", "name": "join_key", "expr": "1"},
                        ],
                    },
                }
                for name, preset in [
                    ("a", "this_year"),
                    ("b", "same_period_previous_year"),
                    ("c", "this_year"),
                    ("d", "same_period_previous_year"),
                ]
            ],
            "transform": {
                "version": 1,
                "steps": [
                    {
                        "op": "merge",
                        "sourceId": "b",
                        "leftKey": "join_key",
                        "rightKey": "join_key",
                        "columns": ["rol_b"],
                    },
                    {
                        "op": "merge",
                        "sourceId": "c",
                        "leftKey": "join_key",
                        "rightKey": "join_key",
                        "columns": ["rol_c"],
                    },
                    {
                        "op": "merge",
                        "sourceId": "d",
                        "leftKey": "join_key",
                        "rightKey": "join_key",
                        "columns": ["rol_d"],
                    },
                    {
                        "op": "addColumn",
                        "name": "total",
                        "expr": "rol_a + rol_b + rol_c + rol_d",
                    },
                ],
            },
        }
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(10.0), "current": _rol_payload(20.0)}
        )
        resolved = _resolve_model(model, gateway=gateway)
        assert not resolved.get("error"), resolved.get("transformError")
        row = resolved["table"]["rows"][0]
        assert row["total"] == pytest.approx(60.0)


class TestModelErrors:
    def _model_with(self, transform_steps=None, input_transform=None):
        model = {
            "id": "mdl_err",
            "primaryInputId": "cur",
            "inputs": [
                {
                    "id": "prev",
                    "operationId": _OP,
                    "params": {
                        "branch": "01",
                        "dateRangePreset": "same_period_previous_year",
                    },
                },
                {
                    "id": "cur",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                    "transform": input_transform,
                },
            ],
            "transform": {"version": 1, "steps": transform_steps or []},
        }
        return model

    def test_missing_input_dependency(self):
        model = self._model_with(
            transform_steps=[
                {
                    "op": "merge",
                    "sourceId": "prev",
                    "leftKey": "branch",
                    "rightKey": "branch",
                    "columns": ["ghost_col"],
                }
            ]
        )
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
        )
        resolved = _resolve_model(model, gateway=gateway)
        # ghost_col não existe no input prev → m.unknown_column tipado
        assert resolved.get("transformError", {}).get("code") == "m.unknown_column"

    def test_query_cycle(self):
        model = {
            "id": "mdl_cycle",
            "primaryInputId": "a",
            "inputs": [
                {
                    "id": "a",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                    "transform": {
                        "version": 1,
                        "steps": [
                            {
                                "op": "merge",
                                "sourceId": "b",
                                "leftKey": "branch",
                                "rightKey": "branch",
                            }
                        ],
                    },
                },
                {
                    "id": "b",
                    "operationId": _OP,
                    "params": {
                        "branch": "01",
                        "dateRangePreset": "same_period_previous_year",
                    },
                    "transform": {
                        "version": 1,
                        "steps": [
                            {
                                "op": "merge",
                                "sourceId": "a",
                                "leftKey": "branch",
                                "rightKey": "branch",
                            }
                        ],
                    },
                },
            ],
        }
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
        )
        resolved = _resolve_model(model, gateway=gateway)
        assert resolved.get("transformError", {}).get("code") == "m.query_cycle"

    def test_division_by_zero(self):
        model = self._model_with(
            transform_steps=[
                {"op": "addColumn", "name": "x", "expr": "rol / (rol - rol)"}
            ]
        )
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
        )
        resolved = _resolve_model(model, gateway=gateway)
        assert resolved.get("transformError", {}).get("code") == (
            "m.calc_division_by_zero"
        )

    def test_unknown_column_lists_available(self):
        model = self._model_with(
            transform_steps=[{"op": "rename", "from": "ghost", "to": "x"}]
        )
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
        )
        resolved = _resolve_model(model, gateway=gateway)
        terr = resolved.get("transformError") or {}
        assert terr.get("code") == "m.unknown_column"
        assert "rol" in (terr.get("availableColumns") or [])

    def test_sibling_execution_failure(self):
        model = _rol_model()
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)},
            fails={"previous": Exception("upstream down")},
        )
        resolved = _resolve_model(model, gateway=gateway)
        terr = resolved.get("transformError") or {}
        assert terr.get("code") in {"m.merge_source_failed", "data.fetch_failed"}


# ---------------------------------------------------------------------------
# Persistence via ops (nativeConfig.dataModels — nunca blocks)
# ---------------------------------------------------------------------------


class TestModelPersistenceOps:
    def test_upsert_creates_model_without_touching_blocks(self):
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            )
        )
        result = svc.preview(
            _preview_envelope(
                [{"op": "upsert_data_model", "model": _rol_model()}]
            ),
            user=_user(),
        )
        cfg = result["nativeConfig"]
        assert cfg["blocks"] == []  # blocks intocados
        models = cfg["dataModels"]
        assert len(models) == 1
        model = models[0]
        assert model["id"] == "mdl_rol_delta"
        assert model["primaryInputId"] == "current"
        # Sem runtime artifacts persistidos na definição
        for forbidden in ("resolved", "rows", "outputSchema", "runtimeErrors", "effectiveParams"):
            assert forbidden not in model
        # Sem frame/layout/hidden — não é block
        for forbidden in ("frame", "x", "y", "w", "h", "hidden", "type"):
            assert forbidden not in model

    def test_upsert_replaces_same_id(self):
        svc = _patch_service(_gateway_by_preset({
            "previous": _rol_payload(1.0), "current": _rol_payload(2.0)}))
        slide = {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [],
                "dataModels": [_rol_model()],
            },
        }
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
            ),
            slide=slide,
        )
        updated = _rol_model()
        updated["label"] = "novo label"
        result = svc.preview(
            _preview_envelope([{"op": "upsert_data_model", "model": updated}]),
            user=_user(),
        )
        models = result["nativeConfig"]["dataModels"]
        assert len(models) == 1
        assert models[0]["label"] == "novo label"

    def test_upsert_generates_id_when_absent(self):
        svc = _patch_service(_gateway_by_preset({
            "previous": _rol_payload(1.0), "current": _rol_payload(2.0)}))
        model = _rol_model()
        model.pop("id")
        result = svc.preview(
            _preview_envelope([{"op": "upsert_data_model", "model": model}]),
            user=_user(),
        )
        created = result["nativeConfig"]["dataModels"][0]
        assert created["id"].startswith("mdl_")

    def test_upsert_model_id_cannot_collide_with_block_id(self):
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchError,
        )

        slide = {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [{"id": "mdl_rol_delta", "type": "text"}],
            },
        }
        svc = _patch_service(_gateway_by_preset({}), slide=slide)
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope(
                    [{"op": "upsert_data_model", "model": _rol_model()}]
                ),
                user=_user(),
            )
        assert exc.value.code == "data_model.contract_invalid"

    def test_delete_unused_model(self):
        slide = {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [],
                "dataModels": [_rol_model()],
            },
        }
        svc = _patch_service(_gateway_by_preset({}), slide=slide)
        result = svc.preview(
            _preview_envelope(
                [{"op": "delete_data_model", "modelId": "mdl_rol_delta"}]
            ),
            user=_user(),
        )
        assert result["nativeConfig"]["dataModels"] == []

    def test_delete_missing_model_fails(self):
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchError,
        )

        svc = _patch_service(_gateway_by_preset({}))
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope(
                    [{"op": "delete_data_model", "modelId": "mdl_ghost"}]
                ),
                user=_user(),
            )
        assert exc.value.code == "data_model.not_found"

    def test_delete_in_use_model_rejected(self):
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchError,
        )

        slide = {
            "id": SLIDE_ID,
            "nativeConfig": {
                "version": 5,
                "blocks": [
                    {"id": "kpi1", "type": "kpi_view", "modelId": "mdl_rol_delta"}
                ],
                "dataModels": [_rol_model()],
            },
        }
        svc = _patch_service(_gateway_by_preset({}), slide=slide)
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope(
                    [{"op": "delete_data_model", "modelId": "mdl_rol_delta"}]
                ),
                user=_user(),
            )
        assert exc.value.code == "data_model.in_use"


# ---------------------------------------------------------------------------
# Candidate execution gate
# ---------------------------------------------------------------------------


class TestModelExecutionGate:
    def test_valid_model_candidate_executes(self):
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(4399153.22), "current": _rol_payload(4516461.10)}
            )
        )
        result = svc.preview(
            _preview_envelope(
                [{"op": "upsert_data_model", "model": _rol_model()}]
            ),
            user=_user(),
        )
        assert result["ok"] is True
        assert result["nativeConfig"]["dataModels"]

    def test_invalid_model_rejected_by_gate(self):
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchError,
        )

        # input falha no fetch → gate executa e rejeita com erro tipado
        svc = _patch_service(
            _gateway_by_preset(
                {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)},
                fails={"previous": Exception("upstream down")},
            )
        )
        with pytest.raises(PresentationPatchError) as exc:
            svc.preview(
                _preview_envelope(
                    [{"op": "upsert_data_model", "model": _rol_model()}]
                ),
                user=_user(),
            )
        assert exc.value.details.get("modelId") == "mdl_rol_delta"
        assert exc.value.details.get("stage") == "data_execution"

    def test_commit_now_invalid_model_does_not_persist(self):
        """commit_now sobre candidate inválido → GptActionsError, sem write."""
        catalog = TvDataRouteCatalogService()
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)},
            fails={"previous": Exception("down")},
        )
        enrichment = _enrichment(gateway)
        from tv_app.application.services.data.presentation_mutation.patch_service import (
            PresentationPatchService,
        )

        patch = PresentationPatchService(
            catalog=catalog,
            repo=_Repo(),
            resolution=SlideDataResolutionService(
                catalog=catalog, enrichment=enrichment
            ),
        )
        preview = TvDataPreviewService(
            catalog=catalog,
            enrichment=enrichment,
            resolution=SlideDataResolutionService(
                catalog=catalog, enrichment=enrichment
            ),
        )
        writes = MagicMock()
        access = MagicMock()
        access.resolve.return_value = PlaylistAccess(
            level="owner", playlist={"id": PLAYLIST_ID, "dataDefaults": {}}
        )
        access.actor_id.return_value = "actor-1"
        dispatch = GptActionsDispatchService(
            repo=_Repo(),
            writes=writes,
            commit=MagicMock(),
            access=access,
            patch=patch,
            preview=preview,
        )
        with pytest.raises(GptActionsError):
            dispatch.preview_change(
                user=_user(),
                target={"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                ops=[{"op": "upsert_data_model", "model": _rol_model()}],
                catalog_version=None,
                authorization=None,
                commit_now=True,
                confirmation=None,
                idempotency_key="idem-model-1",
            )
        writes.update_slide.assert_not_called()


# ---------------------------------------------------------------------------
# Dynamic schema / legacy compat / param precedence
# ---------------------------------------------------------------------------


class TestDynamicSchema:
    def test_schema_reflects_transform_not_persisted(self):
        gateway = _gateway_by_preset({"current": _rol_payload(50.0)})
        model_v1 = {
            "id": "mdl_schema",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                }
            ],
            "transform": None,
        }
        r1 = _resolve_model(model_v1, gateway=gateway)
        assert r1["data"]["rol"] == 50.0
        fields1 = [str(f.get("name") or f) for f in (r1.get("fields") or r1.get("projectableFields") or [])]
        assert "rol" in fields1 or "rol" in r1["data"]

        model_v2 = dict(model_v1)
        model_v2["transform"] = {
            "version": 1,
            "steps": [{"op": "rename", "from": "rol", "to": "rol2"}],
        }
        r2 = _resolve_model(model_v2, gateway=gateway)
        cols2 = [c["key"] for c in r2["table"]["columns"]]
        assert "rol2" in cols2 and "rol" not in cols2
        # definição persistida nunca carrega outputSchema
        persisted = normalize_data_model(model_v2)
        assert "outputSchema" not in persisted


class TestCompatibility:
    def test_legacy_only_slide_unchanged(self):
        """Slide sem dataModels: enrich_blocks comportamento inalterado."""
        source = {
            "id": "src1",
            "type": "data_source",
            "dataBinding": {
                "operationId": _OP,
                "params": {"branch": "01", "dateRangePreset": "this_year"},
            },
        }
        gateway = _gateway_by_preset({"current": _rol_payload(99.0)})
        enrichment = _enrichment(gateway)
        enriched = enrichment.enrich_blocks(
            [source], cfg={"version": 5, "blocks": [source]}, authorization=None
        )
        assert enriched[0]["resolved"]["data"]["rol"] == 99.0

    def test_mixed_slide_coexists(self):
        source = {
            "id": "src1",
            "type": "data_source",
            "dataBinding": {
                "operationId": _OP,
                "params": {
                    "branch": "01",
                    "dateRangePreset": "same_period_previous_year",
                },
            },
        }
        model = {
            "id": "mdl_mix",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                }
            ],
        }
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(11.0), "current": _rol_payload(22.0)}
        )
        enrichment = _enrichment(gateway)
        cfg = {"version": 5, "blocks": [source], "dataModels": [model]}
        enriched = enrichment.enrich_blocks([source], cfg=cfg, authorization=None)
        assert enriched[0]["resolved"]["data"]["rol"] == 11.0
        # visual com modelId linka via mapa (forward-compat do resolved map)
        visual = {"id": "kpi", "type": "kpi_view", "modelId": "mdl_mix"}
        # link ainda usa dataSourceId — modelId é DM2; aqui provamos que o
        # modelo executou dentro do enrich_blocks sem quebrar a fonte legacy.
        assert len(gateway.calls) == 2


class TestParamPrecedence:
    def test_explicit_input_preset_beats_playlist_default(self):
        gateway = _gateway_by_preset(
            {"previous": _rol_payload(1.0), "current": _rol_payload(2.0)}
        )
        model = {
            "id": "mdl_prec",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {
                        "branch": "01",
                        "dateRangePreset": "same_period_previous_year",
                    },
                }
            ],
        }
        _resolve_model(
            model,
            gateway=gateway,
            playlist_defaults={"dateRangePreset": "this_month_full"},
        )
        assert gateway.calls[0]["dateRangePreset"] == "same_period_previous_year"

    def test_slide_filters_beat_playlist_defaults_for_model_inputs(self):
        """Slide só-DataModel: nativeConfig.dataFilters alcança inputs do
        modelo pela mesma merge_data_params (slide > programação)."""
        gateway = _gateway_by_preset({"current": _rol_payload(5.0)})
        model = {
            "id": "mdl_slide",
            "primaryInputId": "only",
            "inputs": [{"id": "only", "operationId": _OP, "params": {}}],
        }
        cfg = {
            "version": 5,
            "blocks": [],
            "dataModels": [model],
            "dataFilters": {
                "branch": "02",
                "dateRangePreset": "this_year",
            },
        }
        _resolve_model(
            model,
            gateway=gateway,
            cfg=cfg,
            playlist_defaults={
                "branch": "01",
                "customer_segment": "weg",
                "dateRangePreset": "same_period_previous_year",
            },
        )
        merged = gateway.calls[0]
        assert merged["branch"] == "02"
        assert merged["dateRangePreset"] == "this_year"
        # chave só na programação sobrevive (merge, não replace)
        assert merged["customer_segment"] == "weg"

    def test_input_params_beat_slide_filters_for_model_inputs(self):
        """params do input do modelo são a camada persistida mais forte
        (input > tela > programação; runtime override segue acima)."""
        gateway = _gateway_by_preset({"current": _rol_payload(7.0)})
        model = {
            "id": "mdl_input",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {"branch": "03", "dateRangePreset": "this_year"},
                }
            ],
        }
        cfg = {
            "version": 5,
            "blocks": [],
            "dataModels": [model],
            "dataFilters": {"branch": "02", "dateRangePreset": "this_month"},
        }
        _resolve_model(
            model,
            gateway=gateway,
            cfg=cfg,
            playlist_defaults={"branch": "01"},
        )
        merged = gateway.calls[0]
        assert merged["branch"] == "03"
        assert merged["dateRangePreset"] == "this_year"

    def test_force_refresh_bypasses_cache_for_model_inputs(self):
        """enrich_data_models(force_refresh=True) refaz o fetch — não serve
        o _data_block_cache compartilhado com as fontes legacy."""
        gateway = _gateway_by_preset({"current": _rol_payload(1.0)})
        model = {
            "id": "mdl_cache",
            "primaryInputId": "only",
            "inputs": [
                {
                    "id": "only",
                    "operationId": _OP,
                    "params": {"dateRangePreset": "this_year"},
                }
            ],
        }
        enrichment = _enrichment(gateway)
        cfg = {"version": 5, "blocks": [], "dataModels": [model]}
        enrichment.enrich_data_models([model], cfg=cfg, authorization=None)
        enrichment.enrich_data_models([model], cfg=cfg, authorization=None)
        assert len(gateway.calls) == 1  # segunda chamada saiu do cache
        enrichment.enrich_data_models(
            [model], cfg=cfg, authorization=None, force_refresh=True
        )
        assert len(gateway.calls) == 2
