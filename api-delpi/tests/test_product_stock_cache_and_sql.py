from app.application.dto.product.list_product_stock_request import ListProductStockRequest
from app.application.models.page import Page
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


def test_list_product_stock_use_case_caches_payload(monkeypatch):
    store: dict = {}

    monkeypatch.setattr(
        "app.application.use_cases.product.list_product_stock_use_case.get_cached_product_stock",
        lambda key: store.get(key),
    )
    monkeypatch.setattr(
        "app.application.use_cases.product.list_product_stock_use_case.set_cached_product_stock",
        lambda key, value: store.__setitem__(key, value),
    )

    repo = _FakeStockRepo()
    use_case = ListProductStockUseCase(repo)
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
