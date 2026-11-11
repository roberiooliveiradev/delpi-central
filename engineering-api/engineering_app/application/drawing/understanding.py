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
        "FIELD_IDENTIFIED", "FIELD_AMBIGUOUS", "FIELD_BAND_CONFLICT",
        "TEXT_ONLY", "NOT_FOUND", "NOT_COMPARABLE",
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
        "obs", "pi", "mp", "ref", "ref.", "cabo",
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
    "cabo": "cable",
    "obs": "note",
}
_REV_LABEL_RE = re.compile(r"^REV\.?:?$", re.IGNORECASE)
_REV_VALUE_RE = re.compile(r"^(\d{2}|[A-Z]{1,2})$")
_NUM_RE = re.compile(r"^\d+([.,]\d+)?$")
_CODE_FIND_RE = re.compile(r"\d{8,11}")
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


def _polygon_extent(box: list | None) -> tuple[float, float, float, float] | None:
    """Extensão de um polígono ou retângulo, sem inventar coordenadas."""
    if not box or len(box) < 4:
        return None
    xs = [float(box[i]) for i in range(0, len(box), 2)]
    ys = [float(box[i]) for i in range(1, len(box), 2)]
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


_SHEET_INDEX_RE = re.compile(r"^\d{1,2}$")
_SHEET_INDEX_SEQ_RE = re.compile(r"^(\d{1,2})(\s+\d{1,2})+$")


def _is_sheet_index_text(text: str) -> bool:
    """Índice de folha/quadro (1–2 dígitos), não código de componente."""
    return bool(_SHEET_INDEX_RE.fullmatch((text or "").strip()))


def _is_sheet_index_noise_cell(text: str) -> bool:
    """Célula só com índices curtos ('4', '4 5') — nunca component_code."""
    t = (text or "").strip()
    return bool(
        _SHEET_INDEX_RE.fullmatch(t) or _SHEET_INDEX_SEQ_RE.fullmatch(t)
    )


def _token_is_table_content(token: dict) -> bool:
    """Token que ancora conteúdo tabular (código/item/cabeçalho).

    Descrições longas isoladas não sustentam a borda do crop — no
    rodapé geram falso 'conteúdo' e impedem excluir índices 1..N.
    """
    text = _text_of(token)
    if not text:
        return False
    if _CODE_RE.match(text):
        return True
    if _is_header_label(text):
        return True
    # Item identifiers are compiled later; resolve at call time.
    if _ITEM_IDENT_RE.fullmatch(text):
        return True
    return False


def _connected_column_crop(
    rows: list[dict], w: float, h: float
) -> list[float] | None:
    """Recorte da tabela = células das colunas já conservadas.

    O envelope de todos os tokens na mesma faixa Y, e a união de
    retângulos de qualquer código da página, atravessam carimbo e
    histórico. As colunas ligadas à coluna de códigos já excluem
    esse vão. A margem é a altura mediana da célula, limitada a 2%
    da página, para a borda imediata entrar no SLANet sem alcançar
    uma região separada por esse vão.
    """
    extents = []
    for row in rows:
        for cell in row.get("cells") or []:
            extent = _polygon_extent(cell.get("bounding_box_px"))
            if extent and extent[2] > extent[0] and extent[3] > extent[1]:
                extents.append(extent)
    if not extents:
        return None
    heights = sorted(extent[3] - extent[1] for extent in extents)
    pad = min(heights[len(heights) // 2], max(w, h) * 0.02)
    return _clip_box(
        [
            min(extent[0] for extent in extents) - pad,
            min(extent[1] for extent in extents) - pad,
            max(extent[2] for extent in extents) + pad,
            max(extent[3] for extent in extents) + pad,
        ],
        w,
        h,
    )


def _hierarchical_code_pair_crop(
    tokens: list[dict], w: float, h: float
) -> list[float] | None:
    """Núcleo hierárquico = coluna esparsa de conjunto + coluna densa.

    Quando há ≥2 colunas de código com itens entre elas, o envelope
    connected_columns ainda pode atravessar carimbo à direita. O
    recorte usa só o par esquerdo/direito vencedor e expande o Y pela
    mediana dos vãos da coluna esquerda — células mescladas cujo
    rótulo fica no meio do bloco vertical.
    """
    codes: list[tuple[float, float]] = []
    items: list[tuple[float, float]] = []
    for token in tokens:
        center = _tok_center(token)
        if not center:
            continue
        text = _text_of(token)
        if _CODE_RE.match(text):
            codes.append((center[0], center[1]))
        elif _ITEM_IDENT_RE.fullmatch(text):
            items.append((center[0], center[1]))
    if len(codes) < 4:
        return None
    x_tol = max(w * 0.07, _cluster_tolerance(
        w, [c[0] for c in codes], page_fraction=0.07,
    ))
    cols: list[list[tuple[float, float]]] = []
    for point in sorted(codes, key=lambda c: c[0]):
        for col in cols:
            mean_x = sum(p[0] for p in col) / len(col)
            if abs(point[0] - mean_x) <= x_tol:
                col.append(point)
                break
        else:
            cols.append([point])
    col_stats = [
        (
            sum(p[0] for p in col) / len(col),
            len(col),
            min(p[0] for p in col),
            max(p[0] for p in col),
            [p[1] for p in col],
        )
        for col in cols
        if len(col) >= 2
    ]
    if len(col_stats) < 2:
        return None
    best: tuple | None = None
    for i, left in enumerate(col_stats):
        for right in col_stats[i + 1 :]:
            lx, ln, lmin, lmax, lys = left
            rx, rn, rmin, rmax, rys = right
            if rx - lx < w * 0.12:
                continue
            between = [
                it
                for it in items
                if lx + (rx - lx) * 0.15 < it[0] < rx - (rx - lx) * 0.05
            ]
            score = ln + rn + 2 * len(between)
            if ln < rn:
                score += rn
            if score < 8 or len(between) < 2:
                continue
            gaps = sorted(
                b - a for a, b in zip(sorted(lys), sorted(lys)[1:]) if b - a > 1
            )
            med_gap = gaps[len(gaps) // 2] if gaps else max(h * 0.04, 40.0)
            pad = max(w, h) * 0.02
            y1 = min(lys) - med_gap * 0.55
            y2 = max(lys) + med_gap * 0.55
            # inclui itens entre colunas que caiam na faixa expandida
            for _ix, iy in between:
                if y1 - med_gap <= iy <= y2 + med_gap:
                    y1 = min(y1, iy - pad)
                    y2 = max(y2, iy + pad)
            crop = [
                max(0.0, lmin - pad),
                max(0.0, y1),
                min(w, rmax + w * 0.18),
                min(h, y2),
            ]
            area = (crop[2] - crop[0]) * (crop[3] - crop[1])
            if area > w * h * 0.55:
                continue
            if area < w * h * 0.02:
                continue
            cand = (score, -area, crop)
            if best is None or cand[:2] > best[:2]:
                best = cand
    if not best:
        return None
    return _clip_box(best[2], w, h)


def _trim_sheet_index_margin(
    box: list[float], tokens: list[dict], w: float, h: float
) -> list[float] | None:
    """Recua bordas quando a faixa marginal só tem índices 1..N.

    Exige vão demonstrável após o último token de conteúdo tabular:
    códigos, itens, cabeçalhos ou texto descritivo. Não remove a
    última linha legítima de componentes. Também observa índices logo
    abaixo/acima do crop (margem), para o pad não engolir o rodapé.
    """
    clipped = _clip_box(box, w, h)
    if not clipped:
        return None
    x1, y1, x2, y2 = clipped
    margin = max(w, h) * 0.03
    search = _clip_box(
        [x1, y1 - margin, x2, y2 + margin], w, h
    ) or clipped
    nearby = [
        t
        for t in tokens
        if _tok_center(t) and _inside(_tok_center(t), search)
    ]
    content_ys = [
        _tok_center(t)[1] for t in nearby if _token_is_table_content(t)
    ]
    if not content_ys:
        return clipped
    last_content_y = max(content_ys)
    first_content_y = min(content_ys)
    bottom_idxs = [
        t
        for t in nearby
        if _is_sheet_index_text(_text_of(t))
        and _tok_center(t)[1] > last_content_y + 4.0
    ]
    if len(bottom_idxs) >= 3:
        idx_band = min(_tok_center(t)[1] for t in bottom_idxs) - 2.0
        if not any(
            _token_is_table_content(t) and _tok_center(t)[1] >= idx_band
            for t in nearby
        ):
            y2 = min(y2, idx_band)
    top_idxs = [
        t
        for t in nearby
        if _is_sheet_index_text(_text_of(t))
        and _tok_center(t)[1] < first_content_y - 4.0
    ]
    if len(top_idxs) >= 3:
        idx_band = max(_tok_center(t)[1] for t in top_idxs) + 2.0
        if not any(
            _token_is_table_content(t) and _tok_center(t)[1] <= idx_band
            for t in nearby
        ):
            y1 = max(y1, idx_band)
    return _clip_box([x1, y1, x2, y2], w, h)


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


def _cluster_tolerance(
    page_span: float, centers: list[float], *, page_fraction: float
) -> float:
    """Tolerância de agrupamento abaixo do passo mediano observado.

    Uma fração fixa da página funde linhas de tabela densa e colunas
    estreitas. O passo é a distância entre centros reais, ignorando
    jitter menor que 0,5% da página. Sem passo observável, permanece
    a fração da página.
    """
    page_tol = page_span * page_fraction
    ordered = sorted(c for c in centers if c is not None)
    noise = page_span * 0.005
    gaps = [
        b - a
        for a, b in zip(ordered, ordered[1:])
        if b - a > noise
    ]
    if not gaps:
        return page_tol
    gaps.sort()
    pitch = gaps[len(gaps) // 2]
    return min(page_tol, pitch * 0.45)


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
    tokens: list[dict], w: float, h: float, tb_box: list[float] | None,
    excluded_ids: set[int] | None = None,
) -> dict | None:
    """Tabela = coluna de ≥2 códigos (6-11 dígitos) alinhados em X +
    linhas adjacentes, em qualquer posição (D2).

    ``excluded_ids`` (RQ-VAL-027): tokens já apropriados por outras
    regiões (carimbo, histórico de revisão) nunca são âncoras de
    coluna nem membros de linhas da tabela de componentes."""
    ex = excluded_ids or set()
    code_tokens = [
        t
        for t in tokens
        if id(t) not in ex
        and _CODE_RE.match(_text_of(t))
        and _tok_center(t)
    ]
    if len(code_tokens) < 2:
        return None
    x_tol = _cluster_tolerance(
        w,
        [_tok_center(t)[0] for t in code_tokens],
        page_fraction=0.045,
    )
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
    y_tol = _cluster_tolerance(
        h,
        [_tok_center(t)[1] for t in code_col],
        page_fraction=0.02,
    )
    # linhas da tabela = tokens na mesma faixa Y dos códigos (vizinhança)
    rows: list[list[dict]] = []
    for t in sorted(
        [t for t in tokens if _tok_center(t) and id(t) not in ex],
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
    # Faixas só com índices de folha/quadro (1..N) sem código/item/
    # cabeçalho — conteúdo extratabular com separação demonstrável.
    def _row_is_sheet_index_strip(row_tokens: list[dict]) -> bool:
        texts = [_text_of(t) for t in row_tokens]
        if len(texts) < 3:
            return False
        short = sum(1 for t in texts if _is_sheet_index_text(t))
        if short < 3 or short / len(texts) < 0.6:
            return False
        return not any(_token_is_table_content(t) for t in row_tokens)

    rows = [
        r for r in rows if not _row_is_sheet_index_strip(r["tokens"])
    ]
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
            if id(t) not in ex
            and _tok_center(t)
            and _inside(_tok_center(t), table_box)
        ],
    }


def _header_type(text: str) -> str | None:
    return _HEADER_TYPE_MAP.get(text.lower().rstrip(".:"))


def _structure_table(
    table: dict, w: float, h: float
) -> list[dict]:
    """Estrutura linhas/células: célula = token na linha, coluna por
    cluster X dos tokens da tabela; cabeçalho por proximidade."""
    all_toks = [
        t for r in table["rows"] for t in r["tokens"]
    ]
    x_tol = _cluster_tolerance(
        w,
        [_tok_center(t)[0] for t in all_toks if _tok_center(t)],
        page_fraction=0.05,
    )
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
        # Coluna cuja maioria são códigos 6–11 dígitos é componente,
        # mesmo se o cabeçalho mais próximo foi Item/QTD. Cabeçalho
        # desalinhado não pode concatenar vários códigos no campo item.
        if cnt["total"] and cnt["codes"] / cnt["total"] >= 0.5:
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
            text_t = _text_of(t)
            # Índice curto só permanece como quantidade tipada; fora
            # disso não vira célula de componente/descrição.
            provisional_type = col_types.get(best_i)
            if _is_sheet_index_text(text_t) and provisional_type not in (
                "quantity",
                "item",
            ):
                continue
            ties = [i for i in range(len(d)) if abs(d[i] - d[best_i]) < 1e-9]
            cell = {
                "text": text_t,
                "col": best_i,
                "row": r_i,
                "bounding_box_px": t.get("bounding_box_px"),
                "confidence": t.get("confidence"),
            }
            if t.get("page") is not None:
                cell["page"] = t.get("page")
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
            if ct == "component_code" and (
                _is_sheet_index_noise_cell(cell["text"])
                or not (
                    _CODE_RE.match(cell["text"])
                    or _CODE_FIND_RE.search(cell["text"])
                )
            ):
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
    # Perfil DELPI também no caminho token-cluster: papéis por
    # evidência de conteúdo (sem item_band — pivô esparso×denso).
    _assign_presentation_roles(
        [c for r in rows_out for c in r["cells"]],
        col_types,
        item_band=None,
        data_row_count=len(rows_out),
    )
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
    tb_ids = set(id(t) for t in (tb["tokens"] if tb else []))
    # RQ-VAL-027: histórico de revisão detectado ANTES da tabela —
    # códigos citados em histórico (ex.: terminal substituído) nunca
    # são ocorrência vigente de componente.
    revh = _detect_revision_history(tokens, w, h, tb_ids)
    revh_ids = set(id(t) for t in (revh["tokens"] if revh else []))
    table = _detect_component_table(
        tokens, w, h, tb["box"] if tb else None,
        excluded_ids=tb_ids | revh_ids,
    )
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
        if i not in tb_ids and i not in revh_ids
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
        column_crop = _connected_column_crop(table_rows, w, h)
        hier_crop = _hierarchical_code_pair_crop(tokens, w, h)
        boundary_source = "connected_columns"
        # Só substitui quando o envelope connected está page-wide
        # (first-loss P12): em páginas já compactas o par hierárquico
        # pode cortar a coluna errada e regressar A2/A3.
        if hier_crop is not None and column_crop is not None:
            connected_w = column_crop[2] - column_crop[0]
            hier_w = hier_crop[2] - hier_crop[0]
            if connected_w > w * 0.70 and hier_w < connected_w * 0.90:
                column_crop = hier_crop
                boundary_source = "hierarchical_code_columns"
        elif hier_crop is not None and column_crop is None:
            column_crop = hier_crop
            boundary_source = "hierarchical_code_columns"
        if column_crop:
            trimmed = _trim_sheet_index_margin(
                column_crop, tokens, w, h
            )
            if trimmed:
                column_crop = trimmed
            table["box"] = column_crop
            table["boundary_source"] = boundary_source
            graphic_boundary = False
            span = (column_crop[2] - column_crop[0]) * (
                column_crop[3] - column_crop[1]
            )
            if span <= w * h * 0.60:
                table["unreliable_boundary"] = False
            for region in regions:
                if region.get("type") == "component_table":
                    region["box_px"] = column_crop

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

    # ---------- contextos de códigos (RQ-VAL-027) ----------
    # Todo token contendo código 8-11 dígitos ganha região+página —
    # menções em revision_history/notes/title_block são evidência
    # contextual, nunca presença estrutural comparável.
    code_contexts: list[dict] = []
    _ctx_seen: set[tuple] = set()
    for a in annotated:
        for code in _CODE_FIND_RE.findall(a["text"]):
            key = (code, a["region"], a["page"])
            if key in _ctx_seen:
                continue
            _ctx_seen.add(key)
            code_contexts.append(
                {
                    "code": code,
                    "region": a["region"],
                    "page": a["page"],
                    "bounding_box_px": a["bounding_box_px"],
                }
            )

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
        "product_code": product_code,
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
                table.get("boundary_source")
                if table and table.get("boundary_source")
                else (
                    "graphic_rects" if graphic_boundary else "tokens_inferred"
                )
            ),
            "detection": "code_column_cluster + row_y_proximity",
            "confidence": "rule_based",
            "box": list(table["box"]) if table and table.get("box") else None,
            "topology_source": "token_cluster",
            "structure_occurrences": drawing_structure_occurrences(
                table_rows,
                product_code=product_code,
                document_hash=document_hash,
            ),
        },
        "identifier_candidates": fields,
        "code_contexts": code_contexts,
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


