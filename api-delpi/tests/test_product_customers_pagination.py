"""Product customers repository — count/item dataset alignment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.application.models.page import Page
from app.infrastructure.persistence.totvs.product_repositories import (
    product_customers_repository as mod,
)
from app.infrastructure.persistence.totvs.product_repositories.product_customers_repository import (
    ProductCustomersRepository,
)


def _module_source() -> str:
    root = Path(__file__).resolve().parents[1]
    return (
        root
        / "app/infrastructure/persistence/totvs/product_repositories/product_customers_repository.py"
    ).read_text(encoding="utf-8")


def test_count_sql_uses_same_inner_joins_as_item_dataset() -> None:
    src = _module_source()
    assert "_CUSTOMER_DATASET_FROM" in src
    assert src.count("INNER JOIN SA1010 SA1") >= 1
    assert src.count("INNER JOIN SB1010 SB1") >= 1
    assert "SA1.D_E_L_E_T_ = ''" in src
    assert "SB1.D_E_L_E_T_ = ''" in src
    # Count must not be SA7-only.
    assert "SELECT COUNT(*) AS total\n            FROM SA7010\n            WHERE" not in src


def test_ordering_has_deterministic_tie_breakers() -> None:
    assert "ORDER BY SA1.A1_NOME, SA1.A1_COD, SA1.A1_LOJA" in _module_source()


class _FakeCustomersRepo(ProductCustomersRepository):
    """Avoid real DB; capture SQL and return scripted totals/rows."""

    def __init__(self, *, total: int, pages: dict[int, list[dict[str, Any]]]):
        super().__init__()
        self._total = total
        self._pages = pages
        self.count_sql: str | None = None
        self.last_offset: int | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def execute_one(self, query, params=None):  # noqa: ANN001
        self.count_sql = query
        return {"total": self._total}

    def execute_query(self, query, params=None):  # noqa: ANN001
        # params: (code, code, offset, page_size) for item SQL
        offset = int(params[2]) if params and len(params) >= 3 else 0
        self.last_offset = offset
        page_num = (offset // int(params[3])) + 1 if params and params[3] else 1
        return list(self._pages.get(page_num, []))


def _row(code: str, name: str) -> dict[str, Any]:
    return {
        "B1_COD": "10080055",
        "B1_DESC": "P",
        "B1_UM": "UN",
        "A1_COD": code,
        "A1_LOJA": "01",
        "A1_NOME": name,
        "A1_MSBLQL": "2",
        "A7_CODCLI": "X",
        "A7_DESCCLI": "X",
        "A7_PRECO01": None,
        "A7_DTREF01": None,
        "average_price": None,
        "last_sale_date": None,
        "total_quantity": None,
    }


def test_list_customers_total_matches_aligned_dataset_not_orphan_sa7() -> None:
    """Canonical dataset excludes SA7 rows without active SA1 (live 000615 case)."""
    repo = _FakeCustomersRepo(
        total=3,
        pages={
            1: [
                _row("000042", "A"),
                _row("000079", "B"),
                _row("000102", "C"),
            ]
        },
    )
    page = repo.list_customers("10080055", 1, 50)
    assert isinstance(page, Page)
    assert page.total == 3
    assert page.total_pages == 1
    assert len(page.items) == 3
    assert repo.count_sql is not None
    assert "INNER JOIN SA1010" in repo.count_sql
    assert "INNER JOIN SB1010" in repo.count_sql
    assert mod._CUSTOMER_DATASET_FROM in repo.count_sql


def test_page_size_1_traversal_sums_to_total() -> None:
    pages = {
        1: [_row("C0", "N0")],
        2: [_row("C1", "N1")],
        3: [_row("C2", "N2")],
        4: [],
    }
    collected: list[str] = []
    for page_num in (1, 2, 3, 4):
        repo = _FakeCustomersRepo(total=3, pages=pages)
        page = repo.list_customers("10080055", page_num, 1)
        assert page.total == 3
        assert page.total_pages == 3
        if page_num <= 3:
            assert len(page.items) == 1
            collected.append(page.items[0].customer_code)
        else:
            assert page.items == []
    assert collected == ["C0", "C1", "C2"]


def test_route_customers_has_no_debug_print() -> None:
    root = Path(__file__).resolve().parents[1]
    route = (
        root / "app/interface/http/routes/product_routes.py"
    ).read_text(encoding="utf-8")
    customers_fn = route.split("def customers(", 1)[1].split("def inspection(", 1)[0]
    assert "print(" not in customers_fn
