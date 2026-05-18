from app.application.services.agent_specialization_service import AgentSpecializationService


def test_build_rag_filters_applies_domain_and_categories():
    service = AgentSpecializationService()

    filters = service.build_rag_filters(
        {
            "enabled": True,
            "domain": "recursos-humanos",
            "knowledgeCategories": ["rh"],
            "includeGlobalKnowledge": True,
        },
        {"include_global": True, "agent_key": "rh-agent"},
    )

    assert filters["include_global"] is True
    assert filters["curatorial"]["domains"] == ["recursos-humanos"]
    assert filters["curatorial"]["categories"] == ["rh"]


def test_normalize_payload_from_preset():
    service = AgentSpecializationService()

    payload = service.normalize_payload({"presetKey": "ti", "enabled": True})

    assert payload["presetKey"] == "ti"
    assert payload["domain"] == "ti"
    assert "get_allowed_apps" in payload["allowedTools"]
