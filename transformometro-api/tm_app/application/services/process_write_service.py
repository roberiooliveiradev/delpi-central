"""Shared process write orchestration for CRUD and GPT Actions facades."""

from __future__ import annotations

from typing import Any

from tm_app.core.catalogs import STATUS_PROCESSO, assert_in
from tm_app.domain.services.branch_catalog_service import assert_filial_ativa
from tm_app.domain.services.process_instance_service import ProcessoInstanciaDomainError
from tm_app.domain.services.process_scope_service import ProcessoEscopoDomainError
from tm_app.infrastructure.persistence.repositories.department_repository import (
    SetorRepository,
)
from tm_app.infrastructure.persistence.repositories.process_instance_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_scope_repository import (
    ProcessoEscopoRepository,
)


class ProcessWriteError(Exception):
    """Domain/validation failure while creating or updating a process."""


def process_master_payload(body: Any) -> dict[str, Any]:
    return {
        "nome_processo": body.nome_processo,
        "descricao_processo": body.descricao_processo,
        "gestor_responsavel": body.gestor_responsavel,
        "objetivo_processo": body.objetivo_processo,
        "status_processo": body.status_processo,
        "codigo_processo": body.codigo_processo,
        "familia_processo": body.familia_processo,
        "agrupador_ferramenta": body.agrupador_ferramenta,
    }


class ProcessWriteService:
    """Create/update process master (+ optional first instance and scope)."""

    def validate_create_body(self, body: Any, *, active_filial_codigos: set[str]) -> None:
        assert_in(body.status_processo, STATUS_PROCESSO, "status_processo")
        has_filial = bool((body.filial_id or "").strip())
        has_setor = bool((body.setor_id or "").strip())
        if has_filial != has_setor:
            raise ProcessWriteError(
                "filial_id e setor_id devem ser informados juntos para criar instância operacional."
            )
        if not has_filial:
            return
        assert_filial_ativa(body.filial_id, active_filial_codigos)
        if not SetorRepository().is_active_for_filial(body.setor_id, body.filial_id):
            raise ProcessWriteError(
                f"setor_id '{body.setor_id}' não está vinculado à unidade {body.filial_id}"
            )

    def create(
        self,
        body: Any,
        *,
        active_filial_codigos: set[str],
        save_escopo,
    ) -> dict[str, Any]:
        """Create process. ``save_escopo(processo_id, body)`` persists optional escopo."""
        self.validate_create_body(body, active_filial_codigos=active_filial_codigos)
        filial_id = (body.filial_id or "").strip() or None
        setor_id = (body.setor_id or "").strip() or None
        create_instancia = bool(filial_id and setor_id)
        try:
            repo = ProcessoRepository()
            row = repo.create(process_master_payload(body))
            pid = str(row["processo_id"])
            save_escopo(pid, body)
            if create_instancia:
                instancia = ProcessoInstanciaRepository().create(
                    {
                        "processo_id": pid,
                        "filial_id": filial_id,
                        "setor_ids": [setor_id],
                    }
                )
                row = repo.get(pid) or {**row, **instancia}
            else:
                row = repo.get(pid) or row
            return row
        except (ProcessoEscopoDomainError, ProcessoInstanciaDomainError, ValueError) as exc:
            raise ProcessWriteError(str(exc)) from exc

    def update(
        self,
        processo_id: str,
        body: Any,
        *,
        save_escopo,
    ) -> dict[str, Any]:
        assert_in(body.status_processo, STATUS_PROCESSO, "status_processo")
        try:
            row = ProcessoRepository().update(processo_id, process_master_payload(body))
            if not row:
                return {}
            save_escopo(processo_id, body)
            return ProcessoRepository().get(processo_id) or row
        except (ProcessoEscopoDomainError, ValueError) as exc:
            raise ProcessWriteError(str(exc)) from exc


class RevisionActivationService:
    """Activate a revision as the operational current version."""

    def activate(self, revisao_id: str) -> dict[str, Any] | None:
        from tm_app.infrastructure.persistence.repositories.revision_repository import (
            RevisaoRepository,
        )

        return RevisaoRepository().activate(str(revisao_id))
