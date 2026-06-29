from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class CustomerMaster:
    code: str
    store: str
    name: str
    blocked: Optional[str] = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)
