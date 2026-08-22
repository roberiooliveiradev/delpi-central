from types import SimpleNamespace

from travel_expenses_app.application.services.package_storage import PackageStorageService
from travel_expenses_app.application.services.receipt_storage import ReceiptStorageService
from travel_expenses_app.application.use_cases.travel_report_service import (
    TravelReportError,
    TravelReportService,
)
from travel_expenses_app.infrastructure.persistence.repositories.in_memory_report_repository import (
    InMemoryTravelReportRepository,
)
from travel_expenses_app.infrastructure.pdf.package_pdf_renderer import TravelPackagePdfRenderer


def _user():
    return SimpleNamespace(
        id="u1",
        email="u1@delpi.com",
        name="Viajante",
        permissions=["travel-expenses.write", "travel-expenses.unit.filial-01"],
        is_superadmin=False,
    )


def test_update_pix_key_and_pdf(tmp_path):
    repo = InMemoryTravelReportRepository()
    service = TravelReportService(
        repo,
        receipt_storage=ReceiptStorageService(base_dir=str(tmp_path / "r")),
        package_storage=PackageStorageService(base_dir=str(tmp_path / "p")),
        pdf_renderer=TravelPackagePdfRenderer(),
    )
    user = _user()
    report = service.create(user, {"unitCode": "01", "destination": "SP"})
    updated = service.update(
        user,
        report["id"],
        {"pixKeyType": "email", "pixKeyValue": "viajante@delpi.com"},
    )
    assert updated["pixKeyType"] == "email"
    assert updated["pixKeyValue"] == "viajante@delpi.com"

    detail = service.get_detail(user, report["id"])
    assert detail["pixKeyType"] == "email"
    assert detail["pixKeyValue"] == "viajante@delpi.com"

    pdf_with_pix = service.build_package_pdf(user, report["id"])
    service.update(user, report["id"], {"pixKeyType": None, "pixKeyValue": None})
    pdf_without_pix = service.build_package_pdf(user, report["id"])

    assert pdf_with_pix.startswith(b"%PDF")
    assert pdf_without_pix.startswith(b"%PDF")
    assert len(pdf_with_pix) >= len(pdf_without_pix)


def test_update_pix_key_requires_both_fields(tmp_path):
    repo = InMemoryTravelReportRepository()
    service = TravelReportService(
        repo,
        receipt_storage=ReceiptStorageService(base_dir=str(tmp_path / "r")),
        package_storage=PackageStorageService(base_dir=str(tmp_path / "p")),
    )
    user = _user()
    report = service.create(user, {"unitCode": "01", "destination": "SP"})
    try:
        service.update(user, report["id"], {"pixKeyType": "cpf"})
        assert False, "expected validation error"
    except TravelReportError as exc:
        assert "tipo e a chave" in str(exc).lower()
