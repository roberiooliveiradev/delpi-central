from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_user_query_improvement_service import (
    ChatUserQueryImprovementService,
)


def test_query_improvement_metadata_shape_for_admin():
    configure_domain_infrastructure_ports()
    ChatUserQueryImprovementService.configure(None)

    result = ChatUserQueryImprovementService.improve(
        "qual a descrião do 10050078?",
        response_mode="fast",
    )
    meta = result.as_metadata()

    assert meta["applied"] is True
    assert meta["original"]
    assert "10050078" in meta["messageForIntelligence"]
    assert meta["reason"] == "rules_only"