def build_document_understanding(
    tokens: list[dict],
    *,
    document_hash: str,
    bom_codes: list[str] | None = None,
    bom_quantities: dict[str, int] | None = None,
    product_code: str | None = None,
    render_size_by_page: dict[int, tuple[int, int]] | None = None,
    graphic_primitives_by_page: dict[int, dict] | None = None,
) -> dict[str, Any]:
    """Understanding de documento multipágina (RQ-VAL-027/029).

    Interpreta cada página separadamente — regiões, tabelas e históricos
    são conceitos por página — e consolida num payload
    ``drawing_understanding.v1`` compatível, com proveniência de página
    em cada linha/região e resumo de cobertura por página."""
    by_page: dict[int, list[dict]] = {}
    for t in tokens:
        p = int(t.get("page") or 1)
        by_page.setdefault(p, []).append(t)
    if not by_page:
        by_page[1] = []

    regions_all: list[dict] = []
    conflicts_all: list[dict] = []
    fields_all: list[dict] = []
    dims_all: list[dict] = []
    excluded_all: list[dict] = []
    revs_all: list[dict] = []
    ctx_all: list[dict] = []
    rows_all: list[dict] = []
    tables_by_page: list[dict] = []
    page_results: list[dict] = []
    tb_labels: list[str] = []
    revh_labels: list[str] = []
    headers_all: list[str] = []
    tb_box = revh_box = None
    ambiguous_cells = 0
    regions_seen: Counter = Counter()
    tokens_processed = 0
    graphic_boundary_any = False
    unreliable_any = False

    for p in sorted(by_page):
        u = build_understanding(
            by_page[p],
            document_hash=document_hash,
            page=p,
            bom_codes=bom_codes,
            bom_quantities=bom_quantities,
            product_code=product_code,
            render_size_px=(render_size_by_page or {}).get(p),
            graphic_primitives=(graphic_primitives_by_page or {}).get(p),
        )
        tokens_processed += u.get("tokens_processed") or 0
        ct = u.get("component_table") or {}
        ambiguous_cells += ct.get("ambiguous_cells") or 0
        graphic_boundary_any = graphic_boundary_any or bool(
            ct.get("graphic_boundary")
        )
        unreliable_any = unreliable_any or bool(
            ct.get("unreliable_boundary")
        )
        tables_by_page.append(
            {
                "page": p,
                "candidate": bool(ct.get("candidate")),
                "row_count": ct.get("row_count") or 0,
                "code_count": ct.get("code_count") or 0,
                "unreliable_boundary": bool(
                    ct.get("unreliable_boundary")
                ),
                "col_types": ct.get("col_types") or {},
                "box": ct.get("box"),
                "topology_source": ct.get("topology_source") or "token_cluster",
            }
        )
        for r in ct.get("rows") or []:
            r2 = dict(r)
            r2["page"] = p
            r2["col_types"] = ct.get("col_types") or {}
            r2["unreliable_boundary"] = bool(ct.get("unreliable_boundary"))
            rows_all.append(r2)
        for reg in u.get("regions") or []:
            reg2 = dict(reg)
            reg2["page"] = p
            regions_all.append(reg2)
        conflicts_all.extend(u.get("ownership_conflicts") or [])
        fields_all.extend(u.get("identifier_candidates") or [])
        dims_all.extend(u.get("dimension_candidates") or [])
        excluded_all.extend(u.get("dimension_excluded") or [])
        revs_all.extend(u.get("revision_candidates") or [])
        ctx_all.extend(u.get("code_contexts") or [])
        regions_seen.update(u.get("regions_summary") or {})
        tb = u.get("title_block") or {}
        if tb.get("candidate"):
            tb_labels = sorted(set(tb_labels) | set(tb.get("labels") or []))
            tb_box = tb_box or tb.get("box_px")
        revh = u.get("revision_history") or {}
        if revh.get("candidate"):
            revh_labels = sorted(
                set(revh_labels) | set(revh.get("labels") or [])
            )
            revh_box = revh_box or revh.get("box_px")
        for htxt in ct.get("headers") or []:
            if htxt not in headers_all:
                headers_all.append(htxt)
        page_results.append(
            {
                "page": p,
                "tokens": len(by_page[p]),
                "component_table_candidate": bool(ct.get("candidate")),
                "component_table_rows": ct.get("row_count") or 0,
                "revision_history_candidate": bool(revh.get("candidate")),
                "title_block_candidate": bool(tb.get("candidate")),
            }
        )

    merged_table = {
        "candidate": any(t["candidate"] for t in tables_by_page),
        "rows": rows_all,
        "row_count": len(rows_all),
        "code_count": sum(t["code_count"] for t in tables_by_page),
        "headers": headers_all,
        "ambiguous_cells": ambiguous_cells,
        "col_types": {
            str(t["page"]): t["col_types"] for t in tables_by_page
        },
        "graphic_boundary": graphic_boundary_any,
        "unreliable_boundary": unreliable_any,
        "boundary_source": (
            "graphic_rects" if graphic_boundary_any else "tokens_inferred"
        ),
        "tables_by_page": tables_by_page,
        "detection": "code_column_cluster + row_y_proximity (per page)",
        "confidence": "rule_based",
        "topology_source": "token_cluster",
        "structure_occurrences": drawing_structure_occurrences(
            rows_all,
            product_code=product_code,
            document_hash=document_hash,
        ),
    }

    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "scope": "multi_page_document",
        "document_hash_sha256": document_hash,
        "product_code": product_code,
        "page": min(by_page),
        "pages_analyzed": sorted(by_page),
        "page_results": page_results,
        "regions": regions_all,
        "ownership_conflicts": conflicts_all,
        "regions_summary": dict(regions_seen),
        "tokens_processed": tokens_processed,
        "title_block": {
            "candidate": tb_box is not None,
            "box_px": tb_box,
            "labels": tb_labels,
            "detection": "label_cluster (≥2 rótulos conhecidos)",
        },
        "component_table": merged_table,
        "identifier_candidates": fields_all,
        "code_contexts": ctx_all,
        "revision_history": {
            "candidate": revh_box is not None,
            "box_px": revh_box,
            "labels": revh_labels,
            "detection": "revhist_label_cluster (≥2 rótulos fora do "
            "carimbo)",
        },
        "revision_candidates": revs_all,
        "dimension_candidates": dims_all,
        "dimension_excluded": excluded_all,
        "bom_comparison": None,
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
            "cobertura por página depende do OCR efetivamente executado "
            "— páginas sem evidência não comprovam ausência",
            "região por estrutura+rótulos — layout atípico pode ainda "
            "classificar errado",
            "tabela candidata parcial não representa BOM completa",
        ],
    }
    return out


def _cell_mixes_quantity_and_code(text: str) -> bool:
    parts = _norm(text).split()
    has_code = any(_CODE_FIND_RE.fullmatch(part) for part in parts)
    has_quantity = any(
        _NUM_RE.fullmatch(part) and not _CODE_FIND_RE.fullmatch(part)
        for part in parts
    )
    return has_code and has_quantity


