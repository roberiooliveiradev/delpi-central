"""Helpers de agregação/marcação da auditoria apontamento × inspeção."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_repository import (
    _aggregate_auditoria_apontamentos,
    _index_ensaiador_map,
    _index_qpr_rows,
    _mark_auditoria_rows,
    _summarize_auditoria_rows,
)


def test_mark_auditoria_same_operator_by_login() -> None:
    aggregated = _aggregate_auditoria_apontamentos(
        [
            {
                "Filial": "02",
                "Cod_Operador": "000177",
                "Login_Operador": "CARLA.JESUS",
                "Nome_Operador": "CARLA SOARES DE JESUS",
                "Ordem_Producao": "10543901002",
                "Codigo_Produto": "P1",
                "Descricao_Produto": "Prod",
                "Operacao": "01",
                "Centro_Trabalho": "CT-01",
                "Data_Producao": "2026-07-13",
                "Hora_Inicio": "080000",
                "Hora_Final": "090000",
            },
            {
                "Filial": "02",
                "Cod_Operador": "000177",
                "Login_Operador": "CARLA.JESUS",
                "Nome_Operador": "CARLA SOARES DE JESUS",
                "Ordem_Producao": "10543901002",
                "Codigo_Produto": "P1",
                "Descricao_Produto": "Prod",
                "Operacao": "01",
                "Centro_Trabalho": "CT-01",
                "Data_Producao": "2026-07-13",
                "Hora_Inicio": "100000",
                "Hora_Final": "110000",
            },
        ]
    )
    assert len(aggregated) == 1
    assert aggregated[0]["Qtde_Apontamentos"] == 2

    ensaiador = _index_ensaiador_map(
        [
            {
                "Matricula_Ensaiador": "20115",
                "Login_Ensaiador": "ANDIA.GONCALVES",
                "Nome_Ensaiador": "ANDIA GOMES GONCALVES",
            },
            {
                "Matricula_Ensaiador": "20145",
                "Login_Ensaiador": "CARLA.JESUS",
                "Nome_Ensaiador": "CARLA SOARES DE JESUS",
            },
        ]
    )
    qpr_other = _index_qpr_rows(
        [
            {
                "Ordem_Producao": "10543901002",
                "Operacao": "01",
                "Matricula_Ensaiador": "20115",
            }
        ]
    )
    marked = _mark_auditoria_rows(
        aggregated,
        ensaiador_by_matricula=ensaiador,
        qpr_by_op_oper=qpr_other,
    )
    assert marked[0]["Operador_Inspecionou"] == 0
    assert marked[0]["Tem_Inspecao_Na_Op_Operacao"] == 1

    qpr_same = _index_qpr_rows(
        [
            {
                "Ordem_Producao": "10543901002",
                "Operacao": "01",
                "Matricula_Ensaiador": "20145",
            }
        ]
    )
    marked_ok = _mark_auditoria_rows(
        aggregated,
        ensaiador_by_matricula=ensaiador,
        qpr_by_op_oper=qpr_same,
    )
    assert marked_ok[0]["Operador_Inspecionou"] == 1
    summary = _summarize_auditoria_rows(marked_ok)
    assert summary["Apontamentos_Total"] == 1
    assert summary["Apontamentos_Pendentes"] == 0
    assert summary["Apontamentos_Com_Inspecao"] == 1
