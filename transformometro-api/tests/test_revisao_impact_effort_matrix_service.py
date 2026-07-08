from unittest.mock import patch

from tm_app.application.services.revisao_impact_effort_matrix_service import (
    RevisaoImpactEffortMatrixService,
    _percentile_rank,
    _resolve_quadrant,
)
from tm_app.domain.raw_data import TransformometroRawData


def _matrix_fixture() -> TransformometroRawData:
    return TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "codigo_processo": "PROC-0001",
                "nome_processo": "Processo teste",
                "status_processo": "ativo",
                "deletado": False,
            }
        ],
        processo_instancias=[
            {
                "instancia_id": "i1",
                "processo_id": "p1",
                "codigo_filial": "01",
                "codigo_setor": "engenharia",
                "deletado": False,
            }
        ],
        revisoes=[
            {
                "revisao_id": "r-baseline",
                "processo_id": "p1",
                "instancia_id": "i1",
                "versao_revisao": "1.0.0",
                "cenario_tipo": "baseline",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "r-quick",
                "processo_id": "p1",
                "instancia_id": "i1",
                "versao_revisao": "1.1.0",
                "cenario_tipo": "melhoria",
                "revisao_referencia_id": "r-baseline",
                "revisao_ativa": True,
                "deletado": False,
            },
            {
                "revisao_id": "r-strategic",
                "processo_id": "p1",
                "instancia_id": "i1",
                "versao_revisao": "2.0.0",
                "cenario_tipo": "automacao",
                "revisao_referencia_id": "r-baseline",
                "revisao_ativa": False,
                "deletado": False,
            },
            {
                "revisao_id": "r-rethink",
                "processo_id": "p1",
                "instancia_id": "i1",
                "versao_revisao": "2.1.0",
                "cenario_tipo": "correcao",
                "revisao_referencia_id": "r-baseline",
                "revisao_ativa": False,
                "deletado": False,
            },
        ],
        medicoes=[
            {
                "revisao_id": "r-baseline",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 60,
                "percentual_retrabalho": 0.2,
                "quantidade_erros_mes": 10,
                "custo_hora_mao_obra": 50,
                "deletado": False,
            },
            {
                "revisao_id": "r-quick",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 30,
                "percentual_retrabalho": 0.05,
                "quantidade_erros_mes": 2,
                "custo_hora_mao_obra": 50,
                "deletado": False,
            },
            {
                "revisao_id": "r-strategic",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 45,
                "percentual_retrabalho": 0.08,
                "quantidade_erros_mes": 4,
                "custo_hora_mao_obra": 50,
                "deletado": False,
            },
            {
                "revisao_id": "r-rethink",
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 55,
                "percentual_retrabalho": 0.18,
                "quantidade_erros_mes": 9,
                "custo_hora_mao_obra": 50,
                "deletado": False,
            },
        ],
        investimentos=[
            {
                "investimento_id": "inv1",
                "revisao_id": "r-quick",
                "tipo_investimento": "software",
                "valor_total": 5000,
                "deletado": False,
            },
            {
                "investimento_id": "inv2",
                "revisao_id": "r-strategic",
                "tipo_investimento": "software",
                "valor_total": 80000,
                "deletado": False,
            },
            {
                "investimento_id": "inv3",
                "revisao_id": "r-rethink",
                "tipo_investimento": "software",
                "valor_total": 60000,
                "deletado": False,
            },
        ],
        recursos_compartilhados=[],
        revisao_recursos_compartilhados=[],
        recurso_custos=[],
    )


def test_percentile_rank_single_value_is_midpoint():
    assert _percentile_rank([10.0], 10.0) == 50.0


def test_resolve_quadrant_quick_win():
    assert _resolve_quadrant(72, 41) == "quick_win"


