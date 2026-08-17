"""Helpers de agregação/marcação da auditoria apontamento × inspeção."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_repository import (
    _aggregate_auditoria_apontamentos,
    _auditoria_sort_bucket,
    _auditoria_status_key,
    _filter_auditoria_by_status,
    _index_ensaiador_map,
    _index_inspecao_cadastrada_rows,
    _index_qpk_rows,
    _index_qpr_rows,
    _mark_auditoria_rows,
    _summarize_auditoria_rows,
    _tem_inspecao_cadastrada,
)


def _apontamento_row(**overrides: object) -> dict:
    base = {
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
    }
    return {**base, **overrides}


def test_mark_auditoria_same_operator_by_login() -> None:
    aggregated = _aggregate_auditoria_apontamentos(
        [
            _apontamento_row(),
            _apontamento_row(Hora_Inicio="100000", Hora_Final="110000"),
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
    qpk = _index_qpk_rows(
        [
            {
                "Ordem_Producao": "10543901002",
                "Codigo_Produto": "P1",
                "Revisao": "03",
            }
        ]
    )
    marked = _mark_auditoria_rows(
        aggregated,
        ensaiador_by_matricula=ensaiador,
        qpr_by_op_oper=qpr_other,
        qpk_by_op=qpk,
        specs_by_product_rev_oper={("P1", "03", "01")},
    )
    assert marked[0]["Operador_Inspecionou"] == 0
    assert marked[0]["Tem_Inspecao_Na_Op_Operacao"] == 1
    assert marked[0]["Tem_Inspecao_Amarrada"] == 1

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
        qpk_by_op=qpk,
        specs_by_product_rev_oper={("P1", "03", "01")},
    )
    assert marked_ok[0]["Operador_Inspecionou"] == 1
    summary = _summarize_auditoria_rows(marked_ok)
    assert summary["Apontamentos_Total"] == 1
    assert summary["Apontamentos_Pendentes"] == 0
    assert summary["Apontamentos_Com_Inspecao"] == 1


def test_mark_auditoria_usa_revisao_do_qpk_nao_a_mais_nova() -> None:
    """Regressão Marinete: QP7 na rev nova tem op 02, mas QPK da OP está na rev 00."""
    aggregated = _aggregate_auditoria_apontamentos(
        [
            _apontamento_row(
                Ordem_Producao="10627201002",
                Codigo_Produto="50212720",
                Operacao="02",
                Nome_Operador="MARINETE O. SANTOS",
                Login_Operador="MARINETE.SANTOS",
            )
        ]
    )
    qpk = _index_qpk_rows(
        [
            {
                "Ordem_Producao": "10627201002",
                "Codigo_Produto": "50212720",
                "Revisao": "00",
            }
        ]
    )
    # Rev 03 (mais nova) tem op 02; rev 00 da OP só tem op 01.
    specs = {("50212720", "03", "01"), ("50212720", "03", "02"), ("50212720", "00", "01")}
    marked = _mark_auditoria_rows(
        aggregated,
        ensaiador_by_matricula={},
        qpr_by_op_oper={},
        qpk_by_op=qpk,
        specs_by_product_rev_oper=specs,
    )
    assert marked[0]["Tem_Inspecao_Amarrada"] == 0
    summary = _summarize_auditoria_rows(marked)
    assert summary["Apontamentos_Pendentes"] == 0
    assert _auditoria_sort_bucket(marked[0]) == 1


def test_mark_auditoria_sem_qpk_nao_conta_pendencia() -> None:
    aggregated = _aggregate_auditoria_apontamentos(
        [_apontamento_row(Ordem_Producao="10627201002", Operacao="02")]
    )
    marked = _mark_auditoria_rows(
        aggregated,
        ensaiador_by_matricula={},
        qpr_by_op_oper={},
        qpk_by_op={},
        specs_by_product_rev_oper={("P1", "03", "02")},
    )
    assert marked[0]["Tem_Inspecao_Amarrada"] == 0
    assert _summarize_auditoria_rows(marked)["Apontamentos_Pendentes"] == 0


def test_mark_auditoria_com_cadastro_na_revisao_da_op_e_pendente() -> None:
    aggregated = _aggregate_auditoria_apontamentos([_apontamento_row()])
    marked = _mark_auditoria_rows(
        aggregated,
        ensaiador_by_matricula={},
        qpr_by_op_oper={},
        qpk_by_op={
            "10543901002": {"product": "P1", "revision": "03"},
        },
        specs_by_product_rev_oper={("P1", "03", "01")},
    )
    assert marked[0]["Tem_Inspecao_Amarrada"] == 1
    summary = _summarize_auditoria_rows(marked)
    assert summary["Apontamentos_Pendentes"] == 1
    assert _auditoria_sort_bucket(marked[0]) == 0


def test_tem_inspecao_cadastrada_aceita_operacao_vazia_na_revisao() -> None:
    specs = _index_inspecao_cadastrada_rows(
        [{"Codigo_Produto": "P1", "Revisao": "01", "Operacao": ""}]
    )
    assert (
        _tem_inspecao_cadastrada(
            specs, product="P1", revision="01", operacao="02"
        )
        is True
    )
    assert (
        _tem_inspecao_cadastrada(
            specs, product="P1", revision="02", operacao="02"
        )
        is False
    )


def test_filter_auditoria_by_status_keeps_only_matching_rows() -> None:
    rows = [
        {
            "Operador_Inspecionou": 1,
            "Tem_Inspecao_Amarrada": 1,
            "Tem_Inspecao_Na_Op_Operacao": 1,
        },
        {
            "Operador_Inspecionou": 0,
            "Tem_Inspecao_Amarrada": 1,
            "Tem_Inspecao_Na_Op_Operacao": 0,
        },
        {
            "Operador_Inspecionou": 0,
            "Tem_Inspecao_Amarrada": 0,
            "Tem_Inspecao_Na_Op_Operacao": 0,
        },
    ]
    assert _auditoria_status_key(rows[0]) == "inspecionou"
    assert _auditoria_status_key(rows[1]) == "nao_inspecionou"
    assert _auditoria_status_key(rows[2]) == "sem_cadastro"

    filtered = _filter_auditoria_by_status(rows, "nao_inspecionou")
    assert len(filtered) == 1
    assert filtered[0] is rows[1]
    assert _filter_auditoria_by_status(rows, "all") == rows
    assert _filter_auditoria_by_status(rows, None) == rows


def test_filter_auditoria_by_status_keeps_matching_keys() -> None:
    rows = [
        {
            "Operador_Inspecionou": 1,
            "Tem_Inspecao_Amarrada": 1,
            "Tem_Inspecao_Na_Op_Operacao": 1,
        },
        {
            "Operador_Inspecionou": 0,
            "Tem_Inspecao_Amarrada": 1,
            "Tem_Inspecao_Na_Op_Operacao": 0,
        },
        {
            "Operador_Inspecionou": 0,
            "Tem_Inspecao_Amarrada": 0,
            "Tem_Inspecao_Na_Op_Operacao": 0,
        },
    ]
    assert [_auditoria_status_key(row) for row in rows] == [
        "inspecionou",
        "nao_inspecionou",
        "sem_cadastro",
    ]
    assert len(_filter_auditoria_by_status(rows, "all")) == 3
    assert len(_filter_auditoria_by_status(rows, "nao_inspecionou")) == 1
    assert len(_filter_auditoria_by_status(rows, "inspecionou")) == 1
    assert len(_filter_auditoria_by_status(rows, "sem_cadastro")) == 1
    assert _filter_auditoria_by_status(rows, "nao_inspecionou")[0] is rows[1]
