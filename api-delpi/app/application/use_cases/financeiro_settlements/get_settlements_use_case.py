"""List settlement events for one side (payable=FK2 / receivable=FK1)."""

from __future__ import annotations

from app.application.dto.financeiro_settlements.constantes import (
    SETTLEMENT_SIDE_PAYABLE,
    SETTLEMENT_SIDE_RECEIVABLE,
)
from app.application.dto.financeiro_settlements.settlements_request import (
    SettlementsQueryRequest,
)
from app.application.dto.financeiro_settlements.settlements_response import (
    SettlementQuality,
    SettlementsListResponse,
)
from app.application.security.settlement_scope import (
    SettlementScopeResolver,
    require_settlement_scope,
)
from app.domain.ports.financeiro_settlements.settlements_repository_port import (
    SettlementsRepositoryPort,
)

from .normalize import as_int, build_pagination, normalize_settlement_item

REPORT_PAYABLES = "financial-settlements-payables"
REPORT_RECEIVABLES = "financial-settlements-receivables"


class GetSettlementsUseCase:
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
        side: str,
        user_subject: str | None,
    ) -> SettlementsListResponse:
        if side not in (SETTLEMENT_SIDE_PAYABLE, SETTLEMENT_SIDE_RECEIVABLE):
            raise ValueError(f"side inválido: {side!r}")
        # Fail-closed: real rows only when the dataset scope is proven
        # authorized (doc 48 D3.1). Unresolved scope raises
        # SettlementScopeUnavailableError -> typed 403 at the route layer.
        require_settlement_scope(self._scope_resolver, user_subject=user_subject)

        start, end = request.resolve_protheus_period()
        counters = self._repository.quality_counters(
            side=side,
            start_date=start,
            end_date=end,
            nature_code=request.nature_code,
            movement_type=request.movement_type,
        )
        total_items = as_int(counters.get("total_events"))
        rows = self._repository.list_settlements(
            side=side,
            start_date=start,
            end_date=end,
            nature_code=request.nature_code,
            movement_type=request.movement_type,
            sort_by=request.sort_by,
            sort_dir=request.sort_dir,
            page=request.page,
            page_size=request.page_size,
        )

        items = [normalize_settlement_item(row) for row in rows]
        movement_types = tuple(
            sorted({item.movementType for item in items if item.movementType})
        )
        movement_lookup = self._repository.movement_descriptions(
            movement_types=movement_types
        )
        for item in items:
            if item.movementType:
                item.movementDescription = (
                    movement_lookup.get(item.movementType) or None
                )
        missing_doc = as_int(counters.get("missing_document"))
        missing_nature = as_int(counters.get("missing_nature"))
        unresolved_branch = as_int(counters.get("unresolved_branch"))
        status = (
            "partial" if (missing_doc or missing_nature or unresolved_branch) else "complete"
        )
        return SettlementsListResponse(
            report=(
                REPORT_PAYABLES if side == SETTLEMENT_SIDE_PAYABLE else REPORT_RECEIVABLES
            ),
            side=side,
            period={"start_date": request.start_date, "end_date": request.end_date},
            status=status,
            quality=SettlementQuality(
                missingDocumentCount=missing_doc,
                missingNatureCount=missing_nature,
                unresolvedBranchCount=unresolved_branch,
            ),
            pagination=build_pagination(
                page=request.page,
                page_size=request.page_size,
                total_items=total_items,
            ),
            sort={"sort_by": request.sort_by, "sort_dir": request.sort_dir},
            items=items,
        )
