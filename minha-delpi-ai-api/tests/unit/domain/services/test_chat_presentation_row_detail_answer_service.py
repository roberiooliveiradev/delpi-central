from app.domain.services.chat_presentation_row_detail_answer_service import (
    ChatPresentationRowDetailAnswerService,
)


def _production_history(*, rows, title="Produtos programados para produção hoje"):
    return [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/data/sql",
                            "presentation": {
                                "type": "table",
                                "title": title,
                                "columns": [
                                    {"key": "COD_PRODUTO", "label": "Cod Produto"},
                                    {"key": "DESCRICAO_PRODUTO", "label": "Descricao Produto"},
                                    {"key": "QTD_PLANEJADA", "label": "Qtd Planejada"},
                                    {"key": "UNIDADE", "label": "U N I D A D E"},
                                    {
                                        "key": "DATA_INICIO_OPERACAO",
                                        "label": "Data Inicio Operacao",
                                    },
                                ],
                                "rows": rows,
                            },
                        },
                    }
                ]
            },
        }
    ]


def test_build_row_detail_from_table_presentation():
    rows = [
        {
            "COD_PRODUTO": "90260260",
            "DESCRICAO_PRODUTO": "CHICOTE DE LIGACAO",
            "QTD_PLANEJADA": 0.002,
            "UNIDADE": "MI",
            "DATA_INICIO_OPERACAO": "20260610",
        }
    ]
    history = _production_history(rows=rows)
    message = (
        "detalhe este registro do último resultado — Cod Produto: 90260260; "
        "Descricao Produto: CHICOTE DE LIGACAO; Qtd Planejada: 0.002; "
        "U N I D A D E: MI; Data Inicio Operacao: 20260610"
    )

    answer = ChatPresentationRowDetailAnswerService.build_answer(message, history)

    assert answer
    assert "Assunto:" not in answer
    assert "Prezados" not in answer
    assert "90260260" in answer
    assert "CHICOTE DE LIGACAO" in answer
    assert "10/06/2026" in answer
    assert "Registro 1 de 1" in answer


def test_row_detail_matches_product_code_when_quantity_display_differs():
    rows = [
        {
            "COD_PRODUTO": "90260260",
            "DESCRICAO_PRODUTO": "CHICOTE DE LIGACAO",
            "QTD_PLANEJADA": 0,
            "UNIDADE": "MI",
            "DATA_INICIO_OPERACAO": "20260610",
        }
    ]
    history = _production_history(rows=rows)
    message = (
        "detalhe este registro do último resultado — Cod Produto: 90260260; "
        "Descricao Produto: CHICOTE DE LIGACAO"
    )

    answer = ChatPresentationRowDetailAnswerService.build_answer(message, history)

    assert answer
    assert "90260260" in answer
    assert "CHICOTE DE LIGACAO" in answer


def test_data_interpretation_no_longer_returns_email_for_row_detail():
    from app.application.services.chat_data_interpretation_answer_service import (
        ChatDataInterpretationAnswerService,
    )

    rows = [
        {
            "COD_PRODUTO": "90260260",
            "DESCRICAO_PRODUTO": "CHICOTE DE LIGACAO",
            "QTD_PLANEJADA": 0.002,
            "UNIDADE": "MI",
            "DATA_INICIO_OPERACAO": "20260610",
        }
    ]
    history = _production_history(rows=rows)
    history[0]["metadata"]["toolCalls"][0]["metadata"]["humanizedSummary"] = {
        "titulo": "Produtos programados para produção hoje",
        "linhas": [
            "Há 105 linha(s) nesta resposta.",
            "99 código(s) de produto distinto(s).",
        ],
    }
    message = (
        "detalhe este registro do último resultado — Cod Produto: 90260260; "
        "Descricao Produto: CHICOTE DE LIGACAO"
    )

    answer = ChatDataInterpretationAnswerService.build_answer(message, history)

    assert answer
    assert "Assunto:" not in answer
    assert "90260260" in answer
