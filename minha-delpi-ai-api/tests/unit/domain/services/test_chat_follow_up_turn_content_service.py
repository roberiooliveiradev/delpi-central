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
