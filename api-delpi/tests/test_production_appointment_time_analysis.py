from app.domain.production.production_appointment_time_analysis import (
    build_appointment_time_analysis,
    build_appointment_time_findings,
)


def test_build_findings_flags_out_of_range_efficiency() -> None:
    findings = build_appointment_time_findings(
        {
            "status": "outlier",
            "oee_pct": 314.4,
            "efficiency_from_times_pct": 300.0,
            "planned_hours": 0.1,
            "real_hours": 0.03,
            "start_date": "20260529",
            "end_date": "20260529",
            "standard_time_factor": 0.02,
            "setup_hours": 0.08,
            "produced_qty": 0.08,
            "order_planned_qty": 0.08,
        }
    )

    codes = {item.code for item in findings}
    assert "oee_out_of_range" in codes
    assert "efficiency_times_out_of_range" in codes
    assert "very_short_real_interval" in codes


def test_build_findings_uses_h6_tempo_source() -> None:
    findings = build_appointment_time_findings(
        {
            "status": "valid",
            "oee_pct": 95.0,
            "efficiency_from_times_pct": 92.0,
            "planned_hours": 1.0,
            "real_hours": 1.1,
            "standard_time_factor": 0.5,
            "setup_hours": 0.1,
            "produced_qty": 10,
            "order_planned_qty": 100,
        },
        real_hours_source="h6_tempo",
    )

    codes = {item.code for item in findings}
    assert "real_hours_from_h6_tempo" in codes


def test_build_time_analysis_includes_findings_payload() -> None:
    payload = build_appointment_time_analysis(
        {
            "status": "outlier",
            "oee_pct": 250.0,
            "efficiency_from_times_pct": 240.0,
            "planned_hours": 0.0,
            "real_hours": 0.02,
            "start_date": "20260529",
            "end_date": "20260529",
            "standard_time_factor": 0,
            "setup_hours": 0,
            "produced_qty": 0,
            "order_planned_qty": 0,
        }
    )

    assert payload["real_hours_source"] == "interval"
    assert payload["has_findings"] is True
    assert len(payload["findings"]) >= 2
    assert payload["findings"][0]["severity"] in {"error", "warning", "info"}
