# domain/entities/parent_node.py

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParentNode:

    code: str
    description: Optional[str]
    type: Optional[str]
    unit: Optional[str]
    quantity: float

    parents: List["ParentNode"] = field(default_factory=list)

    def to_dict(self):

        return {
            "code": self.code,
            "description": self.description,
            "type": self.type,
            "unit": self.unit,
            "quantity": self.quantity,
            "parents": [p.to_dict() for p in self.parents]
        }