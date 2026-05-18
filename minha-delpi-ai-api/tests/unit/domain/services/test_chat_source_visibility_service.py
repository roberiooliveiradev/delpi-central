from app.domain.services.chat_source_visibility_service import (
    filter_client_visible_sources,
    should_hide_source_from_client,
)


def test_hide_global_scope():
    assert should_hide_source_from_client({"scope": "global", "title": "Política"}) is True


def test_show_agent_source():
    assert (
        should_hide_source_from_client(
            {
                "scope": "agent_source",
                "title": "Manual",
                "agentKey": "rh-agent",
            }
        )
        is False
    )


def test_hide_legacy_unscoped_corporate_source():
    assert (
        should_hide_source_from_client(
            {
                "title": "Base corporativa",
                "sourceType": "admin_upload",
            }
        )
        is True
    )


def test_filter_client_visible_sources():
    sources = [
        {"scope": "global", "title": "Global"},
        {"scope": "agent_source", "title": "Agente", "agentKey": "a1"},
    ]

    assert filter_client_visible_sources(sources) == [
        {"scope": "agent_source", "title": "Agente", "agentKey": "a1"},
    ]
