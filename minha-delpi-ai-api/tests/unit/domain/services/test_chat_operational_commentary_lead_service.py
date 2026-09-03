from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_commentary_lead_service import (
    ChatOperationalCommentaryLeadService,
)

configure_domain_infrastructure_ports()


def _commentary() -> dict:
    return {
        "highlights": [
            {"text": "Destaque A"},
            {"text": "Destaque B"},
            {"text": "Destaque C"},
        ],
        "attention": ["Atenção 1", "Atenção 2", "Atenção 3", "Atenção 4"],
        "limitations": ["Limite 1", "Limite 2"],
        "nextAction": "Passo 1\nPasso 2\nPasso 3",
        "narrativeInsight": "Insight narrativo.",
    }


def test_brief_profile_limits_highlights_and_skips_attention():
    lead = ChatOperationalCommentaryLeadService.format_lead(
        _commentary(),
        depth="brief",
    )

    assert lead == "Destaque A"
    assert "Pontos de atenção" not in lead
    assert "Limitações" not in lead


def test_expanded_profile_includes_attention_limitations_without_next_steps_in_prose():
    """Próximos passos vivem nos chips de interatividade — não na prosa do lead."""
    lead = ChatOperationalCommentaryLeadService.format_lead(
        _commentary(),
        depth="expanded",
    )

    assert "Destaque A" in lead
    assert "Destaque C" in lead
    assert "Pontos de atenção" in lead
    assert "Atenção 4" in lead
    assert "Limitações" in lead
    assert "Insight narrativo." in lead
    assert "Próximos passos" not in lead
    assert "Passo 3" not in lead


def test_standard_profile_skips_next_steps_in_prose():
    lead = ChatOperationalCommentaryLeadService.format_lead(
        _commentary(),
        depth="standard",
    )

    assert "Destaque A" in lead
    assert "Próximos passos" not in lead
