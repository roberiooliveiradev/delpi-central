from __future__ import annotations

from typing import Any, Mapping

SCOPE_EMPRESA = "empresa"
SCOPE_FILIAL = "filial"
SCOPE_SETOR = "setor"
VALID_ESCOPOS = (SCOPE_EMPRESA, SCOPE_FILIAL, SCOPE_SETOR)


def normalize_escopo_recurso(value: str) -> str:
    escopo = (value or SCOPE_EMPRESA).strip().lower()
    if escopo not in VALID_ESCOPOS:
        raise ValueError(
            f"escopo_recurso inválido: {value}. Use: {', '.join(VALID_ESCOPOS)}."
        )
    return escopo


def _setor_keys(instancia: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    setores = instancia.get("setores") or []
    if isinstance(setores, list):
        for item in setores:
            if not isinstance(item, dict):
                continue
            for field in ("setor_id", "codigo_setor"):
                value = str(item.get(field) or "").strip().lower()
                if value:
                    keys.add(value)
    for field in ("setor_id", "codigo_setor"):
        value = str(instancia.get(field) or "").strip().lower()
        if value:
            keys.add(value)
    return keys


def resolve_instancia_anchor(
    revisao_id: str,
    *,
    revisoes_by_id: Mapping[str, dict],
    instancias_by_id: Mapping[str, dict],
    processos_by_id: Mapping[str, dict],
) -> dict[str, Any] | None:
    revisao = revisoes_by_id.get(str(revisao_id))
    if not revisao:
        return None

    instancia_id = revisao.get("instancia_id")
    if instancia_id:
        instancia = instancias_by_id.get(str(instancia_id))
        if instancia:
            setores = instancia.get("setores") or []
            first = setores[0] if setores else {}
            return {
                "filial_id": instancia.get("filial_id"),
                "setor_id": first.get("setor_id") if isinstance(first, dict) else instancia.get("setor_id"),
                "codigo_filial": instancia.get("codigo_filial"),
                "codigo_setor": first.get("codigo_setor") if isinstance(first, dict) else instancia.get("codigo_setor"),
                "todas_filiais_ativas": bool(instancia.get("todas_filiais_ativas")),
                "setores": setores,
            }

    processo = processos_by_id.get(str(revisao.get("processo_id") or ""))
    if not processo:
        return None

    return {
        "filial_id": processo.get("filial_id"),
        "setor_id": processo.get("setor_id"),
        "codigo_filial": processo.get("filial_id"),
        "codigo_setor": processo.get("setor_id"),
        "todas_filiais_ativas": False,
        "setores": [],
    }


def _same_filial(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get("todas_filiais_ativas") or right.get("todas_filiais_ativas"):
        return True
    if left.get("filial_id") and right.get("filial_id"):
        return str(left["filial_id"]) == str(right["filial_id"])
    return str(left.get("codigo_filial") or "") == str(right.get("codigo_filial") or "")


def _share_setor(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_keys = _setor_keys(left)
    right_keys = _setor_keys(right)
    if left_keys and right_keys:
        return bool(left_keys & right_keys)
    return str(left.get("codigo_setor") or "") == str(right.get("codigo_setor") or "")


def filter_rateio_pool(
    resource: dict,
    links: list[dict],
    *,
    anchor_revisao_id: str,
    revisoes_by_id: Mapping[str, dict],
    instancias_by_id: Mapping[str, dict],
    processos_by_id: Mapping[str, dict],
) -> list[dict]:
    escopo = normalize_escopo_recurso(str(resource.get("escopo_recurso") or SCOPE_EMPRESA))
    if escopo == SCOPE_EMPRESA:
        return links

    anchor = resolve_instancia_anchor(
        anchor_revisao_id,
        revisoes_by_id=revisoes_by_id,
        instancias_by_id=instancias_by_id,
        processos_by_id=processos_by_id,
    )
    if not anchor:
        return links

    scoped: list[dict] = []
    for link in links:
        revisao_id = str(link.get("revisao_id") or "")
        if not revisao_id:
            continue
        instancia = resolve_instancia_anchor(
            revisao_id,
            revisoes_by_id=revisoes_by_id,
            instancias_by_id=instancias_by_id,
            processos_by_id=processos_by_id,
        )
        if not instancia:
            continue
        if escopo == SCOPE_FILIAL and _same_filial(anchor, instancia):
            scoped.append(link)
        elif escopo == SCOPE_SETOR and _same_filial(anchor, instancia) and _share_setor(anchor, instancia):
            scoped.append(link)

    return scoped
