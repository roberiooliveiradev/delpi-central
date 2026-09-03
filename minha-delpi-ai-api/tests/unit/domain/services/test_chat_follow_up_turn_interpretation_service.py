from app.domain.services.chat_follow_up_turn_interpretation_service import (
    ChatFollowUpTurnInterpretationService,
)
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingService

_ROL_ACTION = {
    "name": "financial_rol",
    "path": "/financial/rol",
    "apiRouteDomain": "department_kpi",
    "params": {"start_date": "2026-08-01", "end_date": "2026-08-28"},
}
_EXCERPT = {
    "title": "ROL do mês",
    "rowCount": 1,
    "preview": "ROL consolidado: R$ 1.000.000",
    "topKeys": [],
}


def test_revise_somente_filial_01():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="somente da filial 01",
        last_action=_ROL_ACTION,
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "revise_last_query"
    assert result.slot_delta.get("branch") == "01"
    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="somente da filial 01",
            excerpt=_EXCERPT,
            last_action=_ROL_ACTION,
        )
        == "grounded_revise_query"
    )


def test_clarify_branch_without_code():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="somente da filial",
        last_action=_ROL_ACTION,
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "clarify_slot"
    assert result.clarify_slot == "branch"
    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="somente da filial",
            excerpt=_EXCERPT,
            last_action=_ROL_ACTION,
        )
        == "grounded_clarify_slot"
    )


def test_challenge_unit_vs_total():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="o rol de uma unidade não pode ser igual ao total",
        last_action=_ROL_ACTION,
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "challenge_last_result"
    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="o rol de uma unidade não pode ser igual ao total",
            excerpt=_EXCERPT,
            last_action=_ROL_ACTION,
        )
        == "grounded_challenge_result"
    )


def test_topic_switch_estoque_after_rol():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="e o estoque?",
        last_action=_ROL_ACTION,
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "new_intent"
    assert result.reason == "topic_switch"
    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="e o estoque?",
            excerpt=_EXCERPT,
            last_action=_ROL_ACTION,
        )
        is None
    )


def test_compound_slot_beats_challenge():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="só filial 01 porque o total não pode ser igual",
        last_action=_ROL_ACTION,
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "revise_last_query"
    assert result.slot_delta.get("branch") == "01"


def test_narrate_resuma_isso():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="resuma isso",
        last_action=_ROL_ACTION,
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "narrate_recap"
    assert result.continuity_mode == "answer_without_tools"
    assert not result.allows_parallel_discovery()
    stage = ChatTurnGroundingService.resolve_grounded_stage(
        message="resuma isso",
        excerpt=_EXCERPT,
        last_action=_ROL_ACTION,
    )
    assert stage in {"grounded_narrate_recap", "grounded_narrate_insight"}


def test_revise_previous_year_same_range_consumes_last_action():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="comparar com ano anterior no mesmo periodo",
        last_action={
            **_ROL_ACTION,
            "params": {
                "start_date": "01-08-2026",
                "end_date": "28-08-2026",
                "branch": "all",
            },
        },
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "revise_last_query"
    assert result.continuity_mode == "consume_last_action"
    assert result.requires_last_action_reexec()
    assert result.slot_delta.get("period") == "previous_year_same_range"
    assert result.slot_delta.get("baseline_start_date") == "01-08-2026"
    assert result.slot_delta.get("baseline_end_date") == "28-08-2026"
    assert result.slot_delta.get("start_date") == "01-08-2025"
    assert result.slot_delta.get("end_date") == "28-08-2025"
    meta = result.to_metadata()
    assert meta["continuityMode"] == "consume_last_action"
    assert meta["allowsParallelDiscovery"] is False


def test_revise_previous_period_consumes_last_action():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="comparar com o período anterior",
        last_action={
            **_ROL_ACTION,
            "params": {
                "start_date": "01-08-2026",
                "end_date": "28-08-2026",
                "branch": "all",
            },
        },
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "revise_last_query"
    assert result.continuity_mode == "consume_last_action"
    assert result.requires_last_action_reexec()
    assert result.slot_delta.get("period") == "previous_period"
    assert result.slot_delta.get("baseline_start_date") == "01-08-2026"
    assert result.slot_delta.get("start_date")
    assert result.slot_delta.get("end_date")


