from app.domain.services.chat_source_visibility_service import (
    filter_client_visible_sources,
    should_hide_source_from_client,
)


def test_hide_global_scope():
    assert should_hide_source_from_client({"scope": "global", "title": "Política"}) is True


def test_hide_agent_source():
    assert (
        should_hide_source_from_client(
            {
                "scope": "agent_source",
                "title": "Manual",
                "agentKey": "rh-agent",
            }
        )
        is True
    )


def test_show_project_and_session_sources():
    assert (
        should_hide_source_from_client(
            {
                "scope": "project_source",
                "title": "Briefing",
                "projectId": "p1",
            }
        )
        is False
    )
    assert (
        should_hide_source_from_client(
            {
                "scope": "session_source",
                "title": "Anexo",
                "sessionId": "s1",
                "attachmentId": "a1",
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
        {"scope": "project_source", "title": "Projeto", "projectId": "p1"},
        {"scope": "session_source", "title": "Anexo", "sessionId": "s1"},
    ]

    assert filter_client_visible_sources(sources) == [
        {"scope": "project_source", "title": "Projeto", "projectId": "p1"},
        {"scope": "session_source", "title": "Anexo", "sessionId": "s1"},
    ]
