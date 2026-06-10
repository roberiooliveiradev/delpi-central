from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)


def test_normalize_adds_summary_alert_and_next_action():
    commentary = {
        "profileKey": "factory_status",
        "highlights": ["Situação fabril: **PA PRODUZIDO**", "Expedição sem movimento."],
        "attention": ["Validar compra de MP exclusiva."],
        "narrativeInsight": "Situação fabril: **PA PRODUZIDO** Expedição sem movimento.",
    }

    normalized = ChatHumanizedDataResponseService.normalize(commentary, profile_key="factory_status")

    assert normalized
    assert normalized["summary"]
    assert normalized["alertLevel"] == "attention"
    assert normalized["nextAction"]
    assert normalized["facts"]
    assert normalized["recommendations"]
    assert normalized["readingLayer"]


def test_render_quick_layer_markdown_includes_summary_section():
    commentary = ChatHumanizedDataResponseService.normalize(
        {
            "profileKey": "stock",
            "highlights": ["Saldo disponível total: **150** un. em **2** posição(ões)."],
            "attention": [],
        },
        profile_key="stock",
    )

    rendered = ChatHumanizedDataResponseService.render_quick_layer_markdown(commentary)

    assert "<!-- section:summary -->" in rendered
    assert "Resumo" in rendered
    assert "Próxima ação" in rendered


def test_to_data_answer_and_commentary_mirror_round_trip():
    commentary = ChatHumanizedDataResponseService.normalize(
        {
            "profileKey": "stock",
            "highlights": ["Saldo disponível total: **150** un."],
            "attention": ["Conferir posição com disponível negativo."],
        },
        profile_key="stock",
    )

    data_answer = ChatHumanizedDataResponseService.to_data_answer(commentary)

    assert data_answer
    assert data_answer["summary"]["answer"]
    assert data_answer["summary"]["riskLevel"] in {"ok", "attention", "critical", "undefined"}
    assert data_answer["recommendations"][0]["query"]

    mirror = ChatHumanizedDataResponseService.to_commentary_mirror(data_answer)

    assert mirror
    assert mirror["summary"] == data_answer["summary"]["answer"]
    assert mirror["alertLevel"] in {"ok", "attention", "critical", "unknown"}
