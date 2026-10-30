import re
from dataclasses import dataclass

from app.domain.totvs.protheus_branches import normalize_branch_code

_PRODUCTION_ORDER_RE = re.compile(r"^[0-9A-Z]{11}$")
MAX_COMPARISON_ORDERS = 10
MIN_COMPARISON_ORDERS = 2


@dataclass(frozen=True)
class GetConsumptionAuditComparisonRequest:
    """Batch bounded de comparação de OPs (GLPI #1353 — F4).

    Mesma filial para todas as OPs — a comparação nunca mistura dados entre
    unidades operacionais diferentes.
    """

    branch: str
    production_orders: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch", normalize_branch_code(self.branch))

        orders = [
            str(op or "").strip().upper()
            for op in (self.production_orders or [])
            if str(op or "").strip()
        ]
        unique = list(dict.fromkeys(orders))
        if not (MIN_COMPARISON_ORDERS <= len(unique) <= MAX_COMPARISON_ORDERS):
            raise ValueError(
                "production_orders deve conter entre "
                f"{MIN_COMPARISON_ORDERS} e {MAX_COMPARISON_ORDERS} OPs distintas."
            )
        invalid = [op for op in unique if not _PRODUCTION_ORDER_RE.match(op)]
        if invalid:
            raise ValueError(
                f"production_order inválida: {invalid[0]!r} — 11 posições "
                "alfanuméricas (C2_NUM 6 + C2_ITEM 2 + C2_SEQUEN 3)."
            )
        object.__setattr__(self, "production_orders", tuple(unique))
