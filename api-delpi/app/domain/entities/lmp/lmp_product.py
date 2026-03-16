from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class LMPProduct:
    code: str
    description: str
    group_code: Optional[str] = None
    type: Optional[str] = None
    qtd_pi: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)