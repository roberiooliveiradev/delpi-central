from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


def test_pre_turn_snapshot_includes_email_preferences():
    snapshot = ChatWorkingMemoryService.build_pre_turn_snapshot(
        message="daqui pra frente sempre faça e-mails curtos e formais",
        previous_messages=[],
    )
    assert snapshot.get("emailPreferences")
    assert snapshot["behaviorInstructions"].get("emailWriting")


def test_context_chips_include_email_preference():
    chips = ChatWorkingMemoryService.build_context_chips(
        {
            "emailPreferences": {"shortEmails": True},
            "operationalFocus": {},
        }
    )
    assert any(chip.get("kind") == "emailPreference" for chip in chips)
