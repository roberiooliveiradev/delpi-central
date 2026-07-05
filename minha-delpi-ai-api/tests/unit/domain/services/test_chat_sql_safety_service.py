"""Playbook 08 — SQL destrutivo."""

from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService


def test_blocks_delete_from():
    assert ChatSqlSafetyService.contains_destructive_sql(
        "execute delete from sc2010 where d_e_l_e_t_ = ''"
    )


def test_allows_select_only():
    assert not ChatSqlSafetyService.contains_destructive_sql(
        "select c2_produto from sc2010 where filial = '01'"
    )


def test_blocks_update_with_sql_context():
    assert ChatSqlSafetyService.contains_destructive_sql(
        "rode update sc2010 set c2_quant = 1"
    )


def test_ignores_delete_outside_sql_context():
    assert not ChatSqlSafetyService.contains_destructive_sql(
        "delete a sessão de memória"
    )


def test_allows_natural_language_execute_intent():
    assert not ChatSqlSafetyService.contains_destructive_sql(
        "execute essa consulta no banco"
    )


def test_allows_execute_essa_query_with_traga_produtos():
    assert not ChatSqlSafetyService.contains_destructive_sql(
        "execute essa query e traga os 5 produtos do grupo 1008"
    )


def test_blocked_direct_answer_none_for_execute_query():
    assert ChatSqlSafetyService.blocked_direct_answer(
        "execute essa query e traga os 5 produtos do grupo 1008"
    ) is None
