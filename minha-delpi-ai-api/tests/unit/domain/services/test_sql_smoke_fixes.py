"""Correções do smoke SQL E2E — LLM, review/explain, capabilities, incremental."""

from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
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


def test_explain_sql_query_not_pure_text_task():
    msg = "Explique essa query: SELECT A1_COD, A1_NOME FROM SA1010 WHERE D_E_L_E_T_ = ''"
    assert ChatSqlIntentService.is_sql_conversation_turn(msg)
    assert not ChatTextTaskIntentService.is_pure_text_task(msg)


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


def test_schema_prefetch_annotates_table_search_on_sql_authoring():
    msg = (
        "use sql para construir uma query que liste 5 produtos "
        "na tabela de produtos, grupo 1008"
    )
    meta = ChatAdvancedSqlSpecialistService.annotate_schema_prefetch_tool_metadata(
        msg,
        {
            "path": "/system/tables/search",
            "ok": True,
            "presentation": {"type": "table", "title": "Resultado da consulta"},
        },
    )

    assert meta.get("sqlSchemaPrefetch") is True
    assert meta.get("suppressClientPresentation") is True
    assert "presentation" not in meta


def test_table_search_not_internal_for_metadata_question():
    meta = ChatAdvancedSqlSpecialistService.annotate_schema_prefetch_tool_metadata(
        "qual a tabela de produtos?",
        {"path": "/system/tables/search", "ok": True},
    )

    assert not meta.get("sqlSchemaPrefetch")


def test_turn_has_only_sql_schema_prefetch_detects_authoring_prefetch():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "statusCode": 200,
                "path": "/system/tables/search",
                "sqlSchemaPrefetch": True,
            },
        }
    ]

    assert ChatAdvancedSqlSpecialistService.turn_has_only_sql_schema_prefetch(tool_calls)


def test_compact_table_search_prefetch_context_lists_candidates():
    humanized = ChatAdvancedSqlSpecialistService.compact_schema_prefetch_context(
        message="use sql para listar produtos",
        data={
            "data": {
                "results": [
                    {"X2_ARQUIVO": "SB1010", "X2_NOME": "Cadastro de Produtos", "X2_CHAVE": "SB1"},
                ]
            }
        },
        metadata={"path": "/system/tables/search"},
    )

    joined = " ".join(str(line) for line in humanized.get("linhas") or [])
    assert "SB1010" in joined
    assert "Cadastro de Produtos" in joined


def test_schema_prefetch_annotates_metadata():
    from app.domain.services.chat_advanced_sql_specialist_service import (
        ChatAdvancedSqlSpecialistService,
    )

    meta = ChatAdvancedSqlSpecialistService.annotate_schema_prefetch_tool_metadata(
        "Monte uma consulta para listar clientes ativos da tabela SA1, sem executar.",
        {"path": "/system/tables/SA1/columns", "ok": True},
    )

    assert meta.get("sqlSchemaPrefetch") is True
    assert meta.get("suppressClientPresentation") is True


def test_schema_relations_prefetch_internal():
    msg = "Como relacionar pedidos SC5 com clientes SA1? Valide no schema."
    meta = ChatAdvancedSqlSpecialistService.annotate_schema_prefetch_tool_metadata(
        msg,
        {"path": "/system/tables/sc5/columns", "ok": True},
    )
    assert meta.get("sqlSchemaPrefetch") is True


def test_strip_schema_presentation_by_prefetch_path():
    result = ChatAdvancedSqlSpecialistService.strip_schema_catalog_presentations(
        {
            "toolCalls": [
                {
                    "metadata": {
                        "path": "/system/tables/sc5/columns",
                        "presentation": {"type": "table", "title": "Colunas"},
                    }
                }
            ]
        }
    )
    assert "presentation" not in result["toolCalls"][0]["metadata"]


def test_strip_schema_prefetch_hides_coverage_and_catalog():
    result = ChatAdvancedSqlSpecialistService.strip_schema_catalog_presentations(
        {
            "toolCalls": [
                {
                    "metadata": {
                        "path": "/system/tables/SA1/columns",
                        "sqlSchemaPrefetch": True,
                        "dataCoverageNotice": {"message": "Parcial · 25 de 265"},
                        "presentation": {"type": "table", "title": "Colunas"},
                        "dataCommentary": {"summary": "Foram retornados **50** registros."},
                        "dataAnswer": {"summary": {"answer": "Foram retornados **50** registros."}},
                        "humanizedSummary": {"titulo": "Colunas da tabela SA1", "linhas": []},
                    }
                }
            ]
        }
    )

    meta = result["toolCalls"][0]["metadata"]
    assert "dataCoverageNotice" not in meta
    assert "presentation" not in meta
    assert "dataCommentary" not in meta
    assert "dataAnswer" not in meta
    assert meta["humanizedSummary"]["titulo"] == "Schema interno (uso interno)"


def test_format_sql_authoring_answer_adds_intro_and_dedupes():
    raw = "```sql\nSELECT A1_COD FROM SA1\n```\n\n```sql\nSELECT A1_COD FROM SA1\n```"
    formatted = ChatAdvancedSqlSpecialistService.format_sql_authoring_answer(raw)

    assert "Segue a consulta em SQL" in formatted
    assert formatted.lower().count("```sql") == 1


