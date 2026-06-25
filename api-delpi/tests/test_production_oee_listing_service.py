from app.domain.production.production_oee_listing_service import (
    filter_production_appointment_rows,
    summarize_production_appointment_rows,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_sh6010_apply import (
    build_fabril_sh6010_scoped_left_join,
)


def test_summarize_production_appointment_rows_includes_branch_averages() -> None:
    rows = [
        {"status": "valid", "branch": "01", "oee_pct": 80.0},
        {"status": "valid", "branch": "01", "oee_pct": 60.0},
        {"status": "valid", "branch": "02", "oee_pct": 70.0},
        {"status": "outlier", "branch": "02", "oee_pct": 250.0},
    ]

    summary = summarize_production_appointment_rows(rows)

    assert summary["total_appointments"] == 4
    assert summary["valid_appointments"] == 3
    assert summary["outlier_appointments"] == 1
    assert summary["avg_oee_pct"] == 70.0
    assert summary["avg_oee_pct_by_branch"] == {"01": 70.0, "02": 70.0}


def test_filter_production_appointment_rows_honors_status() -> None:
    rows = [
        {"status": "valid", "oee_pct": 80.0},
        {"status": "outlier", "oee_pct": 250.0},
    ]

    filtered = filter_production_appointment_rows(rows, status="valid", efficiency_bands=None)

    assert len(filtered) == 1
    assert filtered[0]["status"] == "valid"


def test_scoped_sh6010_join_filters_by_period_and_branch() -> None:
    sql, params = build_fabril_sh6010_scoped_left_join(
        date_start_protheus="20260601",
        date_end_protheus="20260624",
        branch="01",
    )

    assert "H6.H6_DTPROD >= ?" in sql
    assert "ROW_NUMBER()" in sql
    assert "LEFT JOIN" in sql
    assert params == ("20260601", "20260624", "01")
