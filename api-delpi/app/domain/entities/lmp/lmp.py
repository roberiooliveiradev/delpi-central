# app/domain/entities/lmp/lmp.py
from dataclasses import dataclass, field, asdict
from typing import Optional, List

from app.shared.utils.spreadsheet_date import format_date_iso

from .lmp_product import LMPProduct
from .lmp_history_event import LMPHistoryEvent


@dataclass
class LMP:
    branch: Optional[str] = None
    sale_number: str = ""
    sale_description: str = ""
    listing_kind: Optional[str] = None

    # Engineering summary
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reference_revision: Optional[str] = None
    measurement_revision: Optional[str] = None
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

    # Engineering / workflow history (AIJ010)
    list_history: Optional[List[LMPHistoryEvent]] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["start_date"] = format_date_iso(data.get("start_date"))
        data["end_date"] = format_date_iso(data.get("end_date"))
        history = data.get("list_history") or []
        if history:
            data["list_history"] = [
                {
                    **event,
                    "start_date": format_date_iso(event.get("start_date")),
                    "limit_date": format_date_iso(event.get("limit_date")),
                    "end_date": format_date_iso(event.get("end_date")),
                    "next_start_date": format_date_iso(event.get("next_start_date")),
                }
                if isinstance(event, dict)
                else event
                for event in history
            ]
        return data
