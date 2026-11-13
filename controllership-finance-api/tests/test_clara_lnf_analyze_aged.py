"""CLARA F7-R3 — review_aged_pending.value = contagem (≥5 dias)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from controllership_finance_app.interface.mcp import invoice_posting_bridge as bridge


def _list_result(items: list[dict], *, total: int | None = None) -> SimpleNamespace:
    payload = {
        "success": True,
        "message": "ok",
        "data": {
            "items": items,
            "total": total if total is not None else len(items),
            "page": 1,
        },
    }
    return SimpleNamespace(
        structured_content=payload,
        is_error=False,
    )


def _item(*, days_ago: int, status: str = "pending") -> dict:
    received = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {
        "id": f"00000000-0000-4000-8000-{days_ago:012d}",
        "branch_code": "01",
        "status": status,
        "received_at": received.isoformat(),
    }


def test_review_aged_pending_value_is_count(monkeypatch):
    monkeypatch.setattr(bridge, "_user_and_access", lambda: None)

    def fake_call(fn, **kwargs):
        status = kwargs.get("status")
        if status == "pending":
            return _list_result(
                [
                    _item(days_ago=7),
                    _item(days_ago=6),
                    _item(days_ago=2),
                ],
                total=3,
            )
        return _list_result([], total=0)

    monkeypatch.setattr(bridge, "_call_lnf_route", fake_call)
    result = bridge.tool_analyze_invoice_posting_backlog(branch="01")
    assert result.is_error is False
    data = (result.structured_content or {}).get("data") or {}
    findings = data.get("findings") or []
    aged = next(f for f in findings if f.get("code") == "review_aged_pending")
    assert aged["kind"] == "RECOMMENDATION"
    assert aged["value"] == 2
    assert "2 solicitações" in aged["message"]
    assert aged["value"] != 7  # não é a idade máxima


def test_review_aged_pending_omitted_when_none_ge_5(monkeypatch):
    monkeypatch.setattr(bridge, "_user_and_access", lambda: None)

    def fake_call(fn, **kwargs):
        status = kwargs.get("status")
        if status == "pending":
            return _list_result([_item(days_ago=1), _item(days_ago=4)], total=2)
        return _list_result([], total=0)

    monkeypatch.setattr(bridge, "_call_lnf_route", fake_call)
    result = bridge.tool_analyze_invoice_posting_backlog(branch="01")
    findings = ((result.structured_content or {}).get("data") or {}).get(
        "findings"
    ) or []
    assert all(f.get("code") != "review_aged_pending" for f in findings)


def test_age_days_helper():
    today = date(2026, 11, 13)
    assert bridge._age_days("2026-11-06T12:00:00Z", today=today) == 7
    assert bridge._age_days(None, today=today) is None
