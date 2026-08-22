"""Structural readiness of a travel expense package (no policy limits)."""

from __future__ import annotations

from datetime import date
from typing import Any


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _as_amount(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class TravelReportCompletenessService:
    @classmethod
    def evaluate(cls, report: dict[str, Any], expenses: list[dict[str, Any]]) -> dict[str, Any]:
        issues: list[dict[str, str]] = []
        destination = str(report.get("destination") or "").strip()
        if not destination:
            issues.append({"code": "missing_destination", "message": "Informe o destino da viagem."})

        period_start = _as_date(report.get("periodStart") or report.get("period_start"))
        period_end = _as_date(report.get("periodEnd") or report.get("period_end"))
        if not period_start or not period_end:
            issues.append({"code": "missing_period", "message": "Informe o período da viagem."})
        elif period_end < period_start:
            issues.append({"code": "invalid_period", "message": "A data final não pode ser anterior à inicial."})

        if not expenses:
            issues.append({"code": "missing_expenses", "message": "Inclua ao menos uma despesa."})

        missing_receipt = 0
        missing_amount = 0
        date_outside = 0
        for expense in expenses:
            amount = _as_amount(expense.get("amountBrl") if "amountBrl" in expense else expense.get("amount_brl"))
            if amount is None or amount <= 0:
                missing_amount += 1
                issues.append(
                    {
                        "code": "missing_amount",
                        "message": "Há despesa sem valor.",
                        "expenseId": str(expense.get("id") or ""),
                    }
                )
            receipts = expense.get("receipts") or []
            if not receipts:
                missing_receipt += 1
                issues.append(
                    {
                        "code": "missing_receipt",
                        "message": "Há despesa sem cupom fiscal.",
                        "expenseId": str(expense.get("id") or ""),
                    }
                )
            expense_date = _as_date(expense.get("expenseDate") or expense.get("expense_date"))
            if period_start and period_end and expense_date and (
                expense_date < period_start or expense_date > period_end
            ):
                date_outside += 1
                issues.append(
                    {
                        "code": "date_outside_period",
                        "message": "Há despesa com data fora do período da viagem.",
                        "expenseId": str(expense.get("id") or ""),
                    }
                )

        ready = not issues
        return {
            "ready": ready,
            "expenseCount": len(expenses),
            "receiptCount": sum(len(item.get("receipts") or []) for item in expenses),
            "missingReceiptCount": missing_receipt,
            "missingAmountCount": missing_amount,
            "dateOutsidePeriodCount": date_outside,
            "issues": issues,
        }
