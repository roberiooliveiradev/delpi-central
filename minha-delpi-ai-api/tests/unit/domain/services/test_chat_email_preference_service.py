import json

from app.domain.services.chat_email_preference_service import ChatEmailPreferenceService


def test_detect_short_emails_preference():
    prefs = ChatEmailPreferenceService.detect("daqui pra frente sempre faça e-mails curtos")
    assert prefs.get("shortEmails") is True


def test_format_prompt_block():
    block = ChatEmailPreferenceService.format_prompt_block({"formalTone": True, "shortEmails": True})
    assert "curtos" in block.lower()
    assert "formal" in block.lower()


def test_merge_into_behavior():
    merged = ChatEmailPreferenceService.merge_into_behavior(
        "sempre use tom formal nos e-mails",
        {},
    )
    assert "emailWriting" in merged
    parsed = json.loads(merged["emailWriting"])
    assert parsed.get("formalTone") is True


def test_merge_accumulates_preferences():
    first = ChatEmailPreferenceService.merge_into_behavior("sempre e-mails curtos", {})
    second = ChatEmailPreferenceService.merge_into_behavior(
        "sempre tom formal nos e-mails",
        first,
    )
    parsed = json.loads(second["emailWriting"])
    assert parsed.get("shortEmails") is True
    assert parsed.get("formalTone") is True


def test_load_json_from_working_memory():
    prefs = ChatEmailPreferenceService.detect(
        "escreva um e-mail",
        working_memory={
            "behaviorInstructions": {
                "emailWriting": json.dumps({"executiveTone": True}),
            }
        },
    )
    assert prefs.get("executiveTone") is True


def test_apply_to_snapshot():
    snapshot = {"behaviorInstructions": {}}
    ChatEmailPreferenceService.apply_to_snapshot(
        snapshot,
        message="sempre deixe assinatura em branco nos e-mails",
    )
    assert snapshot.get("emailPreferences", {}).get("blankSignature") is True


def test_build_context_chips():
    chips = ChatEmailPreferenceService.build_context_chips(
        {"shortEmails": True, "formalTone": True}
    )
    labels = [chip["label"] for chip in chips]
    assert "E-mails curtos" in labels
    assert all(chip["kind"] == "emailPreference" for chip in chips)


def test_build_metadata():
    meta = ChatEmailPreferenceService.build_metadata({"copyReady": True})
    assert meta is not None
    assert "Pronto para copiar" in (meta.get("labels") or [])
