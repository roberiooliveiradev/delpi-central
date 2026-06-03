from app.domain.services.chat_text_task_preference_service import ChatTextTaskPreferenceService
from app.domain.services.chat_text_task_service import ChatTextTaskService


def test_detect_de_agora_em_diante_sem_explicar():
    prefs = ChatTextTaskPreferenceService.detect_from_message(
        "de agora em diante corrija sem explicar"
    )

    assert prefs.get("deliver_final_only") is True


def test_detect_email_direct_preference():
    prefs = ChatTextTaskPreferenceService.detect_from_message(
        "sempre deixe meus e-mails mais diretos"
    )

    assert prefs.get("email_direct") is True


def test_apply_to_snapshot_merges_across_turns():
    snapshot: dict = {"preferences": {"textTask": {"format_topics": True}}}
    ChatTextTaskPreferenceService.apply_to_snapshot(
        snapshot,
        message="de agora em diante corrija sem explicar",
    )

    assert snapshot["preferences"]["textTask"]["format_topics"] is True
    assert snapshot["preferences"]["textTask"]["deliver_final_only"] is True


def test_classify_applies_session_deliver_final_only():
    workspace = {
        "workingMemory": {
            "preferences": {"textTask": {"deliver_final_only": True}},
        }
    }
    ctx = ChatTextTaskService.classify(
        "corrija: o produto esta bloqueado",
        workspace_context=workspace,
    )

    assert ctx.get("deliverFinalOnly") is True
