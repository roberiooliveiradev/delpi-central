from app.domain.services.caller_request_stats_service import (
    get_caller_stats_summary,
    record_caller_request,
    reset_caller_request_stats_for_tests,
)


def setup_function() -> None:
    reset_caller_request_stats_for_tests()


def test_caller_stats_aggregate_by_caller_and_route() -> None:
    record_caller_request(
        caller_app="api-delpi-console",
        route_path="/quality/ppm/internal/summary",
        operation_id="get_ppm_internal_summary",
        status_code=200,
        duration_ms=120.0,
    )
    record_caller_request(
        caller_app="api-delpi-console",
        route_path="/quality/ppm/external/summary",
        operation_id="get_ppm_external_summary",
        status_code=200,
        duration_ms=80.0,
    )
    record_caller_request(
        caller_app="dashboard-quality",
        route_path="/quality/branches",
        operation_id="list_quality_branches",
        status_code=500,
        duration_ms=12.0,
    )

    summary = get_caller_stats_summary(limit=10)

    assert summary["total_requests"] == 3
    assert summary["by_caller"][0]["caller_app"] == "api-delpi-console"
    assert summary["by_caller"][0]["count"] == 2
    assert summary["by_caller"][1]["errors"] == 1
    assert summary["by_route"]
