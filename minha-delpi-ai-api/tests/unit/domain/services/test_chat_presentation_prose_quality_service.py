from app.domain.services.chat_presentation_prose_quality_service import (
    ChatPresentationProseQualityService,
)


def test_prose_quality_rejects_generic_row_count():
    metadata = {
        "dataAnswer": {
            "summary": {"answer": "Foram retornados 50 registros."},
        },
        "textPresentation": {
            "markdown": "### Lista\n\nForam retornados 50 registros.",
        },
    }

    result = ChatPresentationProseQualityService.evaluate(metadata)

    assert not result["ok"]
    assert "generic_row_count_without_intent" in result["gaps"]


def test_prose_quality_accepts_structured_production_markdown():
    metadata = {
        "dataAnswer": {
            "summary": {
                "answer": "**90260255** — PA **Sim**, PI **Não**.",
            },
        },
        "textPresentation": {
            "markdown": (
                "### Análise produtiva — 90260255\n\n"
                "**90260255** — CHICOTE\n\n"
                "**Situação na data 20260617**\n"
                "- Produção do PA: **Sim**\n"
                "- Produção de PI: **Não**"
            ),
        },
    }

    result = ChatPresentationProseQualityService.evaluate(
        metadata,
        user_message="Situação produtiva do 90260255 na data de hoje.",
    )

    assert result["ok"]


def test_prose_quality_expectations_helper():
    metadata = {
        "dataAnswer": {"summary": {"answer": "**Não** — nenhuma MP exclusiva."}},
        "textPresentation": {"markdown": "**Resposta:** Não"},
    }

    gaps = ChatPresentationProseQualityService.evaluate_expectations(
        metadata,
        forbidden=["Foram retornados"],
        required=["Não", "exclusiva"],
    )

    assert not gaps