# Papéis funcionais por célula — o conteúdo vence o índice de coluna
# (SLANet desloca papéis entre linhas: a mesma coluna pode receber
# código numa linha e descrição na seguinte).
# Identificador de item: 1–2 letras com dígitos opcionais (C, A9, AA)
# OU 3–4 letras exigindo dígito (ABC1) — palavras de 3–4 letras sem
# dígito ("CABO", "CAPA") são texto, nunca item.
_ITEM_IDENT_RE = re.compile(
    r"^[A-Za-z]{1,2}\d{0,3}$|^[A-Za-z]{3,4}\d+$"
)
_ITEM_BODY = r"[A-Za-z]{1,2}\d{0,3}|[A-Za-z]{3,4}\d+"
_ITEM_QTY_RE = re.compile(
    r"^(" + _ITEM_BODY + r")\s+(\d{1,4}(?:[.,]\d+)?)$"
)
_QTY_CODE_RE = re.compile(r"^(\d{1,4}(?:[.,]\d+)?)\s+(\d{6,11})$")
_CODE_TAIL_RE = re.compile(r"^(\d{6,11})\s+(\S.*)$")
_ITEM_TAIL_RE = re.compile(r"^(" + _ITEM_BODY + r")\s+(\S.*)$")
_GROUP_CODE_RE = re.compile(r"^(\d{6,11})\b")
# Célula mesclada do bloco-pai pode absorver o rótulo da própria
# coluna estrutural ("Código 90264174"): só prova âncora de grupo
# quando o texto é exatamente ``<rótulo estrutural> <código>`` —
# texto adicional depois do código mantém a célula ambígua.
_GROUP_LABELED_CODE_RE = re.compile(
    r"^(?:c[óo]digo|codigo|cod|conjunto|conj|produto)\.?\s*:?\s*"
    r"(\d{6,11})\s*$",
    re.IGNORECASE,
)
# Letra prefixada ("A 90264061", "B 50225764"): o PaddleOCR funde o
# marcador de zona da folha ou a letra de item ao código quando o texto
# da célula mesclada sai num token atômico (line_texts=null). O par
# letra+código só é evidência de âncora quando a célula já declara
# rowspan>1 — sem o span declarado pode ser par item/código de linha.
_GROUP_PREFIXED_CODE_RE = re.compile(r"^[A-Za-z]{1,2}\s+(\d{6,11})$")


def _group_code_of(text: str) -> str | None:
    """Código líder de célula-âncora de grupo, com ou sem rótulo."""
    m = _GROUP_CODE_RE.match(text) or _GROUP_LABELED_CODE_RE.match(text)
    return m.group(1) if m else None


def _group_anchor_code_of(cell: dict) -> str | None:
    """Código de grupo da célula, incluindo forma prefixada por letra.

    O padrão prefixado só vale como âncora quando ``rowspan>1`` — o
    span declarado é a evidência estrutural que separa ``<letra>
    <código>`` de um par item/código fundido numa linha comum."""
    code = _group_code_of(_norm(str(cell.get("text") or "")))
    if code is not None:
        return code
    if int(cell.get("rowspan") or 1) <= 1:
        return None
    m = _GROUP_PREFIXED_CODE_RE.match(_norm(str(cell.get("text") or "")))
    return m.group(1) if m else None


def _is_group_anchor_cell(cell: dict) -> bool:
    """Célula de bloco-pai: rowspan>1 liderado por código de grupo.

    Rótulo de cabeçalho nunca tem rowspan>1 — uma célula mesclada
    com código na linha de cabeçalho é o bloco-pai projetado sobre
    o índice da primeira linha, não um rótulo."""
    if int(cell.get("rowspan") or 1) <= 1:
        return False
    return _group_anchor_code_of(cell) is not None


def _line_is_canonical_field_band(text: str) -> bool:
    """Banda textual que, sozinha, já é campo tipado de ocorrência.

    Códigos de componente, identificadores de item e quantidades
    numéricas puras entram aqui para que `line_texts` com centros Y
    distintos recuperem linhas fundidas pelo SLANet. Descrição
    multilinha NÃO é canônica.
    """
    line_s = (text or "").strip()
    if not line_s:
        return False
    if _ITEM_QTY_RE.fullmatch(line_s) or _QTY_CODE_RE.fullmatch(line_s):
        return True
    if _ITEM_IDENT_RE.fullmatch(line_s):
        return True
    if _CODE_RE.match(line_s):
        return True
    if _NUM_RE.fullmatch(line_s):
        return True
    return False


def _line_centers_geometrically_distinct(
    centers: list[float], *, min_gap_px: float = 8.0
) -> bool:
    """True quando há separação Y mínima entre bandas consecutivas."""
    if len(centers) < 2:
        return False
    ordered = sorted(float(c) for c in centers)
    gaps = [b - a for a, b in zip(ordered, ordered[1:])]
    return bool(gaps) and min(gaps) >= min_gap_px


def _cell_role(text: str) -> str | None:
    """Papel funcional de UMA célula pelo seu conteúdo — semântica,
    não posição. Nunca promove descrição a código nem vice-versa.

    Índices curtos (`4`, `4 5`) não são `component_code` (gate à parte);
    um número puro continua podendo ser `quantity` — qty 1/2 é legítima.
    """
    if _CODE_FIND_RE.fullmatch(text) or _CODE_RE.match(text):
        return "component_code"
    if _ITEM_IDENT_RE.fullmatch(text):
        return "item"
    if _NUM_RE.fullmatch(text):
        return "quantity"
    if _is_sheet_index_noise_cell(text):
        return None
    if len(text) > 3 and re.search(r"[A-Za-zÀ-ÿ]", text):
        return "description"
    return None


def _cell_cx(cell: dict) -> float | None:
    tcs = cell.get("token_centers") or []
    xs = [
        float(tc[0])
        for tc in tcs
        if isinstance(tc, (list, tuple)) and len(tc) >= 2
    ]
    if xs:
        return sum(xs) / len(xs)
    b = cell.get("bounding_box_px") or []
    if len(b) >= 8:
        xs = [b[0], b[2], b[4], b[6]]
    elif len(b) >= 4:
        xs = [b[0], b[2]]
    else:
        return None
    return (float(min(xs)) + float(max(xs))) / 2.0


def _cell_cy(cell: dict) -> float | None:
    """Centro Y da fonte do campo — token_centers > bbox > banda."""
    if cell.get("_band_cy") is not None:
        return float(cell["_band_cy"])
    tcs = cell.get("token_centers") or []
    ys = [
        float(tc[1])
        for tc in tcs
        if isinstance(tc, (list, tuple)) and len(tc) >= 2
    ]
    if ys:
        return sum(ys) / len(ys)
    b = cell.get("bounding_box_px") or []
    if len(b) >= 8:
        _ys = [b[1], b[3], b[5], b[7]]
    elif len(b) >= 4:
        _ys = [b[1], b[3]]
    else:
        return None
    return (float(min(_ys)) + float(max(_ys))) / 2.0


def _token_ys(cell: dict) -> list[float]:
    ys = []
    for tc in cell.get("token_centers") or []:
        if isinstance(tc, (list, tuple)) and len(tc) >= 2:
            ys.append(float(tc[1]))
    return ys


