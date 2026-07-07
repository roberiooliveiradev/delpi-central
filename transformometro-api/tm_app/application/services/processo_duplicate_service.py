from __future__ import annotations

from typing import Any

from tm_app.application.services.revisao_evidence_storage import (
    RevisaoEvidenceStorage,
    RevisaoEvidenceStorageError,
)
from tm_app.application.services.revisao_tree_copy_service import copy_revisao_tree
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from tm_app.infrastructure.persistence.repositories.instancia_decomposicao_escopo_repository import (
    InstanciaDecomposicaoEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.instancia_diagram_escopo_repository import (
    InstanciaDiagramEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.investimento_repository import (
    InvestimentoRepository,
)
from tm_app.infrastructure.persistence.repositories.medicao_repository import MedicaoRepository
from tm_app.infrastructure.persistence.repositories.processo_decomposicao_repository import (
    ProcessoDecomposicaoRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_diagram_repository import (
    ProcessoDiagramRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_escopo_repository import (
    ProcessoEscopoRepository,
)
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


class ProcessoNotFoundError(ValueError):
    pass


def _empty_copy_stats() -> dict[str, int]:
    return {
        "melhorias": 0,
        "revisoes": 0,
        "medicoes": 0,
        "investimentos": 0,
        "vinculos": 0,
        "diagramas_macro": 0,
        "decomposicao": 0,
        "escopos_diagrama": 0,
        "escopos_decomposicao": 0,
        "overlays_diagrama": 0,
        "overlays_decomposicao": 0,
        "evidencias": 0,
    }


def _merge_stats(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + int(value or 0)


def _instancia_create_payload(source: dict[str, Any], new_processo_id: str) -> dict[str, Any]:
    setores = source.get("setores") or []
    setor_ids = [
        str(setor.get("codigo_setor") or setor.get("setor_id") or "").strip()
        for setor in setores
        if isinstance(setor, dict)
    ]
    setor_ids = [item for item in setor_ids if item]
    return {
        "processo_id": new_processo_id,
        "filial_id": source.get("codigo_filial"),
        "todas_filiais_ativas": bool(source.get("todas_filiais_ativas")),
        "setor_ids": setor_ids,
        "rotulo_instancia": source.get("rotulo_instancia"),
        "status_instancia": source.get("status_instancia", "ativo"),
        "resumo_melhoria": source.get("resumo_melhoria"),
        "responsavel_local": source.get("responsavel_local"),
        "fase_melhoria": source.get("fase_melhoria", "planejado"),
        "data_alvo_go_live": source.get("data_alvo_go_live"),
        "prioridade": source.get("prioridade", "media"),
    }


class ProcessoDuplicateService:
    """Duplica processo-mestre completo: melhorias, diagrama, WBS, revisões e evidências."""

    def duplicate(
        self,
        processo_id: str,
        *,
        nome_processo: str | None = None,
    ) -> dict[str, Any]:
        conn = get_plugins_connection()
        proc_repo = ProcessoRepository(connection=conn)
        escopo_repo = ProcessoEscopoRepository(connection=conn)
        inst_repo = ProcessoInstanciaRepository(connection=conn)
        rev_repo = RevisaoRepository(connection=conn)
        med_repo = MedicaoRepository(connection=conn)
        inv_repo = InvestimentoRepository(connection=conn)
        vin_repo = VinculoRepository(connection=conn)
        diagram_repo = ProcessoDiagramRepository(connection=conn)
        decomp_repo = ProcessoDecomposicaoRepository(connection=conn)
        inst_diagram_repo = InstanciaDiagramEscopoRepository(connection=conn)
        inst_decomp_repo = InstanciaDecomposicaoEscopoRepository(connection=conn)
        rev_diagram_repo = RevisaoDiagramOverlayRepository(connection=conn)
        rev_decomp_repo = RevisaoDecomposicaoOverlayRepository(connection=conn)
        evidence_repo = RevisaoEvidenceRepository(connection=conn)
        evidence_storage = RevisaoEvidenceStorage()

        source = proc_repo.get(processo_id)
        if not source:
            raise ProcessoNotFoundError("Processo não encontrado.")

        source_instancias = inst_repo.list_by_processo(processo_id)
        stats = _empty_copy_stats()

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

            source_escopo = escopo_repo.get_escopo(processo_id)
            if source_escopo.get("setor_ids") or source_escopo.get("todas_filiais_ativas"):
                escopo_repo.save_escopo(
                    new_processo_id,
                    todas_filiais_ativas=bool(source_escopo.get("todas_filiais_ativas")),
                    filial_ids=source_escopo.get("filial_ids"),
                    setor_ids=source_escopo.get("setor_ids"),
                    auto_commit=False,
                )

            source_diagram = diagram_repo.get(processo_id)
            if source_diagram:
                diagram_repo.upsert_from_backup(
                    {
                        "processo_id": new_processo_id,
                        "conteudo": source_diagram.get("conteudo") or {},
                        "mermaid_cached": source_diagram.get("mermaid_cached"),
                        "created_at": source_diagram.get("created_at"),
                        "updated_at": source_diagram.get("updated_at"),
                    },
                    auto_commit=False,
                )
                stats["diagramas_macro"] = 1

            source_decomp = decomp_repo.get(processo_id)
            if source_decomp:
                decomp_repo.upsert_from_backup(
                    {
                        "processo_id": new_processo_id,
                        "conteudo": source_decomp.get("conteudo") or {},
                        "created_at": source_decomp.get("created_at"),
                        "updated_at": source_decomp.get("updated_at"),
                    },
                    auto_commit=False,
                )
                stats["decomposicao"] = 1

            for source_inst in source_instancias:
                old_inst_id = str(source_inst["instancia_id"])
                new_instancia = inst_repo.create(
                    _instancia_create_payload(source_inst, new_processo_id),
                    auto_commit=False,
                )
                new_inst_id = str(new_instancia["instancia_id"])
                stats["melhorias"] += 1

                contexto = source_inst.get("contexto")
                if isinstance(contexto, dict) and contexto:
                    inst_repo.update_contexto(new_inst_id, contexto, auto_commit=False)

                inst_diagram = inst_diagram_repo.get(old_inst_id)
                if inst_diagram:
                    inst_diagram_repo.upsert_from_backup(
                        {
                            "instancia_id": new_inst_id,
                            "node_ids": list(inst_diagram.get("node_ids") or []),
                            "inherit_all": bool(inst_diagram.get("inherit_all", True)),
                            "include_boundary_edges": bool(
                                inst_diagram.get("include_boundary_edges", False)
                            ),
                            "created_at": inst_diagram.get("created_at"),
                            "updated_at": inst_diagram.get("updated_at"),
                        },
                        auto_commit=False,
                    )
                    stats["escopos_diagrama"] += 1

                inst_decomp = inst_decomp_repo.get(old_inst_id)
                if inst_decomp:
                    inst_decomp_repo.upsert_from_backup(
                        {
                            "instancia_id": new_inst_id,
                            "node_ids": list(inst_decomp.get("node_ids") or []),
                            "inherit_all": bool(inst_decomp.get("inherit_all", True)),
                            "include_descendants": bool(
                                inst_decomp.get("include_descendants", True)
                            ),
                            "created_at": inst_decomp.get("created_at"),
                            "updated_at": inst_decomp.get("updated_at"),
                        },
                        auto_commit=False,
                    )
                    stats["escopos_decomposicao"] += 1

                revisoes = rev_repo.list_by_instancia(old_inst_id)
                tree_stats, revisao_id_map = copy_revisao_tree(
                    revisoes=revisoes,
                    processo_id=new_processo_id,
                    instancia_id=new_inst_id,
                    rev_repo=rev_repo,
                    med_repo=med_repo,
                    inv_repo=inv_repo,
                    vin_repo=vin_repo,
                    auto_commit=False,
                )
                _merge_stats(stats, tree_stats)

                for old_rev_id, new_rev_id in revisao_id_map.items():
                    rev_diagram = rev_diagram_repo.get(old_rev_id)
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
                        stats["overlays_diagrama"] += 1

                    rev_decomp = rev_decomp_repo.get(old_rev_id)
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
                        stats["overlays_decomposicao"] += 1

                    for evidence in evidence_repo.list_by_revisao(old_rev_id):
                        stored_name = (evidence.get("nome_armazenado") or "").strip()
                        new_stored_name = stored_name
                        if stored_name:
                            try:
                                new_stored_name = evidence_storage.copy_file(
                                    source_revisao_id=old_rev_id,
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

            conn.commit()
            return {
                "processo": new_processo,
                "origem_processo_id": processo_id,
                "copiados": stats,
            }
        except ProcessoNotFoundError:
            conn.rollback()
            raise
        except Exception as exc:
            conn.rollback()
            if isinstance(exc, PluginsRepositoryError):
                raise ValueError(str(exc)) from exc
            raise
