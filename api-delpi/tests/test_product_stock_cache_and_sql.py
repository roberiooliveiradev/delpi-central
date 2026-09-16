from pathlib import Path
from unittest.mock import MagicMock

from app.application.dto.product.list_product_stock_request import ListProductStockRequest
from app.application.models.page import Page
from app.application.services.product import product_stock_cache as stock_cache
from app.application.use_cases.product.list_product_stock_use_case import (
    ListProductStockUseCase,
)
from app.domain.entities.product.stock import Stock


class _FakeStockRepo:
    def __init__(self):
        self.calls = 0

    def list_stock(self, **kwargs):
        self.calls += 1
        return Page(
            items=[
                Stock(
                    product_code="10090016",
                    branch="01",
                    warehouse="01",
                    current_quantity=0,
                    committed_quantity=0,
                    reserved_quantity=0,
                    available_quantity=0,
                    physical_location=None,
                    default_warehouse=None,
                    cost_center=None,
                    warehouse_section=None,
                )
            ],
            total=1,
            page=1,
            page_size=50,
        )


class _FakeCache:
    def __init__(self):
        self.store: dict = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value) -> None:
        self.store[key] = value

    def invalidate_all(self) -> None:
        self.store.clear()

    def get_or_set(self, key: str, factory):
        cached = self.get(key)
        if cached is not None:
            return cached
        value = factory()
        self.set(key, value)
        return value


def test_list_product_stock_use_case_caches_payload() -> None:
    repo = _FakeStockRepo()
    cache = _FakeCache()
    use_case = ListProductStockUseCase(repository=repo, cache=cache)
    dto = ListProductStockRequest(
        code="10090016",
        page=1,
        page_size=50,
        branch=None,
        location=None,
    )

    first = use_case.execute(dto)
    second = use_case.execute(dto)

    assert repo.calls == 1
    assert first == second
    assert first["total"] == 1
    assert first["items"][0]["product_code"] == "10090016"
    expected_key = stock_cache.product_stock_cache_key(
        code="10090016",
        page=1,
        page_size=50,
        branch=None,
        location=None,
    )
    assert expected_key in cache.store


def test_list_product_stock_cache_hit_skips_repository() -> None:
    repo = _FakeStockRepo()
    cache = _FakeCache()
    key = stock_cache.product_stock_cache_key(
        code="10090016",
        page=1,
        page_size=50,
        branch=None,
        location=None,
    )
    cached_payload = {
        "items": [{"product_code": "10090016"}],
        "total": 1,
        "page": 1,
        "page_size": 50,
    }
    cache.set(key, cached_payload)

    use_case = ListProductStockUseCase(repository=repo, cache=cache)
    result = use_case.execute(
        ListProductStockRequest(
            code="10090016",
            page=1,
            page_size=50,
            branch=None,
            location=None,
        )
    )

    assert repo.calls == 0
    assert result is cached_payload


def test_product_stock_cache_helpers_use_injected_port() -> None:
    cache = MagicMock()
    cache.get.return_value = {"items": []}
    assert stock_cache.get_cached_product_stock(cache, "k") == {"items": []}
    cache.get.return_value = "not-a-dict"
    assert stock_cache.get_cached_product_stock(cache, "k") is None
    stock_cache.set_cached_product_stock(cache, "k", {"ok": True})
    cache.set.assert_called_once_with("k", {"ok": True})


def test_product_stock_cache_does_not_import_composition_root() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "app/application/services/product/product_stock_cache.py"
    )
    text = path.read_text(encoding="utf-8")
    assert "app.composition" not in text
    assert "query_cache_composer" not in text
    assert "build_query_cache" not in text

    uc_path = (
        Path(__file__).resolve().parents[1]
        / "app/application/use_cases/product/list_product_stock_use_case.py"
    )
    uc_text = uc_path.read_text(encoding="utf-8")
    assert "app.composition" not in uc_text


def test_product_stock_repository_sql_uses_nolock_and_window_count():
    from app.infrastructure.persistence.totvs.product_repositories.product_stock_repository import (
        ProductStockRepository,
    )

    captured: dict = {}

    class _Ctx:
        def execute_query(self, sql, params):
            captured["data_sql"] = sql
            captured["data_params"] = params
            return [
                {
                    "product_code": "10090016",
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": 1,
                    "committed_quantity": 0,
                    "reserved_quantity": 0,
                    "available_quantity": 1,
                    "physical_location": None,
                    "default_warehouse": None,
                    "cost_center": None,
                    "warehouse_section": None,
                    "_total_count": 1,
                }
            ]

        def execute_one(self, sql, params):
            captured["count_sql"] = sql
            return {"total": 0}

    class _Repo(ProductStockRepository):
        def __enter__(self):
            return _Ctx()

        def __exit__(self, *args):
            return False

    page = _Repo().list_stock(
        code="10090016",
        page=1,
        page_size=50,
        branch=None,
        location=None,
    )

    assert "WITH (NOLOCK)" in captured["data_sql"]
    assert "COUNT(*) OVER()" in captured["data_sql"]
    assert "count_sql" not in captured
    assert page.total == 1
    assert len(page.items) == 1
    assert not hasattr(page.items[0], "_total_count")
