from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from production_control_app.application.services.problem_analysis_service import (
    ProblemAnalysisService,
    map_delayed_order,
)
from production_control_app.domain.errors import BranchAccessDenied, InvalidBranch
from production_control_app.domain.services.branch_access_service import BranchAccessService


class FakeGateway:
    def __init__(self, items: list[dict[str, Any]], summary: dict[str, Any] | None = None) -> None:
        self.items = items
        self.summary = summary or {
            "summary": {"open_orders": 10, "delayed_orders": len(items)}
        }
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def fetch_pcp_orders_summary(self, *, branch: str) -> dict[str, Any]:
        self.calls.append(("summary", {"branch": branch}))
        return {"success": True, "data": self.summary}

    def fetch_pcp_orders_items(
        self,
        *,
        branch: str,
        delayed_only: bool,
        page_size: int,
    ) -> dict[str, Any]:
        self.calls.append(
            ("items", {"branch": branch, "delayed_only": delayed_only, "page_size": page_size})
        )
        return {"success": True, "data": {"items": self.items}}


def _user(*permissions: str, superadmin: bool = False):
    return SimpleNamespace(is_superadmin=superadmin, permissions=list(permissions))


FULL_PERMS = (
    "production-control.access",
    "production-control.problem-analysis.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def test_map_delayed_order_severity_from_days() -> None:
    critical = map_delayed_order(
        {
            "production_order": "000010",
            "op_key": "01|000010",
            "product_code": "90300005",
            "days_late": 8,
            "planned_qty": 10,
        },
        critical_days=7,
        title_template="OP {order} atrasada ({days} dias)",
    )
    assert critical["id"] == "delayed-order:01|000010"
    assert critical["severity"] == "critical"
    assert "000010" in critical["title"]

    attention = map_delayed_order(
        {"production_order": "2", "op_key": "01|2", "days_late": 2},
        critical_days=7,
        title_template="OP {order} atrasada ({days} dias)",
    )
    assert attention["severity"] == "attention"


def test_problem_analysis_composes_inbox_from_pcp_orders() -> None:
    gateway = FakeGateway(
        [
            {
                "production_order": "A",
                "op_key": "01|A",
                "product_code": "P1",
                "days_late": 12,
            },
            {
                "production_order": "B",
                "op_key": "01|B",
                "product_code": "P2",
                "days_late": 1,
            },
        ]
    )
    service = ProblemAnalysisService(gateway)
    result = service.build(_user(*FULL_PERMS), branch="01", issue_id="delayed-order:01|B")
    assert result["summary"]["critical"] == 1
    assert result["summary"]["attention"] == 1
    assert result["selected"]["id"] == "delayed-order:01|B"
    assert result["issues"][0]["id"] == "delayed-order:01|A"


def test_branch_gate_rejects_other_filial() -> None:
    service = BranchAccessService()
    user = _user(
        "production-control.access",
        "production-control.view.filial-01",
    )
    service.assert_can_view_branch(user, "01")
    with pytest.raises(BranchAccessDenied):
        service.assert_can_view_branch(user, "02")
    with pytest.raises(InvalidBranch):
        service.assert_can_view_branch(user, "99")
