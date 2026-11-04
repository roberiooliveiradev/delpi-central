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

import re
from typing import Any

_CODE_IN_TEXT_RE = re.compile(r"\d{8,11}")
_CODE_PREFIX_TYPES = {"5": "PI", "1": "MP", "9": "PA"}
_STATUS_DIVERGENT = "DIVERGENCES_CANDIDATES"
_STATUS_MATCH = "NO_DIVERGENCE_DETECTED"
_STATUS_INCONCLUSIVE = "INCONCLUSIVE"


def _infer_item_type(code: str) -> str:
    return _CODE_PREFIX_TYPES.get((code or "")[:1], "UNKNOWN")


def _norm_code(raw: Any) -> str:
    return "".join(ch for ch in str(raw or "") if ch.isdigit())


def _row_codes(row: dict[str, Any]) -> list[str]:
    """Códigos por linha — união das superfícies textuais da linha.

    OCR pode fundir códigos num mesmo campo ou deixar o código em uma
    coluna não tipada (ex.: coluna ``item`` com ``"a 1 10020033"``).
    Extrai tokens 8–11 dígitos de células tipadas, de todas as células
    e dos campos tipados da linha — nunca inventa valores."""
    texts: list[str] = [
        str(c.get("text") or "")
        for c in (row.get("cells") or [])
        if c.get("col_type") == "component_code"
    ]
    texts += [
        str(c.get("text") or "")
        for c in (row.get("cells") or [])
        if c.get("col_type") != "component_code"
    ]
    for f in (row.get("fields") or {}).values():
        texts.append(str(f.get("raw_text") or ""))
        texts.append(str(f.get("normalized_value") or ""))
    texts.append(str(row.get("component_code") or ""))
    seen: set[str] = set()
    codes: list[str] = []
    for text in texts:
        for code in _CODE_IN_TEXT_RE.findall(text):
            if code not in seen:
                seen.add(code)
                codes.append(code)
    return codes


# Regiões cujo conteúdo textual nunca comprova presença estrutural
# vigente (RQ-VAL-027 R3): histórico de revisão, notas e carimbo.
# Alinhado a ``drawing_investigation._NON_COMPONENT_REGIONS`` + notes.
_NON_COMPARABLE_REGIONS = {"revision_history", "notes", "title_block"}


def _code_region_index(
    code_contexts: list[dict] | None,
) -> dict[str, dict[str, Any]]:
    """code → {regions:set, pages:set} a partir de code_contexts."""
    idx: dict[str, dict[str, Any]] = {}
    for c in code_contexts or []:
        code = _norm_code(c.get("code"))
        if not code:
            continue
        e = idx.setdefault(code, {"regions": set(), "pages": set()})
        e["regions"].add(c.get("region") or "unknown")
        if c.get("page") is not None:
            e["pages"].add(int(c["page"]))
    return idx


def _row_page(row: dict[str, Any]) -> int | None:
    if row.get("page") is not None:
        return int(row["page"])
    for cell in row.get("cells") or []:
        if cell.get("page") is not None:
            return int(cell["page"])
    return None


