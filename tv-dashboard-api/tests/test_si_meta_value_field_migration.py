"""Wave 2 — testes do predicado/transformação da migração SI meta.

Cobre: positive (meta-bound text block), siblings (realized / non-SI parity /
presentation value / domain value ficam intactos), negativo (unrelated),
idempotência de rerun e a fronteira do predicado.
"""

from __future__ import annotations

import copy

from tv_app.application.services.data.si_meta_value_field_migration import (
    CANONICAL_FIELD,
    collect_si_meta_value_refs,
    migrate_native_config,
)

META_OP = "get_si_indicator_quality_ppm_internal_meta"
REALIZED_OP = "get_si_indicator_quality_ppm_internal_realized"
NON_SI_OP = "get_nonconformity_streak"
RANKING_OP = "get_refugos_rankings"


def _data_source(block_id: str, operation_id: str) -> dict:
    return {
        "id": block_id,
        "type": "data_source",
        "dataBinding": {"operationId": operation_id},
    }


def _text(block_id: str, source_id: str, field: str = "value") -> dict:
    return {
        "id": block_id,
        "type": "text",
        "dataSourceId": source_id,
        "textProjection": {"field": field},
    }


def _slide(*blocks: dict) -> dict:
    return {"layout": "canvas", "blocks": list(blocks)}


def test_positive_meta_bound_text_block_migrates_to_comparable_goal() -> None:
    doc = _slide(_data_source("src1", META_OP), _text("t1", "src1"))
    refs = collect_si_meta_value_refs(doc)
    assert len(refs) == 1
    assert refs[0]["operationId"] == META_OP
    assert refs[0]["field_path"] == "textProjection.field"

    migrated, applied = migrate_native_config(doc)
    assert len(applied) == 1
    assert migrated["blocks"][1]["textProjection"]["field"] == CANONICAL_FIELD
    # input não é mutado (deepcopy)
    assert doc["blocks"][1]["textProjection"]["field"] == "value"


def test_sibling_realized_binding_is_never_touched() -> None:
    doc = _slide(_data_source("src1", REALIZED_OP), _text("t1", "src1"))
    assert collect_si_meta_value_refs(doc) == []
    migrated, applied = migrate_native_config(doc)
    assert applied == []
    assert migrated is doc


def test_non_si_parity_and_presentation_refs_are_untouched() -> None:
    doc = _slide(
        _data_source("srcA", NON_SI_OP),
        _text("tA", "srcA"),
        _data_source("srcB", "get_production_otd_series"),
        {
            "id": "tB",
            "type": "chart",
            "dataSourceId": "srcB",
            "chartProjection": {"series": [{"field": "value"}]},
        },
    )
    assert collect_si_meta_value_refs(doc) == []
    migrated, applied = migrate_native_config(doc)
    assert applied == []
    assert migrated is doc


def test_legitimate_domain_value_untouched() -> None:
    doc = _slide(
        _data_source("src1", RANKING_OP),
        {
            "id": "t1",
            "type": "table",
            "dataSourceId": "src1",
            "tableProjection": {"columns": [{"field": "value"}]},
        },
    )
    migrated, applied = migrate_native_config(doc)
    assert applied == []
    assert migrated is doc


def test_unbound_and_unresolved_blocks_are_never_touched() -> None:
    doc = _slide(
        {"id": "free", "type": "text", "textProjection": {"field": "value"}},
        _text("orphan", "missing-source"),
    )
    migrated, applied = migrate_native_config(doc)
    assert applied == []
    assert migrated is doc


def test_direct_databinding_on_block_also_resolves() -> None:
    doc = _slide(
        {
            "id": "t1",
            "type": "text",
            "dataBinding": {"operationId": META_OP},
            "textProjection": {"field": "value"},
        }
    )
    migrated, applied = migrate_native_config(doc)
    assert len(applied) == 1
    assert migrated["blocks"][0]["textProjection"]["field"] == CANONICAL_FIELD


def test_only_exact_value_string_migrates() -> None:
    doc = _slide(
        _data_source("src1", META_OP),
        _text("t1", "src1", field="value_label"),
        _text("t2", "src1", field="values"),
    )
    assert collect_si_meta_value_refs(doc) == []


def test_selected_value_fields_list_element_migrates() -> None:
    doc = _slide(
        _data_source("src1", META_OP),
        {
            "id": "k1",
            "type": "kpi",
            "dataSourceId": "src1",
            "kpiProjection": {"selectedValueFields": ["comparable_goal", "value"]},
        },
    )
    migrated, applied = migrate_native_config(doc)
    assert len(applied) == 1
    assert migrated["blocks"][1]["kpiProjection"]["selectedValueFields"] == [
        "comparable_goal",
        "comparable_goal",
    ]


def test_rerun_is_idempotent() -> None:
    doc = _slide(_data_source("src1", META_OP), _text("t1", "src1"))
    migrated, applied = migrate_native_config(doc)
    assert len(applied) == 1
    again, applied2 = migrate_native_config(migrated)
    assert applied2 == []
    assert again is migrated or again == migrated


def test_nested_block_lists_are_supported() -> None:
    doc = {
        "pages": [
            {"blocks": [_data_source("s", META_OP), _text("t", "s")]}
        ]
    }
    refs = collect_si_meta_value_refs(doc)
    assert len(refs) == 1
