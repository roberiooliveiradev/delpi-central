from datetime import date
from types import SimpleNamespace

import pytest

from travel_expenses_app.application.use_cases.travel_report_service import TravelReportError, TravelReportService
from travel_expenses_app.domain.services.transport_pricing import (
    ExpenseValueError, mileage_amount, parse_amount, parse_distance_km,
)
from travel_expenses_app.infrastructure.persistence.repositories.in_memory_report_repository import InMemoryTravelReportRepository


def user():
    return SimpleNamespace(
        id="u1597", email="viajante@delpi.com.br", name="Viajante",
        permissions=["travel-expenses.write", "travel-expenses.unit.filial-01"],
        is_superadmin=False,
    )


class FakeMailer:
    def __init__(self):
        self.calls = []

    def send(self, **kwargs):
        self.calls.append(kwargs)


def service():
    repo = InMemoryTravelReportRepository()
    return TravelReportService(repo), repo


@pytest.mark.parametrize("raw", ["R$324,00", "R$ 324,00", "324,00", "324", 324, "1.234,56"])
def test_valid_currency_inputs(raw):
    result = parse_amount(raw)
    assert result > 0


@pytest.mark.parametrize("raw", [None, "", "R$ xx", "NaN", "Infinity", -1, {}, True])
def test_invalid_currency_is_validation_error(raw):
    with pytest.raises(ExpenseValueError):
        parse_amount(raw)


def test_currency_with_thousands_separator():
    assert parse_amount("R$ 1.234,56") == parse_amount(1234.56)


def test_own_vehicle_uses_server_rate_and_persists_rate():
    svc, repo = service()
    actor = user()
    report = svc.create(actor, {"unitCode": "01", "destination": "Joinville"})
    expense = svc.add_expense(actor, report["id"], {
        "expenseDate": "2026-11-12", "categoryId": "ground_transport",
        "transportMode": "own_vehicle", "distanceKm": "270", "amountBrl": 999,
    })
    assert expense["amountBrl"] == 324.0
    assert expense["distanceKm"] == 270.0
    assert expense["rateBrlPerKm"] == 1.2
    assert expense["categoryId"] == "ground_transport"
    assert repo.get_report(report["id"])["totalAmountBrl"] == 324.0
    repo.mileage_rates[date(2027, 1, 1)] = 1.5
    assert svc.get_detail(actor, report["id"])["expenses"][0]["amountBrl"] == 324.0
    newer = svc.add_expense(actor, report["id"], {
        "expenseDate": "2027-01-02", "categoryId": "ground_transport",
        "transportMode": "own_vehicle", "distanceKm": "10",
    })
    assert newer["amountBrl"] == 15.0


def test_other_transport_types_keep_manual_value():
    svc, _ = service()
    actor = user()
    report = svc.create(actor, {"unitCode": "01"})
    for mode in ("ride_hailing", "public_transport"):
        expense = svc.add_expense(actor, report["id"], {
            "expenseDate": "2026-11-12", "categoryId": "ground_transport",
            "transportMode": mode, "amountBrl": "R$ 24,50",
        })
        assert expense["amountBrl"] == 24.5
        assert expense["distanceKm"] is None


def test_invalid_manual_value_is_not_server_error():
    svc, _ = service()
    actor = user()
    report = svc.create(actor, {"unitCode": "01"})
    with pytest.raises(TravelReportError):
        svc.add_expense(actor, report["id"], {
            "expenseDate": "2026-11-12", "categoryId": "fuel", "amountBrl": None,
        })


def test_finance_submission_sends_pdf_with_cc_and_no_receipt():
    svc, repo = service()
    actor = user()
    report = svc.create(actor, {"unitCode": "01", "destination": "Joinville"})
    svc.add_expense(actor, report["id"], {
        "expenseDate": "2026-11-12", "categoryId": "meals", "amountBrl": "R$ 23,00",
    })
    mailer = FakeMailer()
    result = svc.send_to_finance(actor, report["id"], mailer=mailer)
    assert result["status"] == "submitted"
    assert result["dispatchStatus"] == "sent"
    assert mailer.calls[0]["recipient"] == "financeiro@delpi.com.br"
    assert mailer.calls[0]["cc"] == "viajante@delpi.com.br"
    assert mailer.calls[0]["pdf"].startswith(b"%PDF")
    assert repo.list_audit(report["id"])[-1]["eventType"] == "sent_to_finance"
    with pytest.raises(TravelReportError):
        svc.send_to_finance(actor, report["id"], mailer=mailer)
    assert len(mailer.calls) == 1


def test_send_without_expenses_is_rejected():
    svc, _ = service()
    actor = user()
    report = svc.create(actor, {"unitCode": "01"})
    with pytest.raises(TravelReportError):
        svc.send_to_finance(actor, report["id"], mailer=FakeMailer())
