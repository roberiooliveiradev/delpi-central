from app.application.services.knowledge_ingestion_pipeline_service import (
    KnowledgeIngestionPipelineService,
)
from app.application.services.knowledge_semantic_deduplicator_service import (
    KnowledgeSemanticDeduplicatorService,
)
from app.domain.exceptions.knowledge_exceptions import InvalidKnowledgeDocumentInputError
from app.infrastructure.config.settings import Settings


class PreviewKnowledgeIngestionUseCase:
    def __init__(
        self,
        pipeline: KnowledgeIngestionPipelineService | None = None,
        semantic_deduplicator: KnowledgeSemanticDeduplicatorService | None = None,
    ):
        self.pipeline = pipeline or KnowledgeIngestionPipelineService()
        self.semantic_deduplicator = semantic_deduplicator

    def execute(
        self,
        *,
        content: str,
        title: str = "Pré-visualização",
        source_type: str = "preview",
        source_ref: str | None = None,
        metadata: dict | None = None,
        check_semantic_duplicates: bool = True,
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

        semantic_duplicates: list[dict] = []

        if (
            check_semantic_duplicates
            and Settings.KNOWLEDGE_SEMANTIC_DEDUP_ENABLED
            and self.semantic_deduplicator
        ):
            semantic_duplicates = self.semantic_deduplicator.find_near_duplicates(
                content=prepared.cleaned_content,
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
            "semanticDuplicates": semantic_duplicates,
        }
