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

    components: List["BomNode"] = field(default_factory=list)

    def to_dict(self):
        return {
            "code": self.code,
            "description": self.description,
            "type": self.type,
            "unit": self.unit,
            "quantity": self.quantity,
            "components": [c.to_dict() for c in self.components]
        }