from uuid import UUID

from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.application.services.chat_attachment_preview_service import (
    ChatAttachmentPreviewService,
)
from app.application.services.chat_attachment_text_extractor import ChatAttachmentTextExtractor
from app.application.use_cases.ingest_knowledge_document_use_case import (
    IngestKnowledgeDocumentUseCase,
)
from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.infrastructure.config.settings import Settings


class IndexChatAttachmentUseCase:
    def __init__(
        self,
        attachment_repository: ChatAttachmentRepositoryPort,
        ingest_knowledge_document_use_case: IngestKnowledgeDocumentUseCase,
        text_extractor: ChatAttachmentTextExtractor,
    ):
        self.attachment_repository = attachment_repository
        self.ingest_knowledge_document_use_case = ingest_knowledge_document_use_case
        self.text_extractor = text_extractor

    def execute(self, *, user_id: str, attachment) -> dict:
        extracted = self.text_extractor.extract(
            storage_path=attachment.storage_path,
            filename=attachment.original_filename,
            content_type=attachment.content_type,
            pdf_page_limit=Settings.CHAT_ATTACHMENT_INDEX_PDF_PAGE_LIMIT,
        )

        if not extracted["supported"]:
            updated = self.attachment_repository.update_status(
                attachment_id=attachment.id,
                status="unsupported",
                metadata={
                    "indexed": False,
                    "indexReason": extracted["metadata"],
                },
            )

            return {
                "indexed": False,
                "status": updated.status if updated else "unsupported",
                "reason": extracted["metadata"],
            }

        content = str(extracted.get("content") or "").strip()

        if not content:
            updated = self.attachment_repository.update_status(
                attachment_id=attachment.id,
                status="index_failed",
                metadata={
                    "indexed": False,
                    "indexReason": "empty_extracted_content",
                    "extractor": extracted["metadata"],
                },
            )

            return {
                "indexed": False,
                "status": updated.status if updated else "index_failed",
                "reason": "empty_extracted_content",
            }

        metadata = {
            "scope": "session_source",
            "userId": str(attachment.user_id),
            "sessionId": str(attachment.session_id),
            "messageId": str(attachment.message_id) if attachment.message_id else None,
            "projectId": str(attachment.project_id) if attachment.project_id else None,
            "agentId": str(attachment.agent_id) if attachment.agent_id else None,
            "attachmentId": str(attachment.id),
            "originalFilename": attachment.original_filename,
            "contentType": attachment.content_type,
            "extractor": extracted["metadata"],
        }

        document = self.ingest_knowledge_document_use_case.execute(
            IngestDocumentRequest(
                user_id=user_id,
                title=attachment.original_filename,
                source_type="chat_attachment",
                source_ref=str(attachment.id),
                content=content,
                metadata=metadata,
            )
        )

        preview = ChatAttachmentPreviewService.build_from_extracted(
            extracted,
            filename=attachment.original_filename,
        )
        extractor_meta = dict(extracted.get("metadata") or {})

        updated = self.attachment_repository.update_status(
            attachment_id=attachment.id,
            status="indexed",
            metadata={
                "indexed": True,
                "knowledgeDocumentId": document["id"],
                "chunks": document["chunks"],
                "extractor": str(extractor_meta.get("extractor") or ""),
                "extractorMeta": extractor_meta,
                "preview": preview,
            },
        )

        should_refresh_vision = (
            ChatDocumentVisionService.is_enabled()
            and not Settings.CHAT_ATTACHMENT_DEFER_VISION_ON_INDEX
            and updated
        )

        if should_refresh_vision:
            ChatDocumentVisionService.refresh_attachment_vision_snapshot(
                updated,
                skills={"documentVision": True},
                persist=True,
            )

        return {
            "indexed": True,
            "status": updated.status if updated else "indexed",
            "document": document,
        }
