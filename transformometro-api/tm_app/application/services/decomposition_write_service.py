"""Canonical decomposition/WBS write operations shared by UI routes and GPT Actions."""

from __future__ import annotations

from typing import Any

from tm_app.application.services.revision_decomposition_merge_service import (
    RevisaoDecomposicaoMergeService,
)
from tm_app.domain.decomposition.decomposition_tree_v1 import (
    DecompositionValidationError,
    empty_tree,
    tree_node_ids,
    validate_decomposition_escopo,
    validate_decomposition_tree_v1,
)
from tm_app.infrastructure.persistence.repositories.instance_scope_decomposition_repository import (
    InstanciaDecomposicaoEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_decomposition_repository import (
    ProcessoDecomposicaoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_instance_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_decomposition_overlay_repository import (
    RevisaoDecomposicaoOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import (
    RevisaoRepository,
)


class DecompositionWriteError(ValueError):
    def __init__(self, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DecompositionWriteService:
    """Application owner for WBS/decomposition persistence (UI + GPT)."""

    def __init__(self) -> None:
        self._merge = RevisaoDecomposicaoMergeService()

    def prepare_tree(
        self, processo_id: str, conteudo: dict[str, Any] | None
    ) -> dict[str, Any]:
        if not ProcessoRepository().get(processo_id):
            raise DecompositionWriteError("Processo não encontrado.", status_code=404)
        try:
            validated = validate_decomposition_tree_v1(conteudo or {})
        except DecompositionValidationError as exc:
            raise DecompositionWriteError(str(exc)) from exc
        current = ProcessoDecomposicaoRepository().get(processo_id)
        return {
            "valid": True,
            "processo_id": processo_id,
            "normalized_payload": validated,
            "current_state": (current or {}).get("conteudo"),
            "proposed_state": validated,
            "diff_summary": {"nodes": len(validated.get("nodes") or [])},
            "persisted": False,
        }

    def save_tree(
        self, processo_id: str, conteudo: dict[str, Any] | None
    ) -> dict[str, Any]:
        prepared = self.prepare_tree(processo_id, conteudo)
        validated = prepared["normalized_payload"]
        row = ProcessoDecomposicaoRepository().upsert(processo_id, conteudo=validated)
        return {
            "row": row,
            "conteudo": validated,
            "processo_id": processo_id,
            "nodes": len(validated.get("nodes") or []),
        }

    def prepare_instance_scope(
        self, instancia_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        instancia = ProcessoInstanciaRepository().get(instancia_id)
        if not instancia:
            raise DecompositionWriteError("Instância não encontrada.", status_code=404)
        processo_id = str(instancia["processo_id"])
        tree_row = ProcessoDecomposicaoRepository().get(processo_id)
        tree = (tree_row or {}).get("conteudo") or empty_tree()
        try:
            escopo = validate_decomposition_escopo(
                payload,
                tree_node_ids_set=tree_node_ids(tree),
            )
        except DecompositionValidationError as exc:
            raise DecompositionWriteError(str(exc)) from exc
        current = InstanciaDecomposicaoEscopoRepository().get(instancia_id)
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
        row = InstanciaDecomposicaoEscopoRepository().upsert(
            instancia_id,
            node_ids=escopo["node_ids"],
            inherit_all=escopo["inherit_all"],
            include_descendants=escopo["include_descendants"],
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
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any] | None]:
        revisao = RevisaoRepository().get(revisao_id)
        if not revisao:
            raise DecompositionWriteError("Revisão não encontrada.", status_code=404)
        processo_id = str(revisao["processo_id"])
        instancia_id = str(revisao.get("instancia_id") or "")
        tree_row = ProcessoDecomposicaoRepository().get(processo_id)
        tree = (tree_row or {}).get("conteudo") or empty_tree()
        escopo_row = (
            InstanciaDecomposicaoEscopoRepository().get(instancia_id)
            if instancia_id
            else None
        )
        if escopo_row:
            escopo = {
                "node_ids": escopo_row.get("node_ids") or [],
                "inherit_all": bool(escopo_row.get("inherit_all", True)),
                "include_descendants": bool(escopo_row.get("include_descendants", True)),
            }
        else:
            escopo = {
                "node_ids": [],
                "inherit_all": True,
                "include_descendants": True,
            }
        overlay_row = RevisaoDecomposicaoOverlayRepository().get(revisao_id)
        overlay = (overlay_row or {}).get("conteudo") if overlay_row else None
        return revisao, tree, escopo, overlay

    def prepare_revision_overlay(
        self, revisao_id: str, conteudo: dict[str, Any] | None
    ) -> dict[str, Any]:
        revisao, tree, escopo, current = self._load_merge_context(revisao_id)
        try:
            validated = self._merge.assert_overlay_within_escopo(
                tree=tree,
                escopo=escopo,
                overlay=conteudo or {},
            )
        except DecompositionValidationError as exc:
            raise DecompositionWriteError(str(exc)) from exc
        merged = self._merge.merge(tree=tree, escopo=escopo, overlay=validated)
        return {
            "valid": True,
            "revisao_id": revisao_id,
            "processo_id": str(revisao["processo_id"]),
            "normalized_payload": validated,
            "merged_preview": merged.get("tree"),
            "current_state": current,
            "proposed_state": validated,
            "persisted": False,
        }

    def save_revision_overlay(
        self, revisao_id: str, conteudo: dict[str, Any] | None
    ) -> dict[str, Any]:
        prepared = self.prepare_revision_overlay(revisao_id, conteudo)
        validated = prepared["normalized_payload"]
        row = RevisaoDecomposicaoOverlayRepository().upsert(
            revisao_id, conteudo=validated
        )
        return {
            "row": row,
            "overlay": validated,
            "revisao_id": revisao_id,
            "merged_preview": prepared["merged_preview"],
            "overrides": len(validated.get("node_overrides") or {}),
        }

    def read_back_tree(self, processo_id: str) -> dict[str, Any] | None:
        return ProcessoDecomposicaoRepository().get(processo_id)
