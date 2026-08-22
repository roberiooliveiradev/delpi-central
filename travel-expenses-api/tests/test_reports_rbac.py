from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from travel_expenses_app.application.services.package_storage import PackageStorageService
from travel_expenses_app.application.services.receipt_storage import ReceiptStorageService
from travel_expenses_app.application.use_cases.travel_report_service import (
    TravelReportError,
    TravelReportService,
)
from travel_expenses_app.infrastructure.persistence.repositories.in_memory_report_repository import (
    InMemoryTravelReportRepository,
)


def _user(user_id: str, *codes: str):
    return SimpleNamespace(
        id=user_id,
        email=f"{user_id}@delpi.com",
        name=user_id,
        permissions=list(codes),
        is_superadmin=False,
    )


def _service(tmp_path=None):
    repo = InMemoryTravelReportRepository()
    root = tmp_path or Path("/tmp/te-receipts")
    storage = ReceiptStorageService(base_dir=str(root / "receipts"), max_bytes=2048)
    packages = PackageStorageService(base_dir=str(root / "packages"))
    return TravelReportService(repo, receipt_storage=storage, package_storage=packages), repo


def test_owner_creates_and_other_user_cannot_see(tmp_path):
    service, _repo = _service(tmp_path)
    owner = _user("u1", "travel-expenses.write", "travel-expenses.unit.filial-01")
    other = _user("u2", "travel-expenses.view", "travel-expenses.unit.filial-01")
    created = service.create(owner, {"unitCode": "01", "destination": "SP"})
    assert created["number"].startswith("TE-")
    assert created["status"] == "draft"

    with pytest.raises(PermissionError):
        service.get_detail(other, created["id"])

    listed = service.list_reports(other, scope="mine")
    assert listed == []


def test_manage_sees_unit_reports(tmp_path):
    service, _repo = _service(tmp_path)
    owner = _user("u1", "travel-expenses.write", "travel-expenses.unit.filial-01")
    manager = _user(
        "mgr",
        "travel-expenses.manage",
        "travel-expenses.view",
        "travel-expenses.unit.filial-01",
    )
    created = service.create(owner, {"unitCode": "01", "destination": "ES"})
    items = service.list_reports(manager, scope="unit")
    assert [item["id"] for item in items] == [created["id"]]


def test_cannot_write_other_unit(tmp_path):
    service, _repo = _service(tmp_path)
    user = _user("u1", "travel-expenses.write", "travel-expenses.unit.filial-01")
    with pytest.raises(PermissionError):
        service.create(user, {"unitCode": "02", "destination": "Vitória"})


def test_expense_and_receipt_flow(tmp_path):
    service, _repo = _service(tmp_path)
    owner = _user("u1", "travel-expenses.write", "travel-expenses.unit.filial-01")
    report = service.create(
        owner,
        {
            "unitCode": "01",
            "destination": "Campinas",
            "periodStart": "2026-08-10",
            "periodEnd": "2026-08-12",
        },
    )
    expense = service.add_expense(
        owner,
        report["id"],
        {
            "categoryId": "meals",
            "expenseDate": "2026-08-11",
            "merchant": "Padaria",
            "amountBrl": 32.5,
        },
    )
    receipt = service.add_receipt(
        owner,
        report["id"],
        expense["id"],
        original_name="cupom.jpg",
        mime_type="image/jpeg",
        content=b"jpeg-bytes",
    )
    detail = service.get_detail(owner, report["id"])
    assert detail["completeness"]["ready"] is True
    assert detail["totalAmountBrl"] == 32.5
    _meta, path = service.get_receipt_file(owner, report["id"], expense["id"], receipt["id"])
    assert path.read_bytes() == b"jpeg-bytes"


def test_cannot_add_expense_without_write(tmp_path):
    service, _repo = _service(tmp_path)
    owner = _user("u1", "travel-expenses.write", "travel-expenses.unit.filial-01")
    viewer = _user("u2", "travel-expenses.view", "travel-expenses.manage", "travel-expenses.unit.filial-01")
    report = service.create(owner, {"unitCode": "01"})
    with pytest.raises(PermissionError):
        service.add_expense(
            viewer,
            report["id"],
            {"categoryId": "other", "expenseDate": date(2026, 8, 11), "amountBrl": 1},
        )


def test_delete_draft_only(tmp_path):
    service, repo = _service(tmp_path)
    owner = _user("u1", "travel-expenses.write", "travel-expenses.unit.filial-01")
    report = service.create(owner, {"unitCode": "01"})
    repo.update_report(report["id"], {"status": "submitted"})
    with pytest.raises(TravelReportError):
        service.delete(owner, report["id"])
