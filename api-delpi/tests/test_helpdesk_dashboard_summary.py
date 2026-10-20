"""Testes do GET /helpdesk/dashboard/summary (API DELPI → helpdesk-api BFF → GLPI)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
import pytest

from app.application.use_cases.helpdesk.get_helpdesk_dashboard_summary_use_case import (
    GetHelpdeskDashboardSummaryUseCase,
)
from app.infrastructure.gateways.helpdesk_bff_gateway import (
    HelpdeskBffGateway,
    HelpdeskBffGatewayError,
)

_NOW = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)


class FakeGateway:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self._pages = pages
        self.calls: list[dict[str, Any]] = []

    def list_tickets(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        page = kwargs["page"] - 1
        if page >= len(self._pages):
            return {"items": [], "pagination": {}}
        return self._pages[page]


class RaisingGateway:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def list_tickets(self, **kwargs: Any) -> dict[str, Any]:
        raise self._error


def _page(items: list[dict[str, Any]], *, page: int, page_size: int, total: int) -> dict:
    return {
        "items": items,
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }


def _ticket(status_id: int, **extra: Any) -> dict[str, Any]:
    return {"id": hash((status_id, tuple(sorted(extra)))) % 100000, "status_id": status_id, **extra}


def _use_case(gateway: Any) -> GetHelpdeskDashboardSummaryUseCase:
    return GetHelpdeskDashboardSummaryUseCase(gateway=gateway, now_provider=lambda: _NOW)


def _execute(gateway: Any, **overrides: Any) -> dict[str, Any]:
    params: dict[str, Any] = {
        "authorization": "Bearer test",
        "start_date": None,
        "end_date": None,
        "assignee_id": None,
        "category_id": None,
        "urgency_id": None,
        "scope": None,
    }
    params.update(overrides)
    return _use_case(gateway).execute(**params)


class TestStatusClassification:
    def test_each_status_maps_to_the_right_kpi(self) -> None:
        items = [
            _ticket(1),                    # open
            _ticket(2), _ticket(3),        # in_progress
            _ticket(4), _ticket(10),       # pending
            _ticket(5, solved_at="2026-01-15T10:00:00Z"),  # resolved
            _ticket(6, closed_at="2026-01-20T10:00:00Z"),  # closed: excluded everywhere
        ]
        result = _execute(FakeGateway([_page(items, page=1, page_size=50, total=7)]))
        data = result["data"]
        assert data["open"] == 1
        assert data["in_progress"] == 2
        assert data["pending"] == 2
        assert data["resolved"] == 1

    def test_closed_ticket_is_not_counted_as_resolved(self) -> None:
        items = [_ticket(6, closed_at=_NOW.isoformat(), solved_at=_NOW.isoformat())]
        result = _execute(FakeGateway([_page(items, page=1, page_size=50, total=1)]))
        assert result["data"]["resolved"] == 0


class TestResolvedPeriodWindow:
    def test_resolved_filtered_by_solved_at_within_range(self) -> None:
        items = [
            _ticket(5, solved_at="2026-03-05T08:00:00Z"),
            _ticket(5, solved_at="2026-01-01T08:00:00Z"),   # fora da janela
        ]
        result = _execute(
            FakeGateway([_page(items, page=1, page_size=50, total=2)]),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        assert result["data"]["resolved"] == 1

    def test_solved_without_solved_at_is_excluded_when_range_given(self) -> None:
        items = [_ticket(5)]
        result = _execute(
            FakeGateway([_page(items, page=1, page_size=50, total=1)]),
            start_date=date(2026, 3, 1),
        )
        assert result["data"]["resolved"] == 0

    def test_without_range_every_solved_counts(self) -> None:
        items = [_ticket(5), _ticket(5, solved_at="2020-01-01T00:00:00Z")]
        result = _execute(FakeGateway([_page(items, page=1, page_size=50, total=2)]))
        assert result["data"]["resolved"] == 2


class TestOverdue:
    def test_unfinished_ticket_with_elapsed_sla_counts_as_overdue(self) -> None:
        past = (_NOW - timedelta(hours=2)).isoformat()
        items = [_ticket(1, sla_tto=past)]
        result = _execute(FakeGateway([_page(items, page=1, page_size=50, total=1)]))
        assert result["data"]["overdue"] == 1

    def test_pending_without_deadline_is_never_overdue(self) -> None:
        items = [_ticket(4)]
        result = _execute(FakeGateway([_page(items, page=1, page_size=50, total=1)]))
        assert result["data"]["pending"] == 1
        assert result["data"]["overdue"] == 0
        assert result["data"]["pending_overdue"] == 1

    def test_solved_and_closed_never_overdue(self) -> None:
        past = (_NOW - timedelta(days=5)).isoformat()
        items = [
            _ticket(5, sla_ttr=past, solved_at="2026-03-01T00:00:00Z"),
            _ticket(6, sla_ttr=past),
        ]
        result = _execute(FakeGateway([_page(items, page=1, page_size=50, total=2)]))
        assert result["data"]["overdue"] == 0

    def test_future_deadline_not_overdue(self) -> None:
        future = (_NOW + timedelta(hours=8)).isoformat()
        items = [_ticket(2, sla_tto=future)]
        result = _execute(FakeGateway([_page(items, page=1, page_size=50, total=1)]))
        assert result["data"]["overdue"] == 0

    def test_pending_overdue_is_union_without_double_counting(self) -> None:
        past = (_NOW - timedelta(hours=1)).isoformat()
        items = [
            _ticket(4, sla_tto=past),   # pending AND overdue -> counts once
            _ticket(4),                 # pending only
            _ticket(1, sla_ttr=past),   # overdue only
            _ticket(2),                 # neither
        ]
        result = _execute(FakeGateway([_page(items, page=1, page_size=50, total=4)]))
        data = result["data"]
        assert data["pending"] == 2
        assert data["overdue"] == 2
        assert data["pending_overdue"] == 3  # 2+2-1 overlap


class TestTotalCreatedInPeriod:
    def test_counts_distinct_tickets_created_in_range_once(self) -> None:
        items = [
            _ticket(1, id=10, created_at="2026-03-05T09:00:00Z"),
            _ticket(5, id=11, created_at="2026-03-06T09:00:00Z",
                    solved_at="2026-03-07T09:00:00Z"),
            _ticket(6, id=12, created_at="2026-03-08T09:00:00Z"),  # closed counts too
            _ticket(1, id=10, created_at="2026-03-05T09:00:00Z"),  # dup id: once
        ]
        result = _execute(
            FakeGateway([_page(items, page=1, page_size=50, total=4)]),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        assert result["data"]["total_created_in_period"] == 3

    def test_boundaries_inclusive_and_outside_excluded(self) -> None:
        items = [
            _ticket(1, id=1, created_at="2026-03-01T00:00:00Z"),   # first day edge
            _ticket(1, id=2, created_at="2026-03-31T23:59:59Z"),   # last day edge
            _ticket(1, id=3, created_at="2026-02-28T23:59:59Z"),   # before
            _ticket(1, id=4, created_at="2026-04-01T00:00:00Z"),   # after
        ]
        result = _execute(
            FakeGateway([_page(items, page=1, page_size=50, total=4)]),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        assert result["data"]["total_created_in_period"] == 2

    def test_all_statuses_are_eligible(self) -> None:
        created = "2026-03-10T08:00:00Z"
        items = [
            _ticket(s, id=100 + s, created_at=created)
            for s in (1, 2, 3, 4, 5, 6, 10)
        ]
        result = _execute(
            FakeGateway([_page(items, page=1, page_size=50, total=7)]),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        assert result["data"]["total_created_in_period"] == 7

    def test_empty_result_returns_zero(self) -> None:
        result = _execute(
            FakeGateway([_page([], page=1, page_size=50, total=0)]),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        assert result["data"]["total_created_in_period"] == 0

    def test_not_derived_from_status_groupings(self) -> None:
        # Um chamado closed criado no período não aparece em nenhum KPI de
        # status, mas deve entrar no total — prova de que não é soma de grupos.
        items = [_ticket(6, id=7, created_at="2026-03-05T09:00:00Z")]
        result = _execute(
            FakeGateway([_page(items, page=1, page_size=50, total=1)]),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        data = result["data"]
        assert data["total_created_in_period"] == 1
        assert data["open"] + data["in_progress"] + data["resolved"] + data["pending"] == 0

    def test_missing_created_at_excluded_only_when_range_given(self) -> None:
        items = [_ticket(1, id=1), _ticket(1, id=2, created_at="2026-03-05T00:00:00Z")]
        ranged = _execute(
            FakeGateway([_page(items, page=1, page_size=50, total=2)]),
            start_date=date(2026, 3, 1),
        )
        assert ranged["data"]["total_created_in_period"] == 1
        unranged = _execute(FakeGateway([_page(items, page=1, page_size=50, total=2)]))
        assert unranged["data"]["total_created_in_period"] == 2

    def test_existing_kpis_unchanged_by_new_field(self) -> None:
        past = (_NOW - timedelta(hours=2)).isoformat()
        items = [
            _ticket(1, id=1, created_at="2026-03-05T00:00:00Z", sla_tto=past),
            _ticket(5, id=2, created_at="2025-12-01T00:00:00Z",
                    solved_at="2026-03-05T00:00:00Z"),
        ]
        result = _execute(
            FakeGateway([_page(items, page=1, page_size=50, total=2)]),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        data = result["data"]
        assert data["open"] == 1
        assert data["resolved"] == 1
        assert data["overdue"] == 1
        assert data["total_created_in_period"] == 1


class TestPaginationAndPartial:
    def test_aggregates_across_multiple_pages(self) -> None:
        page1 = _page([_ticket(1)] * 50, page=1, page_size=50, total=75)
        page2 = _page([_ticket(2)] * 25, page=2, page_size=50, total=75)
        result = _execute(FakeGateway([page1, page2]))
        assert result["data"]["open"] == 50
        assert result["data"]["in_progress"] == 25
        assert result["meta"]["partial"] is False
        assert result["meta"]["tickets_evaluated"] == 75

    def test_partial_flag_when_page_cap_reached(self) -> None:
        pages = [
            _page([_ticket(1)] * 50, page=p, page_size=50, total=99999)
            for p in range(1, 201)
        ]
        gateway = FakeGateway(pages)
        result = _execute(gateway)
        assert result["meta"]["partial"] is True
        assert result["data"]["open"] == 200 * 50


class TestFiltersForwarding:
    def test_filters_are_forwarded_to_bff(self) -> None:
        gateway = FakeGateway([_page([], page=1, page_size=50, total=0)])
        _execute(gateway, assignee_id=42, category_id=7, urgency_id=3)
        call = gateway.calls[0]
        assert call["assignee_id"] == 42
        assert call["category_id"] == 7
        assert call["urgency_id"] == 3
        assert call["authorization"] == "Bearer test"


class TestFailureSemantics:
    def test_upstream_error_propagates_without_fake_zeros(self) -> None:
        error = HelpdeskBffGatewayError("Helpdesk indisponível.", 503)
        with pytest.raises(HelpdeskBffGatewayError) as exc_info:
            _execute(RaisingGateway(error))
        assert exc_info.value.status_code == 503

    def test_meta_contract_fields(self) -> None:
        result = _execute(
            FakeGateway([_page([], page=1, page_size=50, total=0)]),
            start_date=date(2026, 3, 1),
        )
        meta = result["meta"]
        assert meta["source"] == "glpi"
        assert meta["partial"] is False
        assert meta["scope"] == "authorized"
        assert meta["filters"]["start_date"] == "2026-03-01"
        assert "calculated_at" in meta
        assert set(meta["status_mapping"]) == {
            "open", "in_progress", "pending", "resolved", "overdue", "pending_overdue"
        }


class TestGatewayHttp:
    def _gateway(self, handler: Any) -> HelpdeskBffGateway:
        transport = httpx.MockTransport(handler)
        client = httpx.Client(transport=transport, base_url="http://bff.test")
        return HelpdeskBffGateway(client=client, base_url="http://bff.test", sleep=lambda _: None)

    def test_bff_raw_page_envelope_is_accepted(self) -> None:
        """Regressão do 502 em produção: o BFF retorna a página crua
        {items, page, page_size, has_more} — sem wrapper success/data."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "items": [{"id": 1, "status_id": 1}],
                    "page": 1,
                    "page_size": 50,
                    "has_more": False,
                },
            )

        data = self._gateway(handler).list_tickets(
            authorization="Bearer abc", page=1, page_size=50
        )
        assert data["items"] == [{"id": 1, "status_id": 1}]
        assert data["has_more"] is False

    def test_200_without_items_is_invalid_format(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": True})

        with pytest.raises(HelpdeskBffGatewayError) as exc_info:
            self._gateway(handler).list_tickets(
                authorization="Bearer x", page=1, page_size=50
            )
        assert exc_info.value.status_code == 502

    def test_bff_error_code_string_is_surfaced(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(409, json={"error": "glpi_link_required"})

        with pytest.raises(HelpdeskBffGatewayError) as exc_info:
            self._gateway(handler).list_tickets(
                authorization="Bearer x", page=1, page_size=50
            )
        assert "glpi_link_required" in str(exc_info.value)

    def test_bearer_forwarded_and_params_sent(self) -> None:
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["auth"] = request.headers.get("authorization")
            seen["params"] = dict(request.url.params)
            return httpx.Response(
                200,
                json={"success": True, "data": {"items": [], "pagination": {}}},
            )

        gateway = self._gateway(handler)
        gateway.list_tickets(
            authorization="Bearer abc", page=2, page_size=50, assignee_id=9
        )
        assert seen["auth"] == "Bearer abc"
        assert seen["params"]["page"] == "2"
        assert seen["params"]["assignee_id"] == "9"

    def test_401_mapped_to_401(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"success": False, "message": "não autenticado"})

        with pytest.raises(HelpdeskBffGatewayError) as exc_info:
            self._gateway(handler).list_tickets(
                authorization="Bearer x", page=1, page_size=50
            )
        assert exc_info.value.status_code == 401

    def test_500_mapped_to_502(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"success": False})

        with pytest.raises(HelpdeskBffGatewayError) as exc_info:
            self._gateway(handler).list_tickets(
                authorization="Bearer x", page=1, page_size=50
            )
        assert exc_info.value.status_code == 502

    def test_connection_error_becomes_503(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with pytest.raises(HelpdeskBffGatewayError) as exc_info:
            self._gateway(handler).list_tickets(
                authorization="Bearer x", page=1, page_size=50
            )
        assert exc_info.value.status_code == 503


class TestRouteRegistration:
    def test_route_registered_with_operation_id(self) -> None:
        from app.interface.http.routes.helpdesk.helpdesk_router import router

        matches = [
            r for r in router.routes
            if getattr(r, "path", None) == "/helpdesk/dashboard/summary"
        ]
        assert matches, "summary route missing"
        route = matches[0]
        assert "GET" in route.methods
        assert route.operation_id == "get_helpdesk_dashboard_summary"
        param_names = {p.name for p in route.dependant.query_params}
        assert {"start_date", "end_date", "assignee_id", "category_id", "urgency_id", "scope"} <= param_names
