from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.repositories.investimento_repository import (
    InvestimentoRepository,
)
from tm_app.infrastructure.persistence.repositories.medicao_repository import MedicaoRepository
from tm_app.infrastructure.persistence.repositories.recurso_repository import VinculoRepository
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository


def copy_revisao_tree(
    *,
    revisoes: list[dict[str, Any]],
    processo_id: str,
    instancia_id: str,
    rev_repo: RevisaoRepository,
    med_repo: MedicaoRepository,
    inv_repo: InvestimentoRepository,
    vin_repo: VinculoRepository,
    auto_commit: bool = False,
) -> tuple[dict[str, int], dict[str, str]]:
    stats = {
        "revisoes": 0,
        "medicoes": 0,
        "investimentos": 0,
        "vinculos": 0,
    }
    revisao_id_map: dict[str, str] = {}

    for revisao in revisoes:
        old_rev_id = str(revisao["revisao_id"])
        new_revisao = rev_repo.create(
            {
                "processo_id": processo_id,
                "instancia_id": instancia_id,
                "versao_revisao": revisao["versao_revisao"],
                "cenario_tipo": revisao["cenario_tipo"],
                "data_inicio_vigencia": revisao["data_inicio_vigencia"],
                "data_implantacao": revisao.get("data_implantacao"),
                "data_fim_vigencia": revisao.get("data_fim_vigencia"),
                "revisao_ativa": bool(revisao.get("revisao_ativa")),
                "descricao_revisao": revisao.get("descricao_revisao"),
                "motivo_revisao": revisao.get("motivo_revisao"),
                "observacoes": revisao.get("observacoes"),
                "status_aprovacao": revisao.get("status_aprovacao") or "aprovada",
            },
            auto_commit=auto_commit,
        )
        new_rev_id = str(new_revisao["revisao_id"])
        revisao_id_map[old_rev_id] = new_rev_id
        stats["revisoes"] += 1

        medicao = med_repo.get_by_revisao(old_rev_id)
        if medicao:
            med_repo.create(
                {
                    "revisao_id": new_rev_id,
                    "volume_mensal": medicao.get("volume_mensal", 0),
                    "tempo_medio_execucao_min": medicao.get("tempo_medio_execucao_min", 0),
                    "tempo_retrabalho_min": medicao.get("tempo_retrabalho_min", 0),
                    "percentual_retrabalho": medicao.get("percentual_retrabalho", 0),
                    "percentual_erro": medicao.get("percentual_erro", 0),
                    "quantidade_erros_mes": medicao.get("quantidade_erros_mes", 0),
                    "custo_hora_mao_obra": medicao.get("custo_hora_mao_obra", 0),
                    "custo_unitario_erro": medicao.get("custo_unitario_erro", 0),
                    "custo_unitario_retrabalho": medicao.get(
                        "custo_unitario_retrabalho", 0
                    ),
                    "custo_outros_desperdicios": medicao.get("custo_outros_desperdicios", 0),
                    "base_referencia_mes": medicao.get("base_referencia_mes"),
                    "observacoes": medicao.get("observacoes"),
                },
                auto_commit=auto_commit,
            )
            stats["medicoes"] += 1

        for inv in inv_repo.list_by_revisao(old_rev_id):
            inv_repo.create(
                {
                    "revisao_id": new_rev_id,
                    "tipo_investimento": inv["tipo_investimento"],
                    "descricao_item": inv["descricao_item"],
                    "quantidade": inv.get("quantidade", 1),
                    "valor_unitario": inv.get("valor_unitario", 0),
                    "recorrencia": inv.get("recorrencia", "unico"),
                    "categoria_investimento": inv.get("categoria_investimento"),
                    "data_investimento": inv.get("data_investimento"),
                    "meses_vigencia": inv.get("meses_vigencia"),
                    "centro_custo": inv.get("centro_custo"),
                    "observacoes": inv.get("observacoes"),
                },
                auto_commit=auto_commit,
            )
            stats["investimentos"] += 1

        for vin in vin_repo.list_by_revisao(old_rev_id):
            vin_repo.create(
                {
                    "revisao_id": new_rev_id,
                    "recurso_compartilhado_id": str(vin["recurso_compartilhado_id"]),
                    "data_inicio_uso": vin.get("data_inicio_uso"),
                    "data_fim_uso": vin.get("data_fim_uso"),
                    "ativo": bool(vin.get("ativo", True)),
                    "peso_rateio": vin.get("peso_rateio"),
                    "observacoes": vin.get("observacoes"),
                },
                auto_commit=auto_commit,
            )
            stats["vinculos"] += 1

    return stats, revisao_id_map
