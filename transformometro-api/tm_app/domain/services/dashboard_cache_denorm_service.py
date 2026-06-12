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


def _first_setor(inst: dict) -> dict[str, Any] | None:
    setores = inst.get("setores") or []
    if isinstance(setores, list) and setores:
        first = setores[0]
        return first if isinstance(first, dict) else None
    if inst.get("setor_id") or inst.get("codigo_setor"):
        return {
            "setor_id": inst.get("setor_id"),
            "codigo_setor": inst.get("codigo_setor"),
        }
    return None


def resolve_cache_scope_for_review(
    review: dict,
    process_row: dict,
    *,
    instancias_by_id: Mapping[str, dict],
) -> dict[str, Any]:
    instancia_id = review.get("instancia_id")
    if instancia_id and str(instancia_id) in instancias_by_id:
        inst = instancias_by_id[str(instancia_id)]
        first = _first_setor(inst)
        return {
            "instancia_id": str(inst["instancia_id"]),
            "filial_id": str(inst["filial_id"]) if inst.get("filial_id") else None,
            "setor_id": str(first["setor_id"]) if first and first.get("setor_id") else None,
            "codigo_filial": inst.get("codigo_filial"),
            "codigo_setor": first.get("codigo_setor") if first else None,
            "todas_filiais_ativas": bool(inst.get("todas_filiais_ativas")),
            "setores": inst.get("setores") or [],
        }

    process_instancia_id = process_row.get("instancia_id")
    return {
        "instancia_id": str(process_instancia_id) if process_instancia_id else None,
        "filial_id": None,
        "setor_id": None,
        "codigo_filial": process_row.get("filial_id"),
        "codigo_setor": process_row.get("setor_id"),
        "todas_filiais_ativas": False,
        "setores": [],
    }


def filial_filter_sql(column_prefix: str, filial_ref: str) -> tuple[str, tuple[Any, ...]]:
    prefix = column_prefix or "d"
    column = f"{prefix}.filial_id"
    codigo_column = f"{prefix}.codigo_filial"
    instancia_column = f"{prefix}.instancia_id"
    todas_sql = (
        f"EXISTS ("
        f"SELECT 1 FROM transformometro.processo_instancias pi_tf "
        f"WHERE pi_tf.instancia_id = {instancia_column} "
        f"AND pi_tf.todas_filiais_ativas = TRUE "
        f"AND pi_tf.deletado = FALSE)"
    )
    if is_uuid(filial_ref):
        return (f"({column} = %s::uuid OR {todas_sql})", (filial_ref,))
    return (f"({codigo_column} = %s OR {todas_sql})", (filial_ref,))


def setor_filter_sql(column_prefix: str, setor_ref: str) -> tuple[str, tuple[Any, ...]]:
    prefix = column_prefix or "d"
    column = f"{prefix}.setor_id"
    codigo_column = f"{prefix}.codigo_setor"
    instancia_column = f"{prefix}.instancia_id"
    junction_sql = (
        f"EXISTS ("
        f"SELECT 1 FROM transformometro.processo_instancia_setores pis "
        f"JOIN transformometro.setores s ON s.setor_id = pis.setor_id "
        f"WHERE pis.instancia_id = {instancia_column} "
        f"AND s.deletado = FALSE "
    )
    if is_uuid(setor_ref):
        junction_sql += f"AND pis.setor_id = %s::uuid)"
        direct = f"{column} = %s::uuid"
        return (f"({direct} OR {junction_sql})", (setor_ref, setor_ref))
    junction_sql += f"AND s.codigo_setor = %s)"
    direct = f"{codigo_column} = %s"
    return (f"({direct} OR {junction_sql})", (setor_ref, setor_ref))
