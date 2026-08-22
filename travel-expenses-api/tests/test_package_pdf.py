from types import SimpleNamespace

from travel_expenses_app.application.services.package_storage import PackageStorageService
from travel_expenses_app.application.services.receipt_storage import ReceiptStorageService
from travel_expenses_app.application.use_cases.travel_report_service import TravelReportService
from travel_expenses_app.infrastructure.persistence.repositories.in_memory_report_repository import (
    InMemoryTravelReportRepository,
)
from travel_expenses_app.infrastructure.pdf.package_pdf_renderer import TravelPackagePdfRenderer


def test_package_pdf_starts_with_pdf_header(tmp_path):
    repo = InMemoryTravelReportRepository()
    service = TravelReportService(
        repo,
        receipt_storage=ReceiptStorageService(base_dir=str(tmp_path / "r")),
        package_storage=PackageStorageService(base_dir=str(tmp_path / "p")),
        pdf_renderer=TravelPackagePdfRenderer(),
    )
    user = SimpleNamespace(
        id="u1",
        email="u1@delpi.com",
        name="Viajante",
        permissions=["travel-expenses.write", "travel-expenses.unit.filial-01"],
        is_superadmin=False,
    )
    report = service.create(
        user,
        {
            "unitCode": "01",
            "destination": "São Paulo",
            "periodStart": "2026-08-10",
            "periodEnd": "2026-08-11",
        },
    )
    service.add_expense(
        user,
        report["id"],
        {"categoryId": "meals", "expenseDate": "2026-08-10", "merchant": "Café", "amountBrl": 18},
    )
    content = service.build_package_pdf(user, report["id"])
    assert content.startswith(b"%PDF")
    assert (tmp_path / "p" / report["id"] / "package.pdf").is_file()
