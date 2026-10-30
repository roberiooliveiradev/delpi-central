import re
from dataclasses import dataclass

from app.domain.totvs.protheus_branches import normalize_branch_code

_PRODUCTION_ORDER_RE = re.compile(r"^[0-9A-Z]{11}$")


@dataclass(frozen=True)
class GetConsumptionAuditOrderRequest:
    production_order: str
    branch: str

    def __post_init__(self) -> None:
        op = str(self.production_order or "").strip().upper()
        if not _PRODUCTION_ORDER_RE.match(op):
            raise ValueError(
                "production_order inválida: 11 posições alfanuméricas "
                "(C2_NUM 6 + C2_ITEM 2 + C2_SEQUEN 3)."
            )
        object.__setattr__(self, "production_order", op)
        object.__setattr__(self, "branch", normalize_branch_code(self.branch))
