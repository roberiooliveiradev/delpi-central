# app/domain/entities/lmp/lmp.py
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from .lmp_product import LMPProduct


@dataclass
class LMP:
    sale_number: str
    sale_description: str

    # Engineering summary
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    engineering_status: Optional[str] = None
    qtd_engineering_entries: Optional[int] = None
    qtd_engineering_closed: Optional[int] = None
    qtd_advanced_from_engineering: Optional[int] = None
    qtd_returned_from_engineering: Optional[int] = None
    engineering_total_minutes: Optional[int] = None

    # PI summary
    qtd_pi: Optional[int] = None

    # Costumer
    costumer_code: Optional[str] = None
    costumer_store: Optional[str] = None
    costumer_name: Optional[str] = None

    # Seller
    seller_code: Optional[str] = None
    seller_name: Optional[str] = None

    # Products
    list_products: Optional[List[LMPProduct]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)