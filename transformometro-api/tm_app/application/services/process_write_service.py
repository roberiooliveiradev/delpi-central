"""Shared process write orchestration for CRUD and GPT Actions facades."""

from __future__ import annotations

import re
from typing import Any

from tm_app.core.catalogs import STATUS_PROCESSO, assert_in
from tm_app.domain.services.branch_catalog_service import assert_filial_ativa
from tm_app.domain.services.process_instance_service import ProcessoInstanciaDomainError
from tm_app.domain.services.process_scope_service import ProcessoEscopoDomainError
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from tm_app.infrastructure.persistence.repositories.department_repository import (
    SetorRepository,
)
from tm_app.infrastructure.persistence.repositories.process_instance_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
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


def _normalize_codigo(value: Any) -> str | None:
    if value is None:
        return None
    code = str(value).strip()
    return code or None


def _duplicate_codigo_message(exc: BaseException, *, requested: str | None) -> str | None:
    text = str(exc)
    lowered = text.lower()
    if "uq_processos_codigo" in lowered or (
        "codigo_processo" in lowered and ("unique" in lowered or "duplicate" in lowered)
    ):
        code = requested or ""
        match = re.search(r"Key \(codigo_processo\)=\(([^)]+)\)", text)
        if match:
            code = match.group(1)
        if code:
            return f"Já existe um processo com o código {code}."
        return "Já existe um processo com este código."
    return None


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
        payload = process_master_payload(body)
        try:
            repo = ProcessoRepository()
            row = repo.create(payload)
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
        except PluginsRepositoryError as exc:
            dup = _duplicate_codigo_message(
                exc, requested=_normalize_codigo(payload.get("codigo_processo"))
            )
            if dup:
                raise ProcessWriteError(dup) from exc
            raise
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
        payload = process_master_payload(body)
        requested_code = _normalize_codigo(payload.get("codigo_processo"))
        try:
            row = ProcessoRepository().update(processo_id, payload)
            if not row:
                return {}
            save_escopo(processo_id, body)
            return ProcessoRepository().get(processo_id) or row
        except PluginsRepositoryError as exc:
            dup = _duplicate_codigo_message(exc, requested=requested_code)
            if dup:
                raise ProcessWriteError(dup) from exc
            raise
        except (ProcessoEscopoDomainError, ValueError) as exc:
            raise ProcessWriteError(str(exc)) from exc


class RevisionActivationService:
    """Activate a revision as the operational current version."""

    def activate(self, revisao_id: str) -> dict[str, Any] | None:
        from tm_app.infrastructure.persistence.repositories.revision_repository import (
            RevisaoRepository,
        )

        return RevisaoRepository().activate(str(revisao_id))
