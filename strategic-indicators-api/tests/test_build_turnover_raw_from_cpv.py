from si_app.application.services.supplies.supplies_metrics_helpers import (
    build_turnover_raw_from_cpv,
)


def test_build_turnover_raw_from_cpv_uses_cpv_summary() -> None:
    result = build_turnover_raw_from_cpv(
        cpv_raw={
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
            "summary": {
                "cpv_total": 1234.5,
                "total_movements": 10,
                "total_quantity": 20,
            },
        },
        start_date="2026-05-01",
        end_date="2026-05-31",
    )

    assert result["cpv_context"]["cpv_total"] == 1234.5
    assert result["cpv_context"]["total_movements"] == 10
    assert result["start_date"] == "2026-05-01"
