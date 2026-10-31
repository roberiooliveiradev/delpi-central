"""Read the R12/R15 closing-state markers (doc 129 §2.1).

Returns RAW markers only: snapshot presence, the SX6 ``MV_ULMES``
per-branch value and TTAT write windows for ``B1_CUSTD``/``D3_CUSTO1``.
The governed node projection (snapshot/cutoff/evidence/wizard/acceptance)
is composed by the controllership BFF — this producer never infers
closing, execution or acceptance.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.application.dto.financeiro_closing_state.closing_state_request import (
    ClosingStateRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
    require_stock_inventory_scope,
)
from app.domain.ports.financeiro_closing_state.closing_state_repository_port import (
    ClosingStateRepositoryPort,
)

REPORT_CLOSING_STATE = "cost-closing-state"

# TTAT-audited fields that mark the proven routines' effects:
# MATA320 -> SB1.B1_CUSTD (BR-R12-001); MATA330 -> SD3.D3_CUSTO1 rewrite
# (BR-R15-002).
_TTAT_EVIDENCE: tuple[tuple[str, str, str], ...] = (
    ("replacementCostWrites", "SB1010_TTAT_LOG", "B1_CUSTD"),
    ("movementCostWrites", "SD3010_TTAT_LOG", "D3_CUSTO1"),
)


class GetClosingStateUseCase:
    def __init__(
        self,
        repository: ClosingStateRepositoryPort,
        scope_resolver: StockInventoryScopeResolver,
    ) -> None:
        self._repository = repository
        self._scope_resolver = scope_resolver

    def execute(
        self,
        request: ClosingStateRequest,
        *,
        user_subject: str | None,
    ) -> dict:
        require_stock_inventory_scope(
            self._scope_resolver, user_subject=user_subject
        )

        snapshot_date = request.snapshot_date()
        branches = request.requested_branches()
        window_start, window_end = request.evidence_window()

        counts = self._repository.snapshot_branch_counts(
            snapshot_date=snapshot_date, branches=branches
        )
        last_dates = self._repository.last_snapshot_dates(
            branches=branches
        )
        ulmes = self._repository.mv_ulmes_values(branches=branches)

        evidence: dict[str, dict] = {}
        for key, log_table, field_name in _TTAT_EVIDENCE:
            row = self._repository.ttat_write_window(
                log_table=log_table,
                field_name=field_name,
                window_start=window_start,
                window_end=window_end,
            )
            evidence[key] = {
                "writeCount": int(row.get("write_count") or 0),
                "firstAt": row.get("first_at"),
                "lastAt": row.get("last_at"),
                "source": f"{log_table}.{field_name}",
            }

        out_branches: dict[str, dict] = {}
        for code in branches:
            last_date = last_dates.get(code) or None
            out_branches[code] = {
                "cutoffMarker": {
                    "value": ulmes.get(code) or None,
                    "source": "SX6010.MV_ULMES",
                },
                "snapshot": {
                    "available": counts.get(code, 0) > 0,
                    "rowCount": counts.get(code) or None,
                    "date": request.snapshot_date_iso(),
                    "lastAvailableDate": (
                        f"{last_date[:4]}-{last_date[4:6]}-{last_date[6:8]}"
                        if last_date
                        else None
                    ),
                },
                "evidence": evidence,
            }

        return {
            "report": REPORT_CLOSING_STATE,
            "period": request.period,
            "referenceDate": request.snapshot_date_iso(),
            "branchCode": request.branch,
            "observedAt": datetime.now(timezone.utc).isoformat(),
            "evidenceWindow": {"start": window_start, "end": window_end},
            "branches": out_branches,
            "provenance": {
                "engine": "protheus-closing-state-markers",
                "officialProducer": "erp_wizard_mata320_mata300_mata330_mata280",
                "writerPending": True,
                "timezoneNote": "I_N_S_D_T_/TTAT_DTIME physical stamps are UTC (-3h local).",
            },
        }
