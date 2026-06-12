from __future__ import annotations

from typing import Any

from tm_app.application.services.revisao_tree_copy_service import copy_revisao_tree
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from tm_app.infrastructure.persistence.repositories.investimento_repository import (
    InvestimentoRepository,
)
from tm_app.infrastructure.persistence.repositories.medicao_repository import MedicaoRepository
from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.recurso_repository import VinculoRepository
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository
from tm_app.infrastructure.providers.database.plugins_postgres_connection import (
    get_plugins_connection,
)


class InstanciaNotFoundError(ValueError):
    pass


class InstanciaDuplicateService:
    """Replica timeline de revisões da instância origem para outro par filial × setor."""

    def duplicate(
        self,
        instancia_id: str,
        *,
        filial_id: str,
        setor_id: str,
        rotulo_instancia: str | None = None,
    ) -> dict[str, Any]:
        conn = get_plugins_connection()
        inst_repo = ProcessoInstanciaRepository(connection=conn)
        rev_repo = RevisaoRepository(connection=conn)
        med_repo = MedicaoRepository(connection=conn)
        inv_repo = InvestimentoRepository(connection=conn)
        vin_repo = VinculoRepository(connection=conn)

        source = inst_repo.get(instancia_id)
        if not source:
            raise InstanciaNotFoundError("Instância não encontrada.")

        target_filial = str(filial_id).strip()
        target_setor = str(setor_id).strip()
        if (
            str(source.get("codigo_filial") or "").lower() == target_filial.lower()
            and str(source.get("codigo_setor") or "").lower() == target_setor.lower()
        ):
            raise ValueError(
                "Destino igual à instância origem. Informe outra filial ou setor."
            )

        processo_id = str(source["processo_id"])
        source_revisoes = rev_repo.list_by_instancia(instancia_id)
        if not source_revisoes:
            raise ValueError("Instância origem não possui revisões para copiar.")

        try:
            target = inst_repo.create(
                {
                    "processo_id": processo_id,
                    "filial_id": target_filial,
                    "setor_id": target_setor,
                    "rotulo_instancia": rotulo_instancia,
                },
                auto_commit=False,
            )
            target_id = str(target["instancia_id"])
            if target_id == str(source["instancia_id"]):
                raise ValueError(
                    "Destino igual à instância origem. Informe outra filial ou setor."
                )

            if rev_repo.list_by_instancia(target_id):
                raise ValueError("Instância destino já possui revisões.")

            stats = copy_revisao_tree(
                revisoes=source_revisoes,
                processo_id=processo_id,
                instancia_id=target_id,
                rev_repo=rev_repo,
                med_repo=med_repo,
                inv_repo=inv_repo,
                vin_repo=vin_repo,
                auto_commit=False,
            )
            conn.commit()
            return {
                "instancia": target,
                "processo_id": processo_id,
                "origem_instancia_id": instancia_id,
                "copiados": stats,
            }
        except InstanciaNotFoundError:
            conn.rollback()
            raise
        except Exception as exc:
            conn.rollback()
            if isinstance(exc, PluginsRepositoryError):
                raise ValueError(str(exc)) from exc
            raise
