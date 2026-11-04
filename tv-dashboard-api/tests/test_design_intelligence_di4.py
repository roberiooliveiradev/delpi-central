"""DI-4 — Q1–Q10 quality rubric over design_audit (golden fixtures)."""
from __future__ import annotations

from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService as D,
)


def _audit(cfg):
    return D.design_audit(cfg)


def test_rubric_present_in_audit():
    a = _audit({"blocks": [{"type": "data_kpi"}]})
    assert "rubric" in a
    assert set(a["rubric"]["criteria"]) == {
        f"Q{i}_{suffix}"
        for i, suffix in enumerate(
            [
                "OBJECTIVE", "INDICATORS", "VISUAL_CHOICE", "HIERARCHY",
                "LEGIBILITY", "DENSITY", "COLOR_SEMANTICS",
                "DATA_INTEGRITY", "TV_FITNESS", "PARITY",
            ],
            start=1,
        )
    }


def test_good_fixture_passes_q1_q2():
    a = _audit({
        "title": "Produção",
        "blocks": [{"type": "heading"}, {"type": "data_kpi"},
                   {"type": "data_chart"}],
    })
    r = a["rubric"]["criteria"]
    assert r["Q1_OBJECTIVE"]["status"] == "PASS"
    assert r["Q2_INDICATORS"]["status"] == "PASS"
    assert r["Q10_PARITY"]["status"] == "NOT_EVALUABLE"
    assert r["Q8_DATA_INTEGRITY"]["status"] == "NOT_EVALUABLE"


def test_kpi_view_counts_as_data_visual_issue_129():
    """VISTA-TV-READABILITY-001 — data bound blocks in the current
    vocabulary (kpi_view/chart_view/table_view) must satisfy Q1/Q2;
    the rubric previously only counted legacy data_* types."""
    a = _audit({
        "title": "OEE",
        "blocks": [{"type": "kpi_view", "dataSourceId": "ds1"},
                   {"type": "data_source", "id": "ds1"}],
    })
    r = a["rubric"]["criteria"]
    assert r["Q1_OBJECTIVE"]["status"] == "PASS"
    assert r["Q2_INDICATORS"]["status"] == "PASS"


def test_legibility_pass_declares_min_scope_limitation():
    """Q5 PASS certifies token minimums only — perceived readability
    at distance requires visual evidence; the rubric must say so."""
    a = _audit({"blocks": [{"type": "kpi_view"}]})
    q5 = a["rubric"]["criteria"]["Q5_LEGIBILITY"]
    assert q5["status"] == "PASS"
    assert "percebida" in q5["limitation"].lower()


def test_no_data_blocks_fails_q1():
    a = _audit({"blocks": [{"type": "text"}]})
    assert a["rubric"]["criteria"]["Q1_OBJECTIVE"]["status"] == "FAIL"


def test_overlap_fails_density_and_tv():
    a = D.quality_rubric(
        {"blocks": [{"type": "data_chart"}]},
        issue_codes=["block_overlap:b1~b2"],
    )
    assert a["criteria"]["Q6_DENSITY"]["status"] == "FAIL"
    assert a["criteria"]["Q9_TV_FITNESS"]["status"] == "FAIL"


def test_contrast_fails_legibility_and_color():
    a = D.quality_rubric(
        {"blocks": [{"type": "data_kpi"}]},
        issue_codes=["low_contrast:b1"],
    )
    assert a["criteria"]["Q5_LEGIBILITY"]["status"] == "FAIL"
    assert a["criteria"]["Q7_COLOR_SEMANTICS"]["status"] == "FAIL"


def test_font_min_fails_legibility():
    a = D.quality_rubric(
        {"blocks": [{"type": "data_kpi"}]},
        issue_codes=["part_font_below_min:b1"],
    )
    assert a["criteria"]["Q5_LEGIBILITY"]["status"] == "FAIL"


def test_hierarchy_inverted_fails_q4():
    a = D.quality_rubric(
        {"blocks": [{"type": "data_kpi"}]},
        issue_codes=["hierarchy_inverted:b1"],
    )
    assert a["criteria"]["Q4_HIERARCHY"]["status"] == "FAIL"


def test_empty_config_not_evaluable():
    a = _audit({})
    r = a["rubric"]["criteria"]
    assert r["Q1_OBJECTIVE"]["status"] == "NOT_EVALUABLE"
    assert r["Q5_LEGIBILITY"]["status"] == "NOT_EVALUABLE"


def test_summary_counts():
    a = D.quality_rubric(
        {"title": "T", "blocks": [{"type": "heading"},
                                  {"type": "data_kpi"}]},
        issue_codes=["low_contrast:b1"],
    )
    s = a["summary"]
    assert s["failed"] >= 1
    assert s["evaluated"] == 10 - s["notEvaluable"]
