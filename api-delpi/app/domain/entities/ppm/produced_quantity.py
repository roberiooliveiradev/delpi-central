from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class ProducedQuantityItem:
    branch: str
    product_code: str
    product_type: str
    description: str
    unit: str
    produced_milheiro: float
    produced_un: float
    orders_count: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProducedQuantityByProduct:
    product_code: str
    product_type: str
    description: str
    unit: str
    produced_milheiro: float
    produced_un: float
    orders_count: int
    branches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProducedQuantityReport:
    branch: Optional[str]
    date_start: str
    date_end: str
    products: list[str]
    items: list[ProducedQuantityItem]
    total_produced_milheiro: float
    total_produced_un: float
    by_product: list[ProducedQuantityByProduct] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "date_start": self.date_start,
            "date_end": self.date_end,
            "products": self.products,
            "items": [item.to_dict() for item in self.items],
            "total_produced_milheiro": self.total_produced_milheiro,
            "total_produced_un": self.total_produced_un,
            "by_product": [row.to_dict() for row in self.by_product],
        }
