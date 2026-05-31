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
