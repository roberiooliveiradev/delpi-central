from dataclasses import dataclass
from typing import Sequence

from app.domain.totvs.protheus_branches import normalize_branch_code
from app.domain.totvs.protheus_product_codes import require_product_codes


@dataclass(frozen=True)
class ListProductPhysicalLocationsRequest:
    product_codes: Sequence[str]
    branch: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch", normalize_branch_code(self.branch))
        object.__setattr__(
            self,
            "product_codes",
            require_product_codes(self.product_codes),
        )
