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


def associate_tokens_to_cells(
    tokens: list,
    cell_bboxes: list,
    *,
    crop_offset: tuple = (0.0, 0.0),
) -> dict:
    """Associa tokens OCR a células SLANet por geometria determinística.

    RQ-01/02/05: token→célula por contenção do centro do token;
    múltiplas células → ``conflicts``; sem match → ``unassigned``.
    Nunca inventa texto nem associa arbitrariamente.
    """
    ox, oy = crop_offset
    assigned: dict = {}
    conflicts: list = []
    unassigned: list = []
    for ti, tok in enumerate(tokens):
        bb = tok.get("bounding_box_px") if isinstance(tok, dict) else None
        if not bb or len(bb) < 4:
            unassigned.append(ti)
            continue
        cx, cy = (bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0
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
            assigned.setdefault(hits[0], []).append(ti)
        else:
            unassigned.append(ti)
    return {
        "cell_token_map": {str(k): v for k, v in assigned.items()},
        "conflicts": conflicts,
        "unassigned": unassigned,
        "method": "center_containment",
    }


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
