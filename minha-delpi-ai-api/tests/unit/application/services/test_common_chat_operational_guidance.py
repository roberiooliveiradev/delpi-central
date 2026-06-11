from app.application.services.chat_common_chat_operational_guidance_service import (
    ChatCommonChatOperationalGuidanceService,
)
from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
    ChatTurnPreparationToolRoutingService,
)


def test_requires_agent_for_lmp_list_in_common_chat():
    workspace = {"userActivatedAgent": False, "actionsEnabled": False}

    assert ChatCommonChatOperationalGuidanceService.requires_agent(
        "listar LMPs desse mês",
        workspace_context=workspace,
    )


def test_requires_agent_for_product_query_in_common_chat():
    workspace = {"userActivatedAgent": False, "actionsEnabled": False}

    assert ChatCommonChatOperationalGuidanceService.requires_agent(
        "me fale do produto 90260015",
        workspace_context=workspace,
    )


def test_skips_capability_inquiry_in_common_chat():
    workspace = {"userActivatedAgent": False, "actionsEnabled": False}

    assert not ChatCommonChatOperationalGuidanceService.requires_agent(
        "o que você pode fazer?",
        workspace_context=workspace,
    )


def test_build_direct_answer_mentions_agent_and_common_capabilities():
    answer = ChatCommonChatOperationalGuidanceService.build_direct_answer()

    assert "chat comum" in answer.lower()
    assert "agente" in answer.lower()
    assert "documentação" in answer.lower() or "conhecimento" in answer.lower()


def test_resolve_operational_guards_returns_guidance_for_lmp_list():
    guards = ChatTurnPreparationToolRoutingService.resolve_operational_guards(
        message="listar LMPs desse mês",
        history_source=[],
        conversation_context="",
        working_memory_snapshot={},
        workspace_context={"userActivatedAgent": False, "actionsEnabled": False},
        canvas_action=None,
        pre_capability_answer=None,
        analysis_mode=False,
        text_task_pure=False,
    )

    assert guards.common_chat_operational_answer
    assert "agente" in guards.common_chat_operational_answer.lower()


def test_requires_agent_for_production_schedule_in_common_chat():
    workspace = {"userActivatedAgent": False, "actionsEnabled": False}

    assert ChatCommonChatOperationalGuidanceService.requires_agent(
        "produtos programados para produzir hoje",
        workspace_context=workspace,
    )


def test_resolve_operational_guards_returns_guidance_in_common_chat():
    guards = ChatTurnPreparationToolRoutingService.resolve_operational_guards(
        message="estoque do produto 10080001",
        history_source=[],
        conversation_context="",
        working_memory_snapshot={},
        workspace_context={"userActivatedAgent": False, "actionsEnabled": False},
        canvas_action=None,
        pre_capability_answer=None,
        analysis_mode=False,
        text_task_pure=False,
    )

    assert guards.common_chat_operational_answer
    assert "agente" in guards.common_chat_operational_answer.lower()


def test_resolve_operational_guards_returns_guidance_for_production_schedule():
    guards = ChatTurnPreparationToolRoutingService.resolve_operational_guards(
        message="produtos programados para produzir hoje",
        history_source=[],
        conversation_context="",
        working_memory_snapshot={},
        workspace_context={"userActivatedAgent": False, "actionsEnabled": False},
        canvas_action=None,
        pre_capability_answer=None,
        analysis_mode=False,
        text_task_pure=False,
    )

    assert guards.common_chat_operational_answer
    assert "agente" in guards.common_chat_operational_answer.lower()
