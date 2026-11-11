"""Drawing Perception Contract — ``drawing_perception_candidate.v1`` (R9).

Contrato comum de percepção documental, independente de motor
(PaddleOCR, PP-StructureV3, Docling, cloud, etc.). Camada Application:
zero dependência de visão, HTTP, SDK de provider, DB ou MCP.

Princípios:
- candidates only — nunca fatos oficiais de Engenharia;
- ``confidence`` de modelo NÃO é aprovação técnica;
- campos sem evidência → ``None``/``UNKNOWN``, nunca inventados;
- coordenadas sempre em ``pixels_top_left`` + page/DPI/rotation;
- falhas retornam erro tipado, nunca exceção para o consumidor.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Protocol

SCHEMA_VERSION = "drawing_perception_candidate.v1"
# Identidade do job: uma observação nativa nova não reutiliza
# COMPLETED produzido pela grade artificial anterior.
TABLE_PERCEPTION_REVISION = "native_slanet_v3"
TABLE_RENDER_DPI = 200
TABLE_RENDER_SCALE = TABLE_RENDER_DPI / 72

REGION_TYPES = frozenset(
    {
        "title_block", "component_table", "revision_history",
        "notes", "drawing_area", "legend", "other", "unknown",
    }
)
ELEMENT_TYPES = frozenset(
    {
        "region", "table", "table_row", "table_cell", "table_header",
        "text_block", "dimension_candidate", "figure",
        "unclassified", "graphic_primitive",
    }
)
ERROR_KINDS = frozenset(
    {
        "UNSUPPORTED_INPUT", "MODEL_NOT_PROVISIONED", "POLICY_DENIED",
        "TIMEOUT", "RESOURCE_LIMIT", "INVALID_PROVIDER_OUTPUT",
        "INCOMPLETE_COVERAGE", "UNAVAILABLE",
        "NO_TABLE_REGION", "PAGE_NOT_IN_DOCUMENT", "INVALID_CROP",
        "COORDINATE_MISMATCH",
        # Integridade documental — falhas de ENTRADA do motor, antes de
        # qualquer inferência. Nunca confundir com UNAVAILABLE (modelo).
        "DOCUMENT_CONTENT_MISSING", "DOCUMENT_CONTENT_INVALID",
        "DOCUMENT_HASH_MISMATCH", "PDF_OPEN_FAILED",
    }
)
QUALITY_STATES = frozenset(
    {"DRAFT", "PARTIAL", "FAILED", "EVAL_PENDING"}
)


def _clip_box(
    box: list[float] | None, w: float, h: float
) -> list[float] | None:
    if not box or len(box) < 4:
        return None
    x1 = max(0.0, min(float(box[0]), w))
    y1 = max(0.0, min(float(box[1]), h))
    x2 = max(0.0, min(float(box[2]), w))
    y2 = max(0.0, min(float(box[3]), h))
    if x2 <= x1 or y2 <= y1:
        return None
    return [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)]


def make_region(
    *,
    region_id: str,
    region_type: str,
    page: int,
    bounding_box_px: list[float] | None,
    evidence: list[str],
    token_count: int = 0,
    state: str = "candidate",
    confidence_label: str | None = None,
) -> dict:
    return {
        "region_id": region_id,
        "region_type": (
            region_type if region_type in REGION_TYPES else "unknown"
        ),
        "page": page,
        "bounding_box_px": bounding_box_px,
        "coordinate_system": "pixels_top_left",
        "evidence": evidence,
        "token_count": token_count,
        "state": state,
        "confidence_label": confidence_label,
        "engineering_validated": False,
    }


def make_cell(
    *,
    row: int,
    col: int,
    text: str,
    bounding_box_px: list[float] | None,
    col_type: str | None = None,
    token_refs: list[int] | None = None,
    ambiguous: bool = False,
    rowspan: int = 1,
    colspan: int = 1,
) -> dict:
    return {
        "row": row,
        "col": col,
        "rowspan": max(1, int(rowspan or 1)),
        "colspan": max(1, int(colspan or 1)),
        "text": text,
        "normalized_text": " ".join((text or "").split()).strip(),
        "col_type": col_type,
        "bounding_box_px": bounding_box_px,
        "token_refs": token_refs or [],
        "ambiguous": ambiguous,
    }


def capability_descriptor(
    *,
    provider_id: str,
    provider_version: str,
    supports: dict[str, bool],
    notes: list[str] | None = None,
) -> dict:
    return {
        "provider_id": provider_id,
        "provider_version": provider_version,
        "supports": supports,
        "notes": notes or [],
    }


def make_result(
    *,
    provider_id: str,
    provider_version: str,
    document_hash_sha256: str,
    product_code: str | None = None,
    model_version: str | None = None,
    model_digest: str | None = None,
    config_digest: str | None = None,
    execution_mode: str = "local_isolated",
    page_width_px: float | None = None,
    page_height_px: float | None = None,
    dpi: int | None = None,
    rotation: int = 0,
    total_pages: int = 1,
    requested_pages: list[int] | None = None,
    processed_pages: list[int] | None = None,
    failed_pages: list[int] | None = None,
    regions: list[dict] | None = None,
    tables: list[dict] | None = None,
    cells: list[dict] | None = None,
    text_blocks: list[dict] | None = None,
    figures: list[dict] | None = None,
    dimension_candidates: list[dict] | None = None,
    provenance: str | None = None,
    limitations: list[str] | None = None,
    duration_ms: float | None = None,
    memory_peak_kb: int | None = None,
    error_kind: str | None = None,
    error_detail: str | None = None,
    quality_status: str = "EVAL_PENDING",
) -> dict:
    """Resultado normalizado por motor — sempre DRAFT/candidato."""
    if quality_status not in QUALITY_STATES:
        quality_status = "EVAL_PENDING"
    return {
        "schema_version": SCHEMA_VERSION,
        "provider_id": provider_id,
        "provider_version": provider_version,
        "model_version": model_version,
        "model_digest": model_digest,
        "config_digest": (
            config_digest
            or hashlib.sha256(
                f"{provider_id}|{provider_version}".encode()
            ).hexdigest()[:12]
        ),
        "document_hash_sha256": document_hash_sha256,
        "product_code": product_code,
        "execution_mode": execution_mode,
        "total_pages": total_pages,
        "requested_pages": requested_pages or [1],
        "processed_pages": processed_pages or [1],
        "failed_pages": failed_pages or [],
        "page": {
            "width_px": page_width_px,
            "height_px": page_height_px,
            "dpi": dpi,
            "rotation": rotation,
            "coordinate_system": "pixels_top_left",
        },
        "regions": regions or [],
        "tables": tables or [],
        "cells": cells or [],
        "text_blocks": text_blocks or [],
        "figures": figures or [],
        "dimension_candidates": dimension_candidates or [],
        "provenance": provenance
        or f"{provider_id}:{provider_version} → {SCHEMA_VERSION}",
        "limitations": limitations or [],
        "quality_status": quality_status,
        "error_kind": (
            error_kind if error_kind in ERROR_KINDS else None
        ),
        "error_detail": error_detail,
        "duration_ms": duration_ms,
        "memory_peak_kb": memory_peak_kb,
        "engineering_validated": False,
    }


class PerceptionEnginePort(Protocol):
    """Porta de percepção — qualquer motor implementa run() → v1 dict."""

    provider_id: str

    def run(
        self,
        pdf_bytes: bytes,
        *,
        document_hash_sha256: str,
        product_code: str | None = None,
        pages: list[int] | None = None,
    ) -> dict:
        ...


def _token_center_px(bb: list) -> tuple[float, float] | None:
    """Centro do token: média dos vértices do polígono (quad 8 pts).

    Tratar ``[x1,y1,x2,y1,...]`` como se fosse ``[x1,y1,x2,y2]`` usa o
    segundo vértice do topo como ``y2`` e coloca o centro na borda —
    tokens de quantidade caem fora da célula da própria linha.
    """
    if not bb or len(bb) < 4:
        return None
    if len(bb) >= 8:
        xs = [float(bb[i]) for i in range(0, 8, 2)]
        ys = [float(bb[i]) for i in range(1, 8, 2)]
        return sum(xs) / 4.0, sum(ys) / 4.0
    return (float(bb[0]) + float(bb[2])) / 2.0, (
        float(bb[1]) + float(bb[3])
    ) / 2.0


def _bbox_center_px(cb: list) -> tuple[float, float] | None:
    if not cb or len(cb) < 4:
        return None
    if len(cb) >= 8:
        xs = [float(cb[i]) for i in range(0, 8, 2)]
        ys = [float(cb[i]) for i in range(1, 8, 2)]
        return sum(xs) / 4.0, sum(ys) / 4.0
    return (float(cb[0]) + float(cb[2])) / 2.0, (
        float(cb[1]) + float(cb[3])
    ) / 2.0


def associate_tokens_to_cells(
    tokens: list,
    cell_bboxes: list,
    *,
    crop_offset: tuple = (0.0, 0.0),
) -> dict:
    """Associa tokens OCR a células SLANet por geometria determinística.

    RQ-01/02/05: token→célula por contenção do centro do token;
    múltiplas células → ``conflicts`` (vence a célula de centro mais
    próximo); sem match → ``unassigned``. Nunca inventa texto nem
    associa arbitrariamente.
    """
    ox, oy = crop_offset
    assigned: dict = {}
    conflicts: list = []
    unassigned: list = []
    for ti, tok in enumerate(tokens):
        bb = tok.get("bounding_box_px") if isinstance(tok, dict) else None
        center = _token_center_px(bb) if isinstance(bb, (list, tuple)) else None
        if center is None:
            unassigned.append(ti)
            continue
        cx, cy = center
        hits = []
        for ci, cb in enumerate(cell_bboxes or []):
            if not cb or len(cb) < 4:
                continue
            xs = [cb[0], cb[2], cb[4], cb[6]] if len(cb) >= 8 else [cb[0], cb[2]]
            ys = [cb[1], cb[3], cb[5], cb[7]] if len(cb) >= 8 else [cb[1], cb[3]]
            if (
                min(xs) + ox <= cx <= max(xs) + ox
                and min(ys) + oy <= cy <= max(ys) + oy
            ):
                hits.append(ci)
        if len(hits) == 1:
            assigned.setdefault(hits[0], []).append(ti)
        elif len(hits) > 1:
            conflicts.append({"token_index": ti, "cells": hits})

            def _dist(ci: int) -> tuple[float, int]:
                mid = _bbox_center_px(cell_bboxes[ci])
                if mid is None:
                    return (float("inf"), ci)
                return (
                    (mid[0] - cx) ** 2 + (mid[1] - cy) ** 2,
                    ci,
                )

            chosen = min(hits, key=_dist)
            assigned.setdefault(chosen, []).append(ti)
        else:
            unassigned.append(ti)
    return {
        "cell_token_map": {str(k): v for k, v in assigned.items()},
        "conflicts": conflicts,
        "unassigned": unassigned,
        "method": "center_containment",
    }


_QTY_TOKEN_RE = re.compile(r"^\d{1,4}([.,]\d+)?$")


def fill_empty_quantity_cells_from_unassigned(
    cells: list[dict],
    tokens: list,
    unassigned: list[int],
) -> list[int]:
    """Preenche célula qty vazia com token OCR órfão alinhado à linha.

    Quando o centro do token fica 1–2px fora do polígono SLANet, a
    contenção falha e a quantidade some. Só atribui se:
    - o token é quantidade curta;
    - existe célula vazia na mesma coluna visual (X);
    - a banda Y do token combina com item/código da mesma linha SLANet
      melhor do que com qualquer outra linha candidata (único vencedor).
    Nunca inventa texto nem move qty já atribuída.
    """
    if not cells or not tokens or not unassigned:
        return list(unassigned)
    remaining: list[int] = []
    row_anchor_cy: dict[int, list[float]] = {}
    for cell in cells:
        text = str(cell.get("text") or "").strip()
        if not text:
            continue
        cy = None
        tcs = cell.get("token_centers") or []
        ys = [
            float(tc[1])
            for tc in tcs
            if isinstance(tc, (list, tuple)) and len(tc) >= 2
        ]
        if ys:
            cy = sum(ys) / len(ys)
        else:
            bb = cell.get("bounding_box_px") or []
            if len(bb) >= 8:
                cy = (min(bb[1::2]) + max(bb[1::2])) / 2.0
            elif len(bb) >= 4:
                cy = (float(bb[1]) + float(bb[3])) / 2.0
        if cy is None:
            continue
        # Âncoras de linha: item (letras curtas) ou código longo.
        if re.fullmatch(r"[A-Za-z]{1,2}\d{0,3}|[A-Za-z]{3,4}\d+", text) or (
            re.fullmatch(r"\d{6,11}", text)
        ):
            row_anchor_cy.setdefault(int(cell.get("row") or 0), []).append(cy)

    def _cell_xy_range(cell: dict) -> tuple[float, float, float, float] | None:
        bb = cell.get("bounding_box_px") or []
        if len(bb) >= 8:
            xs, ys = bb[0::2], bb[1::2]
        elif len(bb) >= 4:
            xs, ys = [bb[0], bb[2]], [bb[1], bb[3]]
        else:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    for ti in unassigned:
        if ti >= len(tokens):
            remaining.append(ti)
            continue
        tok = tokens[ti]
        if not isinstance(tok, dict):
            remaining.append(ti)
            continue
        raw = str(
            tok.get("normalized_text")
            or tok.get("raw_text")
            or tok.get("text")
            or ""
        ).strip()
        if not _QTY_TOKEN_RE.fullmatch(raw):
            remaining.append(ti)
            continue
        center = _token_center_px(tok.get("bounding_box_px"))
        if center is None:
            remaining.append(ti)
            continue
        cx, cy = center
        candidates: list[tuple[float, int, dict]] = []
        for cell in cells:
            if str(cell.get("text") or "").strip():
                continue
            if int(cell.get("rowspan") or 1) > 1:
                continue
            extents = _cell_xy_range(cell)
            if extents is None:
                continue
            x1, y1, x2, y2 = extents
            # Pad horizontal pequeno: centro OCR frequentemente 1–3px
            # à esquerda da borda SLANet da coluna de quantidade.
            pad_x = max(8.0, 0.15 * (x2 - x1))
            pad_y = max(4.0, 0.10 * (y2 - y1))
            if not (x1 - pad_x <= cx <= x2 + pad_x):
                continue
            if not (y1 - pad_y <= cy <= y2 + pad_y):
                continue
            row = int(cell.get("row") or 0)
            anchors = row_anchor_cy.get(row) or []
            if not anchors:
                continue
            anchor = min(anchors, key=lambda a: abs(a - cy))
            dy = abs(anchor - cy)
            # Token deve estar na banda da linha, não na vizinha.
            if dy > max(18.0, 0.55 * abs((y2 - y1) or 18.0) + 8.0):
                continue
            candidates.append((dy, row, cell))
        if not candidates:
            remaining.append(ti)
            continue
        candidates.sort(key=lambda c: (c[0], c[1]))
        best_dy, _best_row, best_cell = candidates[0]
        # Empate com outra linha → abstenção (não migrar qty vizinha).
        close = [
            c for c in candidates if abs(c[0] - best_dy) <= 4.0 and c[2] is not best_cell
        ]
        other_rows = {c[1] for c in close if c[1] != _best_row}
        if other_rows:
            remaining.append(ti)
            continue
        best_cell["text"] = raw
        best_cell["token_centers"] = [[round(cx, 1), round(cy, 1)]]
        refs = list(best_cell.get("token_refs") or [])
        if ti not in refs:
            refs.append(ti)
        best_cell["token_refs"] = refs
        best_cell["association_method"] = "ocr_unassigned_row_band"
    return remaining


def fill_empty_cells_from_unassigned_grid_extent(
    cells: list[dict],
    tokens: list,
    unassigned: list[int],
) -> list[int]:
    """Preenche célula vazia com token órfão dentro da extensão de grade.

    Quando o SLANet declara bbox truncada para uma célula (típico em
    células mescladas cujo texto fica no centro vertical do bloco), a
    contenção falha e o token vira ``unassigned`` — a informação existe
    no OCR mas some da célula (ex.: código de conjunto ``50233810``).

    A extensão real da célula é o retângulo linhas×colunas que ela
    cobre, derivado das bandas dos irmãos da grade — não do quad
    declarado. Só preenche quando:

    - a célula está vazia;
    - o centro do token cai **dentro** da extensão de grade (evidência
      estrita, sem padding);
    - nenhum concorrente reivindica o mesmo token.

    O preenchimento preserva proveniência (``association_method`` e
    ``ambiguous=True`` — a associação reparada é evidência mais fraca
    que a bbox declarada) e nunca remove texto já associado.
    """
    if not cells or not tokens or not unassigned:
        return list(unassigned)

    def _extents(cb: list) -> tuple[float, float, float, float] | None:
        if len(cb) >= 8:
            xs, ys = cb[0::2], cb[1::2]
        elif len(cb) >= 4:
            xs, ys = [cb[0], cb[2]], [cb[1], cb[3]]
        else:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    # Bandas de linha e de coluna derivadas de TODAS as células da
    # grade — a extensão verdadeira de uma célula rowspan N é a união
    # das bandas das N linhas × M colunas que ela cobre.
    row_bands: dict[int, list[float]] = {}
    col_bands: dict[int, list[float]] = {}
    for cell in cells:
        ext = _extents(cell.get("bounding_box_px") or [])
        if ext is None:
            continue
        x1, y1, x2, y2 = ext
        row = int(cell.get("row") or 0)
        col = int(cell.get("col") or 0)
        band = row_bands.setdefault(row, [y1, y2])
        band[0], band[1] = min(band[0], y1), max(band[1], y2)
        cband = col_bands.setdefault(col, [x1, x2])
        cband[0], cband[1] = min(cband[0], x1), max(cband[1], x2)

    def _grid_extent(cell: dict) -> tuple[float, float, float, float] | None:
        row = int(cell.get("row") or 0)
        col = int(cell.get("col") or 0)
        rowspan = max(1, int(cell.get("rowspan") or 1))
        colspan = max(1, int(cell.get("colspan") or 1))
        x1 = y1 = float("inf")
        x2 = y2 = float("-inf")
        own = _extents(cell.get("bounding_box_px") or [])
        if own is not None:
            x1, y1, x2, y2 = own
        for r in range(row, row + rowspan):
            band = row_bands.get(r)
            if band:
                y1, y2 = min(y1, band[0]), max(y2, band[1])
        for c in range(col, col + colspan):
            cband = col_bands.get(c)
            if cband:
                x1, x2 = min(x1, cband[0]), max(x2, cband[1])
        if x1 == float("inf") or y1 == float("inf"):
            return None
        return x1, y1, x2, y2

    empty_cells = [
        c for c in cells if not str(c.get("text") or "").strip()
    ]
    if not empty_cells:
        return list(unassigned)
    extents = {id(c): _grid_extent(c) for c in empty_cells}

    remaining: list[int] = []
    for ti in unassigned:
        if ti >= len(tokens) or not isinstance(tokens[ti], dict):
            remaining.append(ti)
            continue
        tok = tokens[ti]
        center = _token_center_px(tok.get("bounding_box_px"))
        if center is None:
            remaining.append(ti)
            continue
        cx, cy = center
        hits = [
            c
            for c in empty_cells
            if (e := extents[id(c)]) is not None
            and e[0] <= cx <= e[2]
            and e[1] <= cy <= e[3]
        ]
        # Mais de uma célula reivindicando o token → a grade está
        # ambígua; não associar é a resposta honesta.
        if len(hits) != 1:
            remaining.append(ti)
            continue
        cell = hits[0]
        raw = str(
            tok.get("normalized_text")
            or tok.get("raw_text")
            or tok.get("text")
            or ""
        ).strip()
        if not raw:
            remaining.append(ti)
            continue
        cell["text"] = raw if not cell.get("text") else (
            str(cell["text"]).strip() + " " + raw
        )
        cell["ambiguous"] = True
        cell["association_method"] = "grid_extent_unassigned"
        tcs = list(cell.get("token_centers") or [])
        tcs.append([round(cx, 1), round(cy, 1)])
        cell["token_centers"] = tcs
        refs = list(cell.get("token_refs") or [])
        if ti not in refs:
            refs.append(ti)
        cell["token_refs"] = refs
    return remaining


def resolve_requested_page(
    pages: list[int] | None, page_count: int
) -> tuple[int | None, str | None]:
    """Página 1-based a renderizar.

    A omissão pede a página 1 e registra isso. Página fora do
    documento não cai na página zero. Mais de uma página na mesma
    chamada não é multipágina: só a primeira é processada e as
    demais ficam para o chamador repetir a chamada.
    """
    if page_count < 1:
        return None, "PAGE_NOT_IN_DOCUMENT"
    if not pages:
        requested = 1
    else:
        try:
            requested = int(pages[0])
        except (TypeError, ValueError):
            return None, "PAGE_NOT_IN_DOCUMENT"
    if requested < 1 or requested > page_count:
        return None, "PAGE_NOT_IN_DOCUMENT"
    return requested, None


def validate_crop_box(
    crop: list | None, width: float, height: float
) -> str | None:
    """Recorte em pixels da página. Ausência não vira recorte fixo."""
    if crop is None:
        return "NO_TABLE_REGION"
    if not isinstance(crop, (list, tuple)) or len(crop) < 4:
        return "INVALID_CROP"
    try:
        x1, y1, x2, y2 = (float(crop[0]), float(crop[1]), float(crop[2]), float(crop[3]))
    except (TypeError, ValueError):
        return "INVALID_CROP"
    if x2 <= x1 or y2 <= y1:
        return "INVALID_CROP"
    if x1 < -1 or y1 < -1 or x2 > width + 1 or y2 > height + 1:
        return "INVALID_CROP"
    return None


def render_matches_tokens(
    image_size: tuple[int, int],
    expected_size: tuple[int, int] | None,
) -> bool:
    """Largura, altura. Sem tamanho esperado não há o que contradizer."""
    if not expected_size:
        return True
    width, height = image_size
    expected_w, expected_h = expected_size
    return abs(int(width) - int(expected_w)) <= 2 and abs(
        int(height) - int(expected_h)
    ) <= 2


_SPAN_ATTR_RE = re.compile(
    r'(rowspan|colspan)\s*=\s*"(\d+)"', re.IGNORECASE
)


def cells_from_html_structure(
    structure: str | list | None, bboxes: list | None
) -> dict:
    """Topologia declarada pelo HTML do framework.

    A ordem dos ``<td>`` acompanha a ordem dos bboxes. Rowspan e
    colspan ocupam a grade. Conflito de span ou contagem divergente
    permanece como limitação; a função não completa a grade.
    """
    if isinstance(structure, str):
        html = structure
    else:
        html = "".join(str(part) for part in (structure or []))
    boxes = list(bboxes or [])
    limitations: list[str] = []
    if not html.strip():
        limitations.append("empty_structure")
    occupied: dict[tuple[int, int], int] = {}
    cells: list[dict] = []
    row = -1
    col_cursor = 0
    td_index = 0
    for match in re.finditer(r"</?tr\b|<td\b([^>]*)>", html, re.IGNORECASE):
        tag = match.group(0)
        if tag.lower().startswith("</tr"):
            continue
        if tag.lower().startswith("<tr"):
            row += 1
            col_cursor = 0
            continue
        attrs = match.group(1) or ""
        if row < 0:
            limitations.append("td_outside_row")
            row = 0
        spans = {
            name.lower(): int(value)
            for name, value in _SPAN_ATTR_RE.findall(attrs)
        }
        rowspan = max(1, spans.get("rowspan", 1))
        colspan = max(1, spans.get("colspan", 1))
        while (row, col_cursor) in occupied:
            col_cursor += 1
        conflict = False
        for dr in range(rowspan):
            for dc in range(colspan):
                key = (row + dr, col_cursor + dc)
                if key in occupied:
                    conflict = True
                    limitations.append("span_conflict")
                occupied[key] = td_index
        cells.append(
            {
                "row": row,
                "col": col_cursor,
                "rowspan": rowspan,
                "colspan": colspan,
                "bbox_index": td_index,
                "span_conflict": conflict,
            }
        )
        col_cursor += colspan
        td_index += 1
    if boxes and td_index != len(boxes):
        limitations.append("bbox_count_mismatch")
    if not cells and "empty_structure" not in limitations:
        limitations.append("empty_structure")
    # uma ocorrência de span_conflict basta
    deduped: list[str] = []
    for item in limitations:
        if item not in deduped:
            deduped.append(item)
    return {
        "cells": cells,
        "limitations": deduped,
        "td_count": td_index,
        "consistent": not deduped,
    }