def test_format_sql_authoring_answer_strips_redundant_tail_prose():
    before = (
        "Com base nas informações fornecidas, a tabela SA1 no Protheus usa sufixo de filial. "
        "Campos típicos: A1_COD e A1_NOME."
    )
    raw = (
        f"{before}\n\n```sql\nSELECT A1_COD, A1_NOME FROM SA1010\n```\n\n{before}"
    )
    formatted = ChatAdvancedSqlSpecialistService.format_sql_authoring_answer(raw)

    assert formatted.count("Com base nas informações fornecidas") == 1


def test_format_sql_authoring_answer_strips_duplicate_intro():
    intro = ChatAdvancedSqlSpecialistService.SQL_AUTHORING_INTRO
    raw = (
        f"{intro}\n\n```sql\nSELECT A1_COD, A1_NOME FROM SA1010\n```\n\n{intro}"
    )
    formatted = ChatAdvancedSqlSpecialistService.format_sql_authoring_answer(raw)

    assert formatted.lower().count("segue a consulta em sql") == 1


def test_format_sql_authoring_answer_collapses_duplicate_sql_blocks_with_prose():
    intro = ChatAdvancedSqlSpecialistService.SQL_AUTHORING_INTRO
    explanation = (
        'Esta consulta SQL selecionará apenas o código e o nome dos clientes '
        'que estão no status de "Ativo" na tabela SA1.'
    )
    sql = "SELECT A1_COD, A1_NOME\nFROM SA1010\nWHERE D_E_L_E_T_ = ''"
    raw = (
        f"{intro}\n\n```sql\n{sql}\n```\n\n{explanation}\n\n"
        f"{intro}\n\n```sql\n{sql}\n```\n\n{explanation}"
    )
    formatted = ChatAdvancedSqlSpecialistService.format_sql_authoring_answer(raw)

    assert formatted.lower().count("```sql") == 1
    assert formatted.lower().count("segue a consulta em sql") == 1
    assert formatted.count(explanation) == 1


def test_format_sql_authoring_answer_collapses_inline_fence_duplicate():
    before = (
        "Com base nas permissões do papel Superadministrador que você possui, "
        "você pode consultar a tabela SA1 para obter apenas os códigos e nomes "
        "dos clientes ativos. Aqui está uma consulta SQL simples para isso:"
    )
    explanation = (
        "Esta consulta retornará apenas os códigos e nomes dos clientes cujo status é "
        "'ATIVO'. Certifique-se de que você tem permissões suficientes para acessar "
        "a tabela SA1."
    )
    inline_sql = "SELECT A1_COD, A1_NOME FROM SA1010 WHERE D_E_L_E_T_ = ''"
    block_sql = "SELECT A1_COD, A1_NOME\nFROM SA1010\nWHERE D_E_L_E_T_ = ''"
    raw = (
        f"{before} ```sql {inline_sql} ``` {explanation}\n\n"
        f"{before}\n\n```sql\n{block_sql}\n```\n\n{explanation}"
    )
    formatted = ChatAdvancedSqlSpecialistService.format_sql_authoring_answer(raw)

    assert formatted.lower().count("```sql") == 1
    assert formatted.count(before) == 1
    assert formatted.count(explanation) == 1


def test_normalize_protheus_sql_replaces_generic_columns():
    answer = (
        "Segue:\n\n```sql\nSELECT CodigoCliente, NomeCliente FROM SA1 WHERE Status = 'Ativo';\n```"
    )
    tool_calls = [
        {
            "metadata": {
                "path": "/system/tables/SA1/columns",
                "sqlSchemaPrefetch": True,
            }
        }
    ]
    normalized = ChatAdvancedSqlSpecialistService.normalize_protheus_sql_answer(
        answer,
        message="Monte uma consulta para listar clientes ativos da tabela SA1, só código e nome, sem executar.",
        tool_calls=tool_calls,
    )

    assert "A1_COD" in normalized
    assert "A1_NOME" in normalized
    assert "CodigoCliente" not in normalized


def test_resolve_max_tool_calls_sql_turn():
    msg = "Monte uma consulta para listar clientes ativos da tabela SA1, sem executar."
    assert ChatAdvancedSqlSpecialistService.resolve_max_tool_calls(msg, 5) == 50
    assert ChatAdvancedSqlSpecialistService.resolve_max_tool_calls("qual o estoque?", 5) == 5


def test_strip_schema_presentation_from_tool_calls():
    from app.domain.services.chat_advanced_sql_specialist_service import (
        ChatAdvancedSqlSpecialistService,
    )

    result = ChatAdvancedSqlSpecialistService.strip_schema_catalog_presentations(
        {
            "toolCalls": [
                {
                    "metadata": {
                        "sqlSchemaPrefetch": True,
                        "presentation": {"type": "table", "title": "Colunas"},
                    }
                }
            ]
        }
    )

    meta = result["toolCalls"][0]["metadata"]
    assert "presentation" not in meta


