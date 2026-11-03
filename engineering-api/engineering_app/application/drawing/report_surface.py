"""Drawing Intelligence Surface — ponto de entrada substituível para a
interpretação de desenhos (doc 116-B).

`DrawingIntelligencePort` é o contrato estável; a implementação atual
(`UnderstandingIntelligenceAdapter`) encapsula `build_understanding` +
assembly do relatório candidato. Consumidores (MCP bridge) dependem do
port via `get_drawing_intelligence()`, nunca da implementação concreta.
Novo owner: Application/drawing. Sem HTTP/MCP/framework/OCR internals.
"""

from typing import Any, Protocol


class DrawingIntelligencePort(Protocol):
    """Contrato estável de interpretação → relatório candidato."""

    def build_report(
        self,
        understanding: dict[str, Any],
        *,
        document_hash: str,
        provider_id: str | None,
        product_code: str,
    ) -> dict[str, Any]: ...


def build_report(
    understanding: dict[str, Any],
    *,
    document_hash: str,
    provider_id: str | None,
    product_code: str,
) -> dict[str, Any]:
    """Monta o relatório candidato (seções A–H) dos dados governados."""
    comp = (understanding.get("component_table") or {}).get("rows") or []
    sl_e = (understanding.get("table_structure_engines") or [{}])[0]
    return {
        "kind": "drawing_analysis_report",
        "state": "DRAFT/CANDIDATE",
        "identification": {
            "product_code": product_code,
            "document_id": understanding.get("document"),
            "revision": understanding.get("revision"),
            "customer": understanding.get("customer"),
            "document_sha": document_hash,
            "analyzed_at_source": provider_id,
        },
        "summary": {
            "regions_identified": len(understanding.get("regions") or []),
            "component_rows": len(comp),
            "slanet_cells": sl_e.get("cell_count"),
            "slanet_cells_with_text": sl_e.get("cells_with_text"),
            "slanet_executed": sl_e.get("executed"),
            "structure_score": sl_e.get("structure_score"),
        },
        "structure": {
            "regions": understanding.get("regions") or [],
            "title_block": understanding.get("title_block"),
            "revisions": understanding.get("revisions") or [],
            "notes": understanding.get("notes") or [],
        },
        "component_candidates": [
            {
                "item": r.get("item"),
                "quantity": r.get("quantity"),
                "component_code": r.get("component_code"),
                "description": r.get("description"),
                "region": r.get("region"),
                "cell_refs": r.get("cells") or [],
                "evidence": r.get("evidence") or r.get("fields"),
                "association_status": r.get(
                    "association_status", "CANDIDATE"
                ),
            }
            for r in comp
        ],
        "technical_information": {
            "dimensions": understanding.get("dimensions") or [],
            "state": "PENDING_ENGINEERING_VALIDATION",
            "limitations": (
                "cotas/tolerancias/materiais/simbolos ainda nao validados "
                "pela Engenharia (catalogo M3 pendente)"
            ),
        },
        "official_comparison": understanding.get("bom_comparison")
        or {"state": "NOT_CHECKED"},
        "alerts": {
            "ambiguous": understanding.get("ambiguous_fields") or [],
            "unassigned_tokens": (
                (sl_e.get("association") or {}).get("unassigned") or []
            ),
            "conflicts": (
                (sl_e.get("association") or {}).get("conflicts") or []
            ),
            "limitations": understanding.get("limitations") or [],
        },
        "evidence": {
            "document_sha": document_hash,
            "page": 1,
            "engines": {
                "ocr": provider_id,
                "table_structure": sl_e.get("provider_id"),
                "model": sl_e.get("model_version"),
            },
            "cell_bounding_boxes": [
                c.get("bounding_box_px") for c in (sl_e.get("cells") or [])
            ],
        },
        "quality_gate": "EVAL_PENDING",
        "not_official": True,
    }


class UnderstandingIntelligenceAdapter:
    """Implementação atual — encapsula build_understanding + build_report."""

    def build_report(
        self,
        understanding: dict[str, Any],
        *,
        document_hash: str,
        provider_id: str | None,
        product_code: str,
    ) -> dict[str, Any]:
        return build_report(
            understanding,
            document_hash=document_hash,
            provider_id=provider_id,
            product_code=product_code,
        )


# Composition root — resolve a implementação (substituível por injeção).
_default: DrawingIntelligencePort | None = None


def get_drawing_intelligence() -> DrawingIntelligencePort:
    global _default
    if _default is None:
        _default = UnderstandingIntelligenceAdapter()
    return _default


def set_drawing_intelligence(impl: DrawingIntelligencePort) -> None:
    """Injection point para testes/substituição futura."""
    global _default
    _default = impl
