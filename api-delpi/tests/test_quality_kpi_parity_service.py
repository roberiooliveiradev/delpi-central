from __future__ import annotations

from app.application.services.quality.quality_kpi_parity_service import (
    attach_quality_kpi_parity,
)


def test_attach_quality_kpi_parity_adds_value_and_summary_without_clobbering():
    payload = {
        "branch": "01",
        "start_date": "2026-07-01",
        "end_date": "2026-07-31",
        "ppm": 42.5,
        "total_produzido_un": 1000.0,
        "total_produzido_milheiro": 1.0,
        "comparable_goal": 30.0,
        "has_goal": True,
    }
    next_payload = attach_quality_kpi_parity(
        payload,
        primary_field="ppm",
        branch="01",
        start_date="2026-07-01",
        end_date="2026-07-31",
        summary_extra_fields=(
            "ppm",
            "total_produzido_un",
            "total_produzido_milheiro",
        ),
    )
    assert next_payload["ppm"] == 42.5
    assert next_payload["value"] == 42.5
    assert next_payload["comparable_goal"] == 30.0
    summary = next_payload["summary"]
    assert summary["branch_filter_applied"] is True
    assert summary["consolidated_across_branches"] is False
    assert summary["is_complete"] is True
    assert summary["period"] == {"start": "2026-07-01", "end": "2026-07-31"}
    assert summary["ppm"] == 42.5
    assert summary["total_produzido_un"] == 1000.0


def test_attach_quality_kpi_parity_preserves_existing_value_and_summary_keys():
    payload = {
        "ppm": 10.0,
        "value": 99.0,
        "summary": {"is_complete": False, "custom": "keep"},
    }
    next_payload = attach_quality_kpi_parity(
        payload,
        primary_field="ppm",
        summary_extra_fields=("ppm",),
    )
    assert next_payload["value"] == 99.0
    assert next_payload["summary"]["is_complete"] is False
    assert next_payload["summary"]["custom"] == "keep"
    assert next_payload["summary"]["ppm"] == 10.0


def test_attach_quality_kpi_parity_nested_ideas_goal_value():
    payload = {
        "total_kaizens": 3,
        "total_savings": 1500.0,
        "ideas_goal": {
            "total_kaizens": 3,
            "comparable_goal": 8.0,
            "has_goal": True,
        },
    }
    next_payload = attach_quality_kpi_parity(
        payload,
        primary_field="total_savings",
        nested_blocks={"ideas_goal": "total_kaizens"},
        summary_extra_fields=("total_kaizens", "total_savings"),
    )
    assert next_payload["value"] == 1500.0
    assert next_payload["ideas_goal"]["value"] == 3
    assert next_payload["ideas_goal"]["comparable_goal"] == 8.0
