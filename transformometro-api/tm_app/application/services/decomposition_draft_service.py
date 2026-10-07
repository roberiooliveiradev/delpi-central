"""Draft decomposition suggestion from the macro flowchart (compute-only).

Owner of the sugerir_rascunho_decomposicao semantics: derives a
``decomposition_tree_v1`` draft from subprocess/process flowchart nodes.
Pure computation — nothing is persisted; callers decide whether/how to
persist via the governed write path.
"""

from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.repositories.process_diagram_repository import (
    ProcessoDiagramRepository,
)
from tm_app.domain.diagram.flowchart_v1 import empty_flowchart


class DecompositionDraftService:
    """Builds a non-persisted decomposition draft from a process diagram."""

    def suggest_for_processo(self, processo_id: str) -> dict[str, Any]:
        """Draft tree for a process; caller must check process existence/AuthZ."""
        diagram_row = ProcessoDiagramRepository().get(processo_id)
        flowchart = (diagram_row or {}).get("conteudo") or empty_flowchart()
        return {"conteudo": self.suggest_from_flowchart(flowchart), "persisted": False}

    @staticmethod
    def suggest_from_flowchart(flowchart: dict[str, Any]) -> dict[str, Any]:
        draft_nodes: list[dict[str, Any]] = []
        ordem_pk = 1
        for node in flowchart.get("nodes", []):
            if not isinstance(node, dict):
                continue
            if node.get("type") != "subprocess":
                continue
            pk_id = f"pk_{node.get('id', ordem_pk)}"
            draft_nodes.append(
                {
                    "id": pk_id,
                    "level": "processo_chave",
                    "ordem": ordem_pk,
                    "label": str(node.get("label") or f"Processo-chave {ordem_pk}"),
                    "parent_id": None,
                    "descricao": None,
                    "meta": {"source_flow_node_id": str(node.get("id") or "")},
                }
            )
            ordem_pk += 1

        ordem_st = 1
        for node in flowchart.get("nodes", []):
            if not isinstance(node, dict) or node.get("type") != "process":
                continue
            parent_pk = draft_nodes[0]["id"] if draft_nodes else None
            if not parent_pk:
                continue
            draft_nodes.append(
                {
                    "id": f"st_{node.get('id', ordem_st)}",
                    "level": "sub_tarefa",
                    "ordem": ordem_st,
                    "label": str(node.get("label") or f"Sub-tarefa {ordem_st}"),
                    "parent_id": parent_pk,
                    "descricao": None,
                    "meta": {"source_flow_node_id": str(node.get("id") or "")},
                }
            )
            ordem_st += 1

        return {
            "format": "decomposition_tree_v1",
            "format_version": 1,
            "nodes": draft_nodes,
        }
