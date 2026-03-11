# app/domain/entities/supplier.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class Supplier:

    product_code: str
    product_description: Optional[str]
    unit: Optional[str]

    supplier_code: str
    supplier_store: str
    supplier_name: Optional[str]

    supplier_part_number: Optional[str]
    catalog_code: Optional[str]
    barcode: Optional[str]

    registered_lead_time_days: Optional[int]
    real_avg_lead_time_days: Optional[float]
    real_min_lead_time_days: Optional[int]
    real_max_lead_time_days: Optional[int]
    real_lead_time_sample_size: Optional[int]

    last_price: Optional[float]
    last_price_date: Optional[str]