"""Build a fresh IDF report from the exact inspection and receipt evidence.

Reuses the canonical IDF arithmetic. Never joins unrelated inspection/receipt
events by document number; they appear in separate workbook tabs.
"""
from collections import defaultdict
from datetime import datetime
import re
from zoneinfo import ZoneInfo

from app.application.use_cases.supplies.get_supplier_performance_use_case import (
    validate_supplier_performance_filters,
)
from app.domain.services.supplies.supplier_performance import compose_supplier_performance


def _quality_state(row):
    approved, rejected = int(row.get("approved") or 0), int(row.get("rejected") or 0)
    if approved == 1 and rejected == 0:
        return "Aprovada"
    if approved == 0 and rejected == 1:
        return "Rejeitada"
    return "A revisar"


def _delivery_state(row):
    diff = row.get("days_diff")
    if diff is None or diff == "":
        return "Sem data válida"
    return "No prazo/antecipada" if float(diff) >= 0 else "Atrasada"


def _compose_export_counts(inspections, deliveries):
    aggregates = {}
    def add(source, row, *, assessed, positive, unknown, conditional=0, urgent=0):
        key = (
            source, str(row.get("branch") or "").strip(),
            str(row.get("supplier_code") or "").strip(),
            str(row.get("supplier_store") or "").strip(),
        )
        if not key[1] or not key[2] or not key[3]:
            raise ValueError("A origem retornou um registro sem filial, fornecedor ou loja.")
        item = aggregates.setdefault(key, defaultdict(int))
        for field, amount in {
            "assessed_count": assessed, "positive_count": positive,
            "unknown_count": unknown, "conditional_count": conditional,
            "urgent_count": urgent,
        }.items():
            item[field] += amount
        item["supplier_name"] = str(row.get("supplier_name") or key[2]).strip()
    for row in inspections:
        state = _quality_state(row)
        row["evidence_state"] = state
        add(
            "quality", row,
            assessed=int(state != "A revisar"), positive=int(state == "Aprovada"),
            unknown=int(state == "A revisar"),
            conditional=int(row.get("conditional") or 0),
            urgent=int(row.get("urgent") or 0),
        )
    for row in deliveries:
        state = _delivery_state(row)
        row["evidence_state"] = state
        add(
            "delivery", row, assessed=1,
            positive=int(state == "No prazo/antecipada"),
            unknown=int(state == "Sem data válida"),
        )
    return [
        {
            "source": source, "branch": branch, "supplier_code": code,
            "supplier_store": store, **counts,
        }
        for (source, branch, code, store), counts in aggregates.items()
    ]


class GetSupplierPerformanceExportUseCase:
    def __init__(self, repository):
        self._repository = repository

    def execute(self, *, branches, date_from, date_to, supplier_code=None, supplier_store=None):
        branches, start, end = validate_supplier_performance_filters(
            branches, date_from, date_to
        )
        if (supplier_code is None) != (supplier_store is None):
            raise ValueError("Informe código e loja juntos para filtrar o fornecedor.")
        if supplier_code is not None and (
            not re.fullmatch(r"[0-9A-Za-z]{1,12}", supplier_code)
            or not re.fullmatch(r"[0-9A-Za-z]{1,4}", supplier_store)
        ):
            raise ValueError("Código e loja do fornecedor inválidos.")
        inspections, deliveries = self._repository.read_evidence(
            branches=branches, date_from=start.isoformat(), date_to=end.isoformat(),
            supplier_code=supplier_code, supplier_store=supplier_store,
        )
        result = compose_supplier_performance(
            _compose_export_counts(inspections, deliveries)
        )
        result.update({
            "inspections": inspections,
            "deliveries": deliveries,
            "period": {"from": start.isoformat(), "to": end.isoformat()},
            "branches": branches,
            "supplier_selected": (
                {"code": supplier_code, "store": supplier_store}
                if supplier_code is not None else None
            ),
            "calculated_at": datetime.now(
                ZoneInfo("America/Sao_Paulo")
            ).isoformat(),
        })
        return result
