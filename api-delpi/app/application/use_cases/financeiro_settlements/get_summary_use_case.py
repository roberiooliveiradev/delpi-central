"""Grouped settlement summary — side × currency × nature × movement.

Never merges currencies, never emits an official consolidated total while
movement semantics remain unclassified (doc 48 D4).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.dto.financeiro_settlements.settlements_request import (
    SettlementsQueryRequest,
)
from app.application.dto.financeiro_settlements.settlements_response import (
    SettlementQuality,
    SettlementSummaryGroup,
    SettlementsSummaryResponse,
)
from app.application.security.settlement_scope import (
    SettlementScopeResolver,
    require_settlement_scope,
)
from app.domain.ports.financeiro_settlements.settlements_repository_port import (
    SettlementsRepositoryPort,
)

from .normalize import as_int

REPORT_SUMMARY = "financial-settlements-summary"


def _decimal_str(value: Any) -> str:
    if value is None or value == "":
        return "0.00"
    try:
        return str(Decimal(str(value)).quantize(Decimal("0.01")))
    except (InvalidOperation, ValueError):
        return "0.00"


def _opt(value: Any) -> str | None:
    text = "" if value is None else str(value).strip()
    return text or None


class GetSettlementsSummaryUseCase:
    def __init__(
        self,
        repository: SettlementsRepositoryPort,
        scope_resolver: SettlementScopeResolver,
    ) -> None:
        self._repository = repository
        self._scope_resolver = scope_resolver

    def execute(
        self,
        request: SettlementsQueryRequest,
        *,
        user_subject: str | None,
    ) -> SettlementsSummaryResponse:
        require_settlement_scope(self._scope_resolver, user_subject=user_subject)

        start, end = request.resolve_protheus_period()
        rows = self._repository.summary_groups(
            start_date=start,
            end_date=end,
            nature_code=request.nature_code,
            movement_type=request.movement_type,
        )

        nature_codes = tuple(
            sorted(
                {
                    str(row["nature_code"]).strip()
                    for row in rows
                    if row.get("nature_code")
                }
            )
        )
        lookup = (
            self._repository.nature_descriptions(nature_codes=nature_codes)
            if nature_codes
            else {}
        )
        groups = [
            SettlementSummaryGroup(
                side=str(row["side"]),
                currencyCode=_opt(row.get("currency_code")),
                natureCode=_opt(row.get("nature_code")),
                natureDescription=lookup.get(
                    str(row.get("nature_code") or "").strip()
                )
                or None,
                movementType=_opt(row.get("movement_type")),
                eventCount=as_int(row.get("event_count")),
                totalAmount=_decimal_str(row.get("total_amount")),
            )
            for row in rows
        ]
        return SettlementsSummaryResponse(
            report=REPORT_SUMMARY,
            period={"start_date": request.start_date, "end_date": request.end_date},
            status="complete" if groups else "partial",
            quality=SettlementQuality(),
            groups=groups,
        )
