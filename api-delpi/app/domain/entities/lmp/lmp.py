# app/domain/entities/lmp/lmp.py
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from .lmp_product import LMPProduct


@dataclass
class LMP:
    sale_number: str
    sale_description: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
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