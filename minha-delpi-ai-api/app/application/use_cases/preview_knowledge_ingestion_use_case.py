from app.application.services.knowledge_ingestion_pipeline_service import (
    KnowledgeIngestionPipelineService,
)
from app.domain.exceptions.knowledge_exceptions import InvalidKnowledgeDocumentInputError
from app.infrastructure.config.settings import Settings


class PreviewKnowledgeIngestionUseCase:
    def __init__(self, pipeline: KnowledgeIngestionPipelineService | None = None):
        self.pipeline = pipeline or KnowledgeIngestionPipelineService()

    def execute(
        self,
        *,
        content: str,
        title: str = "Pré-visualização",
        source_type: str = "preview",
        source_ref: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        normalized = str(content or "").strip()

        if not normalized:
            raise InvalidKnowledgeDocumentInputError("content is required")

        if len(normalized) > Settings.KNOWLEDGE_DOCUMENT_MAX_CHARS:
            raise InvalidKnowledgeDocumentInputError(
                f"content exceeds {Settings.KNOWLEDGE_DOCUMENT_MAX_CHARS} characters"
            )

        prepared = self.pipeline.prepare(
            normalized,
            title=title,
            source_type=source_type,
            source_ref=source_ref,
            document_metadata=metadata,
        )

        return {
            "title": title,
            "sourceType": source_type,
            "sourceRef": source_ref,
            "contentHash": prepared.content_hash,
            "wordCount": prepared.word_count,
            "cleanedPreview": prepared.cleaned_content[:1200],
            "chunks": [
                {
                    "index": index,
                    "charCount": len(chunk.content),
                    "wordCount": len(chunk.content.split()),
                    "preview": chunk.content[:400],
                    "metadata": chunk.metadata,
                }
                for index, chunk in enumerate(prepared.chunks)
            ],
            "pipeline": prepared.stats,
        }
