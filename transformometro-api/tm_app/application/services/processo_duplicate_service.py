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
from tm_app.infrastructure.persistence.repositories.processo_repository import ProcessoRepository
from tm_app.infrastructure.persistence.repositories.recurso_repository import VinculoRepository
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository
from tm_app.infrastructure.providers.database.plugins_postgres_connection import (
    get_plugins_connection,
)


class ProcessoNotFoundError(ValueError):
    pass


class ProcessoDuplicateService:
    """Duplica processo inteiro (legado). Preferir ``InstanciaDuplicateService``."""

    def duplicate(
        self,
        processo_id: str,
        *,
        nome_processo: str | None = None,
    ) -> dict[str, Any]:
        conn = get_plugins_connection()
        proc_repo = ProcessoRepository(connection=conn)
        rev_repo = RevisaoRepository(connection=conn)
        med_repo = MedicaoRepository(connection=conn)
        inv_repo = InvestimentoRepository(connection=conn)
        vin_repo = VinculoRepository(connection=conn)

        source = proc_repo.get(processo_id)
        if not source:
            raise ProcessoNotFoundError("Processo não encontrado.")

        source_inst = ProcessoInstanciaRepository(connection=conn).get_by_processo(processo_id)
        if not source_inst:
            raise ValueError(
                "Processo sem instância operacional. Cadastre filial × setor antes de duplicar."
            )

        revisoes = rev_repo.list_by_processo(processo_id)

        try:
            new_processo = proc_repo.create(
                {
                    "nome_processo": nome_processo
                    or f"{source['nome_processo']} (cópia)",
                    "descricao_processo": source.get("descricao_processo"),
                    "gestor_responsavel": source.get("gestor_responsavel"),
                    "objetivo_processo": source.get("objetivo_processo"),
                    "status_processo": source["status_processo"],
                    "familia_processo": source.get("familia_processo"),
                    "agrupador_ferramenta": source.get("agrupador_ferramenta"),
                },
                auto_commit=False,
            )
            new_processo_id = str(new_processo["processo_id"])
            new_instancia = ProcessoInstanciaRepository(connection=conn).create(
                {
                    "processo_id": new_processo_id,
                    "filial_id": source_inst["codigo_filial"],
                    "setor_id": source_inst["codigo_setor"],
                },
                auto_commit=False,
            )
            stats = copy_revisao_tree(
                revisoes=revisoes,
                processo_id=new_processo_id,
                instancia_id=str(new_instancia["instancia_id"]),
                rev_repo=rev_repo,
                med_repo=med_repo,
                inv_repo=inv_repo,
                vin_repo=vin_repo,
                auto_commit=False,
            )
            conn.commit()
            return {
                "processo": new_processo,
                "origem_processo_id": processo_id,
                "copiados": stats,
                "deprecated": True,
                "successor": f"/transformometro/instancias/{source_inst['instancia_id']}/duplicar",
            }
        except ProcessoNotFoundError:
            conn.rollback()
            raise
        except Exception as exc:
            conn.rollback()
            if isinstance(exc, PluginsRepositoryError):
                raise ValueError(str(exc)) from exc
            raise