@patch("tm_app.application.services.revisao_impact_effort_matrix_service.count_active_filiais", return_value=1)
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.DashboardDataRepository")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.RevisaoRepository")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.ProcessoInstanciaRepository")
def test_build_for_instancia_excludes_baseline_from_scatter(mock_inst, mock_rev, mock_data, _mock_filiais):
    raw = _matrix_fixture()
    mock_inst.return_value.get.return_value = raw.processo_instancias[0]
    mock_rev.return_value.list_by_instancia.return_value = raw.revisoes
    mock_rev.return_value.find_reference_for_revisao.side_effect = lambda rid, **_: next(
        (r for r in raw.revisoes if r["revisao_id"] == "r-baseline"),
        None,
    )
    mock_data.return_value.load_raw.return_value = raw

    result = RevisaoImpactEffortMatrixService().build_for_instancia("i1", competencia="2026-07")
    assert result is not None
    assert result["instancia_id"] == "i1"
    assert len(result["pontos"]) == 3

    comparaveis = [p for p in result["pontos"] if p["incluir_na_matriz"]]
    assert len(comparaveis) == 3
    assert all(p["quadrante"] in {"quick_win", "strategic", "fill_in", "rethink"} for p in comparaveis)
    assert result["ativo"]["revisao_id"] == "r-quick"


@patch("tm_app.application.services.revisao_impact_effort_matrix_service.count_active_filiais", return_value=1)
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.DashboardDataRepository")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.RevisaoRepository")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.ProcessoInstanciaRepository")
def test_build_for_revisao_returns_neighbors(mock_inst, mock_rev, mock_data, _mock_filiais):
    raw = _matrix_fixture()
    mock_inst.return_value.get.return_value = raw.processo_instancias[0]
    mock_rev.return_value.list_by_instancia.return_value = raw.revisoes
    mock_rev.return_value.get.return_value = next(r for r in raw.revisoes if r["revisao_id"] == "r-quick")
    mock_rev.return_value.find_reference_for_revisao.side_effect = lambda rid, **_: next(
        (r for r in raw.revisoes if r["revisao_id"] == "r-baseline"),
        None,
    )
    mock_data.return_value.load_raw.return_value = raw

    result = RevisaoImpactEffortMatrixService().build_for_revisao("r-quick", competencia="2026-07")
    assert result is not None
    assert result["ponto"]["revisao_id"] == "r-quick"
    assert "impacto" in result["ponto"]
    assert len(result["vizinhos"]) == 2


@patch("tm_app.application.services.revisao_impact_effort_matrix_service.RevisaoImpactEffortMatrixService.build_for_revisao")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.RevisaoRepository")
def test_save_for_revisao_persists_and_returns_matrix(mock_repo, mock_build):
    mock_repo.return_value.get.return_value = {
        "revisao_id": "r-quick",
        "instancia_id": "i1",
    }
    mock_repo.return_value.update_matriz_impacto_esforco.return_value = {"revisao_id": "r-quick"}
    mock_build.return_value = {
        "revisao_id": "r-quick",
        "ponto": {"modo": "hibrido", "impacto": 70.0, "esforco": 45.0},
        "inputs_persistidos": {"modo": "hibrido"},
    }

    result = RevisaoImpactEffortMatrixService().save_for_revisao(
        "r-quick",
        {
            "modo": "hibrido",
            "inputs_manuais": {"impacto_qualitativo": 4, "esforco_qualitativo": 3},
            "overrides": {"impacto": None, "esforco": None},
        },
        atualizado_por="ana@delpi.local",
    )

    assert result is not None
    assert result["ponto"]["modo"] == "hibrido"
    mock_repo.return_value.update_matriz_impacto_esforco.assert_called_once()
    persisted = mock_repo.return_value.update_matriz_impacto_esforco.call_args[0][1]
    assert persisted["modo"] == "hibrido"
    assert persisted["format"] == "revisao_matriz_impacto_esforco_v1"


