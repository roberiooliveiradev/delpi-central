from datetime import date

from travel_expenses_app.domain.services.completeness_service import (
    TravelReportCompletenessService,
)


def test_ready_when_header_and_receipts_ok():
    report = {
        "destination": "São Paulo",
        "periodStart": date(2026, 8, 10),
        "periodEnd": date(2026, 8, 12),
    }
    expenses = [
        {
            "id": "e1",
            "expenseDate": date(2026, 8, 11),
            "amountBrl": 48.0,
            "receipts": [{"id": "r1"}],
        }
    ]
    result = TravelReportCompletenessService.evaluate(report, expenses)
    assert result["ready"] is True
    assert result["missingReceiptCount"] == 0


def test_flags_missing_receipt_and_date_outside():
    report = {
        "destination": "Campinas",
        "period_start": "2026-08-10",
        "period_end": "2026-08-12",
    }
    expenses = [
        {"id": "e1", "expense_date": "2026-08-20", "amount_brl": 10, "receipts": []},
    ]
    result = TravelReportCompletenessService.evaluate(report, expenses)
    codes = {issue["code"] for issue in result["issues"]}
    assert "missing_receipt" in codes
    assert "date_outside_period" in codes
    assert result["ready"] is False
