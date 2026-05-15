# app/domain/entities/ppm/ppm_item.py

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class PpmItem:
    branch: str
    registered_date: Optional[str]
    code: str
    revision: str
    item_code: Optional[str]
    description: Optional[str]
    returned_quantity_original: Optional[str]
    returned_quantity_un: float

    def to_dict(self)->dict:
        return asdict(self)