def test_review_sql_ignores_stale_memory_ambiguity():
    from app.application.services.chat_session_memory_direct_answer_service import (
        ChatSessionMemoryDirectAnswerService,
    )

    review = "Revisa essa query:\n\nSELECT * FROM SA1010 a JOIN SC5010 p ON p.C5_CLIENTE = a.A1_COD"
    wm = {"memoryAmbiguity": {"promptHint": "Quando você diz «isso» ou «esse»..."}}

    assert ChatSessionMemoryDirectAnswerService.build(
        message=review,
        workspace_context={"workingMemory": wm},
    ) is None


def test_ensure_required_sql_block_for_sc5_sa1():
    snapshot = {
        "mode": "schema_explore",
        "message": "como relacionar sc5 com sa1",
        "schemaDiscovery": {"tableCandidates": ["SC5", "SA1"]},
    }
    answer = ChatAdvancedSqlSpecialistService.ensure_required_sql_block(
        "Precisamos validar a relação.",
        snapshot=snapshot,
    )
    assert "```sql" in answer.lower()
    assert "c5_cliente" in answer.lower()


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


def test_incremental_top10_after_authoring_without_execute():
    history = [
        {
            "role": "user",
            "content": (
                "Monte uma consulta para listar clientes ativos da tabela SA1, "
                "só código e nome, sem executar."
            ),
        },
        {
            "role": "assistant",
            "content": (
                "```sql\nSELECT A1_COD, A1_NOME\nFROM SA1010\n"
                "WHERE D_E_L_E_T_ = ''\n```"
            ),
        },
    ]
    msg = "filtro os 10 primeiros"
    refinement = ChatSqlQueryRefinementService.resolve(msg, previous_messages=history)
    assert refinement is not None
    assert refinement.mode == "show_sql"
    assert "TOP 10" in refinement.sql.upper()
    assert ChatSqlQueryRefinementService.is_sql_follow_up(msg, previous_messages=history)


def test_apply_top_limit_inserts_when_missing():
    sql = "SELECT A1_COD, A1_NOME FROM SA1010 WHERE D_E_L_E_T_ = ''"
    updated = ChatSqlQueryRefinementService.apply_top_limit(sql, 10)
    assert "TOP 10" in updated.upper()


def test_authoring_sql_from_message_product_group_sb1():
    from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_prompt_service import (
        ChatAdvancedSqlSpecialistPromptService,
    )

    msg = (
        "use sql para construir uma query que liste 5 produtos "
        "na tabela de produtos, grupo 1008"
    )
    sql = ChatAdvancedSqlSpecialistPromptService._authoring_sql_from_message(msg, [])

    assert sql is not None
    assert "SB1010" in sql
    assert "B1_COD" in sql
    assert "B1_DESC" in sql
    assert "TOP 5" in sql.upper()
    assert "B1_GRUPO" in sql
    assert "1008" in sql


def test_normalize_replaces_sa1_with_sb1_for_product_authoring():
    from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_prose_formatting_service import (
        ChatAdvancedSqlSpecialistProseFormattingService,
    )

    msg = (
        "use sql para construir uma query que liste 5 produtos "
        "na tabela de produtos, grupo 1008"
    )
    bad = (
        "Segue a consulta.\n\n```sql\nSELECT A1_COD, A1_NOME FROM SA1010\n```\n\n"
        "Esta consulta lista produtos do grupo 1008."
    )
    fixed = ChatAdvancedSqlSpecialistProseFormattingService.normalize_protheus_sql_answer(
        bad,
        message=msg,
        tool_calls=[],
    )

    assert "SB1010" in fixed
    assert "B1_COD" in fixed
    assert "TOP 5" in fixed.upper()
    assert "B1_GRUPO" in fixed
    assert "1008" in fixed
    assert "A1_COD" not in fixed
    assert "SA1010" not in fixed


def test_plan_schema_prefetch_chains_sb1_columns_after_table_search():
    from app.domain.services.chat_sql_authoring_guidance_service import (
        ChatSqlAuthoringGuidanceService,
    )

    class _StubSelection:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def select_system_metadata(self, prompt: str, allowed_action_ids: list[str]) -> dict:
            self.calls.append(prompt)

            if "colunas" in prompt.lower():
                return {
                    "arguments": {
                        "actionId": "api_delpi.system.get_table_columns",
                    },
                    "metadata": {"path": "/system/tables/SB1/columns"},
                }

            return {
                "arguments": {
                    "actionId": "api_delpi.system.search_tables_system_tables_search_get",
                },
                "metadata": {"path": "/system/tables/search"},
            }

    msg = (
        "use sql para construir uma query que liste 5 produtos "
        "na tabela de produtos, grupo 1008"
    )
    selection = _StubSelection()
    planned = ChatSqlAuthoringGuidanceService.plan_schema_prefetch(
        selection,
        message=msg,
        allowed_action_ids=["api_delpi.system.search_tables_system_tables_search_get"],
    )

    assert len(planned) == 2
    assert any("colunas da tabela SB1" in call for call in selection.calls)
