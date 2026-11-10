"""Catálogos fechados do domínio — valores técnicos estáveis (labels ficam na UI)."""

from __future__ import annotations

# Unidades operacionais canônicas da DELPI (mesmos códigos TOTVS de
# OPERATIONAL_UNIT_OPTIONS do @delpi/plugin-ui).
UNIT_CODES = ("01", "02")

ENVIRONMENTS = ("production", "staging", "development")
SERVER_TYPES = ("physical", "virtual", "cloud")
CRITICALITIES = ("low", "medium", "high", "critical")
ADMINISTRATIVE_STATUSES = (
    "planned",
    "in_operation",
    "maintenance",
    "decommissioning",
)

ACTION_PRIORITIES = ("low", "medium", "high", "urgent")
ACTION_STATUSES = ("pending", "in_progress", "done", "cancelled")
OPEN_ACTION_STATUSES = ("pending", "in_progress")

HIGH_CRITICALITIES = ("high", "critical")

CRITICALITY_RANK = {value: index for index, value in enumerate(CRITICALITIES)}
PRIORITY_RANK = {value: index for index, value in enumerate(ACTION_PRIORITIES)}
