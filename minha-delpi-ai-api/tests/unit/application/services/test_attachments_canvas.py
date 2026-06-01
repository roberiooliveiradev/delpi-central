from app.application.services.chat_attachment_follow_up_service import (
    ChatAttachmentFollowUpService,
)
from app.application.services.chat_attachment_welcome_service import (
    ChatAttachmentWelcomeService,
)
from app.application.services.chat_canvas_ambiguity_service import (
    ChatCanvasAmbiguityService,
)
from app.application.services.chat_canvas_content_service import (
    ChatCanvasContentService,
    ChatCanvasOpenPayload,
)
from app.application.services.chat_canvas_session_metadata_service import (
    ChatCanvasSessionMetadataService,
)
from tests.fixtures.attachments_canvas_cases import ATTACHMENTS_CANVAS_CASES


def _case(case_id: str) -> dict:
    for item in ATTACHMENTS_CANVAS_CASES:
        if item["id"] == case_id:
            return item

    raise KeyError(case_id)


def test_l1_welcome_pdf():
    case = _case("L1")
    answer = ChatAttachmentWelcomeService.build_direct_answer(
        attachments=case["attachments"],
    )

    assert answer
    assert all(token.lower() in answer.lower() for token in case["expect_substrings"])


def test_l2_attachment_follow_up_chips():
    case = _case("L2")
    metadata: dict = {}

    ChatAttachmentFollowUpService.attach_to_assistant_metadata(
        metadata,
        had_attachments=case["had_attachments"],
        attachments=[{"original_filename": "planilha.xlsx", "status": "indexed"}],
    )

    labels = [
        item["label"]
        for item in metadata.get("attachmentFollowUpSuggestions") or []
    ]

    for label in case["expect_labels"]:
        assert label in labels


def test_l5_canvas_copy_last_response():
    case = _case("L5")
    action = ChatCanvasContentService.resolve(
        case["message"],
        case["previous_messages"],
        {"capabilities": {"canvas": True}},
    )

    assert action
    assert action.open_payload is not None
    assert "estoque" in action.open_payload.markdown.lower()


def test_l7_large_file_notice():
    case = _case("L7")
    answer = ChatAttachmentWelcomeService.build_direct_answer(attachments=case["attachments"])

    assert answer
    assert all(token.lower() in answer.lower() for token in case["expect_substrings"])


def test_l11_unreadable_attachment():
    case = _case("L11")
    answer = ChatAttachmentWelcomeService.build_direct_answer(attachments=case["attachments"])

    assert answer
    assert all(token.lower() in answer.lower() for token in case["expect_substrings"])


def test_l12_canvas_ambiguity():
    case = _case("L12")
    action = ChatCanvasContentService.resolve(
        case["message"],
        case["previous_messages"],
        {"capabilities": {"canvas": True}},
    )

    assert action
    assert action.open_payload is None
    assert "última resposta" in action.answer.lower() or "tabela" in action.answer.lower()


def test_canvas_session_metadata_versioning():
    metadata: dict = {}
    payload = ChatCanvasOpenPayload(
        title="Relatório",
        markdown="# Relatório\n\nConteúdo.",
        source_message_id="msg-1",
    )

    ChatCanvasSessionMetadataService.attach_open(
        metadata,
        open_payload=payload,
        operation="open",
        previous_messages=[
            {"role": "assistant", "metadata": {"canvas": {"version": 2}}},
        ],
    )

    assert metadata["canvas"]["version"] == 3
    assert metadata["canvas"]["active"] is True
    assert metadata["canvasVersion"]["operation"] == "open"


def test_canvas_ambiguity_service_detects_multiple_referents():
    clarification = ChatCanvasAmbiguityService.build_clarification_answer(
        previous_messages=_case("L12")["previous_messages"],
    )

    assert clarification
    assert ChatCanvasAmbiguityService.is_deictic_canvas_request("coloque isso na lousa")
