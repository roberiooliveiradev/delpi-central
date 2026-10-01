from __future__ import annotations

from unittest.mock import MagicMock

from starlette.requests import Request

from app.application.services.strategic_indicators.dashboard_goals_service import (
    DashboardGoalsService,
)
from app.infrastructure.observability.request_context import (
    bind_request_context,
    reset_request_context,
)


def _request(*, caller: str | None, token: str | None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if caller is not None:
        headers.append((b"x-delpi-caller-app", caller.encode()))
    if token is not None:
        headers.append((b"x-delpi-service-token", token.encode()))
    return Request({"type": "http", "headers": headers})


def _sample_goal() -> dict:
    return {
        "source_key": "supplies_otd",
        "goal_label": "≥ 95%",
        "goal_value": 95.0,
        "comparable_goal": 95.0,
        "reference_goal": 95.0,
        "has_goal": True,
    }


def _service() -> tuple[DashboardGoalsService, MagicMock]:
    client = MagicMock()
    client.list_dashboard_goals.return_value = {"items": [_sample_goal()]}
    return DashboardGoalsService(client=client), client


def test_internal_request_declaring_si_makes_zero_dashboard_goals_calls(
    monkeypatch,
) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    service, client = _service()
    request = _request(caller="strategic-indicators-api", token="svc-secret")
    tokens = bind_request_context(request)
    try:
        result = service.attach_goal_fields(
            {"otd_percentage": 88.0},
            source_key="supplies_otd",
            start_date="2026-10-01",
            end_date="2026-10-31",
        )
    finally:
        reset_request_context(tokens)

    assert client.list_dashboard_goals.call_count == 0
    assert result == {"otd_percentage": 88.0}


def test_attach_goals_index_skips_dashboard_goals_call_for_si_internal_request(
    monkeypatch,
) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    service, client = _service()
    request = _request(caller="strategic-indicators-api", token="svc-secret")
    tokens = bind_request_context(request)
    try:
        result = service.attach_goals_index(
            {"total_lmps": 10},
            field_source_keys={"otd": "supplies_otd"},
        )
    finally:
        reset_request_context(tokens)

    assert client.list_dashboard_goals.call_count == 0
    assert result["total_lmps"] == 10


def test_normal_request_still_enriches(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    service, client = _service()
    request = _request(caller=None, token=None)
    tokens = bind_request_context(request)
    try:
        result = service.attach_goal_fields(
            {"otd_percentage": 88.0},
            source_key="supplies_otd",
        )
    finally:
        reset_request_context(tokens)

    assert client.list_dashboard_goals.call_count == 1
    assert result["comparable_goal"] == 95.0
    assert result["has_goal"] is True


def test_caller_header_without_valid_service_token_still_enriches(
    monkeypatch,
) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    service, client = _service()
    request = _request(caller="strategic-indicators-api", token="forged")
    tokens = bind_request_context(request)
    try:
        result = service.attach_goal_fields(
            {"otd_percentage": 88.0},
            source_key="supplies_otd",
        )
    finally:
        reset_request_context(tokens)

    assert client.list_dashboard_goals.call_count == 1
    assert result["comparable_goal"] == 95.0


def test_shared_token_holder_claiming_si_caller_is_indistinguishable(
    monkeypatch,
) -> None:
    """CASE C residual: the internal token is shared platform-wide, so any
    internal service presenting it while declaring caller_app=
    strategic-indicators-api is indistinguishable from a genuine SI call.
    This documents the limitation — flip this assertion when per-service
    credentials land (PERF-001 follow-up).
    """
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    service, client = _service()
    # Same credential any internal service holds + forged caller header.
    request = _request(caller="strategic-indicators-api", token="svc-secret")
    tokens = bind_request_context(request)
    try:
        result = service.attach_goal_fields(
            {"otd_percentage": 88.0},
            source_key="supplies_otd",
        )
    finally:
        reset_request_context(tokens)

    assert client.list_dashboard_goals.call_count == 0
    assert result == {"otd_percentage": 88.0}


def test_other_authenticated_internal_caller_still_enriches(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    service, client = _service()
    request = _request(caller="tv-dashboard-api", token="svc-secret")
    tokens = bind_request_context(request)
    try:
        result = service.attach_goal_fields(
            {"otd_percentage": 88.0},
            source_key="supplies_otd",
        )
    finally:
        reset_request_context(tokens)

    assert client.list_dashboard_goals.call_count == 1
    assert result["comparable_goal"] == 95.0