def _is_group_description_context(
    cell: dict,
    text: str,
    role: str | None,
    *,
    item_band: tuple[float, float] | None,
    description_xs: list[float],
) -> bool:
    """Descrição de conjunto não preenche descrição de componente.

    Âncora de grupo (código longo em rowspan) e texto de descrição à
    esquerda da coluna de item, ou um rowspan de descrição claramente
    à esquerda do cluster de descrições de componente, são contexto
    estrutural. Descrição por linha, à direita do item, permanece
    campo do componente.
    """
    if cell.get("_from_group_anchor"):
        return True
    if role != "description":
        return False
    cx = _cell_cx(cell)
    if item_band is not None and cx is not None and cx < item_band[0] - 4:
        return True
    if int(cell.get("rowspan") or 1) <= 1 or cx is None or not description_xs:
        return False
    ordered = sorted(description_xs)
    median = ordered[len(ordered) // 2]
    return cx < median - 10


def _refresh_row_projection(row: dict) -> None:
    fields = row.get("fields") or {}
    for kind in ("item", "quantity", "component_code", "description"):
        row[kind] = (fields.get(kind) or {}).get("normalized_value")
    conflict = bool(row.get("conflicting_fields"))
    ambiguous = any(
        (f or {}).get("association_state") == "FIELD_AMBIGUOUS"
        for f in fields.values()
    ) or any(c.get("ambiguous") for c in (row.get("cells") or []))
    row["association_conflict"] = conflict
    if conflict or ambiguous:
        row["association_status"] = "INCONCLUSIVE"
    elif fields:
        row["association_status"] = "FIELD_IDENTIFIED"
    else:
        row["association_status"] = "UNRESOLVED"


def _rehome_across_bands(rows: list[dict], band_gap: float) -> None:
    """Move um campo órfão para a única linha cuja banda Y combina.

    Não funde campos que já têm vizinhos na própria banda. Exige um
    único destino. Conflito restante permanece explícito.
    """
    kinds = ("item", "quantity", "component_code", "description")

    def anchor(row: dict) -> float | None:
        cys = [
            f.get("source_cy_px")
            for f in (row.get("fields") or {}).values()
            if isinstance(f, dict) and f.get("source_cy_px") is not None
        ]
        if not cys:
            return None
        cys.sort()
        return cys[len(cys) // 2]

    for kind in kinds:
        for src in rows:
            conflict = src.setdefault("conflicting_fields", {})
            sources = []
            if isinstance(conflict.get(kind), dict):
                sources.append((conflict, True))
            own = (src.get("fields") or {}).get(kind)
            if isinstance(own, dict):
                sources.append((src.get("fields") or {}, False))
            for bucket, from_conflict in sources:
                field = bucket.get(kind)
                if not isinstance(field, dict):
                    continue
                cy = field.get("source_cy_px")
                if cy is None:
                    continue
                siblings = [
                    f
                    for key, f in (src.get("fields") or {}).items()
                    if key != kind
                    and isinstance(f, dict)
                    and f.get("source_cy_px") is not None
                ]
                if (
                    not from_conflict
                    and siblings
                    and all(
                        abs(f["source_cy_px"] - cy) <= band_gap
                        for f in siblings
                    )
                ):
                    continue
                targets = []
                for dst in rows:
                    if dst is src or kind in (dst.get("fields") or {}):
                        continue
                    dst_anchor = anchor(dst)
                    if dst_anchor is None or abs(dst_anchor - cy) > band_gap:
                        continue
                    targets.append(dst)
                if len(targets) != 1:
                    continue
                dst = targets[0]
                bucket.pop(kind, None)
                field["association_state"] = "FIELD_IDENTIFIED"
                field["association_method"] = (
                    str(field.get("association_method") or "native_cell")
                    + "+band_rehome"
                )
                dst.setdefault("fields", {})[kind] = field
                _refresh_row_projection(src)
                _refresh_row_projection(dst)


def _role_band(xs: list[float], pad: float = 12.0):
    """Banda-X do papel funcional — núcleo das colunas observadas
    (descarta ~16% das caudas), para rejeitar células do papel certo
    na posição errada (ex.: item solto na coluna de produto)."""
    if len(xs) < 4:
        return None
    s = sorted(xs)
    i = max(1, len(s) // 6)
    core = s[i:len(s) - i] if len(s) - 2 * i > 0 else s
    return (min(core) - pad, max(core) + pad)


# Perfil de apresentação DELPI — papéis semânticos das colunas de uma
# tabela de estrutura de produto (EVA VAL-01 / Doc 116 §B.9). O bloco
# do pai (código + descrição esparsos) fica à esquerda do bloco de
# ocorrências (item/quantidade/componente/descrição, denso). O perfil
# orienta a interpretação — a geometria SLANet/OCR continua sendo a
# evidência de linhas, colunas e spans; sem prova, nenhum papel é
# atribuído.
DELPI_TABLE_PRESENTATION = {
    "profile_id": "delpi_structure_table",
    "parent_roles": ("parent_code", "parent_description"),
    "occurrence_roles": (
        "item", "quantity", "component_code", "description",
    ),
    "optional_roles": ("cable", "unit", "reference", "note"),
}

_PARENT_ROLES = frozenset({"parent_code", "parent_description"})


def _cell_text(c: dict) -> str:
    return _norm(
        str(
            c["_split_text"]
            if c.get("_split_done")
            else (c.get("text") or "")
        )
    )


def _col_median_cx(cells: list[dict], col: int) -> float | None:
    xs = [
        cx
        for c in cells
        if int(c.get("col") or 0) == col
        for cx in [_cell_cx(c)]
        if cx is not None
    ]
    if not xs:
        return None
    xs.sort()
    return xs[len(xs) // 2]


def _assign_presentation_roles(
    cells: list[dict],
    col_types: dict[int, str],
    *,
    item_band: tuple[float, float] | None,
    data_row_count: int,
) -> dict | None:
    """Atribui papéis do perfil DELPI às colunas tipadas.

    A coluna de código do **pai** é comprovada pela mesma evidência
    que a âncora esparsa já exigia: ≥2 células lideradas por código,
    materialmente menos densa que a coluna de componentes e posicionada
    no bloco do pai (à esquerda da banda de item quando presente, senão
    à esquerda da coluna densa). Descrição no mesmo bloco vira
    ``parent_description``. Sem essa prova, ``col_types`` permanece e
    o chamador se abstém do papel — o perfil não inventa posição.
    """
    if data_row_count < 4:
        return None
    codes_by_col: dict[int, list[tuple[float | None, dict]]] = {}
    stats: dict[int, Counter] = {}
    for c in cells:
        col = int(c.get("col") or 0)
        text = _cell_text(c)
        if not text:
            continue
        st = stats.setdefault(col, Counter())
        st["total"] += 1
        group_code = _group_code_of(text)
        if group_code is None:
            # Âncora prefixada (letra de zona/item fundida ao código)
            # só conta quando rowspan>1 comprova a mesclagem; após o
            # split, a banda na linha pode conter só o rótulo — a
            # identidade de grupo vem do texto original.
            group_code = _group_anchor_code_of(c) or (
                _group_code_of(_norm(str(c.get("text") or "")))
                if c.get("_from_group_anchor")
                else None
            )
        if group_code is not None:
            st["codes"] += 1
            if int(c.get("rowspan") or 1) > 1:
                st["code_rowspans"] += 1
            codes_by_col.setdefault(col, []).append((_cell_cx(c), c))
        elif _cell_role(text) == "description":
            st["descriptions"] += 1
    if not codes_by_col:
        return None
    counts = {col: len(v) for col, v in codes_by_col.items()}
    densest_n = max(counts.values())
    if densest_n < 3:
        return None
    dense_cols = [c for c, n in counts.items() if n == densest_n]
    dense_xs = [
        cx
        for dc in dense_cols
        for cx, _c in codes_by_col[dc]
        if cx is not None
    ]
    densest_mid = (
        sorted(dense_xs)[len(dense_xs) // 2] if dense_xs else None
    )
    item_mid = (
        (item_band[0] + item_band[1]) / 2.0 if item_band else None
    )
    # Lado componente: coluna de código à direita da banda de item —
    # na semântica DELPI o bloco pai (Código|Descrição) fica à
    # esquerda de Item|QTD|Componente|Descrição.
    right_code_cols = []
    if item_mid is not None:
        for col in sorted(counts):
            xs = [cx for cx, _c in codes_by_col[col] if cx is not None]
            if xs and sorted(xs)[len(xs) // 2] > item_mid + 4.0:
                right_code_cols.append(col)
    parent_col = None
    pivot = None
    if item_mid is not None and right_code_cols:
        # Com a banda de item como pivô, a posição separa os blocos:
        # código à esquerda do item é lado pai, à direita é lado
        # componente. A densidade deixa de ser prova — conjuntos
        # pequenos repetem código de pai quase linha a linha, e a
        # coluna de componentes pode colapsar (QTD+Componente fundidas)
        # sem deixar de existir. Preferência: coluna com mais âncoras
        # (evidência mais forte), depois a mais à esquerda.
        # Coluna mista (componentes avulsos + conjuntos na mesma
        # coluna) não pode ser tipada pai inteira — código de linha
        # sem componente em outra coluna nas linhas que ele cobre é
        # evidência de papel ambíguo → veto fail-closed.
        rows_map: dict[int, list[dict]] = {}
        for c in cells:
            rows_map.setdefault(int(c.get("row") or 0), []).append(c)

        def _col_has_loose_codes(col: int) -> bool:
            for _cx, cell in codes_by_col[col]:
                row = int(cell.get("row") or 0)
                rowspan = max(1, int(cell.get("rowspan") or 1))
                companion = False
                # Janela row..row+rowspan: célula rs1 que ABRE um bloco
                # (rótulo fundido ao primeiro código, ou banda rehomed
                # uma linha abaixo) encontra o componente na linha
                # seguinte — código avulso de componente não encontra.
                for r in range(row, row + rowspan + 1):
                    for c2 in rows_map.get(r, []):
                        if c2 is cell or int(c2.get("col") or 0) == col:
                            continue
                        t2 = _cell_text(c2)
                        if _CODE_RE.search(t2) or _QTY_CODE_RE.fullmatch(
                            t2
                        ):
                            companion = True
                            break
                    if companion:
                        break
                if not companion:
                    return True
            return False

        candidates: list[tuple[int, int]] = []
        for col in sorted(counts):
            n = counts[col]
            if n < 2 and not stats[col]["code_rowspans"]:
                continue
            xs = [cx for cx, _c in codes_by_col[col] if cx is not None]
            if not xs:
                continue
            if sorted(xs)[len(xs) // 2] >= item_mid - 4.0:
                continue
            if _col_has_loose_codes(col):
                continue
            candidates.append((col, n))
        if candidates:
            candidates.sort(key=lambda cn: (-cn[1], cn[0]))
            parent_col = candidates[0][0]
            pivot = "item_band"
    else:
        for col in sorted(counts):
            if col in dense_cols:
                continue
            n = counts[col]
            # ≥2 âncoras provam esparsidade; uma única âncora rowspan
            # declarada pelo SLANet também é prova de bloco pai.
            if n < 2 and not stats[col]["code_rowspans"]:
                continue
            if n >= max(3, int(0.45 * data_row_count)):
                continue
            if densest_n < n + 2 or densest_mid is None:
                continue
            sparse_xs = [
                cx for cx, _c in codes_by_col[col] if cx is not None
            ]
            if not sparse_xs:
                continue
            sparse_mid = sorted(sparse_xs)[len(sparse_xs) // 2]
            if item_mid is not None:
                if sparse_mid >= item_mid - 4.0:
                    continue
                pivot = "item_band"
            else:
                if sparse_mid >= densest_mid - 8.0:
                    continue
                pivot = "sparse_dense_columns"
            parent_col = col
            break
    if parent_col is None:
        return None
    col_types[parent_col] = "parent_code"
    parent_mid = _col_median_cx(cells, parent_col)
    ref_right = item_mid if item_mid is not None else densest_mid
    parent_desc_cols: list[int] = []
    for col, st in sorted(stats.items()):
        if col == parent_col or col in dense_cols or st["codes"]:
            continue
        if not st["descriptions"]:
            continue
        mid = _col_median_cx(cells, col)
        if mid is None or parent_mid is None or ref_right is None:
            continue
        if parent_mid - 4.0 <= mid < ref_right - 4.0:
            col_types[col] = "parent_description"
            parent_desc_cols.append(col)
    return {
        "profile_id": DELPI_TABLE_PRESENTATION["profile_id"],
        "parent_code_col": parent_col,
        "parent_description_cols": parent_desc_cols,
        "component_code_cols": sorted(dense_cols),
        "pivot": pivot,
        "confidence": "rule_based",
    }


def rows_from_native_cells(
    cells: list[dict],
    *,
    page: int,
    profile_out: dict | None = None,
    marker_tokens: list[dict] | None = None,
) -> tuple[list[dict], dict[str, str]]:
    """Linhas do Understanding a partir da grade nativa.

    O índice de linha é o do framework. Texto de uma célula com
    rowspan permanece na linha âncora. Quantidade e código na mesma
    célula não são separados: a associação de atributos fica
    inconclusiva.
    """
    grouped: dict[int, list[dict]] = {}
    for cell in cells:
        grouped.setdefault(int(cell.get("row") or 0), []).append(cell)
    header_row = None
    header_score = 0
    for row_index, row_cells in grouped.items():
        score = sum(
            1
            for cell in row_cells
            if _header_type(_norm(str(cell.get("text") or "")))
        )
        if score > header_score:
            header_score = score
            header_row = row_index
    # Célula nativa cobrindo múltiplas bandas Y de tokens (colunas
    # estreitas fundidas, ex.: "C 6 D 3" com rowspan=1 OU >1): cada
    # banda é redistribuída para a linha nativa cujo centroide Y é o
    # mais próximo — evidência geométrica, independente do rowspan.
    # O centroide por linha usa apenas células sem split (colunas
    # confiáveis, ex.: códigos). Bandas que mapeiam para a MESMA
    # linha permanecem juntas — descrição multilinha legítima não é
    # dividida.
    row_cy: dict[int, float] = {}
    row_spans: dict[int, list[tuple[float, float]]] = {}
    for row_index, row_cells in grouped.items():
        if row_index == header_row:
            continue
        cys = []
        for c in row_cells:
            if c.get("line_texts") or int(c.get("rowspan") or 1) > 1:
                continue
            # token_centers delimitam a banda real. O polígono SLANet
            # de uma célula fundida cobre várias linhas e não pode
            # "conter" bandas de outros componentes.
            token_ys = _token_ys(c)
            if token_ys:
                pad = 4.0
                lo, hi = min(token_ys) - pad, max(token_ys) + pad
                cys.extend(token_ys)
            else:
                b = c.get("bounding_box_px") or []
                if len(b) >= 8:
                    _ys = [b[1], b[3], b[5], b[7]]
                elif len(b) >= 4:
                    _ys = [b[1], b[3]]
                else:
                    continue
                lo, hi = float(min(_ys)), float(max(_ys))
                cys.append((lo + hi) / 2.0)
            row_spans.setdefault(row_index, []).append((lo, hi))
        if cys:
            row_cy[row_index] = sum(cys) / len(cys)
    def _rebuild_row_geometry() -> tuple[float, float]:
        row_cy.clear()
        row_spans.clear()
        for ri, rcells in grouped.items():
            if ri == header_row:
                continue
            cys: list[float] = []
            for c in rcells:
                if c.get("line_texts") and not c.get("_split_done"):
                    continue
                if int(c.get("rowspan") or 1) > 1 and not c.get(
                    "_split_done"
                ):
                    continue
                token_ys = _token_ys(c)
                if token_ys:
                    pad = 4.0
                    lo, hi = min(token_ys) - pad, max(token_ys) + pad
                    cys.extend(token_ys)
                else:
                    b = c.get("bounding_box_px") or []
                    if len(b) >= 8:
                        _ys = [b[1], b[3], b[5], b[7]]
                    elif len(b) >= 4:
                        _ys = [b[1], b[3]]
                    else:
                        continue
                    lo, hi = float(min(_ys)), float(max(_ys))
                    cys.append((lo + hi) / 2.0)
                row_spans.setdefault(ri, []).append((lo, hi))
            if cys:
                row_cy[ri] = sum(cys) / len(cys)
        cy_vals = sorted(row_cy.values())
        steps = [b - a for a, b in zip(cy_vals, cy_vals[1:]) if b - a > 1]
        steps.sort()
        return (steps[len(steps) // 2] if steps else 0.0), (
            0.6 * (steps[len(steps) // 2] if steps else 0.0)
            if steps
            else 12.0
        )

    def _split_multiline_cells(*, description_pass: bool) -> None:
        prelim_step, _gap = _rebuild_row_geometry()
        for row_index, row_cells in list(grouped.items()):
            for cell in list(row_cells):
                if cell.get("_split_done"):
                    continue
                lines = cell.get("line_texts") or []
                centers = cell.get("line_centers") or []
                if not (len(lines) > 1 and len(centers) == len(lines)):
                    continue
                all_canonical = all(
                    _line_is_canonical_field_band(str(line).strip())
                    for line in lines
                )
                # 1ª passagem: só bandas canônicas (item/qtd/código).
                # 2ª: descrições multilinha, depois que row_cy reflete
                # as linhas físicas já recuperadas.
                if description_pass == all_canonical:
                    continue
                source_text = _norm(str(cell.get("text") or ""))
                from_group = bool(
                    int(cell.get("rowspan") or 1) > 1
                    and _group_anchor_code_of(cell)
                )
                if from_group:
                    cell["_from_group_anchor"] = True
                targets: dict[int, list[tuple[int, str]]] = {}
                for line_i, (line, cy) in enumerate(zip(lines, centers)):
                    hits = [
                        r
                        for r, spans in row_spans.items()
                        if any(
                            lo - 1.0 <= cy <= hi + 1.0 for lo, hi in spans
                        )
                    ]
                    if len(hits) == 1:
                        target = hits[0]
                    elif row_cy:
                        target = min(
                            row_cy, key=lambda r: abs(row_cy[r] - cy)
                        )
                        _steps = sorted(row_cy.values())
                        _step = (
                            _steps[len(_steps) // 2] - _steps[0]
                            if len(_steps) > 1
                            else 0.0
                        )
                        if (
                            _step
                            and abs(row_cy[target] - cy) > 0.6 * _step
                        ):
                            target = row_index
                    else:
                        target = row_index
                    line_s = line.strip()
                    canonical = _line_is_canonical_field_band(line_s)
                    gap_lim = (
                        0.6 * prelim_step if prelim_step else 12.0
                    )
                    if len(hits) != 1 and not canonical:
                        # Descrição multilinha: só acompanha âncora de
                        # item/código quando o desvio Y cabe no vão das
                        # próprias bandas de descrição — evita saltar
                        # para código de outra ocorrência (TUBO FLEX).
                        if description_pass and row_cy:
                            nearest = min(
                                row_cy,
                                key=lambda r: abs(row_cy[r] - cy),
                            )
                            desc_span = (
                                float(max(centers)) - float(min(centers))
                                if centers
                                else 0.0
                            )
                            lim = max(
                                8.0,
                                min(gap_lim, 0.75 * desc_span + 4.0)
                                if desc_span > 4.0
                                else 8.0,
                            )
                            own_cy = row_cy.get(row_index)
                            if (
                                own_cy is not None
                                and abs(own_cy - cy)
                                <= abs(row_cy[nearest] - cy)
                            ):
                                target = row_index
                            elif abs(row_cy[nearest] - cy) <= lim:
                                target = nearest
                            else:
                                target = row_index
                        else:
                            target = row_index
                    ref_cy = row_cy.get(target)
                    if (
                        canonical
                        and ref_cy is not None
                        and abs(ref_cy - cy) > max(gap_lim, 8.0)
                    ):
                        target = 500000 + int(round(cy * 10))
                    targets.setdefault(int(target), []).append(
                        (line_i, line)
                    )
                if (
                    len(targets) < 2
                    and len(lines) > 1
                    and all_canonical
                    and _line_centers_geometrically_distinct(
                        [float(c) for c in centers]
                    )
                ):
                    targets = {}
                    for line_i, (line, cy) in enumerate(
                        zip(lines, centers)
                    ):
                        targets.setdefault(
                            500000 + int(round(float(cy) * 10)), []
                        ).append((line_i, line))
                if len(targets) < 2:
                    continue
                cell["_split_done"] = True
                stayed = targets.get(row_index, [])
                cell["_split_text"] = " ".join(
                    text for _i, text in stayed
                )
                cell["line_texts"] = []
                source_tcs = [
                    tc
                    for tc in (cell.get("token_centers") or [])
                    if isinstance(tc, (list, tuple)) and len(tc) >= 2
                ]
                source_cx = _cell_cx(cell) or 0.0
                if stayed:
                    cell["_band_cy"] = sum(
                        float(centers[i]) for i, _text in stayed
                    ) / len(stayed)
                    if len(source_tcs) == len(lines):
                        cell["token_centers"] = [
                            source_tcs[i] for i, _text in stayed
                        ]
                else:
                    cell["token_centers"] = []
                for target, tlines in targets.items():
                    if target == row_index:
                        continue
                    virtual = dict(cell)
                    virtual["_split_done"] = True
                    virtual["_split_text"] = " ".join(
                        text for _i, text in tlines
                    )
                    virtual["line_texts"] = []
                    virtual["rowspan"] = 1
                    virtual["_from_group_anchor"] = from_group
                    virtual["_detached_band"] = target >= 500000
                    virtual["_rehomed_from_row"] = row_index
                    virtual["_band_cy"] = sum(
                        float(centers[i]) for i, _text in tlines
                    ) / len(tlines)
                    if len(source_tcs) == len(lines):
                        virtual["token_centers"] = [
                            source_tcs[i] for i, _text in tlines
                        ]
                    else:
                        virtual["token_centers"] = [
                            [source_cx, float(centers[i])]
                            for i, _text in tlines
                        ]
                    grouped.setdefault(target, []).append(virtual)

    _split_multiline_cells(description_pass=False)
    _split_multiline_cells(description_pass=True)
    col_types: dict[int, str] = {}
    if header_row is not None:
        for cell in grouped[header_row]:
            kind = _header_type(_norm(str(cell.get("text") or "")))
            if kind:
                col_types[int(cell.get("col") or 0)] = kind
    content_counts: dict[int, Counter] = {}
    for row_index, row_cells in grouped.items():
        if row_index == header_row:
            continue
        for cell in row_cells:
            col = int(cell.get("col") or 0)
            bucket = content_counts.setdefault(col, Counter())
            bucket["total"] += 1
            if _CODE_RE.search(_norm(str(cell.get("text") or ""))):
                bucket["codes"] += 1
    for col, bucket in content_counts.items():
        if bucket["total"] and bucket["codes"] / bucket["total"] >= 0.5:
            col_types[col] = "component_code"
    # Bandas-X por papel funcional — conteúdo primeiro, posição como
    # salvaguarda contra papel certo na posição errada.
    role_x: dict[str, list[float]] = {}
    for row_index, row_cells in grouped.items():
        if row_index == header_row:
            continue
        for c in row_cells:
            t = _norm(
                str(c.get("_split_text") or c.get("text") or "")
            )
            r = _cell_role(t)
            cx = _cell_cx(c)
            if r and cx is not None:
                role_x.setdefault(r, []).append(cx)
    role_bands = {r: _role_band(xs) for r, xs in role_x.items()}
    # Perfil DELPI (VAL-01): papéis de coluna por evidência de conteúdo
    # + posição relativa — pai esparso à esquerda do item, componente
    # denso à direita. Sem prova suficiente a tipagem atual permanece.
    data_row_indices = sorted(
        i for i in grouped if i != header_row
    )
    # Células-âncora do bloco-pai podem ser projetadas no índice da
    # linha de cabeçalho (rótulo da coluna absorvido pela mesclagem):
    # entram na estatística do perfil porque são dados estruturais,
    # não rótulos — rótulo de cabeçalho nunca tem rowspan>1.
    profile_cells = [
        c for ri in data_row_indices for c in grouped[ri]
    ]
    if header_row is not None:
        profile_cells.extend(
            c for c in grouped[header_row] if _is_group_anchor_cell(c)
        )
    profile_meta = _assign_presentation_roles(
        profile_cells,
        col_types,
        item_band=role_bands.get("item"),
        data_row_count=len(data_row_indices),
    )
    if isinstance(profile_out, dict) and profile_meta:
        profile_out.update(profile_meta)
    # Âncoras de grupo: célula rowspan>1 iniciando por código longo.
    # Linhas abaixo herdam a âncora vigente; sobreposição resolve-se
    # pela âncora mais recente (subconjunto aninhado).
    group_anchors: list[tuple[int, str, int, str]] = []
    group_anchor_ids: set[int] = set()
    group_y_anchors: list[tuple[float, str]] = []

    def _group_anchor_cy(cell: dict) -> float | None:
        tcs = cell.get("token_centers") or []
        ys = [
            float(tc[1])
            for tc in tcs
            if isinstance(tc, (list, tuple)) and len(tc) >= 2
        ]
        if ys:
            return sum(ys) / len(ys)
        return _cell_cy(cell)

    anchor_col_rows: dict[int, set[int]] = {}

    def _register_group_anchor(
        row_index: int, code: str, span: int, cell: dict, source: str
    ) -> None:
        group_anchors.append((row_index, code, span, source))
        group_anchor_ids.add(id(cell))
        if source == "rowspan_anchor":
            anchor_col_rows.setdefault(
                int(cell.get("col") or 0), set()
            ).add(row_index)
        cy = _group_anchor_cy(cell)
        if cy is not None:
            group_y_anchors.append((cy, code))

    # A âncora pode viver na linha de cabeçalho (bloco mesclado
    # absorvendo o rótulo): rowspan>1 + código de grupo já exclui
    # qualquer rótulo de header, então a linha não é pulada.
    for row_index, row_cells in grouped.items():
        for c in row_cells:
            anchor_code = (
                _group_anchor_code_of(c)
                if _is_group_anchor_cell(c)
                else None
            )
            if anchor_code:
                _register_group_anchor(
                    row_index, anchor_code, int(c.get("rowspan") or 1), c,
                    "rowspan_anchor",
                )
    # Âncora por papel de coluna (perfil DELPI): célula liderada por
    # código na coluna tipada ``parent_code`` ancora até a próxima
    # âncora da mesma coluna (span explícito do rowspan quando >1).
    # A prova de esparsa×densa e posição já foi feita por
    # ``_assign_presentation_roles`` — aqui só se lê o papel.
    parent_code_cols = sorted(
        int(c) for c, t in col_types.items() if t == "parent_code"
    )
    for pcol in parent_code_cols:
        entries: list[tuple[int, str, dict]] = []
        entry_rows = list(data_row_indices)
        # O rótulo da coluna pode absorver o primeiro código de grupo
        # ("Código 50215397" no header): na semântica DELPI esse código
        # abre o primeiro bloco pai — entra como âncora mesmo na linha
        # de cabeçalho.
        if header_row is not None:
            entry_rows = [header_row] + entry_rows
        for row_index in entry_rows:
            for c in grouped[row_index]:
                if int(c.get("col") or 0) != pcol:
                    continue
                if id(c) in group_anchor_ids:
                    continue
                # Fragmento de banda de uma âncora já registrada é
                # contexto dela — nunca reancora um novo grupo.
                if c.get("_from_group_anchor"):
                    continue
                anchor_code = _group_anchor_code_of(c) or _group_code_of(
                    _cell_text(c)
                )
                if anchor_code:
                    entries.append((row_index, anchor_code, c))
        entries.sort(key=lambda e: e[0])
        # Fronteira do bloco = próximo âncora de QUALQUER tipo na
        # coluna-pai — rowspan declarado também encerra o bloco
        # anterior, mesmo quando foi excluído das entradas por já ser
        # âncora registrada.
        boundary_rows = sorted(
            {e[0] for e in entries} | anchor_col_rows.get(pcol, set())
        )
        for i, (row_index, code, cell) in enumerate(entries):
            span = int(cell.get("rowspan") or 1)
            if span <= 1:
                next_row = next(
                    (r for r in boundary_rows if r > row_index),
                    data_row_indices[-1] + 1,
                )
                span = int(next_row) - int(row_index)
            # Cada código da coluna-pai abre um bloco que termina no
            # próximo código — bloco de uma única linha é legítimo
            # (uma linha SLANet pode ainda carregar várias bandas de
            # componentes fundidas). Mas código de linha avulsa na
            # mesma coluna de conjuntos NÃO é pai: o bloco precisa
            # conter código de componente em coluna diferente, senão o
            # próprio código é o componente da linha.
            if span < 1:
                continue
            has_component_code = False
            for r in range(row_index, row_index + span):
                for c2 in grouped.get(r, []):
                    if int(c2.get("col") or 0) == pcol:
                        continue
                    t2 = _cell_text(c2)
                    if _CODE_RE.search(t2) or _QTY_CODE_RE.fullmatch(t2):
                        has_component_code = True
                        break
                if has_component_code:
                    break
            if not has_component_code:
                continue
            _register_group_anchor(
                row_index, code, span, cell, "column_span",
            )
    # Sobreposição resolve-se pela âncora mais recente; em empate de
    # linha, a âncora estrutural declarada (rowspan) prevalece sobre a
    # inferida por coluna (column_span) — o span declarado é evidência
    # mais forte que a extensão até o próximo código.
    _ANCHOR_RANK = {"column_span": 0, "rowspan_anchor": 1}
    group_anchors.sort(
        key=lambda a: (a[0], _ANCHOR_RANK.get(a[3], 0), a[1])
    )
    group_y_anchors.sort(key=lambda a: a[0])
    # Passo mediano entre linhas — escala para decidir se dois campos
    # vêm de bandas Y compatíveis (mesma linha física) ou conflitantes.
    row_cys = []
    for row_index, row_cells in grouped.items():
        if row_index == header_row:
            continue
        cys = [
            cy for cy in (_cell_cy(c) for c in row_cells) if cy is not None
        ]
        if cys:
            row_cys.append(min(cys))
    row_cys.sort()
    steps = [b - a for a, b in zip(row_cys, row_cys[1:]) if b - a > 1]
    steps.sort()
    median_step = steps[len(steps) // 2] if steps else 18.0
    band_gap_px = median_step * 0.6
    rows_out: list[dict] = []
    for row_index in sorted(grouped):
        if row_index == header_row:
            continue
        row_cells = sorted(
            grouped[row_index], key=lambda cell: int(cell.get("col") or 0)
        )
        if not any(_norm(str(cell.get("text") or "")) for cell in row_cells):
            continue
        fields: dict[str, dict] = {}
        published = []
        inconclusive = False
        parked: list[tuple[str, dict]] = []

        def _field(value: str, cell: dict, method: str) -> dict:
            return {
                "raw_text": value,
                "normalized_value": value,
                "bounding_box_px": cell.get("bounding_box_px"),
                "source_cy_px": _cell_cy(cell),
                "col": int(cell.get("col") or 0),
                "rehomed_from_row": cell.get("_rehomed_from_row"),
                "association_method": method,
                "association_state": "FIELD_IDENTIFIED",
            }

        def _fits_row(kind: str, cy: float | None) -> bool:
            if cy is None:
                return False
            siblings = [
                f.get("source_cy_px")
                for key, f in fields.items()
                if key != kind and f.get("source_cy_px") is not None
            ]
            return bool(siblings) and all(
                abs(other - cy) <= band_gap_px for other in siblings
            )

        def _put(kind: str, value: str, cell: dict, method: str) -> None:
            nonlocal inconclusive
            incoming = _field(value, cell, method)
            if kind not in fields:
                fields[kind] = incoming
                return
            if fields[kind].get("normalized_value") == value:
                return
            old_cy = fields[kind].get("source_cy_px")
            new_cy = incoming.get("source_cy_px")
            if (
                new_cy is not None
                and old_cy is not None
                and abs(new_cy - old_cy) > band_gap_px
            ):
                # Mesmo papel, bandas diferentes: o que combina com a
                # linha fica; o outro aguarda rehome. Não vira tupla.
                if _fits_row(kind, new_cy) and not _fits_row(kind, old_cy):
                    parked.append((kind, fields[kind]))
                    fields[kind] = incoming
                else:
                    parked.append((kind, incoming))
                return
            inconclusive = True
            fields[kind]["association_state"] = "FIELD_AMBIGUOUS"

        for cell in row_cells:
            text = _norm(
                str(
                    cell["_split_text"]
                    if cell.get("_split_done")
                    else (cell.get("text") or "")
                )
            )
            col = int(cell.get("col") or 0)
            mixed = _cell_mixes_quantity_and_code(text)
            if cell.get("ambiguous"):
                inconclusive = True
            if not text:
                continue
            role = _cell_role(text)
            parent_role = col_types.get(col)
            parent_col_cell = parent_role in _PARENT_ROLES
            group_context = (
                parent_col_cell
                or id(cell) in group_anchor_ids
                or _is_group_description_context(
                    cell,
                    text,
                    role,
                    item_band=role_bands.get("item"),
                    description_xs=role_x.get("description") or [],
                )
            )
            if group_context:
                # Contexto de grupo não entra na tupla do componente —
                # o papel do bloco pai permanece como evidência.
                role = None
                kind = parent_role if parent_col_cell else None
            elif role:
                band = role_bands.get(role)
                cx = _cell_cx(cell)
                # Banda-X só veta o papel 'item' (ruído de rótulos soltos
                # na coluna de produto). Código/descrição seguem o
                # conteúdo — fullmatch de código é evidência forte.
                if role == "item" and band is not None and cx is not None:
                    kind = role if band[0] <= cx <= band[1] else col_types.get(col)
                else:
                    kind = role
            else:
                kind = col_types.get(col)
            published.append(
                {
                    "text": text,
                    "col": col,
                    "row": row_index,
                    "rowspan": cell.get("rowspan") or 1,
                    "colspan": cell.get("colspan") or 1,
                    "bounding_box_px": cell.get("bounding_box_px"),
                    "col_type": kind,
                    "page": page,
                    "token_refs": cell.get("token_refs") or [],
                    "ambiguous": bool(
                        cell.get("ambiguous")
                        or (mixed and kind not in ("quantity",))
                    ),
                }
            )
            # Formas canônicas de célula fundida — a divisão de campos
            # segue a geometria da célula (mesmo retângulo, tokens
            # adjacentes), nunca a string esperada. Em contexto de
            # grupo a agregação nativa pode misturar o token de item
            # (direita) com a descrição do conjunto (esquerda): extrai
            # só o identificador/quantidade; o restante não vira
            # description de componente. O Y do campo item segue o
            # token na banda-X de item, não a média com a descrição.
            def _item_source_cell() -> dict:
                # Célula já destacada por banda (split de line_texts)
                # preserva o Y da linha; não reescolhe entre todos os
                # token_centers do retângulo pai.
                if cell.get("_band_cy") is not None:
                    return cell
                item_band = role_bands.get("item")
                tcs = [
                    tc for tc in (cell.get("token_centers") or [])
                    if isinstance(tc, (list, tuple)) and len(tc) >= 2
                ]
                if len(tcs) < 2 or item_band is None:
                    return cell
                mid = (item_band[0] + item_band[1]) / 2.0
                ranked = sorted(
                    tcs,
                    key=lambda tc: (
                        0
                        if item_band[0] <= float(tc[0]) <= item_band[1]
                        else 1,
                        abs(mid - float(tc[0])),
                    ),
                )
                chosen = dict(cell)
                chosen["_band_cy"] = float(ranked[0][1])
                return chosen

            m = _ITEM_QTY_RE.fullmatch(text)
            if m:
                src = _item_source_cell()
                _put("item", m.group(1), src, "native_cell_pair")
                _put("quantity", m.group(2), src, "native_cell_pair")
                continue
            m = _ITEM_TAIL_RE.fullmatch(text)
            if m and _ITEM_IDENT_RE.fullmatch(m.group(1)):
                _put(
                    "item", m.group(1), _item_source_cell(),
                    "native_cell_partial",
                )
                continue
            if group_context:
                continue
            m = _QTY_CODE_RE.fullmatch(text)
            if m:
                _put("quantity", m.group(1), cell, "native_cell_pair")
                _put(
                    "component_code", m.group(2), cell,
                    "native_cell_pair",
                )
                continue
            m = _CODE_TAIL_RE.fullmatch(text)
            if m and re.search(r"[A-Za-zÀ-ÿ]", m.group(2)):
                _put(
                    "component_code", m.group(1), cell,
                    "native_cell_pair",
                )
                _put("description", m.group(2), cell, "native_cell_pair")
                continue
            if not kind:
                continue
            # Célula qty+código fundidos: só os pares canônicos acima
            # separam campos. Descrição com números/código citado no
            # texto continua descrição — não abster o campo inteiro.
            if mixed and kind != "description":
                continue
            # Índices de folha/quadro nunca são código de componente,
            # mesmo quando a coluna tipada é component_code.
            if kind == "component_code" and _is_sheet_index_noise_cell(
                text
            ):
                continue
            if kind == "component_code" and not (
                _CODE_RE.match(text)
                or _CODE_FIND_RE.search(text)
                or _GROUP_CODE_RE.match(text)
            ):
                continue
            _put(kind, text, cell, "native_cell")
        # Coerência geométrica da tupla: campos projetados no mesmo
        # índice SLANet mas oriundos de bandas Y incompatíveis não
        # formam associação — os de banda minoritária saem da tupla e
        # ficam registrados como conflito, sem promoção.
        conflicting_fields: dict[str, dict] = {}
        band_groups: list[list[str]] = []
        for kind in ("item", "quantity", "component_code", "description"):
            cy = (fields.get(kind) or {}).get("source_cy_px")
            if cy is None:
                continue
            placed = False
            for grp in band_groups:
                rep = (fields[grp[0]] or {}).get("source_cy_px")
                if rep is not None and abs(cy - rep) <= band_gap_px:
                    grp.append(kind)
                    placed = True
                    break
            if not placed:
                band_groups.append([kind])
        if len(band_groups) > 1:
            dominant = max(band_groups, key=len)
            for grp in band_groups:
                if grp is dominant:
                    continue
                for kind in grp:
                    f = fields.pop(kind)
                    f["association_state"] = "FIELD_BAND_CONFLICT"
                    conflicting_fields[kind] = f
                    inconclusive = True
        for kind, parked_field in parked:
            parked_field["association_state"] = "FIELD_BAND_CONFLICT"
            conflicting_fields.setdefault(kind, parked_field)
            inconclusive = True
        # Rowspan nativo primeiro. Se o rótulo do conjunto ficou acima
        # do filho (célula mesclada com texto centrado) e outro pai em
        # Y está materialmente mais perto, corrige a herança — sem
        # trocar filhos que já estão acima do rótulo do próprio grupo.
        group = None
        group_source = None
        for arow, acode, aspan, asource in group_anchors:
            if arow <= row_index < arow + aspan:
                group = acode
                group_source = asource
        row_cy_val = None
        for kind in ("item", "component_code", "quantity"):
            cy = (fields.get(kind) or {}).get("source_cy_px")
            if cy is not None:
                row_cy_val = float(cy)
                break
        if row_cy_val is None:
            cys = [
                cy for cy in (_cell_cy(c) for c in row_cells) if cy is not None
            ]
            if cys:
                row_cy_val = sum(cys) / len(cys)
        if len(group_y_anchors) >= 2 and row_cy_val is not None:
            nearest_cy, nearest_code = min(
                group_y_anchors,
                key=lambda anchor: (
                    abs(anchor[0] - row_cy_val),
                    anchor[0],
                ),
            )
            if group is None:
                group = nearest_code
                group_source = "y_anchor_nearest"
            elif (
                nearest_code != group
                and group_source not in {"rowspan_anchor", "column_span"}
            ):
                span_cy = next(
                    (cy for cy, code in group_y_anchors if code == group),
                    None,
                )
                if (
                    span_cy is not None
                    and span_cy < row_cy_val - 4.0
                    and abs(nearest_cy - row_cy_val)
                    < abs(span_cy - row_cy_val)
                ):
                    group = nearest_code
                    group_source = "y_anchor_correction"
        # Banda rehomed que cruzou a fronteira do bloco-pai: o vínculo
        # estrutural da linha destino não prova o filho da banda
        # migrada — rebaixa para proximidade (UNKNOWN honesto) quando o
        # bloco da linha de origem difere.
        if group is not None:
            for f in fields.values():
                src_row = f.get("rehomed_from_row")
                if src_row is None or src_row == row_index:
                    continue
                src_group = None
                for arow, acode, aspan, _asrc in group_anchors:
                    if arow <= src_row < arow + aspan:
                        src_group = acode
                if src_group is not None and src_group != group:
                    group_source = "band_rehome_boundary"
        rows_out.append(
            {
                "row": row_index,
                "page": page,
                "cells": published,
                "fields": fields,
                "conflicting_fields": conflicting_fields,
                "col_types": {str(k): v for k, v in col_types.items()},
                "parent_group_candidate": group,
                "parent_group_source": group_source,
                "association_conflict": bool(conflicting_fields),
                "band_detached": any(
                    c.get("_detached_band") for c in row_cells
                ),
                "item": fields.get("item", {}).get("normalized_value"),
                "quantity": fields.get("quantity", {}).get(
                    "normalized_value"
                ),
                "component_code": fields.get("component_code", {}).get(
                    "normalized_value"
                ),
                "description": fields.get("description", {}).get(
                    "normalized_value"
                ),
                "association_status": (
                    "INCONCLUSIVE" if inconclusive else (
                        "FIELD_IDENTIFIED" if fields else "UNRESOLVED"
                    )
                ),
                "topology_source": "native_table_cells",
            }
        )
    _recover_item_markers(rows_out, band_gap_px, marker_tokens)
    _rehome_across_bands(rows_out, band_gap_px)
    return rows_out, {str(k): v for k, v in col_types.items()}


_ITEM_MARKER_RE = re.compile(r"^[A-Z]{1,3}\d{0,2}$", re.IGNORECASE)
_ITEM_MARKER_FUSED_RE = re.compile(
    r"^([A-Z]{1,3}\d{0,2})\s+\d{1,3}$", re.IGNORECASE
)


def _recover_item_markers(
    rows: list[dict],
    band_gap_px: float,
    marker_tokens: list[dict] | None = None,
) -> None:
    """Resgata marcador de item em célula de papel incorreto.

    Classe comprovada (VAL-01 RQ-A02): células ``A5``/``A6``/``A1 1``
    tipadas como ``parent_description``/``description`` deixam o campo
    ``item`` vazio embora o marcador exista na linha. Evidência exigida:

    - forma de marcador (letra+opcional dígitos, ou fundida
      ``item + quantidade``);
    - centro-Y dentro da banda dos campos da linha — linhas SLANet
      podem deslocar a célula de marcador uma linha para cima/baixo;
    - posição à esquerda da célula de quantidade/componente — a
      coluna Item precede QTD na apresentação DELPI;
    - não pode ser a célula de âncora de pai nem conter o código do
      componente/pai;
    - candidato único — empate permanece ``item`` ausente (fail-closed).
    """
    tol = max(12.0, band_gap_px) if band_gap_px else 12.0
    by_page: dict[int, list[dict]] = {}
    for r in rows or []:
        by_page.setdefault(int(r.get("page") or 1), []).append(r)
    for row in rows or []:
        fields = row.get("fields") or {}
        if (fields.get("item") or {}).get("normalized_value"):
            continue
        ref_cx: float | None = None
        ref_cy: float | None = None
        for kind in ("component_code", "quantity"):
            f = fields.get(kind) or {}
            box = f.get("bounding_box_px")
            if isinstance(box, (list, tuple)) and len(box) >= 4:
                xs = [float(box[i]) for i in (0, 2, 4, 6) if i < len(box)]
                if xs:
                    ref_cx = sum(xs) / len(xs)
                fval = str(f.get("normalized_value") or "")
                fcol = f.get("col")
                for c in row.get("cells") or []:
                    if fcol is not None and int(
                        c.get("col") or -1
                    ) != int(fcol):
                        continue
                    if fval and fval not in str(c.get("text") or ""):
                        continue
                    tcs = c.get("token_centers") or []
                    if tcs and isinstance(tcs[0], (list, tuple)):
                        ref_cy = float(tcs[0][1])
                    break
                if ref_cy is None:
                    cy = f.get("source_cy_px")
                    if isinstance(cy, (int, float)):
                        ref_cy = float(cy)
                break
        if ref_cx is None:
            continue
        parent = str(row.get("parent_group_candidate") or "")
        comp = str((fields.get("component_code") or {}).get(
            "normalized_value") or "")
        def _marker_of(text: str) -> str | None:
            if _ITEM_MARKER_RE.fullmatch(text):
                return text.upper()
            m = _ITEM_MARKER_FUSED_RE.fullmatch(text)
            return m.group(1).upper() if m else None

        def _dist_cy(obj: dict) -> float | None:
            tcs = obj.get("token_centers") or []
            cy = (
                float(tcs[0][1])
                if tcs and isinstance(tcs[0], (list, tuple))
                and len(tcs[0]) >= 2
                else _cell_cy(obj)
            )
            if cy is None or ref_cy is None:
                return cy
            return abs(cy - ref_cy)

        def _accept(obj: dict) -> bool:
            d = _dist_cy(obj)
            if ref_cy is not None and d is not None and d > tol:
                return False
            cx = _cell_cx(obj)
            return not (cx is not None and cx > ref_cx + 2)

        # Tokens órfãos primeiro: a geometria do token OCR é
        # autoritativa — células SLANet podem estar deslocadas uma
        # linha (classe comprovada: AA/10400035).
        found: list[tuple[str, dict]] = []
        for tok in marker_tokens or []:
            if int(tok.get("page") or row.get("page") or 1) != int(
                row.get("page") or 1
            ):
                continue
            text = str(
                tok.get("normalized_text") or tok.get("raw_text") or ""
            ).strip()
            if not text or (parent and parent in text) or (
                comp and comp in text
            ):
                continue
            marker = _marker_of(text)
            if marker and _accept(tok):
                found.append((marker, tok))
        if len({m for m, _ in found}) != 1:
            found = []
            for other in by_page.get(int(row.get("page") or 1), []):
                for cell in other.get("cells") or []:
                    text = str(cell.get("text") or "").strip()
                    if not text or _CODE_FIND_RE.search(text) or (
                        parent and parent in text
                    ) or (comp and comp in text):
                        continue
                    marker = _marker_of(text)
                    if marker and _accept(cell):
                        found.append((marker, cell))
        if len({m for m, _ in found}) > 1:
            # Desempate por evidência: o marcador cuja geometria está
            # mais próxima da banda da linha vence — empate real
            # permanece fail-closed.
            best: dict[float, set[str]] = {}
            for m, obj in found:
                d = _dist_cy(obj)
                if d is None:
                    continue
                best.setdefault(round(d, 1), set()).add(m)
            if not best:
                continue
            closest = best[sorted(best)[0]]
            if len(closest) != 1:
                continue
            marker = next(iter(closest))
            found = [f for f in found if f[0] == marker]
        if len({m for m, _ in found}) != 1:
            continue
        marker, cell = found[0]
        fields["item"] = {
            "raw_text": str(
                cell.get("text") or cell.get("normalized_text")
                or cell.get("raw_text") or ""
            ).strip(),
            "normalized_value": marker,
            "bounding_box_px": cell.get("bounding_box_px"),
            "source_cy_px": _cell_cy(cell),
            "col": int(cell.get("col") or 0),
            "rehomed_from_row": cell.get("_rehomed_from_row"),
            "association_method": "item_marker_positional",
            "association_state": "FIELD_IDENTIFIED",
        }
        row["item"] = marker


def _derive_occurrence_paths(
    occs: list[dict], *, product_code: str | None = None
) -> None:
    """Caminho e nível visual por ocorrência — só arestas provadas.

    Sobe a cadeia pai→filho observada: o topo é ``product_code``
    (``chain_to_product_code``) ou um código que só aparece como pai
    (``visual_root_candidate``). Cadeia incompleta, ambígua ou cíclica
    deixa ``drawing_level=None`` — nunca copia nível de outra fonte.
    """
    parents_by_child: dict[str, set[str]] = {}
    child_codes: set[str] = set()
    for o in occs:
        child_codes.add(o["component_code"])
        if o["parent_state"] == "IDENTIFIED":
            parents_by_child.setdefault(
                o["component_code"], set()
            ).add(o["parent_code"])
    for o in occs:
        path = [o["component_code"]]
        seen = {o["component_code"]}
        cur = (
            o["parent_code"]
            if o["parent_state"] == "IDENTIFIED"
            else None
        )
        ambiguous = False
        while cur is not None:
            if cur in seen:
                o["uncertainty"].append("cycle_detected")
                ambiguous = True
                break
            path.insert(0, cur)
            seen.add(cur)
            ups = parents_by_child.get(cur) or set()
            if len(ups) > 1:
                o["uncertainty"].append("ambiguous_parent_chain")
                ambiguous = True
                break
            cur = next(iter(ups)) if ups else None
        o["hierarchy_path"] = path if len(path) > 1 else None
        if ambiguous:
            continue
        top = path[0]
        if product_code and top == product_code:
            o["drawing_level"] = len(path) - 1
            o["level_basis"] = "chain_to_product_code"
        elif top not in child_codes:
            o["drawing_level"] = len(path) - 1
            o["level_basis"] = "visual_root_candidate"
        elif o["parent_state"] == "IDENTIFIED" or len(path) > 1:
            o["uncertainty"].append("chain_top_parent_unknown")


def drawing_structure_occurrences(
    rows: list[dict],
    *,
    product_code: str | None = None,
    document_hash: str | None = None,
) -> list[dict]:
    """Ocorrências hierárquicas candidatas das linhas da tabela.

    ``produto/conjunto → subconjunto → componente`` conforme comprovado
    pela observação — sem preencher pai, nível, quantidade ou tipo a
    partir de fonte oficial. O mesmo código sob pais distintos produz
    ocorrências distintas: nunca há deduplicação por ``component_code``.
    """
    occs: list[dict] = []
    for row in rows or []:
        code = None
        code_field = (row.get("fields") or {}).get("component_code") or {}
        m = _CODE_FIND_RE.search(
            str(code_field.get("normalized_value") or "")
        )
        if m:
            code = m.group(0)
        if not code:
            for cell in row.get("cells") or []:
                if cell.get("col_type") != "component_code":
                    continue
                m = _CODE_FIND_RE.search(str(cell.get("text") or ""))
                if m:
                    code = m.group(0)
                    break
        if not code:
            m = _CODE_FIND_RE.search(str(row.get("component_code") or ""))
            code = m.group(0) if m else None
        if not code or code == product_code:
            continue
        parent = row.get("parent_group_candidate") or None
        parent_source = row.get("parent_group_source")
        # Proximidade Y isolada não prova parentesco (RQ-02): âncora
        # por aproximação vira candidata, não vínculo identificado.
        proximity_only = parent_source in {
            "y_anchor_nearest", "y_anchor_correction",
            "band_rehome_boundary",
        }
        status = str(row.get("association_status") or "")
        uncertainty: list[str] = []
        if status == "INCONCLUSIVE" or row.get("association_conflict"):
            uncertainty.append("association_conflict")
        if row.get("band_detached"):
            uncertainty.append("band_detached")
        if not parent:
            uncertainty.append("parent_not_observed")
        elif proximity_only:
            uncertainty.append("parent_inferred_by_proximity")
        unit = (
            (row.get("fields") or {}).get("unit") or {}
        ).get("normalized_value")
        occs.append(
            {
                "occurrence_key": {
                    "document_sha256": document_hash,
                    "page": row.get("page"),
                    "row": row.get("row"),
                    "item": row.get("item"),
                    "parent_path": parent or "UNKNOWN",
                    "component_code": code,
                },
                "component_code": code,
                "parent_code": parent,
                "parent_state": (
                    "IDENTIFIED"
                    if parent and not proximity_only
                    else "UNKNOWN"
                ),
                "parent_evidence": row.get("parent_group_source"),
                "item": row.get("item"),
                "quantity": row.get("quantity"),
                "unit": unit,
                "description": row.get("description"),
                "page": row.get("page"),
                "row": row.get("row"),
                "hierarchy_path": None,
                "drawing_level": None,
                "level_basis": None,
                "state": (
                    "INCONCLUSIVE" if uncertainty else
                    "OCCURRENCE_CANDIDATE"
                ),
                "uncertainty": uncertainty,
                "evidence": {
                    "fields": {
                        k: {
                            "bounding_box_px": f.get("bounding_box_px"),
                            "association_method": f.get(
                                "association_method"
                            ),
                            "association_state": f.get(
                                "association_state"
                            ),
                        }
                        for k, f in (row.get("fields") or {}).items()
                        if isinstance(f, dict)
                    },
                    "token_refs": [
                        ref
                        for c in (row.get("cells") or [])
                        for ref in (c.get("token_refs") or [])
                    ],
                    "topology_source": row.get("topology_source"),
                },
            }
        )
    _derive_occurrence_paths(occs, product_code=product_code)
    return occs


# Limitações de grade que não invalidam, sozinhas, associações
# textuais já sustentadas pelas células (DEC-VAL-042).
_SOFT_STRUCTURE_LIMITATIONS = frozenset({"span_conflict"})
_FUSED_COMPONENT_CODES_RE = re.compile(r"\b\d{6,11}(?:\s+\d{6,11})+\b")


def _count_fused_component_codes(rows: list[dict]) -> int:
    count = 0
    for row in rows or []:
        code = str(row.get("component_code") or "")
        if _FUSED_COMPONENT_CODES_RE.search(code):
            count += 1
    return count


def _usable_native_associations(rows: list[dict]) -> int:
    """Associações item+código único (sem fusão multi-código)."""
    count = 0
    for row in rows or []:
        if not row.get("item"):
            continue
        code = str(row.get("component_code") or "")
        if not code or _FUSED_COMPONENT_CODES_RE.search(code):
            continue
        count += 1
    return count


def _item_key(row: dict) -> str | None:
    item = str(row.get("item") or "").strip().upper()
    return item or None


def _item_frequency(rows: list[dict]) -> Counter:
    counts: Counter = Counter()
    for row in rows or []:
        key = _item_key(row)
        if key:
            counts[key] += 1
    return counts


def _is_single_component_code(code: str | None) -> bool:
    text = str(code or "").strip()
    if not text or _FUSED_COMPONENT_CODES_RE.search(text):
        return False
    return bool(re.fullmatch(r"\d{6,11}", text))


def _native_improves_fallback(native: dict, fallback: dict) -> bool:
    """Native wins only with equal-or-better evidence for the same item."""
    n_code = str(native.get("component_code") or "").strip()
    f_code = str(fallback.get("component_code") or "").strip()
    if not _is_single_component_code(n_code):
        return False
    if _FUSED_COMPONENT_CODES_RE.search(f_code):
        return True
    if not f_code:
        return True
    if f_code == n_code:
        # Mesmo código: preferir native se recupera descrição ausente.
        return bool(native.get("description")) or not fallback.get(
            "description"
        )
    return False


def reconcile_native_and_fallback_rows(
    *,
    native_rows: list[dict],
    fallback_rows: list[dict],
    page: int,
    mode: str,
) -> list[dict]:
    """Decide linhas finais sem merge indiscriminado (DEC-VAL-043).

    Modes:
    - ``replace``: troca integral da página pela grade nativa.
    - ``preserve``: atualiza somente ocorrências com item único na
      página em ambos os lados, quando a nativa melhora a evidência;
      demais linhas do fallback permanecem.
    """
    if mode == "replace":
        return list(native_rows or [])
    fallback = list(fallback_rows or [])
    native = list(native_rows or [])
    if not native:
        return fallback
    fb_freq = _item_frequency(fallback)
    nat_freq = _item_frequency(native)
    native_by_item: dict[str, dict] = {}
    for row in native:
        key = _item_key(row)
        if key and nat_freq[key] == 1 and key not in native_by_item:
            native_by_item[key] = row
    out: list[dict] = []
    replaced: set[str] = set()
    for row in fallback:
        key = _item_key(row)
        if (
            key
            and fb_freq[key] == 1
            and key in native_by_item
            and _native_improves_fallback(native_by_item[key], row)
        ):
            chosen = dict(native_by_item[key])
            chosen["page"] = int(chosen.get("page") or page)
            chosen["topology_source"] = "native_table_cells"
            chosen["association_method"] = (
                chosen.get("association_method")
                or "native_unique_item_upgrade"
            )
            out.append(chosen)
            replaced.add(key)
        else:
            out.append(row)
    # Novas ocorrências nativas com item único ausente no fallback —
    # só quando a identidade não colide.
    for key, row in native_by_item.items():
        if key in replaced or fb_freq.get(key, 0) != 0:
            continue
        if not _is_single_component_code(row.get("component_code")):
            continue
        chosen = dict(row)
        chosen["page"] = int(chosen.get("page") or page)
        chosen["topology_source"] = "native_table_cells"
        out.append(chosen)
    return out


def native_cells_preferable(
    *,
    consistent: bool,
    structure_limitations: list[str] | None,
    native_rows: list[dict],
    fallback_rows: list[dict],
) -> tuple[bool, str | None]:
    """Política conservadora de aceite da grade nativa (DEC-VAL-042/043).

    ``structure_consistent=false`` não implica descarte automático.
    Conflito de span localizado pode coexistir com células textuais
    associáveis.

    Retorna ``(aplicar, reason)`` onde ``reason`` é:
    - ``None`` — substituição integral (estrutura consistente);
    - ``span_conflict_tolerated`` — substituição integral sob cobertura
      suficiente;
    - ``span_conflict_tolerated_partial`` — upgrade só de ocorrências
      com item único, preservando o restante do fallback (DEC-VAL-043);
    - ou motivo de rejeição (``structure_incomplete`` / ``no_text_rows``).
    """
    if consistent:
        return True, None
    limitations = {
        str(item).strip()
        for item in (structure_limitations or [])
        if str(item).strip()
    }
    if not limitations or not limitations.issubset(
        _SOFT_STRUCTURE_LIMITATIONS
    ):
        return False, "structure_incomplete"
    if not native_rows:
        return False, "no_text_rows"
    usable_native = _usable_native_associations(native_rows)
    if usable_native < 1:
        return False, "structure_incomplete"
    if _count_fused_component_codes(native_rows) > _count_fused_component_codes(
        fallback_rows
    ):
        return False, "structure_incomplete"
    usable_fallback = _usable_native_associations(fallback_rows)
    if usable_native >= max(usable_fallback, 1):
        return True, "span_conflict_tolerated"
    # Cobertura parcial: só aplica se existir ao menos um upgrade
    # inequívoco (item único) que melhore fusão/ausência de código.
    fb_freq = _item_frequency(fallback_rows)
    nat_freq = _item_frequency(native_rows)
    native_by_item = {
        _item_key(row): row
        for row in native_rows
        if _item_key(row) and nat_freq[_item_key(row)] == 1
    }
    for row in fallback_rows or []:
        key = _item_key(row)
        if not key or fb_freq[key] != 1:
            continue
        native = native_by_item.get(key)
        if native and _native_improves_fallback(native, row):
            return True, "span_conflict_tolerated_partial"
    return False, "structure_incomplete"


def apply_native_table_observations(
    understanding: dict, observations: list[dict]
) -> dict:
    """Substitui linhas agrupadas quando a grade nativa tem texto.

    Região que não é tabela de componentes fica só na observação
    neutra. Grade sem texto, corrompida ou com erro não apaga as
    linhas já lidas e não fabrica parentesco. Conflito de span
    localizado pode ser tolerado quando as associações nativas são
    comprovadamente utilizáveis (DEC-VAL-042).
    """
    table = dict(understanding.get("component_table") or {})
    rows = list(table.get("rows") or [])
    limitations = list(understanding.get("limitations") or [])
    perceptions: list[dict] = []
    replaced_pages: set[int] = set()
    partial_pages: set[int] = set()
    for obs in observations or []:
        result = obs.get("result") or {}
        render = result.get("render") or {}
        page = int(obs.get("page") or render.get("processed_page") or 1)
        native_cells = result.get("cells") or []
        consistent = False
        structure_limitations: list[str] = []
        if result.get("tables"):
            table0 = result["tables"][0] or {}
            consistent = bool(table0.get("structure_consistent"))
            structure_limitations = list(
                table0.get("structure_limitations") or []
            )
        perceptions.append(
            {
                "region_type": obs.get("region_type"),
                "page": page,
                "processed_pages": result.get("processed_pages") or [],
                "requested_pages": result.get("requested_pages") or [],
                "pdf_sha_match": result.get("pdf_sha_match"),
                "source_pdf_sha256": result.get("source_pdf_sha256"),
                "render": result.get("render"),
                "error_kind": result.get("error_kind"),
                "error_detail": result.get("error_detail"),
                "structure_consistent": consistent,
                "structure_limitations": structure_limitations,
                "cells": native_cells,
                "association": result.get("association"),
                "limitations": result.get("limitations") or [],
                "engineering_validated": False,
            }
        )
        if obs.get("region_type") != "component_table":
            continue
        if result.get("error_kind"):
            limitations.append(
                "table_perception:" + str(result.get("error_kind"))
            )
            continue
        if not any(
            _norm(str(cell.get("text") or "")) for cell in native_cells
        ):
            limitations.append("table_perception:structure_without_text")
            continue
        profile_meta: dict = {}
        native_rows, col_types = rows_from_native_cells(
            native_cells,
            page=page,
            profile_out=profile_meta,
            marker_tokens=(
                (result.get("association") or {}).get("unassigned_tokens")
            ),
        )
        if profile_meta:
            pp = dict(table.get("presentation_profile") or {})
            pp[str(page)] = profile_meta
            table["presentation_profile"] = pp
        if not native_rows:
            limitations.append("table_perception:no_text_rows")
            continue
        page_fallback = [
            row for row in rows
            if int(row.get("page") or page) == page
        ]
        apply_native, tolerate_reason = native_cells_preferable(
            consistent=consistent,
            structure_limitations=structure_limitations,
            native_rows=native_rows,
            fallback_rows=page_fallback,
        )
        if not apply_native:
            limitations.append(
                "table_perception:"
                + str(tolerate_reason or "structure_incomplete")
            )
            continue
        if tolerate_reason:
            limitations.append("table_perception:" + tolerate_reason)
        mode = (
            "preserve"
            if tolerate_reason == "span_conflict_tolerated_partial"
            else "replace"
        )
        reconciled = reconcile_native_and_fallback_rows(
            native_rows=native_rows,
            fallback_rows=page_fallback,
            page=page,
            mode=mode,
        )
        rows = [
            row for row in rows
            if int(row.get("page") or page) != page
        ]
        rows.extend(reconciled)
        replaced_pages.add(page)
        if mode == "preserve":
            partial_pages.add(page)
        per_page = dict(table.get("col_types") or {})
        if mode == "replace":
            if per_page and all(
                isinstance(v, dict) for v in per_page.values()
            ):
                per_page[str(page)] = col_types
                table["col_types"] = per_page
            else:
                table["col_types"] = col_types
    table["rows"] = rows
    table["row_count"] = len(rows)
    table["structure_occurrences"] = drawing_structure_occurrences(
        rows,
        product_code=understanding.get("product_code"),
        document_hash=understanding.get("document_hash_sha256"),
    )
    table["perception_pages"] = sorted(replaced_pages)
    if replaced_pages:
        # Preservação parcial mantém mistura de topologias.
        if partial_pages and partial_pages == replaced_pages:
            table["topology_source"] = "native_partial_over_fallback"
            table["detection"] = "native_partial_over_fallback"
        else:
            table["topology_source"] = "native_table_cells"
            table["detection"] = "native_table_cells"
    updated = dict(understanding)
    updated["component_table"] = table
    updated["table_perception"] = perceptions
    updated["limitations"] = limitations
    return updated
