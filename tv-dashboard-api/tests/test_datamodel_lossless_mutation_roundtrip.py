"""TV-DM-MUT-002 — Lossless DataModel inspection + governed mutation round-trip.

Invariante: persisted DataModel → inspect_data_model.definition →
normalize_data_model → mesmo modelo semântico. Mutação mínima via
``patch_data_model`` (op dentro do PREPARE/ACT existente — não é tool).
"""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.data.data_model_service import normalize_data_model
from tv_app.application.services.data.slide_data_resolution_service import (
    SlideDataResolutionService,
)
from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.application.services.editor_focus_store import EditorFocusStore

from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchError,
)

MODEL_ID = "mdl_commercial_compare"
OP_ROL = "get_commercial_rol_summary"


@pytest.fixture(autouse=True)
def _clear_data_cache():
    reset_comunicado_data_block_cache()
    yield
    reset_comunicado_data_block_cache()


def _user():
    return SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1")


def _ident(name: str) -> dict[str, Any]:
    return {"kind": "identifier", "value": name}


def _lit(value: Any) -> dict[str, Any]:
    return {"kind": "literal", "value": value}


def _call(fn: str, *args: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "call", "value": fn, "children": list(args)}


def _expr(ast: dict[str, Any]) -> dict[str, Any]:
    return {"expression": {"version": 1, "expression": ast}}


_PREV_YEAR = _call("Date.AddYears", _ident("today"), _lit(-1))
_MONTH_CURRENT = {
    "start_date": _expr(_call("Date.StartOfMonth", _ident("today"))),
    "end_date": _expr(_ident("today")),
}
_MONTH_PREV = {
    "start_date": _expr(_call("Date.StartOfMonth", _PREV_YEAR)),
    "end_date": _expr(_PREV_YEAR),
}
_YTD_CURRENT = {
    "start_date": _expr(_call("Date.StartOfYear", _ident("today"))),
    "end_date": _expr(_ident("today")),
}
_YTD_PREV = {
    "start_date": _expr(_call("Date.StartOfYear", _PREV_YEAR)),
    "end_date": _expr(_PREV_YEAR),
}


def _rol_payload(value: float, **extra: Any) -> dict:
    data = {
        "branch": "01",
        "start_date": "2026-10-01",
        "end_date": "2026-10-05",
        "rol": value,
        "comparable_goal": 1000000.0,
    }
    data.update(extra)
    return {
        "meta": {"shape": "scalar", "entity": "commercial_rol_summary"},
        "data": data,
        "route": {"label": "ROL", "valueFields": ["rol"]},
    }


def _gateway_by_segment(payload_by_segment: dict[str, dict]):
    """Gateway fake: distingue inputs pelo param customer_segment."""
    gateway = MagicMock()

    def _fetch(operation_id, params=None, **kw):
        params = dict(params or {})
        segment = str(params.get("customer_segment") or "")
        return payload_by_segment.get(segment, _rol_payload(0.0))

    gateway.fetch_by_operation_id.side_effect = _fetch
    return gateway


