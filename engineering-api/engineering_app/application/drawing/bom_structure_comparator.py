"""Comparador determinístico desenho × BOM vigente (DEC-VAL-022 §18).

Módulo PURO — sem HTTP, DB, SDK de LLM ou MCP. Recebe as ocorrências
já extraídas do desenho (``component_table.rows`` de
``drawing_understanding.v1``, com células tipadas por
``col_type=component_code``) e as ocorrências oficiais achatadas da BOM
(``flatten_bom_occurrences``), e produz a seção
``bom_structure_comparison`` tipada:

- ``DRAWING_ONLY``: ocorrência comprovadamente presente na tabela do
  desenho sem relação correspondente na BOM vigente.
- ``BOM_ONLY``: ocorrência cadastrada ausente do desenho — SOMENTE com
  cobertura visual completa; ausência de OCR nunca prova ausência.
- ``PARENT_RELATION_MISMATCH``: mesmo código em ambos os lados com
  associação pai-filho verificada e divergente.
- Quantidades: nunca comparadas sem regra oficial de unidade/conversão —
  aspecto declarado ``INCONCLUSIVE`` via limitation.
- ``INCONCLUSIVE`` quando a cobertura não permite decidir.
Todo finding é candidato — ``review_status=PENDING_HUMAN_REVIEW``;
a Engenharia permanece autoridade de aprovação e NC.
"""

from __future__ import annotations

from typing import Any

_CODE_PREFIX_TYPES = {"5": "PI", "1": "MP", "9": "PA"}
_STATUS_DIVERGENT = "DIVERGENCES_CANDIDATES"
_STATUS_MATCH = "NO_DIVERGENCE_DETECTED"
_STATUS_INCONCLUSIVE = "INCONCLUSIVE"


def _infer_item_type(code: str) -> str:
    return _CODE_PREFIX_TYPES.get((code or "")[:1], "UNKNOWN")


def _norm_code(raw: Any) -> str:
    return "".join(ch for ch in str(raw or "") if ch.isdigit())


def _drawing_occurrences(
    component_table: dict | None, product_code: str
) -> tuple[list[dict[str, Any]], list[str]]:
    """Extrai ocorrências tipadas das linhas da ``component_table``.

    Regra de hierarquia: uma linha cujo código infere ``PI`` abre um
    grupo — linhas subsequentes associam-se a ela como pai até o
    próximo código ``PI``/``PA``. Quando nenhum grupo foi aberto,
    ``parent_code=None`` e a associação é declarada não verificada.
    Retorna ``(occurrences, limitations)``."""
    rows = (component_table or {}).get("rows") or []
    occurrences: list[dict[str, Any]] = []
    limitations: list[str] = []
    current_parent: str | None = None
    for row in rows:
        code = _norm_code(row.get("component_code"))
        if not code or code == product_code:
            continue
        item_type = _infer_item_type(code)
        if item_type in {"PI", "PA"}:
            current_parent = code
            parent = product_code
        elif current_parent:
            parent = current_parent
        else:
            parent = None
        occurrences.append(
            {
                "item_code": code,
                "item_type": item_type,
                "item_description": row.get("description"),
                "parent_code": parent,
                "parent_verified": parent is not None,
                "quantity": row.get("quantity"),
                "y_px": row.get("y_px"),
                "row": row.get("row"),
                "cells": row.get("cells") or [],
            }
        )
    if any(o["parent_code"] is None for o in occurrences):
        limitations.append(
            "parent_relation_unverified: parte das linhas sem grupo "
            "PI/PA identificado — correspondência por código apenas."
        )
    return occurrences, limitations


def _token_code_set(tokens: list[dict] | None) -> set[str]:
    codes: set[str] = set()
    for t in tokens or []:
        text = str(t.get("normalized_text") or t.get("text") or "")
        code = _norm_code(text)
        if len(code) >= 6:
            codes.add(code)
    return codes


