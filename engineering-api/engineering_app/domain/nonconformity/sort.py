"""Whitelist de ordenação da listagem NC — chaves do contrato legado.

O mapeamento chave → expressão SQL vive no adapter Postgres (a direção
padrão e o fallback são de domínio; a tradução SQL é de infraestrutura).
"""

from __future__ import annotations

NC_SORT_KEYS: tuple[str, ...] = (
    "registered_at",
    "occurrence_date",
    "sale_number",
    "lmp_number",
    "customer_name",
    "launch_date",
    "last_revision_date",
    "executed_by",
    "released_by",
    "status",
    "defect_description",
    "problem_tags",
    "products",
)

_DEFAULT_SORT_KEY = "occurrence_date"
_DEFAULT_SORT_DIR = "desc"


def resolve_nc_sort(sort_by: str | None, sort_dir: str | None) -> tuple[str, str]:
    """Resolve ``(sort_key, sort_dir)`` com fallback seguro ao padrão."""
    key = (sort_by or _DEFAULT_SORT_KEY).strip()
    if key not in NC_SORT_KEYS:
        key = _DEFAULT_SORT_KEY
    direction = (sort_dir or _DEFAULT_SORT_DIR).strip().lower()
    if direction not in {"asc", "desc"}:
        direction = _DEFAULT_SORT_DIR
    return key, direction