def _incident_model() -> dict[str, Any]:
    """Shape fiel ao incidente: ~20 inputs, 7 input transforms,
    model transform com merges + coluna calculada, fieldLabels."""
    inputs: list[dict[str, Any]] = []
    for i in range(20):
        inputs.append(
            {
                "id": f"inp_{i:02d}",
                "label": f"Input {i:02d}",
                "queryName": f"q_{i:02d}",
                "operationId": OP_ROL,
                "params": {
                    "branch": "01",
                    "customer_segment": f"seg_{i:02d}",
                    "dateRangePreset": "this_year"
                    if i % 2 == 0
                    else "same_period_previous_year",
                },
            }
        )
    # 7 inputs com transform (rename rol→rol_i + join_key p/ merge;
    # direita reduz colunas p/ não colidir com a esquerda)
    inputs[0]["transform"] = {
        "steps": [
            {"op": "rename", "from": "rol", "to": "rol_00"},
            {"op": "addColumn", "name": "join_key", "expr": "1"},
        ],
    }
    for i in range(1, 7):
        inputs[i]["transform"] = {
            "steps": [
                {"op": "rename", "from": "rol", "to": f"rol_{i:02d}"},
                {"op": "addColumn", "name": "join_key", "expr": "1"},
                {"op": "select", "columns": ["join_key", f"rol_{i:02d}"]},
            ],
        }
    model_transform = {
        "steps": [
            *[
                {
                    "op": "merge",
                    "sourceId": f"inp_{i:02d}",
                    "leftKey": "join_key",
                    "rightKey": "join_key",
                    "join": "left",
                }
                for i in range(1, 7)
            ],
            {
                "op": "addColumn",
                "name": "nn_es_mom_pct",
                "expr": "(rol_00 / rol_01 - 1) * 100",
            },
        ],
    }
    return {
        "id": MODEL_ID,
        "label": "Realizado 2025 x 2026 - Cards",
        "primaryInputId": "inp_00",
        "inputs": inputs,
        "transform": model_transform,
        "fieldLabels": {
            "weg_sc_m25": "WEG SC M25",
            "nn_es_mom_pct": "ES MoM %",
        },
    }


def _consumer_blocks() -> list[dict[str, Any]]:
    return [
        {
            "id": "rx_weg_sc_m25v",
            "type": "text",
            "modelId": MODEL_ID,
            "textProjection": {"field": "rol_00"},
        },
        {
            "id": "rx_nn_es_mom",
            "type": "text",
            "modelId": MODEL_ID,
            "textProjection": {"field": "nn_es_mom_pct"},
        },
        {
            "id": "kpi_goal",
            "type": "kpi_view",
            "modelId": MODEL_ID,
            "kpiProjection": {"valueField": "comparable_goal"},
        },
    ]


def _slide(slide_id: str, model: dict | None = None) -> dict:
    return {
        "id": slide_id,
        "title": "Realizado 2025 x 2026 - Cards",
        "sortOrder": 0,
        "nativeConfig": {
            "version": 5,
            "blocks": _consumer_blocks(),
            "dataModels": [model if model is not None else _incident_model()],
        },
    }


class _Repo:
    def __init__(self, slide: dict) -> None:
        self._slide = slide

    def get_by_id(self, playlist_id):
        return {"id": str(playlist_id), "dataDefaults": {"branch": "01"}, "revision": 7}

    def get_slide(self, slide_id, *, playlist_id=None):
        return self._slide


def _patch_service(slide: dict):
    from tv_app.application.services.data.presentation_mutation.patch_service import (
        PresentationPatchService,
    )

    gateway = _gateway_by_segment(
        {f"seg_{i:02d}": _rol_payload(1359.0 if i == 0 else 1000.0) for i in range(20)}
    )
    catalog = TvDataRouteCatalogService()
    enrichment = ComunicadoDataEnrichmentService(catalog=catalog, gateway=gateway)
    return PresentationPatchService(
        catalog=catalog,
        repo=_Repo(slide),
        resolution=SlideDataResolutionService(catalog=catalog, enrichment=enrichment),
    )


PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"
SLIDE_ID = "00000000-0000-0000-0000-000000000002"


