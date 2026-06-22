from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_agent_knowledge_coverage_service import (
    ChatDrawingAgentKnowledgeCoverageService,
)

configure_domain_infrastructure_ports()


def test_ingest_sources_include_unit_conversion_tutorial():
    sources = ChatDrawingAgentKnowledgeCoverageService.ingest_sources()

    assert sources
    assert any(
        entry.source_file == "produto-conversao-unidades-protheus.txt" for entry in sources
    )
