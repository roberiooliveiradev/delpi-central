from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.application.services.chat_knowledge_scope_service import ChatKnowledgeScopeService
from app.domain.services.chat_project_sources_intent_service import (
    ChatProjectSourcesIntentService,
)
from tests.fixtures.chat_intelligence_regression_cases import PROJECT_SOURCES_INTENT_CASES


@pytest.mark.parametrize(
    "message,expect_inventory,expect_restrict",
    PROJECT_SOURCES_INTENT_CASES,
)
def test_project_sources_intent_regression(message, expect_inventory, expect_restrict):
    assert (
        ChatProjectSourcesIntentService.is_inventory_question(message)
        is expect_inventory
    )
    assert (
        ChatProjectSourcesIntentService.should_restrict_to_project_sources(message)
        is expect_restrict
    )


def test_is_inventory_question_detects_project_sources_prompt():
    assert ChatProjectSourcesIntentService.is_inventory_question(
        "o que tem nas suas fontes?"
    )


def test_should_restrict_to_project_sources_for_scoped_phrases():
    assert ChatProjectSourcesIntentService.should_restrict_to_project_sources(
        "resuma suas fontes"
    )


def test_build_filters_disable_global_for_project_sources_question():
    session = SimpleNamespace(id=uuid4(), project_id=uuid4())
    user_id = uuid4()
    project_id = str(session.project_id)

    filters = ChatKnowledgeScopeService().build_filters(
        user_id=user_id,
        session=session,
        workspace_context={
            "project": {"id": project_id},
            "skills": {"companyKnowledge": True},
        },
        attachment_ids=None,
        message="o que tem nas suas fontes?",
    )

    assert filters["include_global"] is False
    assert filters["project_id"] == project_id
    assert filters["scope_priority"] == "project_source"


def test_is_content_question_detects_named_project_file():
    message = "o que esta escrito em 1o TREINAMENTO — FEVEREIRO 2026.docx?"

    assert ChatProjectSourcesIntentService.is_content_question(message)
    assert ChatProjectSourcesIntentService.should_restrict_to_project_sources(message)


def test_content_chunk_filter_keeps_matching_project_source_only():
    message = "o que esta escrito em 1o TREINAMENTO — FEVEREIRO 2026.docx?"
    chunk_filter = ChatProjectSourcesIntentService.build_content_chunk_filter(message)

    assert chunk_filter is not None

    training_chunk = {
        "title": "1º TREINAMENTO — FEVEREIRO 2026.docx",
        "sourceType": "project_source",
        "metadata": {"scope": "project_source"},
    }
    global_chunk = {
        "title": "O_ARQUITETO_DO_CODIGO.md",
        "sourceType": "global",
        "metadata": {"scope": "global"},
    }
    other_project_chunk = {
        "title": "CADASTRAR NA MINHA DELPI.xlsx",
        "sourceType": "project_source",
        "metadata": {"scope": "project_source"},
    }

    assert chunk_filter(training_chunk) is True
    assert chunk_filter(global_chunk) is False
    assert chunk_filter(other_project_chunk) is False


def test_build_filters_disable_global_for_project_source_content_question():
    session = SimpleNamespace(id=uuid4(), project_id=uuid4())
    user_id = uuid4()

    filters = ChatKnowledgeScopeService().build_filters(
        user_id=user_id,
        session=session,
        workspace_context={
            "project": {"id": str(session.project_id)},
            "skills": {"companyKnowledge": True},
        },
        attachment_ids=None,
        message="o que esta escrito em treinamento.docx?",
    )

    assert filters["include_global"] is False


def test_build_filters_keep_global_for_unrelated_question():
    session = SimpleNamespace(id=uuid4(), project_id=uuid4())
    user_id = uuid4()

    filters = ChatKnowledgeScopeService().build_filters(
        user_id=user_id,
        session=session,
        workspace_context={
            "project": {"id": str(session.project_id)},
            "skills": {"companyKnowledge": True},
        },
        attachment_ids=None,
        message="qual o estoque do produto 10080001?",
    )

    assert filters["include_global"] is True
    assert filters["scope_priority"] == "project_source"