def _envelope(ops: list[dict]) -> dict:
    return {"target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID}, "ops": ops}


def _inspect_dispatch(slide: dict, playlist_id: str, sid: str):
    writes = MagicMock()
    writes.get_slide.return_value = slide
    writes.get_playlist.return_value = {
        "id": playlist_id,
        "name": "Comercial",
        "dataDefaults": {},
    }
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    user = _user()
    patches = (
        patch.object(
            dispatch._access,
            "resolve",
            return_value=SimpleNamespace(
                can_read=True,
                can_edit=True,
                level="owner",
                playlist={"id": playlist_id, "name": "Comercial", "dataDefaults": {}},
            ),
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
    )
    return dispatch, user, patches


def _inspect(slide: dict, playlist_id: str, sid: str, **kw) -> dict:
    dispatch, user, patches = _inspect_dispatch(slide, playlist_id, sid)
    with patches[0], patches[1]:
        return dispatch.inspect_data_model(
            user=user,
            playlist_id=playlist_id,
            slide_id=sid,
            model_id=MODEL_ID,
            authorization=None,
            **kw,
        )


# ---------------------------------------------------------------------------
# A/B — Lossless inspection
# ---------------------------------------------------------------------------


def test_inspect_lossless_single_input_no_transform():
    slide_id = str(uuid4())
    playlist_id = str(uuid4())
    model = {
        "id": MODEL_ID,
        "label": "Simples",
        "primaryInputId": "only",
        "inputs": [
            {
                "id": "only",
                "operationId": OP_ROL,
                "params": {"branch": "01"},
            }
        ],
    }
    slide = {
        "id": slide_id,
        "nativeConfig": {"version": 5, "blocks": [], "dataModels": [model]},
    }
    out = _inspect(slide, playlist_id, slide_id, include_runtime=False)
    definition = out["definition"]
    assert definition["inputs"][0]["transform"] is None
    assert definition["inputs"][0]["hasTransform"] is False
    assert definition["transform"] is None
    assert out["definitionCompleteness"] == "full"
    assert len(out["definitionDigest"]) == 64
    # definition é diretamente reutilizável como base de candidato
    normalized = normalize_data_model(
        definition, catalog=TvDataRouteCatalogService()
    )
    assert normalized["id"] == MODEL_ID


def test_inspect_lossless_twenty_inputs_seven_transforms():
    slide_id = str(uuid4())
    playlist_id = str(uuid4())
    slide = _slide(slide_id)
    out = _inspect(slide, playlist_id, slide_id, include_runtime=False)
    definition = out["definition"]

    assert len(definition["inputs"]) == 20
    with_transform = [
        i for i in definition["inputs"] if i.get("transform") is not None
    ]
    assert len(with_transform) == 7
    persisted = slide["nativeConfig"]["dataModels"][0]
    for item, raw in zip(definition["inputs"], persisted["inputs"]):
        assert item["id"] == raw["id"]
        assert item["operationId"] == raw["operationId"]
        assert item["params"] == raw["params"]
        expected_transform = raw.get("transform")
        assert item["transform"] == expected_transform
        assert item["hasTransform"] == isinstance(expected_transform, dict)
    assert definition["transform"] == persisted["transform"]
    assert definition["fieldLabels"] == persisted["fieldLabels"]
    assert definition["label"] == persisted["label"]
    assert definition["primaryInputId"] == persisted["primaryInputId"]
    assert out["definitionCompleteness"] == "full"


def test_inspect_definition_round_trips_through_normalization():
    slide_id = str(uuid4())
    playlist_id = str(uuid4())
    slide = _slide(slide_id)
    persisted = slide["nativeConfig"]["dataModels"][0]
    out = _inspect(slide, playlist_id, slide_id, include_runtime=False)
    catalog = TvDataRouteCatalogService()
    from_definition = normalize_data_model(out["definition"], catalog=catalog)
    from_persisted = normalize_data_model(persisted, catalog=catalog)
    assert from_definition == from_persisted


def test_inspect_digest_stable_for_same_definition():
    slide_id = str(uuid4())
    playlist_id = str(uuid4())
    slide = _slide(slide_id)
    first = _inspect(slide, playlist_id, slide_id, include_runtime=False)
    second = _inspect(slide, playlist_id, slide_id, include_runtime=False)
    assert first["definitionDigest"] == second["definitionDigest"]
    changed = copy.deepcopy(slide)
    changed["nativeConfig"]["dataModels"][0]["label"] = "outro"
    third = _inspect(changed, playlist_id, slide_id, include_runtime=False)
    assert third["definitionDigest"] != first["definitionDigest"]


def test_inspect_runtime_compacts_before_definition_under_budget():
    """definition nunca é truncada; metadados de runtime cedem primeiro."""
    slide_id = str(uuid4())
    playlist_id = str(uuid4())
    slide = _slide(slide_id)
    dispatch, user, patches = _inspect_dispatch(slide, playlist_id, slide_id)
    dispatch._preview.preview_data_model = MagicMock(
        return_value={
            "data": {f"consumer_metric_column_{i:05d}": 1 for i in range(15000)}
        }
    )
    with patches[0], patches[1]:
        out = dispatch.inspect_data_model(
            user=user,
            playlist_id=playlist_id,
            slide_id=slide_id,
            model_id=MODEL_ID,
            authorization=None,
            include_runtime=True,
        )
    assert out["definition"]["inputs"] and len(out["definition"]["inputs"]) == 20
    assert out["runtime"]["state"] == "omitted"
    assert out["outputSchema"] is None


def test_inspect_fails_typed_when_definition_alone_exceeds_budget():
    slide_id = str(uuid4())
    playlist_id = str(uuid4())
    model = _incident_model()
    for item in model["inputs"]:
        item["params"]["blob"] = "x" * 6000
    slide = {
        "id": slide_id,
        "nativeConfig": {"version": 5, "blocks": [], "dataModels": [model]},
    }
    dispatch, user, patches = _inspect_dispatch(slide, playlist_id, slide_id)
    with patches[0], patches[1], pytest.raises(GptActionsError) as caught:
        dispatch.inspect_data_model(
            user=user,
            playlist_id=playlist_id,
            slide_id=slide_id,
            model_id=MODEL_ID,
            authorization=None,
            include_runtime=False,
        )
    assert caught.value.code == "RESPONSE_BUDGET_EXCEEDED"
    assert caught.value.details["modelId"] == MODEL_ID


# ---------------------------------------------------------------------------
# D — no-op round-trip via upsert
# ---------------------------------------------------------------------------


def test_upsert_with_inspected_definition_is_semantic_noop():
    slide = _slide(SLIDE_ID)
    persisted = slide["nativeConfig"]["dataModels"][0]
    playlist_id = str(uuid4())
    inspected = _inspect(slide, playlist_id, SLIDE_ID, include_runtime=False)
    definition = inspected["definition"]

    svc = _patch_service(slide)
    result = svc.preview(
        _envelope([{"op": "upsert_data_model", "model": definition}]),
        user=_user(),
    )
    catalog = TvDataRouteCatalogService()
    candidate = result["nativeConfig"]["dataModels"][0]
    assert normalize_data_model(candidate, catalog=catalog) == normalize_data_model(
        persisted, catalog=catalog
    )
    # bindings visuais preservados (style defaults podem ser injetados pelo
    # reducer canônico de persistência — não é mutação do modelo)
    keys = ("id", "type", "modelId", "dataSourceId", "textProjection", "kpiProjection")
    for cand_block, pers_block in zip(
        result["nativeConfig"]["blocks"], slide["nativeConfig"]["blocks"]
    ):
        for key in keys:
            assert cand_block.get(key) == pers_block.get(key), key


# ---------------------------------------------------------------------------
# E–H — patch_data_model semantics
# ---------------------------------------------------------------------------


def _patched_model(result: dict) -> dict:
    return result["nativeConfig"]["dataModels"][0]


def _normalized(model: dict) -> dict:
    """Comparação semântica — mesma normalização canônica em ambos os lados
    (persistido pode omitir chaves default que o normalize emite)."""
    return normalize_data_model(model, catalog=TvDataRouteCatalogService())


def test_patch_one_input_param_preserves_other_nineteen():
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    result = svc.preview(
        _envelope(
            [
                {
                    "op": "patch_data_model",
                    "modelId": MODEL_ID,
                    "inputPatches": [
                        {
                            "inputId": "inp_05",
                            "params": {"set": {"customer_segment": "weg"}},
                        }
                    ],
                }
            ]
        ),
        user=_user(),
    )
    candidate = _patched_model(result)
    persisted = slide["nativeConfig"]["dataModels"][0]
    assert candidate["id"] == MODEL_ID
    target = next(i for i in candidate["inputs"] if i["id"] == "inp_05")
    assert target["params"]["customer_segment"] == "weg"
    assert target["params"]["branch"] == "01"
    assert target["transform"] == persisted["inputs"][5]["transform"]
    cand_norm = _normalized(candidate)
    pers_norm = _normalized(persisted)
    others = [i for i in cand_norm["inputs"] if i["id"] != "inp_05"]
    originals = [i for i in pers_norm["inputs"] if i["id"] != "inp_05"]
    assert others == originals
    assert cand_norm["transform"] == pers_norm["transform"]
    assert cand_norm["fieldLabels"] == pers_norm["fieldLabels"]
    assert result["persisted"] is False
    patch_info = result["sideEffects"]["dataModelPatches"][0]
    assert patch_info["changedInputs"] == ["inp_05"]
    assert patch_info["changedParams"]["inp_05"]["set"]["customer_segment"] == "weg"


def test_patch_expression_spec_persists_ast_not_literal():
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    result = svc.preview(
        _envelope(
            [
                {
                    "op": "patch_data_model",
                    "modelId": MODEL_ID,
                    "inputPatches": [
                        {
                            "inputId": "inp_01",
                            "params": {
                                "set": {
                                    "start_date": _MONTH_PREV["start_date"],
                                    "end_date": _MONTH_PREV["end_date"],
                                },
                                "unset": ["dateRangePreset"],
                            },
                        }
                    ],
                }
            ]
        ),
        user=_user(),
    )
    candidate = _patched_model(result)
    persisted = slide["nativeConfig"]["dataModels"][0]
    target = next(i for i in candidate["inputs"] if i["id"] == "inp_01")
    assert target["params"]["start_date"] == _MONTH_PREV["start_date"]
    assert target["params"]["end_date"] == _MONTH_PREV["end_date"]
    assert "dateRangePreset" not in target["params"]
    # AST preservado — não materializado em literal
    assert target["params"]["start_date"]["expression"]["expression"]["kind"] == "call"
    originals = [i for i in _normalized(persisted)["inputs"] if i["id"] != "inp_01"]
    others = [i for i in _normalized(candidate)["inputs"] if i["id"] != "inp_01"]
    assert others == originals


def test_patch_model_transform_preserves_all_inputs():
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    new_transform = {
        "version": 1,
        "steps": [
            *slide["nativeConfig"]["dataModels"][0]["transform"]["steps"][:-1],
            {
                "op": "addColumn",
                "name": "nn_es_mom_pct",
                "expr": "(rol_00 / rol_01 - 1) * 10",
            },
        ],
    }
    result = svc.preview(
        _envelope(
            [
                {
                    "op": "patch_data_model",
                    "modelId": MODEL_ID,
                    "modelPatch": {"transform": new_transform},
                }
            ]
        ),
        user=_user(),
    )
    candidate = _patched_model(result)
    persisted = slide["nativeConfig"]["dataModels"][0]
    assert _normalized(candidate)["inputs"] == _normalized(persisted)["inputs"]
    assert candidate["fieldLabels"] == persisted["fieldLabels"]
    assert candidate["transform"]["steps"][-1]["name"] == "nn_es_mom_pct"
    assert "10" in candidate["transform"]["steps"][-1]["expr"]
    patch_info = result["sideEffects"]["dataModelPatches"][0]
    assert patch_info["modelTransformChanged"] is True
    assert patch_info["changedInputs"] == []


def test_patch_input_transform_preserves_siblings():
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    new_input_transform = {
        "version": 1,
        "steps": [
            {"op": "rename", "from": "rol", "to": "rol_03b"},
            {"op": "addColumn", "name": "join_key", "expr": "1"},
            {"op": "select", "columns": ["join_key", "rol_03b"]},
        ],
    }
    result = svc.preview(
        _envelope(
            [
                {
                    "op": "patch_data_model",
                    "modelId": MODEL_ID,
                    "inputPatches": [
                        {"inputId": "inp_03", "transform": new_input_transform}
                    ],
                }
            ]
        ),
        user=_user(),
    )
    candidate = _patched_model(result)
    persisted = slide["nativeConfig"]["dataModels"][0]
    target = next(i for i in candidate["inputs"] if i["id"] == "inp_03")
    assert target["transform"]["steps"][0]["to"] == "rol_03b"
    others = [i for i in _normalized(candidate)["inputs"] if i["id"] != "inp_03"]
    originals = [i for i in _normalized(persisted)["inputs"] if i["id"] != "inp_03"]
    assert others == originals


# ---------------------------------------------------------------------------
# I–K — failure cases (zero writes / typed errors)
# ---------------------------------------------------------------------------


def test_patch_unknown_input_fails_without_writes():
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    with pytest.raises(PresentationPatchError) as caught:
        svc.preview(
            _envelope(
                [
                    {
                        "op": "patch_data_model",
                        "modelId": MODEL_ID,
                        "inputPatches": [
                            {"inputId": "ghost", "params": {"set": {"branch": "02"}}}
                        ],
                    }
                ]
            ),
            user=_user(),
        )
    assert caught.value.code == "data_model.input_not_found"
    assert slide["nativeConfig"]["dataModels"][0]["inputs"][0]["params"]["branch"] == "01"


def test_patch_unknown_model_fails():
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    with pytest.raises(PresentationPatchError) as caught:
        svc.preview(
            _envelope(
                [
                    {
                        "op": "patch_data_model",
                        "modelId": "mdl_ghost",
                        "modelPatch": {"label": "x"},
                    }
                ]
            ),
            user=_user(),
        )
    assert caught.value.code == "data_model.not_found"


def test_patch_invalid_transform_fails():
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    with pytest.raises(PresentationPatchError):
        svc.preview(
            _envelope(
                [
                    {
                        "op": "patch_data_model",
                        "modelId": MODEL_ID,
                        "modelPatch": {
                            "transform": {"script": "let x = 1", "language": "m"}
                        },
                    }
                ]
            ),
            user=_user(),
        )


def test_patch_noop_fails_typed():
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    with pytest.raises(PresentationPatchError) as caught:
        svc.preview(
            _envelope(
                [
                    {
                        "op": "patch_data_model",
                        "modelId": MODEL_ID,
                        "inputPatches": [
                            {
                                "inputId": "inp_10",
                                "params": {"set": {"customer_segment": "seg_10"}},
                            }
                        ],
                    }
                ]
            ),
            user=_user(),
        )
    assert caught.value.code == "data_model.patch_noop"


def test_patch_candidate_losing_consumer_field_fails():
    """Remover coluna ligada por consumer (nn_es_mom_pct) → PREPARE falha."""
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    drop_calc = {
        "version": 1,
        "steps": [
            {"op": "select", "columns": ["rol_00", "join_key"]},
        ],
    }
    with pytest.raises(PresentationPatchError) as caught:
        svc.preview(
            _envelope(
                [
                    {
                        "op": "patch_data_model",
                        "modelId": MODEL_ID,
                        "modelPatch": {"transform": drop_calc},
                    }
                ]
            ),
            user=_user(),
        )
    assert caught.value.code == "DATA_BINDING_FIELD_MISSING"
    assert "nn_es_mom_pct" in str(caught.value.details)


# ---------------------------------------------------------------------------
# Business case — October comparative + calculated field
# ---------------------------------------------------------------------------


def test_business_case_period_expressions_and_calculated_field():
    """Modelo incidente: 4 períodos equivalentes via ExpressionSpec +
    coluna calculada preservada (preview produz nn_es_mom_pct ≈ 35.9%)."""
    slide = _slide(SLIDE_ID)
    svc = _patch_service(slide)
    result = svc.preview(
        _envelope(
            [
                {
                    "op": "patch_data_model",
                    "modelId": MODEL_ID,
                    "inputPatches": [
                        {
                            "inputId": "inp_00",
                            "params": {
                                "set": {
                                    "start_date": _MONTH_CURRENT["start_date"],
                                    "end_date": _MONTH_CURRENT["end_date"],
                                },
                                "unset": ["dateRangePreset"],
                            },
                        },
                        {
                            "inputId": "inp_01",
                            "params": {
                                "set": {
                                    "start_date": _MONTH_PREV["start_date"],
                                    "end_date": _MONTH_PREV["end_date"],
                                },
                                "unset": ["dateRangePreset"],
                            },
                        },
                        {
                            "inputId": "inp_02",
                            "params": {
                                "set": {
                                    "start_date": _YTD_CURRENT["start_date"],
                                    "end_date": _YTD_CURRENT["end_date"],
                                },
                                "unset": ["dateRangePreset"],
                            },
                        },
                        {
                            "inputId": "inp_03",
                            "params": {
                                "set": {
                                    "start_date": _YTD_PREV["start_date"],
                                    "end_date": _YTD_PREV["end_date"],
                                },
                                "unset": ["dateRangePreset"],
                            },
                        },
                    ],
                }
            ]
        ),
        user=_user(),
    )
    candidate = _patched_model(result)
    params = {i["id"]: i["params"] for i in candidate["inputs"]}
    assert params["inp_00"]["start_date"] == _MONTH_CURRENT["start_date"]
    assert params["inp_00"]["end_date"] == _MONTH_CURRENT["end_date"]
    assert params["inp_01"]["start_date"] == _MONTH_PREV["start_date"]
    assert params["inp_01"]["end_date"] == _MONTH_PREV["end_date"]
    assert params["inp_02"]["start_date"] == _YTD_CURRENT["start_date"]
    assert params["inp_03"]["start_date"] == _YTD_PREV["start_date"]
    # AST — nunca literal persistido
    assert params["inp_00"]["start_date"]["expression"]["expression"] == _call(
        "Date.StartOfMonth", _ident("today")
    )
    assert params["inp_03"]["end_date"]["expression"]["expression"] == _PREV_YEAR
    # Nada mais mudou
    keep = {"inp_00", "inp_01", "inp_02", "inp_03"}
    untouched = [
        i for i in _normalized(candidate)["inputs"] if i["id"] not in keep
    ]
    originals = [
        i
        for i in _normalized(slide["nativeConfig"]["dataModels"][0])["inputs"]
        if i["id"] not in keep
    ]
    assert untouched == originals

    # preview runtime do candidato — coluna calculada presente e correta
    catalog = TvDataRouteCatalogService()
    gateway = _gateway_by_segment(
        {f"seg_{i:02d}": _rol_payload(1359.0 if i == 0 else 1000.0) for i in range(20)}
    )
    enrichment = ComunicadoDataEnrichmentService(catalog=catalog, gateway=gateway)
    resolved = enrichment.enrich_data_models(
        [candidate],
        cfg=result["nativeConfig"],
        authorization=None,
        playlist_defaults={"branch": "01"},
    )[MODEL_ID]
    assert not resolved.get("error"), resolved.get("error")
    row = resolved["table"]["rows"][0]
    assert row["nn_es_mom_pct"] == pytest.approx(35.9, abs=0.05)
    assert row["rol_00"] == pytest.approx(1359.0)
    assert row["rol_01"] == pytest.approx(1000.0)
