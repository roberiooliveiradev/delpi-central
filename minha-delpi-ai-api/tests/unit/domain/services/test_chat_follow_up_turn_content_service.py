import re

from app.domain.services.chat_follow_up_turn_content_service import (
    ChatFollowUpTurnContentService,
)
from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)


def test_follow_up_decisions_and_stages_loaded():
    decisions = ChatFollowUpTurnContentService.decisions()
    assert "revise_last_query" in decisions
    assert "challenge_last_result" in decisions
    assert "clarify_slot" in decisions
    assert (
        ChatFollowUpTurnContentService.stage_for_decision("revise_last_query")
        == "grounded_revise_query"
    )
    assert (
        ChatFollowUpTurnContentService.stage_for_decision("challenge_last_result")
        == "grounded_challenge_result"
    )


def test_follow_up_patterns_compile():
    branch = ChatFollowUpTurnContentService.compile_pattern("branchWithCode")
    assert branch.search("somente da filial 01")
    assert branch.search("rol filail 01 deste mês")
    assert ChatFollowUpTurnContentService.revise_slot_triggers()
    assert ChatFollowUpTurnContentService.challenge_triggers()


def test_filail_normalizes_and_extracts_branch():
    assert (
        ChatFollowUpTurnContentService.normalize_branch_typos("rol filail 01 deste mês")
        .lower()
        .find("filial")
        >= 0
    )
    assert ChatFollowUpTurnContentService.extract_branch_code("rol filail 01 deste mês") == "01"
    assert ChatFollowUpTurnContentService.extract_branch_code("somente da filial 01") == "01"
    assert ChatFollowUpTurnContentService.extract_branch_code("somente da filial") is None
    assert ChatFollowUpTurnContentService.has_branch_trigger_without_code("somente da filial")


def test_api_route_domains_branch_pattern_accepts_typos():
    spec = ChatOperationalApiDomainService.parameter_strategy_spec("date_branch")
    patterns = spec.get("patterns") if isinstance(spec.get("patterns"), dict) else {}
    branch_re = re.compile(str(patterns.get("branch") or ""), re.IGNORECASE)
    assert branch_re.search("filial 01")
    assert branch_re.search("filail 01")
    assert branch_re.search("unidade 02")
    assert branch_re.search("filal 01")


def test_clarify_and_challenge_content_present():
    assert "filial" in ChatFollowUpTurnContentService.clarify_slot_prompt("branch").lower()
    assert ChatFollowUpTurnContentService.challenge_faithfulness_instruction()
    assert ChatFollowUpTurnContentService.challenge_suggestions()
    assert "01" in ChatFollowUpTurnContentService.revise_ack_branch("01")


def test_previous_period_and_branch_compare_vocab_loaded():
    assert "previous_period" in ChatFollowUpTurnContentService.period_slot_kinds()
    assert (
        ChatFollowUpTurnContentService.period_slot_kind_for_message(
            "comparar com o periodo anterior"
        )
        == "previous_period"
    )
    assert (
        ChatFollowUpTurnContentService.period_slot_kind_for_message(
            "compara com o periodo anteriror"
        )
        == "previous_period"
    )
    assert (
        ChatFollowUpTurnContentService.period_slot_kind_for_message(
            "compara c ano anteriror mesmo periodo"
        )
        == "previous_year_same_range"
    )
    assert "período anterior" in ChatFollowUpTurnContentService.period_compare_prior_label(
        "previous_period"
    ).lower()
    keys = ChatFollowUpTurnContentService.period_compare_preferred_metric_keys()
    assert "rol" in keys
    assert ChatFollowUpTurnContentService.extract_branch_codes(
        "comparar filial 01 com filial 02"
    ) == ["01", "02"]
    ack = ChatFollowUpTurnContentService.period_compare_format(
        "branchCompareAckTemplate",
        baseline_branch="01",
        compare_branch="02",
        start="01-08-2026",
        end="28-08-2026",
    )
    assert "filiais" in ack.lower()
    assert "01" in ack and "02" in ack


def test_period_compare_branch_slot_labels_and_ack():
    assert (
        ChatFollowUpTurnContentService.period_compare_slot_label(
            "branch", "baseline", branch="01"
        )
        == "filial 01"
    )
    assert (
        ChatFollowUpTurnContentService.period_compare_slot_label(
            "branch", "prior", branch="02"
        )
        == "filial 02"
    )
    ack = ChatFollowUpTurnContentService.period_compare_branch_ack(
        baseline_branch="01",
        compare_branch="02",
        start="01-08-2026",
        end="31-08-2026",
    )
    assert "filiais" in ack.lower()
    assert "01" in ack and "02" in ack
    assert "31-08-2026" in ack


def test_continuity_contract_and_period_vocab_loaded():
    modes = ChatFollowUpTurnContentService.continuity_modes()
    assert "consume_last_action" in modes
    assert "answer_without_tools" in modes
    assert "allow_discovery" in modes
    assert (
        ChatFollowUpTurnContentService.continuity_mode_for_decision("revise_last_query")
        == "consume_last_action"
    )
    assert (
        ChatFollowUpTurnContentService.continuity_mode_for_decision("new_intent")
        == "allow_discovery"
    )
    assert ChatFollowUpTurnContentService.period_revise_triggers()
    assert "previous_year_same_range" in ChatFollowUpTurnContentService.period_slot_kinds()
    assert (
        ChatFollowUpTurnContentService.period_slot_kind_for_message(
            "comparar com ano anterior no mesmo periodo"
        )
        == "previous_year_same_range"
    )
    assert "revise_period" in ChatFollowUpTurnContentService.classifier_labels()
    assert (
        ChatFollowUpTurnContentService.decision_for_classifier_label("revise_period")
        == "revise_last_query"
    )
    families = ChatFollowUpTurnContentService.entity_families()
    assert "product" in families
    assert "metric" in families
    assert ChatFollowUpTurnContentService.entity_family_for_markers("department_kpi") == "metric"
