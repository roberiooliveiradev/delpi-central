"""Regressão #1508: mínimo de duas inspeções por operador, OP e operação."""

from __future__ import annotations

import pytest

from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_auditoria_apontamentos_use_case import (
    ListInspecoesProcessoAuditoriaApontamentosUseCase,
)
from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_auditoria_sql import (
    build_auditoria_inspecoes_operador_sql,
)
from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_repository import (
    _filter_auditoria_by_status,
    _index_auditoria_inspecoes_operador,
    _mark_auditoria_rows,
    _summarize_auditoria_rows,
)
from unittest.mock import MagicMock


def test_sql_counts_sessions_not_assays_and_filters_branch_and_ops() -> None:
    sql, params = build_auditoria_inspecoes_operador_sql(2, "02")
    assert params == ["02"]
    assert "vw_minha_delpi_inspecoes_processo_historico_tela" in sql
    assert "H.Filial = ?" in sql
    assert sql.count("H.Ordem_Producao LIKE ?") == 2
    assert "H.Data_Medicao_Date" in sql
    assert "H.Hora_Medicao" in sql
    assert "COUNT_BIG(*) AS Qtde_Inspecoes" in sql
    assert "GROUP BY S.Filial, S.Ordem_Producao, S.Operacao, S.Matricula_Ensaiador" in sql
    assert "QPR_RECNO" not in sql
    # Não restringir por DATA_PRODUCAO: mínimo é por OP/operação inteira.
    assert "DATA_PRODUCAO" not in sql.upper()


def test_sql_rejects_zero_ops() -> None:
    with pytest.raises(ValueError):
        build_auditoria_inspecoes_operador_sql(0)


def _audit_row(op: str, operation: str, branch: str = "02") -> dict:
    return {
        "Filial": branch,
        "Ordem_Producao": op,
        "Operacao": operation,
        "Login_Operador": "CARLA.JESUS",
        "Nome_Operador": "CARLA SOARES DE JESUS",
        "Cod_Operador": "000177",
    }


def test_counts_scope_and_matching_do_not_duplicate_assays() -> None:
    counts = _index_auditoria_inspecoes_operador([
        {"Filial": "02", "Ordem_Producao": "OP1", "Operacao": "01",
         "Matricula_Ensaiador": "20145", "Qtde_Inspecoes": 1},
        {"Filial": "02", "Ordem_Producao": "OP1", "Operacao": "02",
         "Matricula_Ensaiador": "20145", "Qtde_Inspecoes": 2},
        {"Filial": "01", "Ordem_Producao": "OP1", "Operacao": "01",
         "Matricula_Ensaiador": "20145", "Qtde_Inspecoes": 9},
        {"Filial": "02", "Ordem_Producao": "OP2", "Operacao": "01",
         "Matricula_Ensaiador": "20145", "Qtde_Inspecoes": 3},
        {"Filial": "02", "Ordem_Producao": "OP1", "Operacao": "01",
         "Matricula_Ensaiador": "99999", "Qtde_Inspecoes": 8},
    ])
    operators = {
        ("02", "20145"): {"login": "CARLA.JESUS", "nome": "CARLA SOARES DE JESUS"},
        ("02", "99999"): {"login": "OUTRO", "nome": "OUTRO OPERADOR"},
    }
    qpr = {
        ("02", "OP1", "01"): {"20145", "99999"},
        ("02", "OP1", "02"): {"20145"},
        ("02", "OP2", "01"): {"20145"},
    }
    rows = [_audit_row("OP1", "01"), _audit_row("OP1", "02"),
            _audit_row("OP2", "01"), _audit_row("OP1", "03")]
    result = _mark_auditoria_rows(
        rows,
        ensaiador_by_matricula=operators,
        qpr_by_op_oper=qpr,
        inspecoes_por_operador=counts,
        qpk_by_op={
            ("02", "OP1"): {"product": "P1", "revision": "00"},
            ("02", "OP2"): {"product": "P1", "revision": "00"},
        },
        specs_by_product_rev_oper={("P1", "00", "")},
    )
    assert [r["Qtde_Inspecoes_Operador"] for r in result] == [1, 2, 3, 0]
    assert [r["Operador_Inspecionou"] for r in result] == [1, 1, 1, 0]
    # O 0 e o 1 aparecem no mesmo filtro, já antes da paginação.
    assert [r["Operacao"] for r in _filter_auditoria_by_status(result, "abaixo_minimo")] == [
        "01", "03"
    ]
    assert [r["Operacao"] for r in _filter_auditoria_by_status(result, "minimo_atingido")] == [
        "02", "01"
    ]
    assert [r["Operacao"] for r in _filter_auditoria_by_status(result, "nao_inspecionou")] == [
        "03"
    ]
    summary = _summarize_auditoria_rows(result)
    assert summary["Apontamentos_Abaixo_Minimo"] == 2
    assert summary["Apontamentos_Minimo_Atingido"] == 2
    assert summary["Apontamentos_Com_Inspecao"] == 3
    assert summary["Apontamentos_Pendentes"] == 1


def test_without_registered_inspection_is_not_flagged_below_minimum() -> None:
    rows = _mark_auditoria_rows(
        [_audit_row("OP1", "01")],
        ensaiador_by_matricula={},
        qpr_by_op_oper={},
        inspecoes_por_operador={},
        qpk_by_op={},
        specs_by_product_rev_oper=set(),
    )
    assert rows[0]["Qtde_Inspecoes_Operador"] == 0
    assert _filter_auditoria_by_status(rows, "abaixo_minimo") == []


def test_api_accepts_below_minimum_filter_and_serializes_counts() -> None:
    repository = MagicMock()
    repository.list_auditoria_apontamentos_page.return_value = (
        {"Apontamentos_Abaixo_Minimo": 1, "Apontamentos_Minimo_Atingido": 0},
        [{**_audit_row("OP1", "01"), "Qtde_Inspecoes_Operador": 1}],
    )
    payload = ListInspecoesProcessoAuditoriaApontamentosUseCase(repository).execute(
        branch="02", data="2026-11-11", status="abaixo_minimo"
    ).to_dict()
    assert payload["items"][0]["qtd_inspecoes_operador"] == 1
    assert payload["summary"]["apontamentos_abaixo_minimo"] == 1
    repository.list_auditoria_apontamentos_page.assert_called_once()
    assert repository.list_auditoria_apontamentos_page.call_args.kwargs["status"] == "abaixo_minimo"
