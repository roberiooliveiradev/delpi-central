from types import SimpleNamespace
from uuid import uuid4

from app.application.services.chat_knowledge_scope_service import ChatKnowledgeScopeService


def test_include_global_follows_company_knowledge_skill():
    session = SimpleNamespace(id=uuid4(), project_id=None)
    user_id = uuid4()

    filters_on = ChatKnowledgeScopeService().build_filters(
        user_id=user_id,
        session=session,
        workspace_context={"skills": {"companyKnowledge": True}},
        attachment_ids=None,
    )
    filters_off = ChatKnowledgeScopeService().build_filters(
        user_id=user_id,
        session=session,
        workspace_context={"skills": {"companyKnowledge": False}},
        attachment_ids=None,
    )

    assert filters_on["include_global"] is True
    assert filters_off["include_global"] is False
