from __future__ import annotations

import re
from typing import Any, Mapping
from uuid import UUID

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_uuid(value: Any) -> bool:
    text = str(value or "").strip()
    if not _UUID_PATTERN.match(text):
        return False
    try:
        UUID(text)
    except ValueError:
        return False
    return True


def resolve_cache_scope_for_review(
    review: dict,
    process_row: dict,
    *,
    instancias_by_id: Mapping[str, dict],
) -> dict[str, Any]:
    instancia_id = review.get("instancia_id")
    if instancia_id and str(instancia_id) in instancias_by_id:
        inst = instancias_by_id[str(instancia_id)]
        return {
            "instancia_id": str(inst["instancia_id"]),
            "filial_id": str(inst["filial_id"]) if inst.get("filial_id") else None,
            "setor_id": str(inst["setor_id"]) if inst.get("setor_id") else None,
            "codigo_filial": inst.get("codigo_filial"),
            "codigo_setor": inst.get("codigo_setor"),
        }

    process_instancia_id = process_row.get("instancia_id")
    return {
        "instancia_id": str(process_instancia_id) if process_instancia_id else None,
        "filial_id": None,
        "setor_id": None,
        "codigo_filial": process_row.get("filial_id"),
        "codigo_setor": process_row.get("setor_id"),
    }


def filial_filter_sql(column_prefix: str, filial_ref: str) -> tuple[str, tuple[Any, ...]]:
    column = f"{column_prefix}.filial_id"
    codigo_column = f"{column_prefix}.codigo_filial"
    if is_uuid(filial_ref):
        return (f"{column} = %s::uuid", (filial_ref,))
    return (f"{codigo_column} = %s", (filial_ref,))


def setor_filter_sql(column_prefix: str, setor_ref: str) -> tuple[str, tuple[Any, ...]]:
    column = f"{column_prefix}.setor_id"
    codigo_column = f"{column_prefix}.codigo_setor"
    if is_uuid(setor_ref):
        return (f"{column} = %s::uuid", (setor_ref,))
    return (f"{codigo_column} = %s", (setor_ref,))
