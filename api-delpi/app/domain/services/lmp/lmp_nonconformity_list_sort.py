"""Ordenação segura da listagem de NCs LMP."""

from __future__ import annotations

_SORT_COLUMNS: dict[str, str] = {
    "registered_at": "n.registered_at",
    "sale_number": "n.sale_number",
    "customer_name": "n.customer_name",
    "launch_date": "n.launch_date",
    "last_revision_date": "n.last_revision_date",
    "executed_by": "n.executed_by",
    "released_by": "n.released_by",
    "status": "n.status",
    "defect_description": "n.defect_description",
    "problem_tags": (
        "(SELECT COALESCE(string_agg(t.label, ', ' ORDER BY t.label), '')"
        " FROM engineering.lmp_nonconformity_problem_tags npt"
        " JOIN engineering.lmp_problem_tags t ON t.id = npt.tag_id"
        " WHERE npt.nonconformity_id = n.id)"
    ),
    "products": (
        "(SELECT COALESCE(string_agg(p.product_code, ', ' ORDER BY p.product_code), '')"
        " FROM engineering.lmp_nonconformity_products p"
        " WHERE p.nonconformity_id = n.id)"
    ),
}

_DEFAULT_SORT_KEY = "registered_at"
_DEFAULT_SORT_DIR = "desc"


def resolve_lmp_nc_order_by(
    sort_by: str | None,
    sort_dir: str | None,
) -> tuple[str, str, str]:
    """
    Retorna ``(sort_key, sort_dir, order_by_sql_fragment)``.

    ``order_by_sql_fragment`` já inclui a direção (ASC/DESC) e desempate estável.
    """
    key = (sort_by or _DEFAULT_SORT_KEY).strip()
    if key not in _SORT_COLUMNS:
        key = _DEFAULT_SORT_KEY

    direction = (sort_dir or _DEFAULT_SORT_DIR).strip().lower()
    if direction not in {"asc", "desc"}:
        direction = _DEFAULT_SORT_DIR

    sql_dir = "ASC" if direction == "asc" else "DESC"
    expression = _SORT_COLUMNS[key]
    # NULLS LAST em ASC; NULLS FIRST em DESC (Postgres)
    nulls = "NULLS LAST" if direction == "asc" else "NULLS FIRST"
    order_sql = f"{expression} {sql_dir} {nulls}, n.created_at DESC, n.id DESC"
    return key, direction, order_sql
