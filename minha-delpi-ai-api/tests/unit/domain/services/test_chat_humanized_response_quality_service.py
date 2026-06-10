from app.domain.services.chat_humanized_response_quality_service import (
    ChatHumanizedResponseQualityService,
)


def test_evaluate_passes_complete_data_answer():
    metadata = {
        "dataAnswer": {
            "summary": {
                "answer": "Saldo confortável em duas filiais.",
                "meaning": "Não há bloqueio aparente.",
                "riskLevel": "ok",
            },
            "facts": [{"text": "Total disponível: 150"}],
            "analysis": [{"text": "Concentração moderada por filial."}],
            "attention": [],
            "limitations": ["Esta análise considera apenas os registros desta página."],
            "recommendations": [
                {
                    "label": "Ver concentração por filial",
                    "query": "Mostrar concentração de estoque por filial",
                }
            ],
        },
        "presentationDecision": {
            "purpose": "Evidenciar saldo por filial",
            "scores": {"table": 0.8, "text": 0.9},
        },
        "tablePresentations": [{"role": "list", "rows": [{"branch": "01"}]}],
    }

    result = ChatHumanizedResponseQualityService.evaluate(metadata)

    assert result["ok"] is True
    assert result["checklist"]["starts_with_conclusion"] is True
    assert result["checklist"]["visual_has_purpose"] is True


def test_evaluate_flags_missing_summary_and_purpose():
    metadata = {
        "dataAnswer": {
            "summary": {"answer": ""},
            "limitations": [],
            "recommendations": [{"label": "Ação", "query": ""}],
        },
        "presentationDecision": {"scores": {}},
        "chartPresentation": {"type": "chart"},
    }

    result = ChatHumanizedResponseQualityService.evaluate(metadata)

    assert result["ok"] is False
    assert "missing_summary_answer" in result["gaps"]
    assert "visual_without_purpose" in result["gaps"]
    assert "recommendations_missing_query" in result["gaps"]
