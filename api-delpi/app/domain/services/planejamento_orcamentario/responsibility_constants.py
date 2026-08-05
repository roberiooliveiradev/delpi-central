"""Constantes de responsabilidade orçamentária (Fase 2A.1)."""

from __future__ import annotations

BUDGET_MODULE_CAPEX = "capex"
BUDGET_MODULE_PERSONNEL = "personnel"
ALLOWED_BUDGET_MODULES = frozenset({BUDGET_MODULE_CAPEX, BUDGET_MODULE_PERSONNEL})

RESPONSIBILITY_TYPE_OWNER = "owner"
RESPONSIBILITY_TYPE_COLLABORATOR = "collaborator"
ALLOWED_RESPONSIBILITY_TYPES = frozenset({
    RESPONSIBILITY_TYPE_OWNER,
    RESPONSIBILITY_TYPE_COLLABORATOR,
})

# Exercícios nestes status não aceitam novos vínculos nem reativação
EXERCISE_STATUSES_BLOCKING_RESPONSIBILITY = frozenset({"archived"})
