from uuid import UUID

from app.application.services.chat_attachment_text_extractor import ChatAttachmentTextExtractor
from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.infrastructure.config.settings import Settings


class ChatAttachmentContextService:
    def __init__(
        self,
        *,
        attachment_repository: ChatAttachmentRepositoryPort,
        knowledge_repository: KnowledgeRepositoryPort,
        text_extractor: ChatAttachmentTextExtractor,
    ):
        self.attachment_repository = attachment_repository
        self.knowledge_repository = knowledge_repository
        self.text_extractor = text_extractor

    def build_context(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        attachment_ids: list[UUID],
    ) -> str:
        if not Settings.CHAT_ATTACHMENT_CONTEXT_ENABLED or not attachment_ids:
            return ""

        attachments = self.attachment_repository.list_attachments_by_ids(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachments:
            return ""

        max_chars = Settings.CHAT_ATTACHMENT_CONTEXT_MAX_CHARS
        remaining = max_chars
        blocks: list[str] = []

        for attachment in attachments:
            if remaining <= 0:
                break

            excerpt = self._resolve_excerpt(attachment, max_chars=remaining)

            if not excerpt:
                continue

            clipped = excerpt[:remaining]
            remaining -= len(clipped)

            blocks.append(
                "\n".join(
                    [
                        f"### {attachment.original_filename}",
                        clipped,
                    ]
                )
            )

        if not blocks:
            return ""

        body = "\n\n".join(blocks)

        return (
            "Conteúdo dos arquivos anexados nesta mensagem "
            "(use como fonte primária para esta pergunta):\n\n"
            f"{body}\n\n"
            "Observação: trechos podem estar truncados; o RAG pode trazer fontes adicionais."
        )

    def _resolve_excerpt(self, attachment, *, max_chars: int) -> str:
        metadata = attachment.metadata or {}

        if attachment.status == "indexed":
            document_id = metadata.get("knowledgeDocumentId")

            if document_id:
                try:
                    chunks = self.knowledge_repository.list_chunks_by_document_id(
                        UUID(str(document_id)),
                        limit=12,
                    )
                except (TypeError, ValueError):
                    chunks = []

                if chunks:
                    combined = "\n\n".join(
                        str(chunk.content or "").strip()
                        for chunk in chunks
                        if str(chunk.content or "").strip()
                    )

                    if combined:
                        return self._truncate(combined, max_chars)

        if attachment.status == "unsupported":
            return ""

        extracted = self.text_extractor.extract(
            storage_path=attachment.storage_path,
            filename=attachment.original_filename,
            content_type=attachment.content_type,
        )

        if not extracted.get("supported"):
            return ""

        content = str(extracted.get("content") or "").strip()

        content = ChatDocumentVisionService.enrich_attachment_excerpt(
            storage_path=attachment.storage_path,
            filename=attachment.original_filename,
            content_type=attachment.content_type,
            extracted_content=content,
        )

        if not content:
            return ""

        return self._truncate(content, max_chars)

    def _truncate(self, value: str, max_chars: int) -> str:
        normalized = value.strip()

        if len(normalized) <= max_chars:
            return normalized

        return f"{normalized[: max_chars - 1].rstrip()}…"