@patch("tm_app.application.services.revisao_impact_effort_matrix_service.count_active_filiais", return_value=1)
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.DashboardDataRepository")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.RevisaoRepository")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.ProcessoInstanciaRepository")
def test_hibrido_modo_blends_manual_scores(mock_inst, mock_rev, mock_data, _mock_filiais):
    raw = _matrix_fixture()
    revisao_quick = next(r for r in raw.revisoes if r["revisao_id"] == "r-quick")
    revisao_quick["matriz_impacto_esforco"] = {
        "format": "revisao_matriz_impacto_esforco_v1",
        "format_version": 1,
        "modo": "hibrido",
        "inputs_manuais": {"impacto_qualitativo": 5, "esforco_qualitativo": 1},
        "overrides": {},
    }

    mock_inst.return_value.get.return_value = raw.processo_instancias[0]
    mock_rev.return_value.list_by_instancia.return_value = raw.revisoes
    mock_rev.return_value.find_reference_for_revisao.side_effect = lambda rid, **_: next(
        (r for r in raw.revisoes if r["revisao_id"] == "r-baseline"),
        None,
    )
    mock_data.return_value.load_raw.return_value = raw

    result = RevisaoImpactEffortMatrixService().build_for_instancia("i1", competencia="2026-07")
    quick = next(p for p in result["pontos"] if p["revisao_id"] == "r-quick")
    assert quick["modo"] == "hibrido"
    assert quick["impacto"] >= 50


@patch("tm_app.application.services.revisao_impact_effort_matrix_service.count_active_filiais", return_value=1)
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.DashboardDataRepository")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.RevisaoRepository")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.ProcessoInstanciaRepository")
@patch("tm_app.application.services.revisao_impact_effort_matrix_service.ProcessoRepository")
def test_build_for_processo_aggregates_melhorias(
    mock_processo,
    mock_inst,
    mock_rev,
    mock_data,
    _mock_filiais,
):
    raw = _matrix_fixture()
    instancia_2 = {
        **raw.processo_instancias[0],
        "instancia_id": "i2",
        "rotulo_instancia": "Piloto ES",
    }
    revisao_other = {
        **raw.revisoes[1],
        "revisao_id": "r-other",
        "instancia_id": "i2",
        "versao_revisao": "1.0.0",
        "revisao_referencia_id": "r-baseline-2",
        "revisao_ativa": True,
    }
    baseline_2 = {
        **raw.revisoes[0],
        "revisao_id": "r-baseline-2",
        "instancia_id": "i2",
        "versao_revisao": "1.0.0",
    }
    raw.processo_instancias.append(instancia_2)
    raw.revisoes.extend([baseline_2, revisao_other])
    raw.medicoes.extend(
        [
            {
                **raw.medicoes[0],
                "revisao_id": "r-baseline-2",
            },
            {
                **raw.medicoes[1],
                "revisao_id": "r-other",
            },
        ]
    )
    raw.investimentos.append(
        {
            **raw.investimentos[0],
            "investimento_id": "inv-other",
            "revisao_id": "r-other",
        }
    )

    mock_processo.return_value.get.return_value = raw.processos[0]
    mock_inst.return_value.list_by_processo.return_value = raw.processo_instancias

    def list_by_instancia(instancia_id: str):
        return [r for r in raw.revisoes if r["instancia_id"] == instancia_id]

    mock_rev.return_value.list_by_instancia.side_effect = list_by_instancia

    def find_reference(revisao_id: str, **_: object):
        revisao = next((r for r in raw.revisoes if r["revisao_id"] == revisao_id), None)
        if not revisao:
            return None
        ref_id = revisao.get("revisao_referencia_id")
        if ref_id:
            return next((r for r in raw.revisoes if r["revisao_id"] == ref_id), None)
        return next(
            (
                r
                for r in raw.revisoes
                if r["instancia_id"] == revisao.get("instancia_id") and r["cenario_tipo"] == "baseline"
            ),
            None,
        )

    mock_rev.return_value.find_reference_for_revisao.side_effect = find_reference
    mock_data.return_value.load_raw.return_value = raw

    result = RevisaoImpactEffortMatrixService().build_for_processo("p1", competencia="2026-07")
    assert result is not None
    assert result["processo_id"] == "p1"
    assert len(result["melhorias"]) == 2
    assert len(result["pontos"]) >= 2
    instancia_ids = {p["instancia_id"] for p in result["pontos"] if p.get("instancia_id")}
    assert instancia_ids == {"i1", "i2"}
