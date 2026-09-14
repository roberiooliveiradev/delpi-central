"""Canonical diagram write operations shared by UI routes and GPT Actions.

Validates flowchart_v1 / escopo / overlay before persistence. Mermaid is always
server-derived — never trust client-provided mermaid_cached as source of truth.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.services.diagram_mermaid_export_service import (
    DiagramMermaidExportService,
)
from tm_app.application.services.revision_diagram_merge_service import (
    RevisaoDiagramMergeService,
)
from tm_app.domain.diagram.flowchart_v1 import (
    FlowchartValidationError,
    empty_escopo,
    empty_flowchart,
    macro_node_ids,
    validate_escopo,
    validate_flowchart_v1,
    validate_overlay_v1,
)
from tm_app.infrastructure.persistence.repositories.instance_scope_diagram_repository import (
    InstanciaDiagramEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_diagram_repository import (
    ProcessoDiagramRepository,
)
from tm_app.infrastructure.persistence.repositories.process_instance_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_diagram_overlay_repository import (
    RevisaoDiagramOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import (
    RevisaoRepository,
)


class DiagramWriteError(ValueError):
    """Domain/validation failure for diagram writes (maps to HTTP 400)."""

    def __init__(self, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DiagramWriteService:
    """Application owner for diagram persistence (UI + GPT)."""

    def __init__(self) -> None:
        self._mermaid = DiagramMermaidExportService()
        self._merge = RevisaoDiagramMergeService()

    def prepare_macro(
        self, processo_id: str, conteudo: dict[str, Any] | None
    ) -> dict[str, Any]:
        if not ProcessoRepository().get(processo_id):
            raise DiagramWriteError("Processo não encontrado.", status_code=404)
        try:
            validated = validate_flowchart_v1(conteudo or {})
        except FlowchartValidationError as exc:
            raise DiagramWriteError(str(exc)) from exc
        mermaid = self._mermaid.flowchart_to_mermaid(validated)
        current = ProcessoDiagramRepository().get(processo_id)
        return {
            "valid": True,
            "processo_id": processo_id,
            "normalized_payload": validated,
            "mermaid": mermaid,
            "current_state": (current or {}).get("conteudo"),
            "proposed_state": validated,
            "diff_summary": {
                "nodes": len(validated.get("nodes") or []),
                "edges": len(validated.get("edges") or []),
            },
            "postcondition": "process_diagram will store flowchart_v1; mermaid server-derived",
            "persisted": False,
        }

    def save_macro(
        self, processo_id: str, conteudo: dict[str, Any] | None
    ) -> dict[str, Any]:
        prepared = self.prepare_macro(processo_id, conteudo)
        validated = prepared["normalized_payload"]
        mermaid = prepared["mermaid"]
        row = ProcessoDiagramRepository().upsert(
            processo_id,
            conteudo=validated,
            mermaid_cached=mermaid,
        )
        return {
            "row": row,
            "conteudo": validated,
            "mermaid": mermaid,
            "processo_id": processo_id,
            "nodes": len(validated.get("nodes") or []),
        }

    def prepare_instance_scope(
        self, instancia_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        instancia = ProcessoInstanciaRepository().get(instancia_id)
        if not instancia:
            raise DiagramWriteError("Instância não encontrada.", status_code=404)
        processo_id = str(instancia["processo_id"])
        macro_row = ProcessoDiagramRepository().get(processo_id)
        macro = (macro_row or {}).get("conteudo") or empty_flowchart()
        try:
            escopo = validate_escopo(
                payload,
                macro_node_ids=macro_node_ids(macro),
            )
        except FlowchartValidationError as exc:
            raise DiagramWriteError(str(exc)) from exc
        current = InstanciaDiagramEscopoRepository().get(instancia_id)
        return {
            "valid": True,
            "instancia_id": instancia_id,
            "processo_id": processo_id,
            "normalized_payload": escopo,
            "current_state": current,
            "proposed_state": escopo,
            "persisted": False,
        }

    def save_instance_scope(
        self, instancia_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        prepared = self.prepare_instance_scope(instancia_id, payload)
        escopo = prepared["normalized_payload"]
        row = InstanciaDiagramEscopoRepository().upsert(
            instancia_id,
            node_ids=escopo["node_ids"],
            inherit_all=escopo["inherit_all"],
            include_boundary_edges=escopo["include_boundary_edges"],
        )
        return {
            "row": row,
            "escopo": escopo,
            "instancia_id": instancia_id,
            "inherit_all": escopo["inherit_all"],
            "nodes": len(escopo["node_ids"]),
        }

    def _load_merge_context(
        self, revisao_id: str
    ) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any], dict[str, Any] | None]:
        revisao = RevisaoRepository().get(revisao_id)
        if not revisao:
            raise DiagramWriteError("Revisão não encontrada.", status_code=404)
        processo_id = str(revisao["processo_id"])
        instancia_id = str(revisao.get("instancia_id") or "")
        macro_row = ProcessoDiagramRepository().get(processo_id)
        macro = (macro_row or {}).get("conteudo") if macro_row else None
        escopo_row = (
            InstanciaDiagramEscopoRepository().get(instancia_id) if instancia_id else None
        )
        if escopo_row:
            escopo = {
                "node_ids": escopo_row.get("node_ids") or [],
                "inherit_all": bool(escopo_row.get("inherit_all", True)),
                "include_boundary_edges": bool(
                    escopo_row.get("include_boundary_edges", False)
                ),
            }
        else:
            escopo = empty_escopo()
        overlay_row = RevisaoDiagramOverlayRepository().get(revisao_id)
        overlay = (overlay_row or {}).get("conteudo") if overlay_row else None
        return revisao, macro, escopo, overlay

    def prepare_revision_overlay(
        self, revisao_id: str, conteudo: dict[str, Any] | None
    ) -> dict[str, Any]:
        revisao, macro, escopo, current_overlay = self._load_merge_context(revisao_id)
        try:
            overlay = validate_overlay_v1(conteudo or {})
        except FlowchartValidationError as exc:
            raise DiagramWriteError(str(exc)) from exc
        merged = self._merge.merge(macro=macro, escopo=escopo, overlay=overlay)
        return {
            "valid": True,
            "revisao_id": revisao_id,
            "processo_id": str(revisao["processo_id"]),
            "normalized_payload": overlay,
            "mermaid": merged["mermaid"],
            "merged_preview": merged["flowchart"],
            "current_state": current_overlay,
            "proposed_state": overlay,
            "persisted": False,
        }

    def save_revision_overlay(
        self, revisao_id: str, conteudo: dict[str, Any] | None
    ) -> dict[str, Any]:
        prepared = self.prepare_revision_overlay(revisao_id, conteudo)
        overlay = prepared["normalized_payload"]
        mermaid = prepared["mermaid"]
        row = RevisaoDiagramOverlayRepository().upsert(
            revisao_id,
            conteudo=overlay,
            mermaid_cached=mermaid,
        )
        return {
            "row": row,
            "overlay": overlay,
            "mermaid": mermaid,
            "merged_preview": prepared["merged_preview"],
            "revisao_id": revisao_id,
            "overrides": len(overlay.get("node_overrides") or {}),
        }

    def read_back_macro(self, processo_id: str) -> dict[str, Any] | None:
        return ProcessoDiagramRepository().get(processo_id)
