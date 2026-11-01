"""Drawing Understanding — camada de interpretação estrutural (R8).

Contrato ``drawing_understanding.v1``: consome evidência OCR existente
(tokens + bounding boxes em pixels, sistema de coordenadas explícito)
e produz candidatos estruturados — regiões, carimbo, revisão, tabela,
cotas, notas, ambiguidades — com provenance e estados honestos.

Determinístico e explicável: agrupamento por posição/alinhamento,
regras declaradas, zero ML. Nenhuma confiança técnica inventada:
``DIMENSION_TEXT_FOUND`` ≠ ``DIMENSION_ASSOCIATION_VERIFIED`` e
``OCR_TEXT_FOUND`` ≠ ``ENGINEERING_VALIDATED``.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

SCHEMA_VERSION = "drawing_understanding.v1"

# Status de associação (escopo fechado, honesto)
FIELD_STATES = frozenset(
    {
        "FIELD_IDENTIFIED",      # texto + região atribuídos com regra
        "FIELD_AMBIGUOUS",       # múltiplos candidatos igualmente plausíveis
        "TEXT_ONLY",             # texto achado, sem região/campo
        "NOT_FOUND",
        "NOT_COMPARABLE",
    }
)
DIMENSION_STATES = frozenset(
    {
        "DIMENSION_TEXT_FOUND",
        "DIMENSION_REGION_CANDIDATE",
        "DIMENSION_GEOMETRY_ASSOCIATION_CANDIDATE",
        # DIMENSION_ASSOCIATION_VERIFIED só por validação governada —
        # nunca emitido automaticamente.
    }
)
REGION_TYPES = frozenset(
    {
        "title_block", "component_table", "revision_history",
        "drawing_area", "notes", "dimension", "legend",
        "other", "unknown",
    }
)

_DIM_RE = re.compile(
    r"^~?\d{1,4}([.,]\d+)?(\s?[±+/-]\s?\d+([.,]\d+)?)?(\s?(mm|pol|in|[°º]))?$"
)
_REV_RE = re.compile(r"^(REV\.?|R)?\s?(\d{2}|[A-Z])$", re.IGNORECASE)
_CODE_RE = re.compile(r"^\d{6,11}(-\d+)?$")


def _norm(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _tok_center(token: dict) -> tuple[float, float] | None:
    box = token.get("bounding_box_px") or []
    if len(box) < 8:
        return None
    xs = [box[i] for i in range(0, 8, 2)]
    ys = [box[i] for i in range(1, 8, 2)]
    return (sum(xs) / 4.0, sum(ys) / 4.0)


def _page_size(tokens: Iterable[dict]) -> tuple[float, float]:
    maxx = maxy = 0.0
    for t in tokens:
        for p in _tok_center(t) or ():
            pass
        c = _tok_center(t)
        if c:
            maxx, maxy = max(maxx, c[0]), max(maxy, c[1])
    return (maxx or 1.0, maxy or 1.0)


def classify_region(cx: float, cy: float, w: float, h: float) -> str:
    """Região candidata por posição relativa (layout DELPI: carimbo
    inferior-direito; tabela de componentes acima do carimbo; histórico
    de revisão na faixa superior do carimbo; área de desenho à esquerda)."""
    fx, fy = cx / w, cy / h
    if fx >= 0.55 and fy >= 0.72:
        return "title_block"
    if fx >= 0.55 and fy >= 0.45:
        return "component_table"
    if fy < 0.10:
        return "revision_history"
    if fx < 0.45 and fy < 0.35:
        return "notes"
    return "drawing_area"


def _cluster_rows(tokens: list[dict], y_tol: float) -> list[list[dict]]:
    """Agrupa tokens em linhas por proximidade de centro-Y (determinístico)."""
    rows: list[list[dict]] = []
    for t in sorted(
        [t for t in tokens if _tok_center(t)],
        key=lambda t: _tok_center(t)[1],
    ):
        cy = _tok_center(t)[1]
        for row in rows:
            rc = [_tok_center(r)[1] for r in row]
            if abs(cy - (sum(rc) / len(rc))) <= y_tol:
                row.append(t)
                break
        else:
            rows.append([t])
    return rows


def _cluster_cols(tokens: list[dict], x_tol: float) -> list[float]:
    """Centros X candidatos de colunas por cluster de tokens."""
    centers = sorted(
        _tok_center(t)[0] for t in tokens if _tok_center(t)
    )
    cols: list[float] = []
    for x in centers:
        if not cols or abs(x - cols[-1]) > x_tol:
            cols.append(x)
        else:
            cols[-1] = (cols[-1] + x) / 2.0
    return cols


def build_understanding(
    tokens: list[dict],
    *,
    document_hash: str,
    page: int = 1,
    bom_codes: list[str] | None = None,
    bom_quantities: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Constrói candidatos estruturados a partir de tokens OCR.

    ``tokens`` itens com ``text``, ``bounding_box_px`` [x1,y1..x4,y4],
    ``confidence``, ``page``. Retorna ``drawing_understanding.v1``.
    """
    w, h = _page_size(tokens)
    annotated: list[dict] = []
    regions_seen: dict[str, int] = {}
    for idx, t in enumerate(tokens):
        text = _norm(
            str(
                t.get("normalized_text")
                or t.get("raw_text")
                or t.get("text")
                or ""
            )
        )
        c = _tok_center(t)
        region = classify_region(c[0], c[1], w, h) if c else "unknown"
        regions_seen[region] = regions_seen.get(region, 0) + 1
        annotated.append(
            {
                "index": idx,
                "text": text,
                "region": region,
                "center_px": [round(c[0], 1), round(c[1], 1)] if c else None,
                "bounding_box_px": t.get("bounding_box_px"),
                "confidence": t.get("confidence"),
                "page": t.get("page", page),
            }
        )

    # ---------- tabela de componentes ----------
    table_tokens = [
        a for a in annotated if a["region"] == "component_table"
    ]
    table_rows: list[dict] = []
    ambiguous_cells = 0
    if len(table_tokens) >= 4:
        y_tol = h * 0.015
        x_tol = w * 0.03
        for r_i, row in enumerate(_cluster_rows(table_tokens, y_tol)):
            cols = _cluster_cols(row, x_tol)
            cells = []
            for t in row:
                x = _tok_center(t)[0]
                best = min(cols, key=lambda c: abs(c - x))
                ties = [c for c in cols if abs(abs(c - x) - abs(best - x)) < 1e-9]
                cell = {
                    "text": t["text"],
                    "col": cols.index(best),
                    "row": r_i,
                    "bounding_box_px": t["bounding_box_px"],
                    "confidence": t["confidence"],
                }
                if len(ties) > 1:
                    cell["ambiguous"] = True
                    cell["alternatives"] = [
                        cols.index(c) for c in ties
                    ]
                    ambiguous_cells += 1
                cells.append(cell)
            table_rows.append(
                {
                    "row": r_i,
                    "y_px": round(
                        sum(_tok_center(t)[1] for t in row) / len(row), 1
                    ),
                    "cells": cells,
                    "col_count": len(cols),
                }
            )

    # ---------- campos / códigos ----------
    fields: list[dict] = []
    for a in annotated:
        if _CODE_RE.match(a["text"]):
            fields.append(
                {
                    "text": a["text"],
                    "kind": "identifier_candidate",
                    "region": a["region"],
                    "page": a["page"],
                    "bounding_box_px": a["bounding_box_px"],
                    "state": (
                        "FIELD_IDENTIFIED"
                        if a["region"] in {"title_block", "component_table"}
                        else "TEXT_ONLY"
                    ),
                    "association": "position_rule:title_or_table_region",
                    "association_confidence": "rule_based",
                }
            )

    # ---------- revisão ----------
    revisions: list[dict] = []
    for i, a in enumerate(annotated):
        if a["region"] == "title_block" and re.match(
            r"^(REV|R)\.?$", a["text"], re.IGNORECASE
        ):
            nxt = annotated[i + 1] if i + 1 < len(annotated) else None
            rev = {
                "field": "revision_candidate",
                "label_text": a["text"],
                "value_text": nxt["text"] if nxt else None,
                "region": "title_block",
                "bounding_box_px": a["bounding_box_px"],
                "state": (
                    "FIELD_IDENTIFIED" if nxt else "TEXT_ONLY"
                ),
            }
            revisions.append(rev)

    # ---------- cotas ----------
    dimensions: list[dict] = []
    for a in annotated:
        if not _DIM_RE.match(a["text"].replace(",", ".")):
            continue
        if len(a["text"]) < 2:
            continue
        state = "DIMENSION_TEXT_FOUND"
        if a["region"] == "dimension" or a["region"] == "drawing_area":
            state = "DIMENSION_REGION_CANDIDATE"
        dimensions.append(
            {
                "text": a["text"],
                "region": a["region"],
                "page": a["page"],
                "bounding_box_px": a["bounding_box_px"],
                "state": state,
                "association": None,
                "limitations": [
                    "texto numérico não comprova associação geométrica",
                    "unidade/tolerância só quando explicitamente escrita",
                ],
            }
        )

    # ---------- comparação com BOM oficial (multiplicidade-aware) ----------
    bom_comparison: dict | None = None
    if bom_codes:
        from collections import Counter

        ocr_counts = Counter(
            f["text"]
            for f in fields
            if f["region"] == "component_table" or f["state"] == "FIELD_IDENTIFIED"
        )
        bom_counts = Counter(bom_codes)
        matched, missing_draw, missing_bom, qty_mismatch = [], [], [], []
        for code in set(bom_counts) | set(ocr_counts):
            o_n, b_n = ocr_counts.get(code, 0), bom_counts.get(code, 0)
            if o_n and b_n:
                if b_n != o_n:
                    qty_mismatch.append(
                        {"code": code, "bom": b_n, "drawing_table": o_n}
                    )
                matched.append({"code": code, "occurrences": min(o_n, b_n)})
            elif b_n:
                missing_draw.append(code)
            else:
                missing_bom.append(code)
        bom_comparison = {
            "matched": matched,
            "missing_in_drawing_table": missing_draw,
            "not_in_bom": missing_bom,
            "occurrence_mismatches": qty_mismatch,
            "state": "COMPARED_PARTIAL" if matched else "NOT_COMPARABLE",
            "limitations": [
                "ausência no desenho não prova erro de BOM",
                "ausência em OCR não prova ausência visual",
                "BOM oficial permanece source of truth",
            ],
        }

    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "document_hash_sha256": document_hash,
        "page": page,
        "page_size_px": [round(w, 0), round(h, 0)],
        "regions_summary": regions_seen,
        "tokens_processed": len(annotated),
        "title_block_candidates": [
            a for a in annotated if a["region"] == "title_block"
        ],
        "component_table": {
            "candidate": bool(table_rows),
            "rows": table_rows,
            "row_count": len(table_rows),
            "ambiguous_cells": ambiguous_cells,
            "association": "row_cluster:y_proximity + col_cluster:x",
            "confidence": "rule_based",
        },
        "identifier_candidates": fields,
        "revision_candidates": revisions,
        "dimension_candidates": dimensions,
        "bom_comparison": bom_comparison,
        "states": {
            "fields": sorted(FIELD_STATES),
            "dimensions": sorted(DIMENSION_STATES),
        },
        "validation": {
            "status": "DRAFT",
            "engineering_validated": False,
            "note": "candidatos — revisão técnica pelo owner de Engenharia",
        },
        "limitations": [
            "região por posição relativa — layout atípico pode classificar errado",
            "associação cota↔geometria não verificada automaticamente",
            "confidence de OCR não é confiança técnica",
        ],
    }
    return out
