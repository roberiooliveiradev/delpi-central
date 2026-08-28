"""Unit — provider e Excel de saldos PA (Delpi Reports)."""

from __future__ import annotations

import base64
from io import BytesIO

from openpyxl import load_workbook

from app.domain.services.reports.providers.stock_balances_pa_provider import (
    StockBalancesPaProvider,
)
from app.domain.services.reports.stock_balances_pa_excel_builder import (
    StockBalancesPaExcelBuilder,
)
from app.domain.services.reports.stock_balances_pa_rules import (
    PROVIDER_KEY,
    export_file_base,
    export_quantity,
    product_code_matches_prefixes,
)


class _FakeRepo:
    def __init__(self, items: list[dict]) -> None:
        self.items = items
        self.calls = 0

    def count_items(self, **kwargs) -> int:
        return len(self.items)

    def fetch_items(self, *, offset: int, page_size: int, **kwargs) -> list[dict]:
        self.calls += 1
        return self.items[offset : offset + page_size]


def test_product_code_prefixes() -> None:
    assert product_code_matches_prefixes("9001", ("9",))
    assert not product_code_matches_prefixes("8001", ("9",))
    assert product_code_matches_prefixes("8001", ("8", "9"))


def test_export_quantity_multiplies_by_1000() -> None:
    assert export_quantity(12.5) == 12500.0


def test_export_file_base_by_branch() -> None:
    assert export_file_base("01", "2026-08-28") == "ESTOQUE MATRIZ - 28-08-2026"
    assert export_file_base("02", "2026-08-28") == "SALDO FILIAL - 28-08-2026"


def test_collect_filters_prefix_by_branch() -> None:
    repo = _FakeRepo(
        [
            {"product_code": "9001234", "quantity": 10},
            {"product_code": "90350341", "quantity": 7},
            {"product_code": "80012849", "quantity": 3},
            {"product_code": "50120001", "quantity": 99},
        ]
    )
    provider = StockBalancesPaProvider(repo)
    dataset = provider.collect({"branch": "01"})
    assert dataset.provider_key == PROVIDER_KEY
    assert [row["product_code"] for row in dataset.rows] == ["9001234"]

    dataset_02 = provider.collect({"branch": "02"})
    assert [row["product_code"] for row in dataset_02.rows] == ["80012849", "9001234"]


def test_collect_excludes_9035_family() -> None:
    repo = _FakeRepo(
        [
            {"product_code": "90350341", "quantity": 7},
            {"product_code": "90260014", "quantity": 2},
        ]
    )
    provider = StockBalancesPaProvider(repo)
    dataset = provider.collect({"branch": "01"})
    assert [row["product_code"] for row in dataset.rows] == ["90260014"]


def test_excel_attachment_has_borders_and_scaled_qty() -> None:
    rows = [{"product_code": "90260014", "quantity": 12.5}]
    attachment = StockBalancesPaExcelBuilder.build_attachment(
        rows, branch="01", issued_on="2026-08-28"
    )
    assert attachment.name == "ESTOQUE MATRIZ - 28-08-2026.xlsx"
    assert "spreadsheetml" in attachment.content_type
    raw = base64.b64decode(attachment.content_base64)
    wb = load_workbook(BytesIO(raw))
    sheet = wb.active
    assert sheet["A1"].value == "Produto"
    assert sheet["B1"].value == "Quantidade"
    assert sheet["A2"].value == "90260014"
    assert sheet["B2"].value == 12500.0
    assert sheet["A2"].border.left.style == "thin"


def test_render_email_includes_xlsx_attachment() -> None:
    repo = _FakeRepo([{"product_code": "9001234", "quantity": 1}])
    provider = StockBalancesPaProvider(repo)
    dataset = provider.collect({"branch": "01"})
    email = provider.render_email(dataset)
    assert "ESTOQUE MATRIZ" in email.subject
    names = [item.name for item in email.attachments]
    assert any(name.endswith(".xlsx") for name in names)
    assert "anexo" in email.html_body.lower()