def _drawing_occurrences(
    component_table: dict | None,
    product_code: str,
    tokens: list[dict] | None = None,
    code_contexts: list[dict] | None = None,
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    """Extrai ocorrências tipadas das linhas da ``component_table``.

    Regra de hierarquia (RQ-VAL-028): quando a tabela possui coluna de
    conjuntos tipada (≥2 colunas de código), códigos nela são âncoras
    explícitas de nível raiz; códigos nas demais colunas associam-se ao
    conjunto ativo (mesma linha = ``set_member``, célula mesclada/
    continuação = ``set_span``). Sem coluna de conjuntos, vale o
    fallback vigente: PI/PA abre grupo (``set_anchor`` raiz),
    ``row_group`` por âncora única na linha, ``pi_group_inference`` por
    carry-over. ``set_span`` é verificado para matching mas nunca
    promovido a divergência — célula vazia pode não ser continuação.
    Retorna ``(occurrences, limitations, contextual_codes)``."""
    rows = (component_table or {}).get("rows") or []
    table_is_candidate = bool((component_table or {}).get("candidate"))
    occurrences: list[dict[str, Any]] = []
    limitations: list[str] = []
    contextual_codes: list[dict[str, Any]] = []
    current_parent: str | None = None
    set_anchor_by_page: dict[int, str | None] = {}
    region_idx = _code_region_index(code_contexts)
    last_page: int | None = None
    for row in rows:
        codes = [c for c in _row_codes(row) if c != product_code]
        # Coluna de cada código na linha (evidência tabular real).
        code_cols: dict[str, set[int]] = {}
        for cell in row.get("cells") or []:
            col_i = cell.get("col")
            if col_i is None:
                continue
            for c in _CODE_IN_TEXT_RE.findall(str(cell.get("text") or "")):
                if c != product_code:
                    code_cols.setdefault(c, set()).add(int(col_i))
        row_col_types = row.get("col_types") or (
            component_table or {}
        ).get("col_types") or {}
        if row_col_types and all(
            isinstance(v, dict) for v in row_col_types.values()
        ):
            row_col_types = row_col_types.get(
                str(_row_page(row)), {}
            ) or {}
        code_typed_cols = sorted(
            int(k)
            for k, v in row_col_types.items()
            if v == "component_code" and str(k).lstrip("-").isdigit()
        )
        set_col = code_typed_cols[0] if len(code_typed_cols) >= 2 else None
        page = _row_page(row)
        if page != last_page:
            current_parent = None
            last_page = page
        set_codes = (
            sorted(
                c for c in codes
                if set_col is not None
                and set_col in (code_cols.get(c) or set())
            )
            if set_col is not None
            else []
        )
        if len(set_codes) == 1:
            set_anchor_by_page[page] = set_codes[0]
        elif len(set_codes) > 1:
            set_anchor_by_page[page] = None
        current_set = set_anchor_by_page.get(page)
        # Âncoras da linha: códigos PI/PA presentes na MESMA linha —
        # evidência geométrica real de agrupamento. Uma âncora única
        # verifica a associação dos demais códigos da linha; mais de
        # uma torna a associação ambígua (não inventa relação).
        row_anchors = [
            c for c in codes if _infer_item_type(c) in {"PI", "PA"}
        ]
        for code in codes:
            item_type = _infer_item_type(code)
            cols = code_cols.get(code) or set()
            other_anchors = [a for a in row_anchors if a != code]
            if set_col is not None and code in set_codes:
                # Código na coluna de conjuntos de tabela multi-coluna:
                # é PAI dos itens da linha — seu próprio pai não é
                # determinado por esta tabela. Nunca âncora de raiz
                # (RQ-VAL-028 R5: não inventar relação com a raiz).
                current_parent = code
                parent = None
                parent_source = "set_parent"
                verified = False
            elif set_col is not None and current_set:
                parent = current_set
                parent_source = (
                    "set_member" if set_codes else "set_span"
                )
                verified = True
            elif item_type in {"PI", "PA"} and set_col is None:
                current_parent = code
                parent = product_code
                parent_source = "set_anchor"
                verified = True
            elif item_type in {"PI", "PA"}:
                # multi-coluna: PI/PA fora da coluna de conjuntos e sem
                # conjunto ativo — pai indeterminado, não raiz fabricada
                current_parent = code
                parent = None
                parent_source = None
                verified = False
            elif len(other_anchors) == 1:
                parent = other_anchors[0]
                parent_source = "row_group"
                verified = True
            elif len(other_anchors) > 1:
                parent = None
                parent_source = None
                verified = False
            elif current_parent:
                parent = current_parent
                parent_source = "pi_group_inference"
                verified = False
            else:
                parent = None
                parent_source = None
                verified = False
            mentions = sorted(
                r
                for r in (region_idx.get(code) or {}).get("regions", set())
                if r in _NON_COMPARABLE_REGIONS
            )
            occurrences.append(
                {
                    "item_code": code,
                    "item_type": item_type,
                    "item_description": row.get("description"),
                    "parent_code": parent,
                    "parent_verified": verified,
                    "parent_source": parent_source,
                    "extraction_source": "typed_table_cell",
                    "flaggable": True,
                    "quantity": row.get("quantity"),
                    "y_px": row.get("y_px"),
                    "row": row.get("row"),
                    "page": page,
                    "region": "component_table",
                    "also_mentioned_in_regions": mentions or None,
                    "cells": row.get("cells") or [],
                }
            )
    if any(o["parent_code"] is None for o in occurrences):
        limitations.append(
            "parent_relation_unverified: parte das linhas sem grupo "
            "PI/PA identificado — correspondência por código apenas."
        )
    # Presença residual: códigos visíveis no documento fora das linhas
    # tipadas (ex.: tabela detectada mas células não segmentadas).
    # Conta como evidência de presença — nunca como DRAWING_ONLY, pois
    # sem linha não se comprova que é item da tabela de componentes.
    # RQ-VAL-027: código cuja ÚNICA menção está em revision_history/
    # notes/title_block é evidência contextual — registrado separado,
    # não participa da comparação vigente (não consome BOM).
    typed = {o["item_code"] for o in occurrences}
    residual = 0
    if table_is_candidate:
        pool = (
            set(region_idx)
            if code_contexts is not None
            else _token_code_set(tokens)
        )
        for code in sorted(pool - typed):
            if code == product_code:
                continue
            ctx = region_idx.get(code)
            regions = (ctx or {}).get("regions") or set()
            if (
                code_contexts is not None
                and regions
                and regions <= _NON_COMPARABLE_REGIONS
            ):
                contextual_codes.append(
                    {
                        "code": code,
                        "regions": sorted(regions),
                        "pages": sorted((ctx or {}).get("pages") or []),
                    }
                )
                continue
            occurrences.append(
                {
                    "item_code": code,
                    "item_type": _infer_item_type(code),
                    "item_description": None,
                    "parent_code": None,
                    "parent_verified": False,
                    "parent_source": None,
                    "extraction_source": "code_token",
                    "flaggable": False,
                    "quantity": None,
                    "y_px": None,
                    "row": None,
                    "cells": [],
                }
            )
            residual += 1
    if residual:
        limitations.append(
            f"presence_by_token_only: {residual} código(s) visíveis "
            "fora das linhas tipadas — presença conta, relação não."
        )
    if contextual_codes:
        limitations.append(
            "contextual_code_mentions: código(s) citados apenas em "
            "regiões não comparáveis (histórico/notas/carimbo) — "
            "evidência contextual preservada, não presença estrutural: "
            + ", ".join(
                f"{c['code']}@{'/'.join(c['regions'])}"
                for c in contextual_codes
            )
        )
    return occurrences, limitations, contextual_codes


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
    code_contexts: list[dict] | None = None,
    page_coverage: dict | None = None,
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
    drawing_occ, ext_limitations, contextual_codes = _drawing_occurrences(
        component_table, product_code, tokens, code_contexts
    )
    limitations.extend(ext_limitations)
    table_meta = component_table or {}
    _ctx_regions = _code_region_index(code_contexts)
    if code_contexts is not None:
        # Código com menção apenas em região não comparável NÃO conta
        # como presença visual vigente (RQ-VAL-027 R3/R5).
        visible_codes = {
            c
            for c, ctx in _ctx_regions.items()
            if not (ctx["regions"] <= _NON_COMPARABLE_REGIONS)
        }
    else:
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

    # Cobertura integral exige tabela confiável E todas as páginas do
    # documento processadas E evidência não truncada (RQ-VAL-029):
    # página não lida ou tokens descartados por sampling podem conter
    # outra tabela — conclusão parcial nunca é integral.
    _pc = page_coverage or {}
    _total = _pc.get("pdf_page_count") or drawing_pages
    _attempted = set(_pc.get("pages_attempted") or [])
    _missing = sorted(
        p for p in range(1, _total + 1) if p not in _attempted
    ) if (_pc and _total) else list(
        _pc.get("pages_not_processed") or []
    )
    pages_missing = sorted(
        set(_missing)
        | set(_pc.get("pages_not_processed") or [])
        | {
            f.get("page")
            for f in _pc.get("pages_failed") or []
            if f.get("page") is not None
        }
    )
    evidence_truncated = bool(_pc.get("token_sample_truncated"))
    coverage_complete = bool(
        table_meta.get("candidate")
        and not table_meta.get("unreliable_boundary")
        and not pages_missing
        and not evidence_truncated
    )

    # ---------- matching por ocorrência -------------------------------------
    bom_remaining: dict[str, list[dict[str, Any]]] = {
        c: list(o) for c, o in bom_by_code.items()
    }
    matched = 0
    drawing_only_parents: set[str] = set()
    occurrence_excess: list[str] = []
    unverified_relations: list[str] = []
    unprovenanced: list[str] = []

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
            if not occ.get("flaggable"):
                continue
            # Código existe na BOM mas todas as ocorrências já foram
            # consumidas — excesso de multiplicidade, não ausência.
            # Pode ser duplicata OCR (célula fundida) ou ocorrência
            # extra real: candidato a revisão, não prova de divergência.
            if code in bom_by_code:
                occurrence_excess.append(code)
                continue
            page = _occurrence_page(occ, tokens)
            if page is None:
                # RQ-VAL-027 R7: finding estrutural exige proveniência
                # verificável — sem página/região comprovada degrada a
                # candidato não promovido, nunca DRAWING_ONLY.
                unprovenanced.append(code)
                continue
            evidence = {
                "drawing_page": page,
                "drawing_region": "component_table",
                "drawing_row": occ.get("row"),
                "drawing_y_px": occ.get("y_px"),
                "bom_relationship": "ABSENT_IN_CURRENT_STRUCTURE",
            }
            if occ.get("also_mentioned_in_regions"):
                evidence["also_mentioned_in_regions"] = occ[
                    "also_mentioned_in_regions"
                ]
            findings.append(
                _finding(
                    type="DRAWING_ONLY",
                    item_code=code,
                    item_type=occ["item_type"],
                    item_description=occ.get("item_description"),
                    parent_code=occ.get("parent_code") or product_code,
                    level=1 if occ["item_type"] in {"PI", "PA"} else None,
                    evidence=evidence,
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
        # Divergência de relação só quando o pai do desenho é
        # VERIFICADO por evidência real (não heurística de grupo).
        # Pai inferido por agrupamento ou por continuação de conjunto
        # (célula mesclada) registra-se como relação não verificada —
        # nunca promovido a divergência comprovada (RQ-VAL-028 R6/R7).
        if (
            occ.get("parent_source")
            in ("pi_group_inference", "row_group", "set_member", "set_span")
            and chosen.get("parent_code") != occ["parent_code"]
            and not same_parent
            and all(
                o.get("parent_code") != occ["parent_code"]
                for o in bom_by_code[code]
            )
        ):
            unverified_relations.append(
                f"{code}@drawing:{occ['parent_code']}≠bom:{chosen.get('parent_code')}"
            )
        # Só set_anchor (código tipado como item de nível raiz na
        # coluna de conjuntos) é elegível — row_group usa a linha
        # extraída, que pode fundir linhas visuais de grupos distintos;
        # esses casos viram unverified_relations, nunca finding.
        if (
            occ["parent_verified"]
            and occ.get("parent_source") == "set_anchor"
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
                        "parent_source": occ.get("parent_source"),
                    },
                    confidence={
                        "row_group": "row_associated",
                        "set_anchor": "column_anchor",
                    }.get(occ.get("parent_source"), "inferred_parent"),
                    explanation=(
                        f"O item {code} aparece no desenho sob "
                        f"{occ['parent_code']} (associação inferida "
                        "por agrupamento), mas a BOM vigente o "
                        "associa a outro(s) conjunto(s) — candidato "
                        "a verificação, não fato."
                    ),
                )
            )

    # ---------- reconciliação por similaridade OCR ---------------------------
    # Par espelho: um código mal-lido pelo OCR gera DRAWING_ONLY do
    # falso + BOM_ONLY do verdadeiro. Se um código só-no-desenho difere
    # por ≤2 dígitos de um código só-na-BOM (mesmo comprimento), ambos
    # são ambiguidade de extração — não divergência comprovada.
    def _near_code(a: str, b: str) -> bool:
        if len(a) != len(b) or not a or not b:
            return False
        # distância 1: famílias de códigos com prefixo comum colidem
        # com distância 2 — restrito a um dígito para não ocultar
        # divergências reais (candidatos demais → FN).
        return sum(x != y for x, y in zip(a, b)) <= 1

    bom_only_codes = set(bom_remaining)
    ambiguous_pairs: list[tuple[str, str]] = []
    drawing_only_finds = [
        f for f in findings if f["type"] == "DRAWING_ONLY"
    ]
    for f in drawing_only_finds:
        d_code = f["item_code"]
        for b_code in sorted(bom_only_codes):
            if _near_code(d_code, b_code):
                ambiguous_pairs.append((d_code, b_code))
                break
    if ambiguous_pairs:
        ambiguous_d = {p[0] for p in ambiguous_pairs}
        ambiguous_b = {p[1] for p in ambiguous_pairs}
        findings = [
            f for f in findings
            if not (f["type"] == "DRAWING_ONLY"
                    and f["item_code"] in ambiguous_d)
        ]
        for code, occs in list(bom_remaining.items()):
            if code in ambiguous_b:
                bom_remaining.pop(code)
                bom_by_code.pop(code, None)
        limitations.append(
            "ocr_ambiguous_code: pares visualmente similares entre "
            "desenho e BOM tratados como ambiguidade de extração, não "
            f"divergência: "
            + ", ".join(f"{d}≈{b}" for d, b in ambiguous_pairs)
        )

    # ---------- BOM_ONLY só com cobertura suficiente -------------------------
    # Ausência no desenho exige escopo integralmente lido: tabela
    # detectada + boundary confiável + rendimento de matching alto o
    # bastante para que a ausência seja provável (parcial não prova).
    visible_bom = sum(
        len(occs)
        for code, occs in bom_remaining.items()
        if code in visible_codes
    )
    accounted_ratio = (
        (matched + visible_bom) / max(1, len(bom_occurrences))
    )
    bom_only_allowed = coverage_complete and accounted_ratio >= 0.6
    bom_only_unverified = 0
    unclassified: list[str] = []
    for code, occs in bom_remaining.items():
        if not bom_only_allowed:
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
    if occurrence_excess:
        limitations.append(
            f"occurrence_excess: {sorted(set(occurrence_excess))} — "
            "código(s) com mais ocorrências extraídas no desenho do "
            "que na BOM; possível duplicata OCR ou ocorrência extra "
            "real — candidato a revisão, não divergência comprovada."
        )
    if unverified_relations:
        limitations.append(
            "unverified_parent_relations: associação pai-filho "
            "inferida diverge da BOM — evidência, não fato: "
            + ", ".join(unverified_relations)
        )
    if unprovenanced:
        limitations.append(
            "unprovenanced_drawing_occurrence: código(s) extraído(s) "
            "sem página/região comprovável — degradado a inconclusivo, "
            f"não DRAWING_ONLY: {sorted(unprovenanced)}"
        )
    if pages_missing:
        limitations.append(
            "pages_not_processed: página(s) do documento sem cobertura "
            f"OCR efetiva: {pages_missing} — ausência em página não "
            "lida nunca é ausência comprovada."
        )
    if evidence_truncated:
        limitations.append(
            "evidence_truncated: amostra de tokens OCR atingiu o limite "
            "operacional — parte do documento sem evidência; ausência "
            "não comprovada."
        )

    # ---------- quantidades — sem contrato de conversão ---------------------
    limitations.append(
        "quantitative_comparison: INCONCLUSIVE — sem regra oficial de "
        "unidade/base de consumo/conversão; quantidades não comparadas."
    )

    # ---------- status agregado ----------------------------------------------
    unverified_typed = sum(
        1
        for o in drawing_occ
        if o.get("extraction_source") == "typed_table_cell"
        and not o["parent_verified"]
    )
    token_only = sum(
        1
        for o in drawing_occ
        if o.get("extraction_source") == "code_token"
    )
    verification_gaps = (
        bom_only_unverified
        + len(unclassified)
        + unverified_typed
        + token_only
        + len(unprovenanced)
        + len(pages_missing)
        + (1 if evidence_truncated else 0)
        + (0 if coverage_complete else 1)
    )
    if findings:
        status = _STATUS_DIVERGENT
    elif verification_gaps:
        status = _STATUS_INCONCLUSIVE
    else:
        status = _STATUS_MATCH

    analyzed_pages = sorted(
        {int(t.get("page") or 1) for t in tokens or []}
    )
    tables_by_page = table_meta.get("tables_by_page") or []
    tables_identified = sum(
        1 for t in tables_by_page if t.get("candidate")
    )
    tables_verified = sum(
        1
        for t in tables_by_page
        if t.get("candidate") and not t.get("unreliable_boundary")
    )
    coverage = {
        "bom_available": True,
        "drawing_pages": drawing_pages,
        "analyzed_pages": analyzed_pages or None,
        "component_table_detected": bool(table_meta.get("candidate")),
        "component_table_rows": table_meta.get("row_count"),
        "component_table_codes": table_meta.get("code_count"),
        "unreliable_boundary": bool(
            table_meta.get("unreliable_boundary")
        ),
        "complete_for_requested_scope": coverage_complete
        and not verification_gaps,
        "unverified_parent_occurrences": unverified_typed,
        "token_only_occurrences": token_only,
        "contextual_code_mentions": len(contextual_codes),
    }
    if page_coverage:
        coverage.update(
            {
                "pdf_page_count": page_coverage.get("pdf_page_count"),
                "pages_ocr_ok": page_coverage.get("pages_ocr_ok"),
                "pages_failed": page_coverage.get("pages_failed"),
                "pages_not_processed": pages_missing or None,
                "pages_attempted": page_coverage.get("pages_attempted"),
                "token_sample_truncated": page_coverage.get(
                    "token_sample_truncated"
                ),
            }
        )
    if tables_by_page:
        coverage["tables_identified"] = tables_identified
        coverage["tables_verified"] = tables_verified
        coverage["tables_by_page"] = [
            {k: v for k, v in t.items() if k != "col_types"}
            for t in tables_by_page
        ]
    return {
        "status": status,
        "coverage": coverage,
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
            "occurrence_excess": len(set(occurrence_excess)),
            "unverified_parent_relations": len(unverified_relations),
            "unprovenanced_occurrences": len(unprovenanced),
            "contextual_codes": len(contextual_codes),
            "ocr_ambiguous_pairs": len(ambiguous_pairs),
            "divergences": len(findings),
        },
        "contextual_codes": contextual_codes,
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
