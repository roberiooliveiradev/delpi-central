"""Drawing Understanding — camada de interpretação estrutural (R8.1).

Contrato ``drawing_understanding.v1``: consome evidência OCR existente
(tokens + bounding boxes em pixels, sistema de coordenadas explícito)
e produz candidatos estruturados — regiões, carimbo, revisão, tabela,
cotas, notas, ambiguidades — com provenance e estados honestos.

R8.1 (correções D1–D5):
- região por estrutura/semântica (rótulos + cluster de códigos), não
  só posição relativa — funciona em carimbo superior ou inferior;
- tabela detectada por coluna de códigos + rótulos, em qualquer posição;
- pareamento rótulo→valor para REV (proximidade/alinhamento);
- filtro contextual de cotas (exclui valores de rótulos, itens de
  tabela, códigos longos, células de carimbo/tabela);
- BOM compare fail-closed: sem tabela estruturada → NOT_COMPARABLE
  com listas vazias (nunca falsa ausência).

Determinístico e explicável: zero ML. ``OCR_TEXT_FOUND`` nunca é
``ENGINEERING_VALIDATED``; ``DIMENSION_TEXT_FOUND`` nunca é
``DIMENSION_ASSOCIATION_VERIFIED``.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Iterable

from engineering_app.domain.drawing.object_profiles import (
    COMPONENT_CODE_RE as _CODE_RE,
)

SCHEMA_VERSION = "drawing_understanding.v1"

FIELD_STATES = frozenset(
    {
        "FIELD_IDENTIFIED", "FIELD_AMBIGUOUS", "TEXT_ONLY",
        "NOT_FOUND", "NOT_COMPARABLE",
    }
)
DIMENSION_STATES = frozenset(
    {
        "DIMENSION_TEXT_FOUND",
        "DIMENSION_REGION_CANDIDATE",
        "DIMENSION_GEOMETRY_ASSOCIATION_CANDIDATE",
        # DIMENSION_ASSOCIATION_VERIFIED — somente validação governada.
    }
)
REGION_TYPES = frozenset(
    {
        "title_block", "component_table", "revision_history",
        "drawing_area", "notes", "dimension", "legend",
        "other", "unknown",
    }
)

# Rótulos de carimbo DELPI / vocabulário técnico (case-insensitive).
_TITLEBLOCK_LABELS = frozenset(
    {
        "cod", "cod.", "des", "des.", "rev", "rev.", "rev:",
        "cliente", "desenho", "esc", "esc.", "escala", "data",
        "ref", "ref.", "mat", "material", "peso", "unid",
        "unidade", "folha", "fl", "fl.", "obs", "obs.",
        "aprov", "aprov.", "aprovado", "verific", "resp",
        "respons", "liberado", "desenhado", "conferido",
    }
)
# Rótulos de cabeçalho de tabela de componentes.
_TABLE_HEADER_LABELS = frozenset(
    {
        "item", "cod", "cod.", "código", "codigo",
        "descrição", "descricao", "descr", "qtd",
        "qtde", "quant", "unid", "un", "componente",
        "obs", "pi", "mp", "ref", "ref.",
    }
)
_REVHIST_LABELS = frozenset(
    {
        'lmp', 'ov', 'ov.', 'modificações', 'modificacoes',
        'resumo', 'revisão', 'revisao', 'alteração', 'alteracao',
        'observação', 'observacao', 'motivo', 'solic', 'solicitante',
        'autoriz', 'autorizado', 'eng', 'eng.',
    }
)
_HEADER_TYPE_MAP = {
    "item": "item", "nº": "item", "no": "item", "n": "item",
    "qtd": "quantity", "qtde": "quantity", "quant": "quantity",
    "quantidade": "quantity", "unid": "unit", "un": "unit",
    "unidade": "unit",
    "cod": "component_code", "código": "component_code",
    "codigo": "component_code", "componente": "component_code",
    "pi": "component_code", "mp": "component_code",
    "ref": "reference", "descrição": "description",
    "descricao": "description", "descr": "description",
    "obs": "note",
}
_REV_LABEL_RE = re.compile(r"^REV\.?:?$", re.IGNORECASE)
_REV_VALUE_RE = re.compile(r"^(\d{2}|[A-Z]{1,2})$")
_NUM_RE = re.compile(r"^\d+([.,]\d+)?$")
# cota explícita: tolerância ±/±n ou unidade escrita — nunca só número
_DIM_EXPLICIT_RE = re.compile(
    r"^\d+([.,]\d+)?\s*([±+/-]\s*\d+([.,]\d+)?|mm|pol|in|[°ºøØ])\s*$",
    re.IGNORECASE,
)


def _norm(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _text_of(t: dict) -> str:
    return _norm(
        str(
            t.get("normalized_text")
            or t.get("raw_text")
            or t.get("text")
            or ""
        )
    )


def _tok_center(token: dict) -> tuple[float, float] | None:
    box = token.get("bounding_box_px") or []
    if len(box) < 8:
        return None
    xs = [box[i] for i in range(0, 8, 2)]
    ys = [box[i] for i in range(1, 8, 2)]
    return (sum(xs) / 4.0, sum(ys) / 4.0)


def _box(tokens: list[dict]) -> list[float] | None:
    """BBox agregada (min/min, max/max) de um conjunto de tokens."""
    pts = [_tok_center(t) for t in tokens]
    pts = [p for p in pts if p]
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def _inside(center: tuple[float, float], box: list[float],
            margin: float = 0.0) -> bool:
    return (
        box[0] - margin <= center[0] <= box[2] + margin
        and box[1] - margin <= center[1] <= box[3] + margin
    )


def _is_label(text: str) -> bool:
    return text.lower().rstrip(".:") in _TITLEBLOCK_LABELS


def _is_header_label(text: str) -> bool:
    return text.lower().rstrip(".:") in _TABLE_HEADER_LABELS


def _page_size(
    tokens: Iterable[dict], render_size: tuple[float, float] | None
) -> tuple[float, float]:
    """Dimensões reais da página: render_size (px) quando disponível;
    senão max centro OCR (limitação documentada)."""
    if render_size and render_size[0] > 0 and render_size[1] > 0:
        return float(render_size[0]), float(render_size[1])
    maxx = maxy = 0.0
    for t in tokens:
        c = _tok_center(t)
        if c:
            maxx, maxy = max(maxx, c[0]), max(maxy, c[1])
    return (maxx or 1.0, maxy or 1.0)


def _clip_box(box: list[float] | None, w: float, h: float) -> list[float] | None:
    """AC04: todo bbox dentro de 0..w / 0..h; inválido → None."""
    if not box:
        return None
    x1 = max(0.0, min(float(box[0]), w))
    y1 = max(0.0, min(float(box[1]), h))
    x2 = max(0.0, min(float(box[2]), w))
    y2 = max(0.0, min(float(box[3]), h))
    if x2 <= x1 or y2 <= y1:
        return None
    return [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)]


def _nearest_value_right(
    label_tok: dict, tokens: list[dict], y_tol: float, x_tol: float
) -> dict | None:
    """Token mais próximo à direita do rótulo (mesma linha)."""
    lc = _tok_center(label_tok)
    if not lc:
        return None
    best, best_d = None, None
    for t in tokens:
        if t is label_tok:
            continue
        c = _tok_center(t)
        if not c:
            continue
        if abs(c[1] - lc[1]) <= y_tol and 0 < c[0] - lc[0] <= x_tol:
            d = c[0] - lc[0]
            if best_d is None or d < best_d:
                best, best_d = t, d
    return best


def _nearest_value_below(
    label_tok: dict, tokens: list[dict], x_tol: float, y_tol: float
) -> dict | None:
    """Token mais próximo abaixo do rótulo (mesma coluna)."""
    lc = _tok_center(label_tok)
    if not lc:
        return None
    best, best_d = None, None
    for t in tokens:
        if t is label_tok:
            continue
        c = _tok_center(t)
        if not c:
            continue
        if abs(c[0] - lc[0]) <= x_tol and 0 < c[1] - lc[1] <= y_tol:
            d = c[1] - lc[1]
            if best_d is None or d < best_d:
                best, best_d = t, d
    return best


def _cluster_y(
    tokens: list[dict], y_tol: float
) -> list[list[dict]]:
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


def _detect_title_block(
    tokens: list[dict], w: float, h: float
) -> dict | None:
    """Carimbo = cluster de ≥2 rótulos de carimbo (em qualquer posição).

    D1/D5: posição é apenas um indício; rótulos conhecidos (COD/DES/
    REV/CLIENTE...) definem a região. Bbox ampliada por margem de
    célula e tokens internos marcados como title_block.
    """
    labels = [
        t for t in tokens
        if _is_label(_text_of(t)) and _tok_center(t)
    ]
    if len(labels) < 2:
        return None
    # agrupa rótulos próximos — o maior cluster vence
    y_tol = h * 0.06
    groups: list[list[dict]] = []
    for t in sorted(
        labels, key=lambda t: (_tok_center(t)[1], _tok_center(t)[0])
    ):
        c = _tok_center(t)
        for g in groups:
            gb = _box(g)
            if _inside(c, gb, margin=max(w * 0.12, y_tol)):
                g.append(t)
                break
        else:
            groups.append([t])
    best = max(groups, key=len)
    if len(best) < 2:
        return None
    box = _box(best)
    box[0] -= w * 0.02
    box[1] -= h * 0.02
    box[2] += w * 0.30  # rótulo → valor à direita
    box[3] += h * 0.06
    members = [
        t
        for t in tokens
        if _tok_center(t) and _inside(_tok_center(t), box)
    ]
    return {
        "box": box,
        "label_count": len(best),
        "labels": [_text_of(t) for t in best],
        "tokens": members,
    }


def _is_revhist_label(text: str) -> bool:
    return text.lower().rstrip('.:') in _REVHIST_LABELS


def _detect_revision_history(
    tokens: list[dict], w: float, h: float, used_ids: set[int]
) -> dict | None:
    """Histórico de revisão = cluster ≥2 rótulos de histórico
    (LMP/OV/MODIFICAÇÕES/RESUMO...) fora do carimbo já detectado —
    região independente mesmo adjacente (isolamento R8.2)."""
    labels = [
        t
        for t in tokens
        if id(t) not in used_ids
        and _is_revhist_label(_text_of(t))
        and _tok_center(t)
    ]
    if len(labels) < 2:
        return None
    y_tol = h * 0.06
    groups: list[list[dict]] = []
    for t in sorted(
        labels, key=lambda t: (_tok_center(t)[1], _tok_center(t)[0])
    ):
        c = _tok_center(t)
        for g in groups:
            if _inside(c, _box(g), margin=max(w * 0.14, y_tol)):
                g.append(t)
                break
        else:
            groups.append([t])
    best = max(groups, key=len)
    if len(best) < 2:
        return None
    box = _box(best)
    box[0] -= w * 0.02
    box[1] -= h * 0.02
    box[2] += w * 0.35
    box[3] += h * 0.05
    return {
        box: box,
        label_count: len(best),
        labels: [_text_of(t) for t in best],
        tokens: [
            t
            for t in tokens
            if _tok_center(t) and _inside(_tok_center(t), box)
        ],
    }


_ADMIN_WORD_RE = re.compile(
    r"^(cod|des|rev|cliente|client|esc|escala|data|ref|mat|material|"
    r"peso|folha|fl|obs|aprov|verific|resp|respons|liberado|"
    r"desenhado|conferido|lmp|ov|resumo|modifica|executado|"
    r"autoriz|solic|eng)\b",
    re.IGNORECASE,
)


def _has_admin_word(text: str) -> bool:
    """Prefixo administrativo (COD:5101.5561, CLIENTE:FAMAC,
    RESUMO DAS MODIFICAÇÕES) — exclusão contextual por vocabulário
    de rótulo, não lista global de termos."""
    return bool(_ADMIN_WORD_RE.match((text or "").strip()))


def _detect_component_table(
    tokens: list[dict], w: float, h: float, tb_box: list[float] | None
) -> dict | None:
    """Tabela = coluna de ≥2 códigos (6-11 dígitos) alinhados em X +
    linhas adjacentes, em qualquer posição (D2)."""
    code_tokens = [
        t
        for t in tokens
        if _CODE_RE.match(_text_of(t)) and _tok_center(t)
    ]
    if len(code_tokens) < 2:
        return None
    x_tol = w * 0.045
    cols: list[list[dict]] = []
    for t in sorted(
        code_tokens, key=lambda t: _tok_center(t)[0]
    ):
        cx = _tok_center(t)[0]
        for col in cols:
            xs = [_tok_center(c)[0] for c in col]
            if abs(cx - (sum(xs) / len(xs))) <= x_tol:
                col.append(t)
                break
        else:
            cols.append([t])
    # Multi-coluna: além da maior, unir colunas com ≥3 códigos —
    # layouts com coluna de conjunto (PI/PA) + coluna de componentes
    # perdem linhas quando só a maior ancora as faixas Y.
    code_col = max(cols, key=len)
    if len(code_col) < 2:
        return None
    anchor_cols = [code_col] + [
        c for c in cols if c is not code_col and len(c) >= 3
    ]
    anchor_tokens = [t for c in anchor_cols for t in c]
    col_box = _box(anchor_tokens)
    y_tol = h * 0.02
    # linhas da tabela = tokens na mesma faixa Y dos códigos (vizinhança)
    rows: list[list[dict]] = []
    for t in sorted(
        [t for t in tokens if _tok_center(t)],
        key=lambda t: _tok_center(t)[1],
    ):
        c = _tok_center(t)
        row_y = None
        for code_t in anchor_tokens:
            if abs(c[1] - _tok_center(code_t)[1]) <= y_tol:
                row_y = _tok_center(code_t)[1]
                break
        if row_y is not None:
            for row in rows:
                if abs(row_y - row["y"]) <= y_tol:
                    row["tokens"].append(t)
                    break
            else:
                rows.append({"y": row_y, "tokens": [t]})
    if not rows:
        return None
    table_box = _box(
        [t for r in rows for t in r["tokens"]]
    )
    table_box[0] -= w * 0.03
    table_box[2] += w * 0.30  # descrição à direita do código
    header = [
        t
        for t in tokens
        if _tok_center(t)
        and _is_header_label(_text_of(t))
        and abs(_tok_center(t)[0] - col_box[0]) <= w * 0.10
        and _tok_center(t)[1] < table_box[1] - h * 0.005
        and _tok_center(t)[1] > table_box[1] - h * 0.12
    ]
    # não engolir o carimbo: se a tabela coincide com o carimbo,
    # limitar à coluna de códigos
    if tb_box and _inside(
        (col_box[0], col_box[1]), tb_box, margin=w * 0.02
    ):
        table_box[0] = col_box[0] - w * 0.02
        table_box[1] = col_box[1] - h * 0.005
        table_box[2] = col_box[2] + w * 0.30
        table_box[3] = col_box[3] + h * 0.01
    return {
        "box": table_box,
        "code_col_x": (col_box[0] + col_box[2]) / 2,
        "code_count": len(anchor_tokens),
        "rows": rows,
        "header_tokens": header,
        "tokens": [
            t
            for t in tokens
            if _tok_center(t) and _inside(_tok_center(t), table_box)
        ],
    }


def _header_type(text: str) -> str | None:
    return _HEADER_TYPE_MAP.get(text.lower().rstrip(".:"))


def _structure_table(
    table: dict, w: float, h: float
) -> list[dict]:
    """Estrutura linhas/células: célula = token na linha, coluna por
    cluster X dos tokens da tabela; cabeçalho por proximidade."""
    y_tol = h * 0.015
    x_tol = w * 0.05
    all_toks = [
        t for r in table["rows"] for t in r["tokens"]
    ]
    col_centers: list[float] = []
    for t in sorted(
        all_toks, key=lambda t: _tok_center(t)[0]
    ):
        cx = _tok_center(t)[0]
        if not col_centers or abs(cx - col_centers[-1]) > x_tol:
            col_centers.append(cx)
        else:
            col_centers[-1] = (col_centers[-1] + cx) / 2.0
    col_types: dict[int, str] = {}
    # header→col: atribuição greedy sem colisão — cada rótulo ocupa a
    # coluna livre mais próxima (headers em ordem x).
    hdr_toks = sorted(
        [t for t in (table.get("header_tokens") or []) if _tok_center(t)],
        key=lambda t: _tok_center(t)[0],
    )
    used_cols: set[int] = set()
    for ht in hdr_toks:
        tpe = _header_type(_text_of(ht))
        c = _tok_center(ht)
        if not (tpe and c and col_centers):
            continue
        free = [i for i in range(len(col_centers)) if i not in used_cols]
        if not free:
            break
        ci = min(free, key=lambda i: abs(col_centers[i] - c[0]))
        col_types[ci] = tpe
        used_cols.add(ci)
    # tipagem por conteúdo (evidência de dados): coluna cujas células
    # são majoritariamente códigos 6-11 dígitos → component_code,
    # quando o header não a tipou (header pode estar desalinhado em x).
    content_counts: dict[int, Counter] = {}
    for row in table["rows"]:
        for t in row["tokens"]:
            c = _tok_center(t)
            if not c or not col_centers:
                continue
            ci = min(
                range(len(col_centers)),
                key=lambda i: abs(col_centers[i] - c[0]),
            )
            cnt = content_counts.setdefault(ci, Counter())
            cnt["total"] += 1
            if _CODE_RE.match(_text_of(t)):
                cnt["codes"] += 1
    for ci, cnt in content_counts.items():
        if ci not in col_types and cnt["total"] and cnt["codes"] / cnt["total"] >= 0.5:
            col_types[ci] = "component_code"
    # colunas conectadas à coluna de códigos — gap >12% da largura
    # rompe a faixa da tabela (campos administrativos ficam fora).
    keep_cols: set[int] = set()
    code_x = table.get("code_col_x")
    if code_x is not None and col_centers:
        ci = min(
            range(len(col_centers)),
            key=lambda i: abs(col_centers[i] - code_x),
        )
        keep_cols.add(ci)
        gap = w * 0.15
        for i in range(ci - 1, -1, -1):
            if col_centers[i + 1] - col_centers[i] > gap:
                break
            keep_cols.add(i)
        for i in range(ci + 1, len(col_centers)):
            if col_centers[i] - col_centers[i - 1] > gap:
                break
            keep_cols.add(i)
    # Colunas tipadas component_code por conteúdo mantêm-se mesmo com
    # gap — layouts multi-coluna (conjunto + componentes) usam faixas
    # X não contíguas.
    keep_cols.update(
        i for i, tpe in col_types.items() if tpe == "component_code"
    )
    rows_out = []
    ambiguous = 0
    for r_i, row in enumerate(sorted(table["rows"], key=lambda r: r["y"])):
        cells = []
        for t in sorted(
            [
                tok
                for tok in row["tokens"]
                if not _has_admin_word(_text_of(tok))
            ],
            key=lambda t: _tok_center(t)[0],
        ):
            x = _tok_center(t)[0]
            d = [abs(x - c) for c in col_centers]
            best_i = min(range(len(d)), key=lambda i: d[i])
            if keep_cols and best_i not in keep_cols:
                continue
            ties = [i for i in range(len(d)) if abs(d[i] - d[best_i]) < 1e-9]
            cell = {
                "text": _text_of(t),
                "col": best_i,
                "row": r_i,
                "bounding_box_px": t.get("bounding_box_px"),
                "confidence": t.get("confidence"),
            }
            if best_i in col_types:
                cell["col_type"] = col_types[best_i]
            if len(ties) > 1:
                cell["ambiguous"] = True
                cell["alternatives"] = ties
                ambiguous += 1
            cells.append(cell)
        # R10 — tipagem de campos por linha a partir de col_type:
        # item/quantity/component_code/description com proveniência real.
        fields: dict[str, dict] = {}
        for cell in cells:
            ct = cell.get("col_type")
            if not ct:
                continue
            if ct not in fields:
                fields[ct] = {
                    "raw_text": cell["text"],
                    "normalized_value": cell["text"],
                    "bounding_box_px": cell.get("bounding_box_px"),
                    "col": cell["col"],
                    "association_method": "col_type_header_or_content",
                    "association_state": "FIELD_IDENTIFIED",
                }
            else:
                # mesma coluna tipada → concatena (multilinha/descrição)
                fields[ct]["raw_text"] += " " + cell["text"]
                fields[ct]["normalized_value"] = fields[ct]["raw_text"]
                b = fields[ct]["bounding_box_px"]
                nb = cell.get("bounding_box_px")
                if b and nb:
                    fields[ct]["bounding_box_px"] = [
                        min(b[0], nb[0]), min(b[1], nb[1]),
                        max(b[2], nb[2]), max(b[3], nb[3]),
                    ]
        # quantity → número só se formato válido
        if "quantity" in fields:
            q = fields["quantity"]["raw_text"].strip()
            if q.replace(",", ".").replace(".", "", 1).isdigit() or q.isdigit():
                fields["quantity"]["normalized_value"] = q
        typed = {
            "row": r_i,
            "y_px": round(row["y"], 1),
            "cells": cells,
            "col_count": len(col_centers),
            "fields": fields,
            "item": fields.get("item", {}).get("normalized_value"),
            "quantity": fields.get("quantity", {}).get("normalized_value"),
            "component_code": fields.get(
                "component_code", {}
            ).get("normalized_value"),
            "description": fields.get(
                "description", {}
            ).get("normalized_value"),
            "association_status": (
                "FIELD_IDENTIFIED" if fields else "UNRESOLVED"
            ),
        }
        rows_out.append(typed)
    return rows_out, ambiguous, col_types


def _match_revisions(
    tokens: list[dict], w: float, h: float
) -> list[dict]:
    """REV: → valor (mesma linha à direita ou abaixo na coluna). D3."""
    revs = []
    y_tol = h * 0.015
    x_tol = w * 0.12
    for t in tokens:
        text = _text_of(t)
        if not _REV_LABEL_RE.match(text):
            continue
        val = _nearest_value_right(t, tokens, y_tol, x_tol)
        rule = "label_right_same_row"
        if val is None or not _REV_VALUE_RE.match(_text_of(val)):
            val = _nearest_value_below(t, tokens, x_tol, y_tol * 3)
            rule = "label_below_same_col"
        if val and _REV_VALUE_RE.match(_text_of(val)):
            revs.append(
                {
                    "field": "revision_candidate",
                    "label_text": text,
                    "value_text": _text_of(val),
                    "region": "title_block",
                    "bounding_box_px": t.get("bounding_box_px"),
                    "value_bounding_box_px": val.get("bounding_box_px"),
                    "state": "FIELD_IDENTIFIED",
                    "association": f"label_value:{rule}",
                    "association_confidence": "rule_based",
                }
            )
        else:
            revs.append(
                {
                    "field": "revision_candidate",
                    "label_text": text,
                    "value_text": None,
                    "region": "title_block",
                    "bounding_box_px": t.get("bounding_box_px"),
                    "state": "TEXT_ONLY",
                    "association": None,
                }
            )
    return revs


def _is_dimension_candidate(
    text: str, region: str, paired: bool
) -> tuple[bool, str]:
    """Filtro contextual de cota (D4): nunca número solto em
    carimbo/tabela/rótulo; exige tolerância/unidade explícita ou
    região de desenho SEM contexto de exclusão."""
    if paired:
        return False, "paired_label_value"
    if _CODE_RE.match(text):
        return False, "long_code_not_dimension"
    if region in {"title_block", "component_table", "revision_history"}:
        return False, "inside_structured_region"
    if _DIM_EXPLICIT_RE.match(text):
        return True, "explicit_tolerance_or_unit"
    if region == "drawing_area" and _NUM_RE.match(text) and len(text) >= 3:
        return True, "drawing_area_number_ge3"
    if region == "dimension" and _NUM_RE.match(text):
        return True, "dimension_region_number"
    return False, "number_without_dimension_context"


def build_understanding(
    tokens: list[dict],
    *,
    document_hash: str,
    page: int = 1,
    bom_codes: list[str] | None = None,
    bom_quantities: dict[str, int] | None = None,
    product_code: str | None = None,
    render_size_px: tuple[int, int] | None = None,
    graphic_primitives: dict | None = None,
) -> dict[str, Any]:
    """Constrói candidatos estruturados a partir de tokens OCR."""
    w, h = _page_size(tokens, render_size_px)
    annotated: list[dict] = []

    tb = _detect_title_block(tokens, w, h)
    table = _detect_component_table(
        tokens, w, h, tb["box"] if tb else None
    )
    tb_ids = set(id(t) for t in (tb["tokens"] if tb else []))
    # R8.2.2: fronteira gráfica real — retângulos detectados contendo a
    # coluna de códigos delimitam a tabela; sem evidência → fallback
    # token-derived com limitação explícita (nunca promove inferência).
    graphic_boundary = False
    if table and graphic_primitives and graphic_primitives.get("rects"):
        code_tokens = table.get("code_tokens") or [
            t
            for t in tokens
            if _CODE_RE.match(_text_of(t)) and _tok_center(t)
        ]
        # por token de código da coluna: menor retângulo que o contém
        # = célula real (exclui a moldura externa que engloba carimbo
        # e histórico junto com a tabela).
        containing = []
        for t in code_tokens:
            c = _tok_center(t)
            cands = [
                r
                for r in graphic_primitives["rects"]
                if _inside(c, r)
            ]
            if cands:
                containing.append(
                    min(cands, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
                )
        if containing:
            x1 = min(r[0] for r in containing)
            y1 = min(r[1] for r in containing)
            x2 = max(r[2] for r in containing)
            y2 = max(r[3] for r in containing)
            table["box"] = [x1, y1, x2, y2]
            table["tokens"] = [
                t
                for t in tokens
                if _tok_center(t)
                and _inside(_tok_center(t), table["box"])
            ]
            graphic_boundary = True
            area = (x2 - x1) * (y2 - y1)
            if area > w * h * 0.60:
                # moldura quase integral NÃO é tabela (AC04/AC15) —
                # fronteira rejeitada: tokens não reivindicados, cotas
                # preservadas, BOM fail-closed.
                graphic_boundary = False
                table["unreliable_boundary"] = True
                table["tokens"] = []
    # AC06/AC08: ownership exclusivo — tokens do carimbo nunca são
    # células de tabela (bordas sobrepostas → tb prevalece, conflito
    # registrado abaixo).
    tbl_ids = {
        i
        for i in set(id(t) for t in (table["tokens"] if table else []))
        if i not in tb_ids
    }
    revh = _detect_revision_history(tokens, w, h, tb_ids | tbl_ids)
    revh_ids = {
        i
        for i in set(id(t) for t in (revh["tokens"] if revh else []))
        if i not in tb_ids and i not in tbl_ids
    }

    # isolamento (AC02): um token pertence a exatamente uma região;
    # sobreposição de regiões candidatas → conflito explícito.
    ownership_conflicts: list[dict] = []
    for t in tokens:
        belongs = sum(
            1 for ids in (tbl_ids, tb_ids, revh_ids) if id(t) in ids
        )
        if belongs > 1:
            c = _tok_center(t)
            ownership_conflicts.append(
                {
                    "text": _text_of(t),
                    "bounding_box_px": t.get("bounding_box_px"),
                    "center_px": list(c) if c else None,
                }
            )
    regions: list[dict] = []
    for rid, rtype, obj, ids in (
        ("region_title_block", "title_block", tb, tb_ids),
        ("region_component_table", "component_table", table, tbl_ids),
        ("region_revision_history", "revision_history", revh, revh_ids),
    ):
        if obj:
            regions.append(
                {
                    "id": rid,
                    "type": rtype,
                    "box_px": _clip_box(obj["box"], w, h),
                    "token_count": len(ids),
                    "evidence": obj.get("labels")
                    or [
                        _text_of(t)
                        for t in obj.get("header_tokens") or []
                    ],
                    "state": "candidate",
                }
            )

    for idx, t in enumerate(tokens):
        text = _text_of(t)
        c = _tok_center(t)
        if id(t) in tbl_ids:
            region = "component_table"
        elif id(t) in tb_ids:
            region = "title_block"
        elif id(t) in revh_ids:
            region = "revision_history"
        elif c and c[0] < w * 0.45 and c[1] < h * 0.35:
            region = "notes"
        else:
            region = "drawing_area"
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

    regions_seen = Counter(a["region"] for a in annotated)

    # ---------- tabela estruturada ----------
    table_rows: list[dict] = []
    ambiguous_cells = 0
    col_types: dict[int, str] = {}
    if table:
        table_rows, ambiguous_cells, col_types = _structure_table(
            table, w, h
        )

    # ---------- revisão contextual ----------
    revisions = _match_revisions(tokens, w, h)
    paired_values = set()
    for r in revisions:
        vb = r.get("value_bounding_box_px")
        if vb:
            paired_values.add(tuple(vb))
    # tokens cujo texto foi consumido como valor de rótulo
    label_value_texts = {
        _text_of(t)
        for r in revisions
        if r.get("value_text")
        for t in tokens
        if _text_of(t) == r["value_text"]
        and t.get("bounding_box_px") == r.get("value_bounding_box_px")
    }

    # ---------- identificadores ----------
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
                    "association": (
                        "structure_rule:inside_"
                        + a["region"]
                        if a["region"] in {"title_block", "component_table"}
                        else None
                    ),
                    "association_confidence": "rule_based",
                }
            )

    # ---------- cotas (filtro contextual) ----------
    dimensions: list[dict] = []
    excluded: list[dict] = []
    for a in annotated:
        if not _NUM_RE.match(a["text"]) and not _DIM_EXPLICIT_RE.match(
            a["text"]
        ):
            continue
        paired = a["bounding_box_px"] and tuple(
            a["bounding_box_px"]
        ) in paired_values or a["text"] in label_value_texts
        ok, reason = _is_dimension_candidate(
            a["text"], a["region"], paired
        )
        if ok:
            dimensions.append(
                {
                    "text": a["text"],
                    "region": a["region"],
                    "page": a["page"],
                    "bounding_box_px": a["bounding_box_px"],
                    "state": (
                        "DIMENSION_REGION_CANDIDATE"
                        if a["region"] == "drawing_area"
                        else "DIMENSION_TEXT_FOUND"
                    ),
                    "association": None,
                    "rule": reason,
                    "limitations": [
                        "associação geométrica não verificada automaticamente",
                        "unidade/tolerância só quando explicitamente escrita",
                    ],
                }
            )
        else:
            excluded.append({"text": a["text"], "reason": reason})

    # ---------- comparação BOM (fail-closed, D5) ----------
    bom_comparison: dict | None = None
    if bom_codes is not None:
        if not table_rows:
            bom_comparison = {
                "state": "NOT_COMPARABLE",
                "matched": [],
                "missing_in_drawing_table": [],
                "not_in_bom": [],
                "occurrence_mismatches": [],
                "limitations": [
                    "tabela do desenho não estruturada com evidência "
                    "suficiente — ausência na tabela não pode ser "
                    "afirmada",
                ],
            }
        elif (
            table and table.get("unreliable_boundary")
        ) or not col_types:
            bom_comparison = {
                "state": "NOT_COMPARABLE",
                "matched": [],
                "missing_in_drawing_table": [],
                "not_in_bom": [],
                "occurrence_mismatches": [],
                "extracted_but_unclassified": [],
                "limitations": [
                    "tabela sem cabeçalho tipado ou fronteira "
                    "não confiável — sequência de códigos não comprova "
                    "tabela de componentes",
                ],
            }
        else:
            table_code_counts: Counter = Counter()
            for r in table_rows:
                for c in r["cells"]:
                    if (
                        _CODE_RE.match(c["text"])
                        and c.get("col_type") == "component_code"
                        and c["text"] != (product_code or "")
                    ):
                        table_code_counts[c["text"]] += 1
            bom_counts = Counter(bom_codes)
            matched, missing_draw, missing_bom, qty_mm = [], [], [], []
            unclassified: list[str] = []
            for code in set(bom_counts) | set(table_code_counts):
                o_n, b_n = table_code_counts.get(code, 0), bom_counts.get(
                    code, 0
                )
                if o_n and b_n:
                    if b_n != o_n:
                        qty_mm.append(
                            {
                                "code": code,
                                "bom": b_n,
                                "drawing_table": o_n,
                            }
                        )
                    matched.append(
                        {"code": code, "occurrences": min(o_n, b_n)}
                    )
                elif b_n:
                    # AC12: código visível no OCR mas fora das células
                    # tipadas NÃO é ausência na tabela — não comparável.
                    visible = any(
                        _text_of(t) == code for t in tokens
                    )
                    if visible:
                        unclassified.append(code)
                    else:
                        missing_draw.append(code)
                else:
                    missing_bom.append(code)
            # fail-closed: sem matches → NOT_COMPARABLE; com matches →
            # COMPARED_PARTIAL (cobertura incompleta sinalizada por
            # extracted_but_unclassified, nunca por falsa ausência).
            state = "COMPARED_PARTIAL" if matched else "NOT_COMPARABLE"
            bom_comparison = {
                "state": state,
                "matched": matched,
                "missing_in_drawing_table": missing_draw if matched else [],
                "not_in_bom": missing_bom if matched else [],
                "occurrence_mismatches": qty_mm if matched else [],
                "extracted_but_unclassified": unclassified,
                "limitations": [
                    "ausência na tabela candidata não prova ausência visual",
                    "tabela parcial não representa BOM completa",
                    "BOM oficial permanece source of truth",
                ],
            }

    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "document_hash_sha256": document_hash,
        "page": page,
        "page_size_px": [round(w, 0), round(h, 0)],
        "regions": regions,
        "ownership_conflicts": ownership_conflicts,
        "regions_summary": dict(regions_seen),
        "tokens_processed": len(annotated),
        "title_block": {
            "candidate": tb is not None,
            "box_px": tb["box"] if tb else None,
            "labels": tb["labels"] if tb else [],
            "detection": "label_cluster (≥2 rótulos conhecidos)",
        },
        "title_block_candidates": [
            a for a in annotated if a["region"] == "title_block"
        ],
        "component_table": {
            "candidate": table is not None and bool(table_rows),
            "rows": table_rows,
            "row_count": len(table_rows),
            "code_count": table["code_count"] if table else 0,
            "headers": [
                _text_of(t)
                for t in (table["header_tokens"] if table else [])
            ],
            "ambiguous_cells": ambiguous_cells,
            "col_types": {str(k): v for k, v in col_types.items()},
            "graphic_boundary": graphic_boundary,
            "unreliable_boundary": bool(
                table and table.get("unreliable_boundary")
            ),
            "boundary_source": (
                "graphic_rects" if graphic_boundary else "tokens_inferred"
            ),
            "detection": "code_column_cluster + row_y_proximity",
            "confidence": "rule_based",
        },
        "identifier_candidates": fields,
        "revision_history": {
            "candidate": revh is not None,
            "box_px": revh["box"] if revh else None,
            "labels": revh["labels"] if revh else [],
            "detection": "revhist_label_cluster (≥2 rótulos fora do "
            "carimbo)",
        },
        "revision_candidates": revisions,
        "dimension_candidates": dimensions,
        "dimension_excluded": excluded,
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
            "região por estrutura+rótulos — layout atípico pode ainda "
            "classificar errado",
            "associação cota↔geometria não verificada automaticamente",
            "confidence de OCR não é confiança técnica",
            "tabela candidata parcial não representa BOM completa",
        ],
    }
    return out
