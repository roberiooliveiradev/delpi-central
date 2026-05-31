import json

from app.domain.services.chat_text_correction_preference_service import (
    ChatTextCorrectionPreferenceService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


def test_detect_deliver_final_only():
    prefs = ChatTextCorrectionPreferenceService.detect(
        "daqui para frente, quando eu pedir correção, entregue só a versão final",
    )
    assert prefs.get("deliverFinalOnly") is True


def test_merge_into_behavior_persists():
    merged = ChatTextCorrectionPreferenceService.merge_into_behavior(
        "sempre mostre antes e depois quando corrigir texto",
        {},
    )
    assert "textCorrection" in merged
    parsed = json.loads(merged["textCorrection"])
    assert parsed.get("showBeforeAfter") is True
    assert merged.get("scope") == "session"


def test_working_memory_snapshot_carries_preferences():
    snapshot = ChatWorkingMemoryService.build_pre_turn_snapshot(
        message="daqui pra frente sempre corrija sem explicar, só a versão final",
        previous_messages=[],
    )
    assert snapshot.get("textCorrectionPreferences", {}).get("deliverFinalOnly")


def test_build_context_chips():
    chips = ChatTextCorrectionPreferenceService.build_context_chips(
        {"formalTone": True, "preserveStyle": True},
    )
    labels = {chip["label"] for chip in chips}
    assert "Tom formal" in labels
    assert "Manter estilo" in labels
