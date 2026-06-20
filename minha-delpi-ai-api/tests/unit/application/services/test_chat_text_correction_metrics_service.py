from app.application.services.chat_text_correction_metrics_service import (
    ChatTextCorrectionMetricsService,
)
from app.application.services.chat_text_correction_follow_up_service import (
    ChatTextCorrectionFollowUpService,
)


def test_build_snapshot_for_correction_turn():
    snapshot = ChatTextCorrectionMetricsService.build_snapshot(
        message="corrija: o estoque esta baixo",
        answer="Segue a versão corrigida:\n\nO estoque está baixo.",
        workspace_context={"textCorrectionMode": True},
        follow_up_count=3,
    )

    assert snapshot is not None
    assert snapshot["subtype"] == "text_correct_basic"
    assert snapshot["source"] == "user_message"
    assert snapshot["followUpChipCount"] == 3


def test_build_snapshot_includes_spell_preflight_metrics():
    snapshot = ChatTextCorrectionMetricsService.build_snapshot(
        message="corrija: o estoque esta baixo",
        workspace_context={
            "textCorrectionMode": True,
            "textCorrectionSpellPreflight": {
                "used": True,
                "issueCount": 2,
                "filteredIssueCount": 1,
                "engine": "languagetool",
            },
        },
    )

    assert snapshot is not None
    assert snapshot["spellPreflightUsed"] is True
    assert snapshot["spellPreflightIssueCount"] == 2
    assert snapshot["spellPreflightFilteredIssueCount"] == 1


def test_attach_via_follow_up_metadata():
    metadata: dict = {}
    ChatTextCorrectionFollowUpService.attach_to_assistant_metadata(
        metadata,
        message="corrija: texto com erro",
        answer="Segue a versão corrigida:\n\nTexto ok.",
        workspace_context={"textCorrectionMode": True},
    )

    assert metadata.get("textCorrectionMetrics", {}).get("subtype") == "text_correct_basic"
    assert metadata.get("textCorrectionFollowUpSuggestions")
