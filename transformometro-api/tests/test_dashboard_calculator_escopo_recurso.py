from __future__ import annotations

from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService


def _shared_resource_raw(*, escopo_recurso: str = "empresa") -> TransformometroRawData:
    return TransformometroRawData(
        processos=[
            {"processo_id": "p1", "codigo_processo": "P1", "nome_processo": "A", "status_processo": "ativo"},
            {"processo_id": "p2", "codigo_processo": "P2", "nome_processo": "B", "status_processo": "ativo"},
        ],
        processo_instancias=[
            {
                "instancia_id": "i1",
                "processo_id": "p1",
                "filial_id": "f1",
                "setor_id": "s1",
                "codigo_filial": "01",
                "codigo_setor": "engenharia",
            },
            {
                "instancia_id": "i2",
                "processo_id": "p2",
                "filial_id": "f2",
                "setor_id": "s2",
                "codigo_filial": "02",
                "codigo_setor": "engenharia",
            },
        ],
        revisoes=[
            {
                "revisao_id": "r1",
                "processo_id": "p1",
                "instancia_id": "i1",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": True,
            },
            {
                "revisao_id": "r2",
                "processo_id": "p2",
                "instancia_id": "i2",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": True,
            },
        ],
        medicoes=[
            {
                "revisao_id": "r1",
                "volume_mensal": 1,
                "tempo_medio_execucao_min": 10,
                "custo_hora_mao_obra": 0,
            },
            {
                "revisao_id": "r2",
                "volume_mensal": 1,
                "tempo_medio_execucao_min": 10,
                "custo_hora_mao_obra": 0,
            },
        ],
        investimentos=[],
        recursos_compartilhados=[
            {
                "recurso_compartilhado_id": "rc1",
                "nome_recurso": "Licença",
                "tipo_custo": "fixo",
                "recorrencia": "mensal",
                "criterio_rateio": "igualitario",
                "escopo_recurso": escopo_recurso,
                "base_competencia": "mensal_cheio",
                "status_recurso": "ativo",
                "valor_total_recorrente": 1000,
                "data_inicio_vigencia": "2025-01-01",
            }
        ],
        revisao_recursos_compartilhados=[
            {
                "vinculo_id": "v1",
                "revisao_id": "r1",
                "recurso_compartilhado_id": "rc1",
                "data_inicio_uso": "2025-01-01",
                "ativo": True,
            },
            {
                "vinculo_id": "v2",
                "revisao_id": "r2",
                "recurso_compartilhado_id": "rc1",
                "data_inicio_uso": "2025-01-01",
                "ativo": True,
            },
        ],
        recurso_custos=[],
    )


def _shared_cost(raw: TransformometroRawData, revisao_id: str) -> float:
    row = next(
        item
        for item in DashboardCalculatorService().build_dashboard_rows(raw)
        if item["revisao_id"] == revisao_id and item["competencia"] == "2025-01"
    )
    return float(row["custo_recursos_compartilhados_mes"])


def test_escopo_empresa_splits_cost_between_filiais():
    raw = _shared_resource_raw(escopo_recurso="empresa")
    assert _shared_cost(raw, "r1") == 500.0
    assert _shared_cost(raw, "r2") == 500.0


def test_escopo_filial_charges_full_pool_locally():
    raw = _shared_resource_raw(escopo_recurso="filial")
    assert _shared_cost(raw, "r1") == 1000.0
    assert _shared_cost(raw, "r2") == 1000.0