def compare_bom_to_drawing(
    *,
    product_code: str,
    bom_occurrences: list[dict[str, Any]] | None,
    component_table: dict | None,
    tokens: list[dict] | None = None,
    drawing_pages: int | None = None,
    bom_error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Diff bidirecional por ocorrência estrutural.

    ``bom_occurrences=None`` ⇒ BOM indisponível → INCONCLUSIVE.
    ``component_table=None``/sem códigos ⇒ desenho não lido → INCONCLUSIVE
    no lado do desenho (sem falsa aprovação nem falso BOM_ONLY)."""
    findings: list[dict[str, Any]] = []
    limitations: list[str] = []
    fid = 0

    def _finding(**kw: Any) -> dict[str, Any]:
        nonlocal fid
        fid += 1
        f = {
            "id": f"D-{fid:03d}",
            "review_status": "PENDING_HUMAN_REVIEW",
            "method": "deterministic_occurrence_diff",
            "confidence": "rule_based",
        }
        f.update(kw)
        return f

    # ---------- lado BOM ----------------------------------------------------
    if bom_occurrences is None:
        limitations.append(
            f"bom_unavailable: {bom_error or 'estrutura não obtida'} — "
            "comparação estrutural não executada."
        )
        return {
            "status": _STATUS_INCONCLUSIVE,
            "coverage": {"bom_available": False},
            "counts": {},
            "findings": [],
            "limitations": limitations,
        }

    bom_by_code: dict[str, list[dict[str, Any]]] = {}
    for occ in bom_occurrences:
        code = _norm_code(occ.get("component_code"))
        if code:
            bom_by_code.setdefault(code, []).append(occ)

    # ---------- lado desenho -------------------------------------------------
    drawing_occ, ext_limitations = _drawing_occurrences(
        component_table, product_code
    )
    limitations.extend(ext_limitations)
    table_meta = component_table or {}
    visible_codes = _token_code_set(tokens)

    if not drawing_occ:
        limitations.append(
            "drawing_table_unread: tabela de componentes não "
            "reconhecida ou sem códigos tipados — presença no desenho "
            "não pode ser afirmada nem negada."
        )
        return {
            "status": _STATUS_INCONCLUSIVE,
            "coverage": {
                "bom_available": True,
                "component_table_detected": bool(
                    table_meta.get("candidate")
                ),
                "drawing_occurrences_recognized": 0,
            },
            "counts": {"bom_occurrences": len(bom_occurrences)},
            "findings": [],
            "limitations": limitations,
        }

    coverage_complete = bool(
        table_meta.get("candidate")
        and not table_meta.get("unreliable_boundary")
    )

    # ---------- matching por ocorrência -------------------------------------
    bom_remaining: dict[str, list[dict[str, Any]]] = {
        c: list(o) for c, o in bom_by_code.items()
    }
    matched = 0
    drawing_only_parents: set[str] = set()

    # Passe 0: pais ausentes primeiro — necessário para guardar os
    # filhos órfãos antes dos passes de matching.
    for occ in drawing_occ:
        code = occ["item_code"]
        if code not in bom_by_code and occ["item_type"] in {"PI", "PA"}:
            drawing_only_parents.add(code)

    # Passe 1: matches exatos (code + parent verificado).
    for occ in drawing_occ:
        candidates = bom_remaining.get(occ["item_code"])
        if not candidates or not occ["parent_verified"]:
            continue
        same_parent = [
            o for o in candidates
            if o.get("parent_code") == occ["parent_code"]
        ]
        if same_parent:
            chosen = same_parent[0]
            candidates.remove(chosen)
            if not candidates:
                bom_remaining.pop(occ["item_code"])
            matched += 1
            occ["_matched"] = True

    # Passe 2: matches por código para ocorrências restantes.
    for occ in drawing_occ:
        if occ.get("_matched"):
            continue
        code = occ["item_code"]
        candidates = bom_remaining.get(code)
        if not candidates:
            page = _occurrence_page(occ, tokens)
            findings.append(
                _finding(
                    type="DRAWING_ONLY",
                    item_code=code,
                    item_type=occ["item_type"],
                    item_description=occ.get("item_description"),
                    parent_code=occ.get("parent_code") or product_code,
                    level=1 if occ["item_type"] in {"PI", "PA"} else None,
                    evidence={
                        "drawing_page": page,
                        "drawing_region": "component_table",
                        "drawing_row": occ.get("row"),
                        "drawing_y_px": occ.get("y_px"),
                        "bom_relationship": "ABSENT_IN_CURRENT_STRUCTURE",
                    },
                    explanation=(
                        f"O item {code} consta na tabela do desenho "
                        "oficial, mas não possui ocorrência na "
                        "estrutura vigente."
                    ),
                )
            )
            continue
        # Mesma ocorrência por código+pai quando ambos verificados.
        same_parent = [
            o for o in candidates
            if occ["parent_verified"] and o.get("parent_code") == occ["parent_code"]
        ]
        chosen = (same_parent or candidates)[0]
        candidates.remove(chosen)
        if not candidates:
            bom_remaining.pop(code)
        matched += 1
        if (
            occ["parent_verified"]
            and chosen.get("parent_code") != occ["parent_code"]
            and occ["parent_code"] not in drawing_only_parents
            and not same_parent
            and all(
                o.get("parent_code") != occ["parent_code"]
                for o in bom_by_code[code]
            )
        ):
            findings.append(
                _finding(
                    type="PARENT_RELATION_MISMATCH",
                    item_code=code,
                    item_type=occ["item_type"],
                    item_description=occ.get("item_description"),
                    parent_code=occ["parent_code"],
                    evidence={
                        "drawing_page": _occurrence_page(occ, tokens),
                        "drawing_region": "component_table",
                        "drawing_parent": occ["parent_code"],
                        "bom_parents": sorted(
                            {
                                o.get("parent_code")
                                for o in bom_by_code[code]
                                if o.get("parent_code")
                            }
                        ),
                        "bom_relationship": "PRESENT_UNDER_OTHER_PARENT",
                    },
                    explanation=(
                        f"O item {code} aparece no desenho sob "
                        f"{occ['parent_code']}, mas a BOM vigente o "
                        "associa a outro(s) conjunto(s)."
                    ),
                )
            )

    # ---------- BOM_ONLY só com cobertura completa ---------------------------
    bom_only_unverified = 0
    unclassified: list[str] = []
    for code, occs in bom_remaining.items():
        if not coverage_complete:
            bom_only_unverified += len(occs)
            continue
        if code in visible_codes:
            unclassified.append(code)
            continue
        for occ in occs:
            findings.append(
                _finding(
                    type="BOM_ONLY",
                    item_code=code,
                    item_type=occ.get("component_type")
                    or _infer_item_type(code),
                    parent_code=occ.get("parent_code"),
                    level=occ.get("depth"),
                    occurrence_path=occ.get("path"),
                    evidence={
                        "drawing_region": "component_table",
                        "drawing_relationship": "NOT_FOUND_WITH_FULL_COVERAGE",
                        "bom_occurrence": occ.get("occurrence_id"),
                        "bom_path": occ.get("path"),
                    },
                    explanation=(
                        f"O item {code} consta na estrutura vigente "
                        f"({occ.get('path') or occ.get('parent_code')}) "
                        "mas não foi localizado na tabela do desenho "
                        "oficial com cobertura completa."
                    ),
                )
            )
    if bom_only_unverified:
        limitations.append(
            f"bom_only_unverified: {bom_only_unverified} ocorrência(s) "
            "da BOM sem contraparte tipada, porém cobertura visual "
            "incompleta — ausência não declarada."
        )
    if unclassified:
        limitations.append(
            f"extracted_but_unclassified: {sorted(unclassified)} "
            "visíveis no documento fora das células tipadas."
        )

    # ---------- quantidades — sem contrato de conversão ---------------------
    limitations.append(
        "quantitative_comparison: INCONCLUSIVE — sem regra oficial de "
        "unidade/base de consumo/conversão; quantidades não comparadas."
    )

    # ---------- status agregado ----------------------------------------------
    if findings:
        status = _STATUS_DIVERGENT
    elif not coverage_complete or bom_only_unverified:
        status = _STATUS_INCONCLUSIVE
    else:
        status = _STATUS_MATCH

    analyzed_pages = sorted(
        {int(t.get("page") or 1) for t in tokens or []}
    )
    return {
        "status": status,
        "coverage": {
            "bom_available": True,
            "drawing_pages": drawing_pages,
            "analyzed_pages": analyzed_pages or None,
            "component_table_detected": bool(table_meta.get("candidate")),
            "component_table_rows": table_meta.get("row_count"),
            "component_table_codes": table_meta.get("code_count"),
            "unreliable_boundary": bool(
                table_meta.get("unreliable_boundary")
            ),
            "complete_for_requested_scope": coverage_complete,
        },
        "counts": {
            "drawing_occurrences": len(drawing_occ),
            "bom_occurrences": len(bom_occurrences),
            "matched_occurrences": matched,
            "drawing_only": sum(
                1 for f in findings if f["type"] == "DRAWING_ONLY"
            ),
            "bom_only": sum(
                1 for f in findings if f["type"] == "BOM_ONLY"
            ),
            "parent_relation_mismatches": sum(
                1 for f in findings
                if f["type"] == "PARENT_RELATION_MISMATCH"
            ),
            "bom_occurrences_unverified": bom_only_unverified,
            "divergences": len(findings),
        },
        "findings": findings,
        "limitations": limitations,
    }


def _occurrence_page(
    occ: dict[str, Any], tokens: list[dict] | None
) -> int | None:
    """Página da ocorrência via células/tokens (desenhos multipágina)."""
    for cell in occ.get("cells") or []:
        if cell.get("page"):
            return int(cell["page"])
    code = occ.get("item_code")
    for t in tokens or []:
        if _norm_code(t.get("normalized_text") or t.get("text")) == code:
            return int(t.get("page") or 1)
    return None


__all__ = ["compare_bom_to_drawing"]
