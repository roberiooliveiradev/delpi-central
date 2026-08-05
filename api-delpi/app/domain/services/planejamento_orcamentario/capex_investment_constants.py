"""Constantes — itens de investimento CAPEX (Fase 2B.1).

Prioridade e classificação seguem a planilha original (1–4 e 1–6).
Origem segue a Carta (nacional/importado). Categoria ≠ conta contábil ERP.
"""

from __future__ import annotations

ENTITY_TYPE_CAPEX_INVESTMENT = "capex_investment"

STATUS_DRAFT = "draft"
STATUS_ARCHIVED = "archived"
ALLOWED_STATUSES = frozenset({STATUS_DRAFT, STATUS_ARCHIVED})

DEFAULT_CURRENCY = "BRL"

# Planilha: 1 Compra aprovada/em andamento; 2 Maior; 3 Média; 4 Menor
ALLOWED_PRIORITIES = frozenset({"1", "2", "3", "4"})

# Carta: nacional / importado
ALLOWED_ORIGINS = frozenset({"national", "imported"})

# Planilha Classif. 1–6
ALLOWED_CLASSIFICATIONS = frozenset({"1", "2", "3", "4", "5", "6"})

# Planilha Turno
ALLOWED_SHIFTS = frozenset({"1", "2", "3"})

# Campos necessários para considerar o item completo (futura submissão)
COMPLETENESS_FIELDS = (
    "description",
    "category_id",
    "estimated_amount",
    "required_date",
    "priority",
    "origin",
    "cost_center_id",
    "exercise_id",
)
