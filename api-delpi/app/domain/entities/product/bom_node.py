# app/domain/entities/bom_node.py
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BomNode:

    code: str
    description: Optional[str]
    type: Optional[str]
    unit: Optional[str]
    quantity: float
    secondary_unit: Optional[str] = None
    conversion_factor: Optional[float] = None
    conversion_type: Optional[str] = None

    components: List["BomNode"] = field(default_factory=list)

    def to_dict(self):
        payload = {
            "code": self.code,
            "description": self.description,
            "type": self.type,
            "unit": self.unit,
            "quantity": self.quantity,
            "components": [c.to_dict() for c in self.components],
        }

        if self.secondary_unit:
            payload["secondary_unit"] = self.secondary_unit

        if self.conversion_factor is not None:
            payload["conversion_factor"] = self.conversion_factor

        if self.conversion_type:
            payload["conversion_type"] = self.conversion_type

        return payload