from app.application.services.chat_turn.chat_turn_preparation_content_service import (
    ChatTurnPreparationContentService,
)
from app.application.services.chat_turn.chat_turn_preparation_direct_answer_service import (
    ChatTurnPreparationDirectAnswerService,
)


def test_stream_think_keys_exist():
    assert ChatTurnPreparationContentService.stream_think("ingressQuestion")
    assert ChatTurnPreparationContentService.stream_think("questionHistoryDone")
    assert ChatTurnPreparationContentService.stream_think_target("questionHistory")


def test_common_chat_operational_guidance_reads_turn_preparation_json():
    title = ChatTurnPreparationContentService.get(
        "directAnswers",
        "commonChatOperationalGuidance",
        "title",
    )

    assert "agente" in title.lower()


def test_interpretation_without_data_reads_turn_preparation_json():
    message = ChatTurnPreparationContentService.get(
        "directAnswers",
        "interpretationWithoutData",
    )

    assert "Ainda não há dados nesta conversa" in message
    assert "consulta operacional" in message


def test_production_operational_gap_messages_exist():
    missing = ChatTurnPreparationContentService.format(
        "directAnswers",
        "productionOperational",
        "actionMissingFromCatalog",
        pathLabel="/production/schedule/today",
        providerKey="api-delpi",
    )
    disabled = ChatTurnPreparationContentService.format(
        "directAnswers",
        "productionOperational",
        "actionNotEnabledOnAgent",
        pathLabel="/production/schedule/today",
        actionId="get_production_schedule_today",
    )

    assert "Atualizar rotas" in missing
    assert "habilitada" in disabled.lower()


def test_resolve_interpretation_without_data_when_no_tool_history():
    answer = ChatTurnPreparationDirectAnswerService.resolve_interpretation_without_data(
        message="explique os dados acima",
        history_source=[],
        canvas_action=None,
        pre_capability_answer=None,
        analysis_mode=False,
        text_task_pure=False,
    )

    assert answer is not None
    assert "Ainda não há dados nesta conversa" in answer


def test_resolve_interpretation_without_data_skips_when_text_task():
    answer = ChatTurnPreparationDirectAnswerService.resolve_interpretation_without_data(
        message="explique os dados acima",
        history_source=[],
        canvas_action=None,
        pre_capability_answer=None,
        analysis_mode=False,
        text_task_pure=True,
    )

    assert answer is None
