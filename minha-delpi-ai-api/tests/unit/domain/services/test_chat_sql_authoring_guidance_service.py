from unittest.mock import MagicMock

from app.domain.services.chat_sql_authoring_guidance_service import (
    ChatSqlAuthoringGuidanceService,
)


def test_detects_custom_sql_authoring_without_execute():
    assert ChatSqlAuthoringGuidanceService.is_custom_sql_authoring(
        "monte uma consulta de faturamento por cliente sem executar"
    )


def test_extract_domain_hint_from_authoring_message():
    hint = ChatSqlAuthoringGuidanceService.extract_domain_hint(
        "monte uma consulta de faturamento por cliente"
    )

    assert hint == "faturamento por cliente"


def test_should_prefetch_when_domain_hint_present():
    assert ChatSqlAuthoringGuidanceService.should_prefetch_schema(
        message="crie uma query de vendas por filial sem rodar",
        workspace_context={
            "skills": {"sqlAuthoring": True},
            "actionsEnabled": True,
            "allowedActionIds": ["system-search"],
        },
    )


def test_should_not_prefetch_without_agent_actions():
    assert not ChatSqlAuthoringGuidanceService.should_prefetch_schema(
        message="crie uma query de vendas por filial",
        workspace_context={"skills": {"sqlAuthoring": True}, "actionsEnabled": False},
    )


def test_plan_prefetch_table_search(monkeypatch):
    selection = MagicMock()
    selection.select_system_metadata.return_value = {
        "name": "execute_external_action",
        "arguments": {"actionId": "system-search"},
    }

    planned = ChatSqlAuthoringGuidanceService.plan_schema_prefetch(
        selection,
        message="monte uma consulta de faturamento por cliente",
        allowed_action_ids=["system-search"],
    )

    assert len(planned) == 1
    selection.select_system_metadata.assert_called_once()
    assert "qual a tabela de" in selection.select_system_metadata.call_args.args[0]


def test_extract_table_name_ignores_que_stopword():
    # "qual a tabela QUE guarda informações de produto?" → "que" é pronome,
    # não a tabela QUE. Não pode virar nome de tabela.
    assert (
        ChatSqlAuthoringGuidanceService.extract_table_name(
            "qual a tabela que guarda informações de produto?"
        )
        is None
    )


def test_extract_table_name_keeps_real_table_code():
    assert (
        ChatSqlAuthoringGuidanceService.extract_table_name("colunas da tabela SB1")
        == "SB1"
    )


def test_extract_table_names_empty_for_que_question():
    assert (
        ChatSqlAuthoringGuidanceService.extract_table_names(
            "qual a tabela que guarda informações de produto?"
        )
        == []
    )


def test_build_follow_up_suggestions_for_authoring():
    suggestions = ChatSqlAuthoringGuidanceService.build_follow_up_suggestions(
        message="monte uma query na tabela SB1",
        tool_calls=[],
    )

    labels = {item["label"] for item in suggestions}

    assert "Executar query" in labels
    assert any("SB1" in item["query"] for item in suggestions)
