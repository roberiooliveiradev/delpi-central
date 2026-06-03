"""Correções do smoke SQL E2E — LLM, review/explain, capabilities, incremental."""

from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.domain.services.chat_advanced_sql_specialist_service import (
    ChatAdvancedSqlSpecialistService,
)
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)


def test_review_message_not_auto_execute():
    msg = "Revisa essa query:\n\nSELECT * FROM SA1010 a JOIN SC5010 p ON p.C5_CLIENTE = a.A1_COD"
    assert ChatSqlIntentService.is_authoring_request(msg)
    assert not ChatSqlIntentService.should_auto_execute_sql(msg)
    assert ChatSqlIntentService.router_sub_intent(msg) == "sql_review"


def test_explain_message_not_auto_execute():
    msg = "Explique essa query: SELECT A1_COD, A1_NOME FROM SA1010 WHERE D_E_L_E_T_ = ''"
    assert ChatSqlIntentService.is_authoring_request(msg)
    assert not ChatSqlIntentService.should_auto_execute_sql(msg)
    assert ChatSqlIntentService.router_sub_intent(msg) == "sql_explain"


def test_schema_relations_not_capability_inquiry():
    msg = "Como relacionar pedidos SC5 com clientes SA1? Valide no schema."
    assert not ChatCapabilitiesService.is_capability_inquiry(msg)
    assert not ChatCapabilitiesService._is_feature_capability_inquiry(msg)
    assert ChatSqlIntentService.is_sql_conversation_turn(msg)


def test_requires_llm_for_sql_authoring_modes():
    snapshot = {"mode": "create", "message": "monte select"}
    assert ChatAdvancedSqlSpecialistService.requires_llm_response(snapshot)

    rel = {"mode": "schema_explore", "message": "como relacionar sc5 e sa1"}
    assert ChatAdvancedSqlSpecialistService.requires_llm_response(rel)


def test_incremental_add_city_authoring():
    history = [
        {
            "role": "assistant",
            "content": "Segue a consulta:\n\n```sql\nSELECT A1_COD, A1_NOME FROM SA1\n```",
        }
    ]
    msg = "Adicione a coluna cidade na consulta anterior, sem executar."
    refinement = ChatSqlQueryRefinementService.resolve(msg, previous_messages=history)
    assert refinement is not None
    assert refinement.mode == "show_sql"
    assert "A1_MUN" in refinement.sql or "CIDADE" in refinement.sql
