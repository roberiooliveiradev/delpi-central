"""Escopo canônico de apontamentos produtivos (eficiência fabril / OEE alinhado)."""

from __future__ import annotations

from typing import Any

from app.domain.production.production_efficiency_valid_range import (
    PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
    PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
)

EFICIENCIA_FABRIL_VIEW = "dbo.vw_Apontamentos_Eficiencia"
STATUS_REGISTRO_OK = "OK"
DEFAULT_PRODUCTION_BRANCHES = ("01", "02")
EXCLUDED_WORK_CENTERS = ("CT-00", "CT-70", "CT-16A", "CT-99")
# Exclusão vale para KPI de eficiência/OEE. Histórico de saldo da OP (cockpit)
# pode pedir include_excluded_work_centers=True para não perder CT-00 etc.

# Produtos amostra/teste (código inicia com 8) — fora do KPI de eficiência/OEE.
# Alinhado à convenção DELPI de PA amostra (ex.: safety stock / OTD).
EXCLUDED_PRODUCT_CODE_PREFIXES: tuple[str, ...] = ("8",)

EFFICIENCY_PERCENTUAL_COLUMN = "EFICIENCIA_PERCENTUAL"


def is_excluded_sample_product_code(product_code: Any) -> bool:
    """True se o código do produto do apontamento é amostra (prefixo excluído)."""
    code = str(product_code or "").strip()
    if not code:
        return False
    return any(code.startswith(prefix) for prefix in EXCLUDED_PRODUCT_CODE_PREFIXES)
