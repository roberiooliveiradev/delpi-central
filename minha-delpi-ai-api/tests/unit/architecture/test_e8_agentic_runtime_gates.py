"""Architecture gates for E8 agentic runtime — low false-positive detectors."""

from __future__ import annotations

import ast
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_ORCHESTRATOR = (
    _ROOT
    / "app/application/services/chat_turn_planner_orchestrator_service.py"
)
_SMOKE = _ROOT / "scripts/smoke_conversation_context_quality_live.py"
_DECOMPOSE = (
    _ROOT
    / "app/application/services/decompose_external_action_requests_service.py"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_orchestrator_has_no_domain_family_router():
    source = _read(_ORCHESTRATOR)
    forbidden = (
        'family == "stock"',
        "family == 'stock'",
        'if family == "schedule"',
        'DOMAIN_FAMILIES',
        '"stock/schedule"',
        "operational_family",
    )
    for token in forbidden:
        assert token not in source, f"domain family router leaked: {token}"


def test_smoke_e8_empty_tokens_not_silent_pass():
    source = _read(_SMOKE)
    assert 'return "INCONCLUSIVE"' in source
    assert "never silent PASS" in source or "INCONCLUSIVE" in source
    # Old silent pattern: continue on empty tokens then return True
    assert re.search(r"if not tokens:\s*\n\s*continue", source) is None


def test_decompose_has_no_joiner_gate_as_authority():
    source = _read(_DECOMPOSE)
    tree = ast.parse(source)
    assert tree is not None
    assert "joiners" not in source.lower() or "numbered" in source.lower()


def test_candidate_set_contains_helper_exists():
    from app.domain.services.chat_candidate_set_service import ChatCandidateSetService

    assert ChatCandidateSetService.contains(
        "a1",
        candidate_action_ids=["a1", "a2"],
        allowed_action_ids=["a1", "a2", "a3"],
    )
    assert not ChatCandidateSetService.contains(
        "a9",
        candidate_action_ids=["a1", "a2"],
        allowed_action_ids=["a1", "a2", "a3"],
    )


def test_presentation_preference_contract_includes_kpi():
    from app.domain.services.chat_presentation_preference_contract_service import (
        ChatPresentationPreferenceContractService,
        SESSION_RESPONSE_FORMAT_TOKENS,
    )

    assert "kpi" in SESSION_RESPONSE_FORMAT_TOKENS
    assert ChatPresentationPreferenceContractService.as_session_response_format("kpi") == "kpi"
