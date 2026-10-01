"""Wave 3 — testes do predicado/transformação da migração de parity aliases.

Cobre: positive por família semântica (streak / 5s / scrap / rework), siblings
(SI meta já migrado, SI realized, non-target op), presentation/domain value
intocados, count-mismatch fail-closed, idempotência e fronteira do predicado.
"""

from __future__ import annotations

from tv_app.application.services.data.value_field_binding_migration import (
    PARITY_ALIAS_FIELD_MAP,
    collect_value_refs,
    migrate_native_config,
    parity_alias_canonical_field,
)

STREAK_OP = "get_nonconformity_streak"
AUDIT_OP = "get_audit_5s_summary"
SCRAP_OP = "get_quality_scrap_cost_pct"
REWORK_OP = "get_quality_rework_cost_pct"
META_OP = "get_si_indicator_quality_ppm_internal_meta"
REALIZED_OP = "get_si_indicator_quality_ppm_internal_realized"
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


def _collect(doc):
    return collect_value_refs(doc, parity_alias_canonical_field)


def _migrate(doc):
    return migrate_native_config(doc, parity_alias_canonical_field)


def test_positive_streak_migrates_to_current_days_without_nc() -> None:
    doc = _slide(_data_source("src1", STREAK_OP), _text("t1", "src1"))
    refs = _collect(doc)
    assert len(refs) == 1
    assert refs[0]["canonical_field"] == "current_days_without_nc"
    migrated, applied = _migrate(doc)
    assert len(applied) == 1
    assert migrated["blocks"][1]["textProjection"]["field"] == "current_days_without_nc"
    assert doc["blocks"][1]["textProjection"]["field"] == "value"


def test_positive_audit_5s_migrates_to_average_score() -> None:
    doc = _slide(_data_source("src1", AUDIT_OP), _text("t1", "src1"))
    migrated, applied = _migrate(doc)
    assert len(applied) == 1
    assert migrated["blocks"][1]["textProjection"]["field"] == "average_score"


def test_positive_scrap_and_rework_migrate_to_semantic_pct() -> None:
    doc = _slide(
        _data_source("s1", SCRAP_OP),
        _text("t1", "s1"),
        _text("t2", "s1"),
        _data_source("s2", REWORK_OP),
        _text("t3", "s2"),
        _text("t4", "s2"),
    )
    migrated, applied = _migrate(doc)
    assert len(applied) == 4
    fields = [b["textProjection"]["field"] for b in migrated["blocks"] if b["type"] == "text"]
    assert fields == [
        "scrap_cost_pct",
        "scrap_cost_pct",
        "rework_cost_pct",
        "rework_cost_pct",
    ]


def test_sibling_ops_not_in_map_are_untouched() -> None:
    doc = _slide(
        _data_source("s1", "get_refugos_scrap_cost_pct"),  # irmão non-target
        _text("t1", "s1"),
        _data_source("s2", "get_kaizen_summary"),
        _text("t2", "s2"),
    )
    migrated, applied = _migrate(doc)
    assert applied == []
    assert migrated is doc


def test_same_operation_with_non_value_field_not_touched() -> None:
    doc = _slide(
        _data_source("src1", STREAK_OP),
        _text("t1", "src1", field="record_days_without_nc"),
    )
    migrated, applied = _migrate(doc)
    assert applied == []
    assert migrated is doc


def test_si_meta_and_realized_bindings_are_untouched() -> None:
    doc = _slide(
        _data_source("s1", META_OP),
        _text("t1", "s1", field="comparable_goal"),  # já migrado na Wave 2
        _data_source("s2", META_OP),
        _text("t2", "s2"),  # meta ainda em value: não é alvo da Wave 3
        _data_source("s3", REALIZED_OP),
        _text("t3", "s3"),
    )
    migrated, applied = _migrate(doc)
    assert applied == []
    assert migrated is doc


def test_presentation_and_domain_value_untouched() -> None:
    doc = _slide(
        _data_source("s1", "get_production_otd_series"),
        {
            "id": "t1",
            "type": "chart",
            "dataSourceId": "s1",
            "chartProjection": {"series": [{"field": "value"}]},
        },
        _data_source("s2", RANKING_OP),
        {
            "id": "t2",
            "type": "table",
            "dataSourceId": "s2",
            "tableProjection": {"columns": [{"field": "value"}]},
        },
    )
    migrated, applied = _migrate(doc)
    assert applied == []
    assert migrated is doc


def test_selected_value_fields_list_element_migrates_per_operation() -> None:
    doc = _slide(
        _data_source("s1", AUDIT_OP),
        {
            "id": "k1",
            "type": "kpi",
            "dataSourceId": "s1",
            "kpiProjection": {"selectedValueFields": ["average_score", "value"]},
        },
    )
    migrated, applied = _migrate(doc)
    assert len(applied) == 1
    assert migrated["blocks"][1]["kpiProjection"]["selectedValueFields"] == [
        "average_score",
        "average_score",
    ]


def test_rerun_is_idempotent() -> None:
    doc = _slide(_data_source("s1", STREAK_OP), _text("t1", "s1"))
    migrated, applied = _migrate(doc)
    assert len(applied) == 1
    again, applied2 = _migrate(migrated)
    assert applied2 == []
    assert again == migrated


def test_map_is_exact_operation_match_not_prefix() -> None:
    assert parity_alias_canonical_field("get_nonconformity_streak") == "current_days_without_nc"
    assert parity_alias_canonical_field("get_nonconformity_streak_v2") is None
    assert parity_alias_canonical_field("get_nonconformity_streak_extra") is None
    assert parity_alias_canonical_field(META_OP) is None
    assert parity_alias_canonical_field(REALIZED_OP) is None


def test_map_covers_exactly_the_wave3_targets() -> None:
    assert PARITY_ALIAS_FIELD_MAP == {
        "get_nonconformity_streak": "current_days_without_nc",
        "get_audit_5s_summary": "average_score",
        "get_quality_scrap_cost_pct": "scrap_cost_pct",
        "get_quality_rework_cost_pct": "rework_cost_pct",
    }
