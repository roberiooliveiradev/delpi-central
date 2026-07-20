from __future__ import annotations

from typing import Any

from tm_app.application.services.revisao_evidence_storage import (
    RevisaoEvidenceStorage,
    RevisaoEvidenceStorageError,
)
from tm_app.application.services.revisao_tree_copy_service import copy_revisao_dependents
from tm_app.application.services.revisao_version_utils import suggest_duplicate_versao_revisao
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from tm_app.infrastructure.persistence.repositories.investimento_repository import (
    InvestimentoRepository,
)
from tm_app.infrastructure.persistence.repositories.medicao_repository import MedicaoRepository
from tm_app.infrastructure.persistence.repositories.recurso_repository import VinculoRepository
from tm_app.infrastructure.persistence.repositories.revisao_decomposicao_overlay_repository import (
    RevisaoDecomposicaoOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_diagram_overlay_repository import (
    RevisaoDiagramOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_evidence_repository import (
    RevisaoEvidenceRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository
from tm_app.infrastructure.providers.database.plugins_postgres_connection import (
    get_plugins_connection,
)


class RevisaoNotFoundError(ValueError):
    pass


class RevisaoDuplicateService:
    """Duplica uma revisão na mesma instância, incluindo cadastro operacional e overlays."""

    def duplicate(
        self,
        revisao_id: str,
        *,
        versao_revisao: str | None = None,
    ) -> dict[str, Any]:
        conn = get_plugins_connection()
        rev_repo = RevisaoRepository(connection=conn)
        med_repo = MedicaoRepository(connection=conn)
        inv_repo = InvestimentoRepository(connection=conn)
        vin_repo = VinculoRepository(connection=conn)
        rev_diagram_repo = RevisaoDiagramOverlayRepository(connection=conn)
        rev_decomp_repo = RevisaoDecomposicaoOverlayRepository(connection=conn)
        evidence_repo = RevisaoEvidenceRepository(connection=conn)

        source = rev_repo.get(revisao_id)
        if not source:
            raise RevisaoNotFoundError("Revisão não encontrada.")

        instancia_id = str(source["instancia_id"])
        processo_id = str(source["processo_id"])
        existing_versions = {
            str(row["versao_revisao"])
            for row in rev_repo.list_by_instancia(instancia_id)
            if row.get("versao_revisao")
        }
        target_version = (versao_revisao or "").strip() or suggest_duplicate_versao_revisao(
            str(source.get("versao_revisao") or ""),
            existing_versions,
        )
        if target_version in existing_versions:
            raise ValueError(f"A versão {target_version} já existe nesta instância.")

        stats = {
            "revisoes": 1,
            "medicoes": 0,
            "investimentos": 0,
            "vinculos": 0,
            "overlays_diagrama": 0,
            "overlays_decomposicao": 0,
            "evidencias": 0,
            "matriz_impacto_esforco": 0,
        }

        try:
            new_revisao = rev_repo.create(
                {
                    "processo_id": processo_id,
                    "instancia_id": instancia_id,
                    "versao_revisao": target_version,
                    "cenario_tipo": source["cenario_tipo"],
                    "beneficio_calculo_categoria": source.get(
                        "beneficio_calculo_categoria"
                    )
                    or "automatico",
                    "data_inicio_vigencia": source["data_inicio_vigencia"],
                    "data_implantacao": source.get("data_implantacao"),
                    "data_fim_vigencia": source.get("data_fim_vigencia"),
                    "revisao_ativa": False,
                    "descricao_revisao": source.get("descricao_revisao"),
                    "motivo_revisao": source.get("motivo_revisao"),
                    "observacoes": source.get("observacoes"),
                    "status_aprovacao": source.get("status_aprovacao") or "aprovada",
                    "revisao_referencia_id": source.get("revisao_referencia_id"),
                },
                auto_commit=False,
            )
            new_rev_id = str(new_revisao["revisao_id"])

            dep_stats = copy_revisao_dependents(
                old_rev_id=revisao_id,
                new_rev_id=new_rev_id,
                med_repo=med_repo,
                inv_repo=inv_repo,
                vin_repo=vin_repo,
                auto_commit=False,
            )
            stats["medicoes"] = dep_stats["medicoes"]
            stats["investimentos"] = dep_stats["investimentos"]
            stats["vinculos"] = dep_stats["vinculos"]

            rev_diagram = rev_diagram_repo.get(revisao_id)
            if rev_diagram:
                rev_diagram_repo.upsert_from_backup(
                    {
                        "revisao_id": new_rev_id,
                        "conteudo": rev_diagram.get("conteudo") or {},
                        "mermaid_cached": rev_diagram.get("mermaid_cached"),
                        "created_at": rev_diagram.get("created_at"),
                        "updated_at": rev_diagram.get("updated_at"),
                    },
                    auto_commit=False,
                )
                stats["overlays_diagrama"] = 1

            rev_decomp = rev_decomp_repo.get(revisao_id)
            if rev_decomp:
                rev_decomp_repo.upsert_from_backup(
                    {
                        "revisao_id": new_rev_id,
                        "conteudo": rev_decomp.get("conteudo") or {},
                        "created_at": rev_decomp.get("created_at"),
                        "updated_at": rev_decomp.get("updated_at"),
                    },
                    auto_commit=False,
                )
                stats["overlays_decomposicao"] = 1

            evidences = evidence_repo.list_by_revisao(revisao_id)
            if evidences:
                evidence_storage = RevisaoEvidenceStorage()
            for evidence in evidences:
                stored_name = (evidence.get("nome_armazenado") or "").strip()
                new_stored_name = stored_name
                if stored_name:
                    try:
                        new_stored_name = evidence_storage.copy_file(
                            source_revisao_id=revisao_id,
                            stored_name=stored_name,
                            target_revisao_id=new_rev_id,
                        )
                    except RevisaoEvidenceStorageError:
                        new_stored_name = None
                evidence_repo.create(
                    new_rev_id,
                    {
                        "tipo": evidence.get("tipo", "anexo"),
                        "nome_arquivo": evidence.get("nome_arquivo"),
                        "nome_armazenado": new_stored_name or None,
                        "tipo_mime": evidence.get("tipo_mime"),
                        "tamanho_bytes": evidence.get("tamanho_bytes"),
                        "descricao": evidence.get("descricao"),
                        "url_externa": evidence.get("url_externa"),
                        "enviado_por_id": evidence.get("enviado_por_id"),
                        "enviado_por_nome": evidence.get("enviado_por_nome"),
                    },
                    auto_commit=False,
                )
                stats["evidencias"] += 1

            matriz = source.get("matriz_impacto_esforco")
            if isinstance(matriz, dict) and matriz:
                rev_repo.update_matriz_impacto_esforco(new_rev_id, matriz, auto_commit=False)
                stats["matriz_impacto_esforco"] = 1

            conn.commit()
            refreshed = rev_repo.get(new_rev_id) or new_revisao
            return {
                "revisao": refreshed,
                "origem_revisao_id": revisao_id,
                "processo_id": processo_id,
                "instancia_id": instancia_id,
                "copiados": stats,
            }
        except RevisaoNotFoundError:
            conn.rollback()
            raise
        except Exception as exc:
            conn.rollback()
            if isinstance(exc, PluginsRepositoryError):
                raise ValueError(str(exc)) from exc
            raise
