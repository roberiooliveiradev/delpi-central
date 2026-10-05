"""TV-DM-ADDR-001 — DataModel addressability na leitura compacta da VISTA.

GET_PLAYLIST_CONTEXT (scope=editorFocus e downgrade full→editorFocus) deve
expor ids persistidos de DataModel sem reconstrução: ``dataModels[]``,
``blockIndex[].modelId`` e ``focusedBinding``. O id descoberto deve ser
aceito diretamente por ``inspect_data_model``.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.response_compact import (
    GPT_ACTIONS_RESPONSE_MAX_BYTES,
    focused_binding_from_blocks,
    project_block_index_item,
    project_data_models_from_slide,
    utf8_size,
)
from tv_app.application.services.editor_focus_store import EditorFocusStore

MODEL_ID = "mdl_commercial_compare"
SECOND_MODEL_ID = "mdl_other"
OP_ROL = "get_commercial_rol_summary"


def _dm_model(model_id: str, label: str) -> dict:
    return {
        "id": model_id,
        "label": label,
        "primaryInputId": "inp_current",
        "inputs": [
            {
                "id": "inp_current",
                "label": "Ano corrente",
                "queryName": "q_current",
                "operationId": OP_ROL,
                "params": {
                    "branch": "01",
                    "dateRangePreset": "this_year",
                },
            },
            {
                "id": "inp_prev",
                "label": "Ano anterior",
                "queryName": "q_prev",
                "operationId": OP_ROL,
                "params": {
                    "branch": "01",
                    "dateRangePreset": "same_period_previous_year",
                },
            },
        ],
        "transform": {"version": 1, "steps": [{"op": "addColumn", "name": "join_key", "expr": "1"}]},
    }


def _fixture_blocks() -> list[dict]:
    return [
        {
            "id": "rx_weg_sc_m25v",
            "type": "text",
            "modelId": MODEL_ID,
            "textProjection": {"field": "weg_sc_m25"},
        },
        {
            "id": "rx_weg_sc_m26v",
            "type": "text",
            "modelId": MODEL_ID,
            "textProjection": {"field": "weg_sc_m26"},
        },
        {
            "id": "legacy_kpi",
            "type": "kpi_view",
            "dataSourceId": "ds1",
        },
        {
            "id": "ds1",
            "type": "data_source",
            "dataBinding": {
                "operationId": "op.demo",
                "params": {"branch": "01"},
                "label": "Fonte legada",
            },
        },
        {
            "id": "hybrid_kpi",
            "type": "kpi_view",
            "modelId": MODEL_ID,
            "dataSourceId": "ds1",
            "kpiProjection": {"valueField": "tot_m25"},
        },
        {
            "id": "grid1",
            "type": "canvas_table",
            "cells": [
                [
                    {"modelId": SECOND_MODEL_ID, "dataRef": {"field": "nn_sc_m25"}},
                    {"modelId": MODEL_ID, "dataRef": {"field": "weg_es_m25"}},
                ]
            ],
        },
    ]


def _fixture_slide(slide_id: str) -> dict:
    return {
        "id": slide_id,
        "title": "Realizado 2025 x 2026 - Cards",
        "sortOrder": 0,
        "nativeConfig": {
            "version": 5,
            "blocks": _fixture_blocks(),
            "dataModels": [
                _dm_model(MODEL_ID, "Comparativo Comercial"),
                _dm_model(SECOND_MODEL_ID, "Outro modelo"),
            ],
        },
    }


def _dispatch_with_fixture(selected_ids: list[str] | None = None):
    """Dispatch com slide canônico (dataModels + bindings persistidos)."""
    writes = MagicMock()
    playlist_id = str(uuid4())
    sid = str(uuid4())
    slide = _fixture_slide(sid)
    writes.get_playlist.return_value = {
        "id": playlist_id,
        "name": "Comercial - Alinhamento Estratégico",
        "dataDefaults": {},
    }
    writes.list_slides.return_value = [slide]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 2788
    writes.get_slide.return_value = slide
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    store = EditorFocusStore(ttl_seconds=90)
    if selected_ids is not None:
        store.record(
            user_id="u1",
            playlist_id=playlist_id,
            slide_id=sid,
            selected_ids=selected_ids,
        )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")
    return dispatch, store, playlist_id, sid, slide, user


def _patches(dispatch, store, playlist_id):
    return (
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
        patch.object(dispatch, "_actor", return_value="u1"),
        patch(
            "tv_app.application.services.editor_focus_store.editor_focus_store",
            store,
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
        patch(
            "tv_app.application.services.data.brand_logo_media_service.BrandLogoMediaService.list_brand_assets",
            return_value={},
        ),
        patch(
            "tv_app.application.services.data.brand_logo_media_service.BrandLogoMediaService.list_playlist_assets",
            return_value=[],
        ),
    )


def test_block_index_item_exposes_model_id_and_preserves_data_source_id():
    row = project_block_index_item(
        {
            "id": "rx_weg_sc_m25v",
            "type": "text",
            "modelId": MODEL_ID,
            "textProjection": {"field": "weg_sc_m25"},
        }
    )
    assert row["modelId"] == MODEL_ID
    assert row["bindingField"] == "weg_sc_m25"
    assert "dataSourceId" not in row

    legacy = project_block_index_item(
        {"id": "legacy_kpi", "type": "kpi_view", "dataSourceId": "ds1"}
    )
    assert legacy["dataSourceId"] == "ds1"
    assert "modelId" not in legacy

    hybrid = project_block_index_item(
        {
            "id": "hybrid_kpi",
            "type": "kpi_view",
            "modelId": MODEL_ID,
            "dataSourceId": "ds1",
        }
    )
    assert hybrid["modelId"] == MODEL_ID
    assert hybrid["dataSourceId"] == "ds1"


def test_project_data_models_from_slide_compact_summary():
    slide = _fixture_slide("s1")
    models = project_data_models_from_slide(slide)
    ids = [m["id"] for m in models]
    assert ids == sorted(ids) == [MODEL_ID, SECOND_MODEL_ID]

    primary = models[0]
    assert primary["label"] == "Comparativo Comercial"
    assert primary["primaryInputId"] == "inp_current"
    assert primary["inputCount"] == 2
    assert primary["hasTransform"] is True
    # consumers = blocos (não campos): 3 binds diretos + 1 célula do grid1
    assert primary["consumerCount"] == 4
    assert set(primary["consumerBlockIds"]) == {
        "rx_weg_sc_m25v",
        "rx_weg_sc_m26v",
        "hybrid_kpi",
        "grid1",
    }

    second = models[1]
    assert set(second["consumerBlockIds"]) == {"grid1"}
    assert "rx_weg_sc_m25v" not in second["consumerBlockIds"]

    # Nenhuma definição completa vaza para a projeção compacta.
    for row in models:
        assert "inputs" not in row
        assert "transform" not in row
        assert "fieldLabels" not in row


def test_project_data_models_empty_slide_and_no_models():
    assert project_data_models_from_slide(None) == []
    assert project_data_models_from_slide({"nativeConfig": {"blocks": []}}) == []
    legacy_only = {
        "nativeConfig": {
            "blocks": [{"id": "b1", "type": "kpi_view", "dataSourceId": "ds1"}]
        }
    }
    assert project_data_models_from_slide(legacy_only) == []


def test_focused_binding_derives_from_persisted_block_only():
    blocks = _fixture_blocks()
    binding = focused_binding_from_blocks(blocks, ["rx_weg_sc_m25v"])
    assert binding == {
        "blockId": "rx_weg_sc_m25v",
        "modelId": MODEL_ID,
        "dataSourceId": None,
        "bindingField": "weg_sc_m25",
    }

    # Legacy block: dataSourceId verdadeiro, sem modelId inventado.
    legacy = focused_binding_from_blocks(blocks, ["legacy_kpi"])
    assert legacy["modelId"] is None
    assert legacy["dataSourceId"] == "ds1"

    # Hybrid: ambos verdadeiros (modelId tem precedência semântica).
    hybrid = focused_binding_from_blocks(blocks, ["hybrid_kpi"])
    assert hybrid["modelId"] == MODEL_ID
    assert hybrid["dataSourceId"] == "ds1"

    # Sem seleção única / seleção inexistente / bloco sem binding → None.
    assert focused_binding_from_blocks(blocks, None) is None
    assert focused_binding_from_blocks(blocks, []) is None
    assert focused_binding_from_blocks(blocks, ["a", "b"]) is None
    assert focused_binding_from_blocks(blocks, ["ghost"]) is None
    assert focused_binding_from_blocks(blocks, ["ds1"]) is None


def test_editor_focus_scope_exposes_datamodel_addressability():
    dispatch, store, playlist_id, sid, _slide, user = _dispatch_with_fixture(
        selected_ids=["rx_weg_sc_m25v"]
    )
    patches = _patches(dispatch, store, playlist_id)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        out = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            scope="editorFocus",
            preview_slide_id=sid,
        )

    assert out["scope"] == "editorFocus"
    assert "nativeConfig" not in (out.get("focusedSlide") or {})

    models = out["dataModels"]
    assert [m["id"] for m in models] == [MODEL_ID, SECOND_MODEL_ID]
    assert "rx_weg_sc_m25v" in models[0]["consumerBlockIds"]

    index = {item["id"]: item for item in out["blockIndex"]["items"]}
    assert index["rx_weg_sc_m25v"]["modelId"] == MODEL_ID
    assert index["rx_weg_sc_m25v"]["bindingField"] == "weg_sc_m25"
    assert index["legacy_kpi"]["dataSourceId"] == "ds1"
    assert "modelId" not in index["legacy_kpi"]
    assert index["hybrid_kpi"]["modelId"] == MODEL_ID
    assert index["hybrid_kpi"]["dataSourceId"] == "ds1"
    # grid1 não tem modelId top-level — não inventar um.
    assert "modelId" not in index["grid1"]

    binding = out["focusedBinding"]
    assert binding["blockId"] == "rx_weg_sc_m25v"
    assert binding["modelId"] == MODEL_ID
    assert binding["bindingField"] == "weg_sc_m25"

    assert utf8_size(out) < GPT_ACTIONS_RESPONSE_MAX_BYTES


def test_context_to_inspect_end_to_end_acceptance():
    """context modelId == inspect modelId == persisted model id."""
    dispatch, store, playlist_id, sid, slide, user = _dispatch_with_fixture(
        selected_ids=["rx_weg_sc_m25v"]
    )
    patches = _patches(dispatch, store, playlist_id)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        ctx = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            scope="editorFocus",
            preview_slide_id=sid,
        )
        discovered = ctx["focusedBinding"]["modelId"]
        assert discovered
        inspect = dispatch.inspect_data_model(
            user=user,
            playlist_id=playlist_id,
            slide_id=sid,
            model_id=discovered,
            authorization=None,
            include_runtime=False,
        )

    persisted_id = slide["nativeConfig"]["dataModels"][0]["id"]
    assert discovered == persisted_id
    assert inspect["modelId"] == persisted_id
    assert inspect["definition"]["id"] == persisted_id
    assert inspect["definition"]["primaryInputId"] == "inp_current"
    assert {i["id"] for i in inspect["definition"]["inputs"]} == {
        "inp_current",
        "inp_prev",
    }
    assert inspect["consumerCount"] == 4
    assert "rx_weg_sc_m25v" in inspect["consumers"]


def test_full_scope_downgrade_retains_datamodel_addressability():
    """full → editorFocus downgrade por budget preserva modelId/da-taModels."""
    writes = MagicMock()
    playlist_id = str(uuid4())
    sid = str(uuid4())
    pad = "P" * 2500
    heavy_blocks: list[dict] = [
        {
            "id": "rx_weg_sc_m25v",
            "type": "text",
            "modelId": MODEL_ID,
            "textProjection": {"field": "weg_sc_m25"},
        }
    ]
    for i in range(60):
        heavy_blocks.append(
            {
                "id": f"txt-{i}",
                "type": "text",
                "frame": {"x": i, "y": i, "w": 40, "h": 20},
                "content": pad,
                "style": {"fontFamily": "Arial", "notes": pad},
            }
        )
    slide = {
        "id": sid,
        "title": "Realizado 2025 x 2026 - Cards",
        "sortOrder": 0,
        "nativeConfig": {
            "version": 5,
            "blocks": heavy_blocks,
            "dataModels": [_dm_model(MODEL_ID, "Comparativo Comercial")],
            "speakerNotes": pad * 20,
        },
    }
    writes.get_playlist.return_value = {
        "id": playlist_id,
        "name": "Comercial - Alinhamento Estratégico",
        "dataDefaults": {},
    }
    writes.list_slides.return_value = [slide]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 2788
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    store = EditorFocusStore(ttl_seconds=90)
    store.record(
        user_id="u1",
        playlist_id=playlist_id,
        slide_id=sid,
        selected_ids=["rx_weg_sc_m25v"],
    )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")
    patches = _patches(dispatch, store, playlist_id)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        out = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            preview_slide_id=sid,
            scope="full",
        )

    assert out["scope"] == "editorFocus"
    assert out.get("scopeDowngraded") is True
    assert out.get("scopeDowngradeReason") == "response_budget"
    assert "nativeConfig" not in (out.get("focusedSlide") or {})

    assert [m["id"] for m in out["dataModels"]] == [MODEL_ID]
    assert out["dataModels"][0]["consumerBlockIds"] == ["rx_weg_sc_m25v"]
    assert out["focusedBinding"]["modelId"] == MODEL_ID
    assert out["focusedBinding"]["blockId"] == "rx_weg_sc_m25v"

    index = {item["id"]: item for item in out["blockIndex"]["items"]}
    assert index["rx_weg_sc_m25v"]["modelId"] == MODEL_ID
    assert utf8_size(out) < GPT_ACTIONS_RESPONSE_MAX_BYTES


def test_no_datamodel_slide_regression():
    """Slide legado sem dataModels: dataModels=[] e nenhum modelId inventado."""
    writes = MagicMock()
    playlist_id = str(uuid4())
    sid = str(uuid4())
    slide = {
        "id": sid,
        "title": "Legado",
        "sortOrder": 0,
        "nativeConfig": {
            "version": 5,
            "blocks": [
                {"id": "ds1", "type": "data_source", "dataBinding": {"operationId": "op.demo"}},
                {"id": "kpi1", "type": "kpi_view", "dataSourceId": "ds1"},
            ],
        },
    }
    writes.get_playlist.return_value = {"id": playlist_id, "name": "P", "dataDefaults": {}}
    writes.list_slides.return_value = [slide]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 1
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    store = EditorFocusStore(ttl_seconds=90)
    store.record(
        user_id="u1", playlist_id=playlist_id, slide_id=sid, selected_ids=["kpi1"]
    )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")
    patches = _patches(dispatch, store, playlist_id)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        out = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            scope="editorFocus",
            preview_slide_id=sid,
        )

    assert out["dataModels"] == []
    assert out["focusedBinding"]["dataSourceId"] == "ds1"
    assert out["focusedBinding"]["modelId"] is None
    index = {item["id"]: item for item in out["blockIndex"]["items"]}
    assert index["kpi1"]["dataSourceId"] == "ds1"
    assert "modelId" not in index["kpi1"]
    assert utf8_size(out) < GPT_ACTIONS_RESPONSE_MAX_BYTES


def _ident(name: str) -> dict[str, Any]:
    return {"kind": "identifier", "value": name}


def _lit(value: Any) -> dict[str, Any]:
    return {"kind": "literal", "value": value}


def _call(fn: str, *args: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "call", "value": fn, "children": list(args)}


def _expr(ast: dict[str, Any]) -> dict[str, Any]:
    return {"expression": {"version": 1, "expression": ast}}


_PREV_YEAR = _call("Date.AddYears", _ident("today"), _lit(-1))

# Comparativo de outubro — períodos equivalentes 2025 x 2026 (ExpressionSpec).
_MONTH_CURRENT_PARAMS = {
    "start_date": _expr(_call("Date.StartOfMonth", _ident("today"))),
    "end_date": _expr(_ident("today")),
}
_MONTH_PREV_PARAMS = {
    "start_date": _expr(_call("Date.StartOfMonth", _PREV_YEAR)),
    "end_date": _expr(_PREV_YEAR),
}
_YTD_CURRENT_PARAMS = {
    "start_date": _expr(_call("Date.StartOfYear", _ident("today"))),
    "end_date": _expr(_ident("today")),
}
_YTD_PREV_PARAMS = {
    "start_date": _expr(_call("Date.StartOfYear", _PREV_YEAR)),
    "end_date": _expr(_PREV_YEAR),
}


def test_business_case_prepare_only_flow():
    """Fluxo completo sem mutação: context → inspect → candidate → preview.

    Prova que, com o modelId descoberto, o caso de negócio (comparativo de
    outubro 2025 x 2026, mensal + YTD) é construtível sobre a definição
    persistida — sem inventar ids nem reconstruir o modelo às cegas.
    """
    import copy

    dispatch, store, playlist_id, sid, slide, user = _dispatch_with_fixture(
        selected_ids=["rx_weg_sc_m25v"]
    )
    preview = MagicMock()
    preview.preview_data_model.return_value = {
        "fields": ["rol", "rol_prev", "value"],
        "valueFields": ["value"],
    }
    dispatch._preview = preview
    patches = _patches(dispatch, store, playlist_id)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        ctx = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            scope="editorFocus",
            preview_slide_id=sid,
        )
        model_id = ctx["focusedBinding"]["modelId"]

        inspected = dispatch.inspect_data_model(
            user=user,
            playlist_id=playlist_id,
            slide_id=sid,
            model_id=model_id,
            authorization=None,
            include_runtime=False,
        )
        definition = inspected["definition"]

        # Candidate = cópia do modelo persistido; só os params de período dos
        # inputs mudam (mensal corrente vs mensal ano anterior).
        persisted = next(
            m
            for m in slide["nativeConfig"]["dataModels"]
            if m["id"] == model_id
        )
        candidate = copy.deepcopy(persisted)
        candidate["inputs"][0]["params"] = {
            "branch": "01",
            **_MONTH_CURRENT_PARAMS,
        }
        candidate["inputs"][1]["params"] = {
            "branch": "01",
            **_MONTH_PREV_PARAMS,
        }

        out = dispatch.preview_data_model(
            user=user,
            body={
                "playlistId": playlist_id,
                "slideId": sid,
                "model": candidate,
            },
            authorization=None,
        )

    assert out["modelId"] == model_id
    resolved_arg, kwargs = preview.preview_data_model.call_args
    sent_model = resolved_arg[0]
    assert sent_model["id"] == model_id
    # Nada além dos params de período mudou — definição preservada.
    assert sent_model["label"] == persisted["label"]
    assert sent_model["primaryInputId"] == persisted["primaryInputId"]
    assert sent_model["transform"]["steps"] == persisted["transform"]["steps"]
    assert {i["operationId"] for i in sent_model["inputs"]} == {OP_ROL}
    cur = next(i for i in sent_model["inputs"] if i["id"] == "inp_current")
    prev = next(i for i in sent_model["inputs"] if i["id"] == "inp_prev")
    assert cur["params"]["start_date"] == _MONTH_CURRENT_PARAMS["start_date"]
    assert cur["params"]["end_date"] == _MONTH_CURRENT_PARAMS["end_date"]
    assert prev["params"]["start_date"] == _MONTH_PREV_PARAMS["start_date"]
    assert prev["params"]["end_date"] == _MONTH_PREV_PARAMS["end_date"]
    # YTD variants — mesmo contrato ExpressionSpec, períodos equivalentes.
    assert _YTD_CURRENT_PARAMS["start_date"]["expression"]["expression"]["value"] == (
        "Date.StartOfYear"
    )
    assert _YTD_PREV_PARAMS["end_date"]["expression"]["expression"] == _PREV_YEAR
