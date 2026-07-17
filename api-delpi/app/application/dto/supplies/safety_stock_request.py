from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.supplies.safety_stock_classification_service import ALLOWED_STATUSES

VALID_BRANCHES = frozenset({"01", "02"})
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

ALLOWED_SORT_FIELDS = frozenset(
    {
        "product_code",
        "product_description",
        "product_group",
        "unit",
        "safety_stock",
        "primary_stock",
        "work_in_process_stock",
        "deficit_quantity",
        "status",
    }
)


@dataclass
class SafetyStockQueryRequest:
    branch: str
    include_blocked: bool = False
    product_group: str | None = None
    unit: str | None = None
    search: str | None = None
    status: str | None = None
    include_without_safety_stock: bool = True

    def __post_init__(self) -> None:
        self.branch = (self.branch or "").strip()
        if not self.branch:
            raise ValueError("O parâmetro branch é obrigatório.")
        if self.branch not in VALID_BRANCHES:
            raise ValueError("Filial inválida. Utilize 01 ou 02.")

        if self.status:
            normalized = self.status.strip()
            if normalized not in ALLOWED_STATUSES:
                raise ValueError(
                    "Status inválido. Utilize without_safety_stock, "
                    "below_safety_stock, at_safety_stock ou above_safety_stock."
                )
            self.status = normalized

        if self.product_group is not None:
            self.product_group = self.product_group.strip() or None
        if self.unit is not None:
            self.unit = self.unit.strip() or None
        if self.search is not None:
            self.search = self.search.strip() or None


@dataclass
class SafetyStockItemsRequest(SafetyStockQueryRequest):
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE
    sort_by: str = "product_code"
    sort_direction: str = "asc"

    def __post_init__(self) -> None:
        super().__post_init__()

        self.page = max(int(self.page or DEFAULT_PAGE), 1)
        self.page_size = max(int(self.page_size or DEFAULT_PAGE_SIZE), 1)
        if self.page_size > MAX_PAGE_SIZE:
            raise ValueError(f"page_size não pode exceder {MAX_PAGE_SIZE}.")

        self.sort_by = (self.sort_by or "product_code").strip()
        if self.sort_by not in ALLOWED_SORT_FIELDS:
            raise ValueError(
                "Campo de ordenação inválido. Utilize um dos campos permitidos "
                "pela API de estoque de segurança."
            )

        direction = (self.sort_direction or "asc").strip().lower()
        if direction not in {"asc", "desc"}:
            raise ValueError("sort_direction deve ser asc ou desc.")
        self.sort_direction = direction

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass
class SafetyStockItemDetailsRequest:
    branch: str
    product_code: str

    def __post_init__(self) -> None:
        self.branch = (self.branch or "").strip()
        if not self.branch:
            raise ValueError("O parâmetro branch é obrigatório.")
        if self.branch not in VALID_BRANCHES:
            raise ValueError("Filial inválida. Utilize 01 ou 02.")

        self.product_code = (self.product_code or "").strip()
        if not self.product_code:
            raise ValueError("O código do produto é obrigatório.")


@dataclass
class SafetyStockSupplierPriceHistoryRequest:
    branch: str
    product_code: str
    supplier_code: str
    supplier_store: str

    def __post_init__(self) -> None:
        self.branch = (self.branch or "").strip()
        if not self.branch:
            raise ValueError("O parâmetro branch é obrigatório.")
        if self.branch not in VALID_BRANCHES:
            raise ValueError("Filial inválida. Utilize 01 ou 02.")

        self.product_code = (self.product_code or "").strip()
        if not self.product_code:
            raise ValueError("O código do produto é obrigatório.")

        self.supplier_code = (self.supplier_code or "").strip()
        if not self.supplier_code:
            raise ValueError("O código do fornecedor é obrigatório.")

        self.supplier_store = (self.supplier_store or "").strip()
        if not self.supplier_store:
            raise ValueError("A loja do fornecedor é obrigatória.")
