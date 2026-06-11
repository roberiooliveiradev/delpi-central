from dataclasses import dataclass


@dataclass(slots=True)
class ProductionOperationalRequest:
    date_start: str | None = None
    date_end: str | None = None
    reference_date: str | None = None
    branch: str | None = None
    limit: int | None = None
    group_by: str = "general"
    loss_type: str = "both"
    work_center: str | None = None
    item_code: str | None = None
    product_group: str | None = None
    legacy: bool = False