def test_revise_mes_passado_maps_to_previous_period():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="e no mês passado?",
        last_action={
            **_ROL_ACTION,
            "params": {
                "start_date": "01-08-2026",
                "end_date": "31-08-2026",
                "branch": "01",
            },
        },
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "revise_last_query"
    assert result.continuity_mode == "consume_last_action"
    assert result.slot_delta.get("period") == "previous_period"
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="comparar filial 01 com filial 02",
        last_action={
            **_ROL_ACTION,
            "params": {
                "start_date": "01-08-2026",
                "end_date": "28-08-2026",
                "branch": "all",
            },
        },
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "revise_last_query"
    assert result.slot_delta.get("compareAxis") == "branch"
    assert result.slot_delta.get("baseline_branch") == "01"
    assert result.slot_delta.get("branch") == "02"


def test_revise_deste_mes_overrides_inherited_yoy_dates():
    """«deste mês» deve resolver calendário da mensagem, não herdar 2025 do lastAction."""
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="rol da filial 01 deste mês",
        last_action={
            **_ROL_ACTION,
            "params": {
                "start_date": "01-08-2025",
                "end_date": "28-08-2025",
                "branch": "01",
            },
        },
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "revise_last_query"
    assert result.slot_delta.get("period") == "message_resolved"
    assert result.slot_delta.get("branch") == "01"
    start = result.slot_delta.get("start_date") or ""
    end = result.slot_delta.get("end_date") or ""
    assert start.endswith("-2026") or start.startswith("2026")
    assert end.endswith("-2026") or end.startswith("2026")
    assert "2025" not in start and "2025" not in end


def test_revise_does_not_fall_through_to_narrate_without_last_action():
    stage = ChatTurnGroundingService.resolve_grounded_stage(
        message="somente da filial 01",
        excerpt=_EXCERPT,
        last_action=None,
    )
    assert stage != "grounded_narrate_recap"
    assert stage is None


def test_rol_after_suppliers_is_new_intent_not_revise():
    suppliers = {
        "name": "product_suppliers",
        "path": "/products/10080047/suppliers",
        "apiRouteDomain": "product",
        "params": {"code": "10080047"},
    }
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="ROL filial 01 agosto 2026",
        last_action=suppliers,
        last_result_excerpt={"title": "Fornecedores", "rowCount": 4},
    )
    assert result.decision == "new_intent"
    assert result.reason in {"topic_switch", "domain_affinity_mismatch"}
    assert result.slot_delta.get("branch") == "01"


def test_compare_filail_after_rol_revises_with_compare_axis():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="compara filail 01 vs filail 02",
        last_action={
            **_ROL_ACTION,
            "params": {
                "start_date": "01-08-2026",
                "end_date": "31-08-2026",
                "branch": "01",
            },
        },
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "revise_last_query"
    assert result.slot_delta.get("compareAxis") == "branch"
    assert result.slot_delta.get("baseline_branch") == "01"
    assert result.slot_delta.get("branch") == "02"


def test_compare_entre_filiais_sets_compare_axis():
    result = ChatFollowUpTurnInterpretationService.interpret(
        message="compara entre filiais 01 e 02",
        last_action={
            **_ROL_ACTION,
            "params": {
                "start_date": "01-08-2026",
                "end_date": "31-08-2026",
                "branch": "01",
            },
        },
        last_result_excerpt=_EXCERPT,
    )
    assert result.decision == "revise_last_query"
    assert result.slot_delta.get("compareAxis") == "branch"
    assert result.slot_delta.get("baseline_branch") == "01"
    assert result.slot_delta.get("branch") == "02"


def test_classifier_cannot_revise_after_topic_switch_to_financial():
    suppliers = {
        "name": "product_suppliers",
        "path": "/products/10080047/suppliers",
        "apiRouteDomain": "product",
        "params": {"code": "10080047"},
    }
    current = ChatFollowUpTurnInterpretationService.interpret(
        message="ROL filial 01 agosto 2026",
        last_action=suppliers,
    )
    assert current.decision == "new_intent"
    assert current.reason == "topic_switch"
    overridden = ChatFollowUpTurnInterpretationService.apply_classifier_label(
        current,
        "revise_branch",
        message="ROL filial 01 agosto 2026",
        last_action=suppliers,
    )
    assert overridden.decision == "new_intent"
    assert overridden.reason == "topic_switch"
