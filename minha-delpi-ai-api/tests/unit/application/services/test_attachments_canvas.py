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
from app.application.services.chat_attachment_artifact_telemetry_service import (
    ChatAttachmentArtifactTelemetryService,
)
from app.application.services.chat_attachment_source_citation_service import (
    ChatAttachmentSourceCitationService,
)
from app.application.services.chat_canvas_follow_up_service import (
    ChatCanvasFollowUpService,
)
from app.application.services.chat_canvas_session_metadata_service import (
    ChatCanvasSessionMetadataService,
)
from app.domain.services.chat_canvas_transform_service import ChatCanvasTransformService
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
        message="resuma o anexo",
    )

    labels = [
        item["label"]
        for item in metadata.get("attachmentFollowUpSuggestions") or []
    ]

    for label in case["expect_labels"]:
        assert label in labels


def test_attachment_follow_up_includes_summarize_chips():
    metadata: dict = {}

    ChatAttachmentFollowUpService.attach_to_assistant_metadata(
        metadata,
        had_attachments=True,
        message="resuma o arquivo anexado",
    )

    labels = [item["label"] for item in metadata.get("attachmentFollowUpSuggestions") or []]

    assert "Resumo executivo" in labels or "Resumir" in labels


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


def test_l3_attachment_summary_to_canvas_query():
    case = _case("L3")
    action = ChatCanvasContentService.resolve(
        case["message"],
        case["previous_messages"],
        {"capabilities": {"canvas": True}},
    )

    assert action
    assert action.open_payload is not None


def test_l4_canvas_append_merges_sections():
    case = _case("L4")
    action = ChatCanvasContentService.resolve(
        case["message"],
        case["previous_messages"],
        {"capabilities": {"canvas": True}},
    )

    assert action
    assert action.open_payload is not None

    for token in case["expect_substrings"]:
        assert token in action.open_payload.markdown


def test_l6_canvas_transform_checklist():
    case = _case("L6")
    action = ChatCanvasContentService.resolve(
        case["message"],
        case["previous_messages"],
        {"capabilities": {"canvas": True}},
    )

    assert action
    assert action.open_payload is not None

    for token in case["expect_markdown_substrings"]:
        assert token in action.open_payload.markdown


def test_l9_canvas_version_increments():
    case = _case("L9")
    metadata: dict = {}
    payload = ChatCanvasOpenPayload(
        title="Doc",
        markdown="# Doc",
        source_message_id="m1",
    )

    ChatCanvasSessionMetadataService.attach_open(
        metadata,
        open_payload=payload,
        operation="transform",
        previous_messages=[{"role": "assistant", "metadata": {"canvas": {"version": 3}}}],
    )

    assert metadata["canvas"]["version"] == case["expect_version"]


def test_l10_attachment_source_citation_metadata():
    case = _case("L10")
    metadata: dict = {}

    ChatAttachmentSourceCitationService.attach_to_assistant_metadata(
        metadata,
        attachments=case["attachments"],
        answer=case["answer"],
    )

    assert case["expect_citation"] is bool(metadata.get("attachmentSourceCitation"))


def test_attachment_source_citation_skipped_for_drawing_report():
    from app.domain.services.chat_drawing_validation_orchestration_service import (
        ChatDrawingValidationOrchestrationService,
    )
    from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
        _analyser_payload_with_guide_and_inspection,
    )

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90261877",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "productCode": "90261877",
            "revision": "01",
            "legible": True,
        },
    )
    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)
    metadata: dict = {}

    ChatAttachmentSourceCitationService.attach_to_assistant_metadata(
        metadata,
        attachments=[
            {
                "original_filename": "90261877.pdf",
                "status": "indexed",
            }
        ],
        answer=report,
    )

    assert metadata.get("attachmentSourceCitation") is None


def test_canvas_follow_up_when_lousa_active():
    metadata: dict = {}

    ChatCanvasFollowUpService.attach_to_assistant_metadata(
        metadata,
        workspace_context={"capabilities": {"canvas": True}},
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {
                    "canvasOpen": {"title": "X", "markdown": "## X\n\nConteúdo."},
                },
            }
        ],
    )

    labels = [item["label"] for item in metadata.get("canvasFollowUpSuggestions") or []]

    assert "Transformar em checklist" in labels


def test_canvas_transform_service_checklist():
    markdown, label = ChatCanvasTransformService.transform(
        "Revisar estoque\nEnviar e-mail",
        ChatCanvasTransformService.KIND_CHECKLIST,
    )

    assert label == "Checklist"
    assert "- [ ]" in markdown


def test_attachment_artifact_telemetry_canvas():
    metadata: dict = {"canvas": {"version": 2, "documentType": "report"}}

    ChatAttachmentArtifactTelemetryService.attach_canvas_open(
        metadata,
        operation="transform",
    )

    assert metadata["canvasArtifact"]["operation"] == "transform"


def test_canvas_ambiguity_service_detects_multiple_referents():
    clarification = ChatCanvasAmbiguityService.build_clarification_answer(
        previous_messages=_case("L12")["previous_messages"],
    )

    assert clarification
    assert ChatCanvasAmbiguityService.is_deictic_canvas_request("coloque isso na lousa")
