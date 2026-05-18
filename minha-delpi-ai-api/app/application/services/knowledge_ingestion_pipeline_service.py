import hashlib
from dataclasses import dataclass, field

from app.application.services.knowledge_adaptive_chunker_service import (
    KnowledgeAdaptiveChunkerService,
)
from app.application.services.knowledge_chunk_deduplicator_service import (
    KnowledgeChunkDeduplicatorService,
)
from app.application.services.knowledge_content_cleaner_service import (
    KnowledgeContentCleanerService,
)
from app.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class PreparedKnowledgeChunk:
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeIngestionPipelineResult:
    cleaned_content: str
    content_hash: str
    word_count: int
    chunks: list[PreparedKnowledgeChunk]
    stats: dict


class KnowledgeIngestionPipelineService:
    PIPELINE_VERSION = "1"

    def __init__(
        self,
        cleaner: KnowledgeContentCleanerService | None = None,
        chunker: KnowledgeAdaptiveChunkerService | None = None,
        deduplicator: KnowledgeChunkDeduplicatorService | None = None,
    ):
        self.cleaner = cleaner or KnowledgeContentCleanerService()
        self.chunker = chunker or KnowledgeAdaptiveChunkerService()
        self.deduplicator = deduplicator or KnowledgeChunkDeduplicatorService()

    def prepare(
        self,
        content: str,
        *,
        title: str,
        source_type: str,
        source_ref: str | None,
        document_metadata: dict | None = None,
    ) -> KnowledgeIngestionPipelineResult:
        original_chars = len(str(content or ""))
        cleaned = self.cleaner.clean(content) if Settings.KNOWLEDGE_PIPELINE_ENABLED else str(content or "").strip()
        cleaned_chars = len(cleaned)
        content_hash = self._content_hash(cleaned)
        word_count = len(cleaned.split()) if cleaned else 0

        raw_chunks: list[str] = []

        if Settings.KNOWLEDGE_PIPELINE_ENABLED:
            raw_chunks, chunk_strategy = self.chunker.chunk(cleaned)
            chunks, duplicates_removed = self.deduplicator.dedupe(raw_chunks)
        else:
            chunk_strategy = "legacy"
            raw_chunks = [cleaned] if cleaned else []
            chunks = raw_chunks
            duplicates_removed = 0

        prepared = [
            self._prepare_chunk(
                chunk,
                index=index,
                title=title,
                source_type=source_type,
                source_ref=source_ref,
                document_metadata=document_metadata,
                chunk_strategy=chunk_strategy,
            )
            for index, chunk in enumerate(chunks)
        ]

        stats = {
            "version": self.PIPELINE_VERSION,
            "enabled": Settings.KNOWLEDGE_PIPELINE_ENABLED,
            "chunkStrategy": chunk_strategy,
            "originalChars": original_chars,
            "cleanedChars": cleaned_chars,
            "charsRemoved": max(0, original_chars - cleaned_chars),
            "wordCount": word_count,
            "contentHash": content_hash,
            "chunksBeforeDedup": len(raw_chunks),
            "chunksAfterDedup": len(prepared),
            "duplicatesRemoved": duplicates_removed,
        }

        return KnowledgeIngestionPipelineResult(
            cleaned_content=cleaned,
            content_hash=content_hash,
            word_count=word_count,
            chunks=prepared,
            stats=stats,
        )

    def _prepare_chunk(
        self,
        content: str,
        *,
        index: int,
        title: str,
        source_type: str,
        source_ref: str | None,
        document_metadata: dict | None,
        chunk_strategy: str,
    ) -> PreparedKnowledgeChunk:
        chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        metadata = {
            "title": title,
            "source_type": source_type,
            "source_ref": source_ref,
            "chunkIndex": index,
            "charCount": len(content),
            "wordCount": len(content.split()),
            "contentHash": chunk_hash,
            "chunkStrategy": chunk_strategy,
            "pipelineVersion": self.PIPELINE_VERSION,
        }

        if document_metadata:
            for key in ("category", "namespace", "domain", "scope"):
                if document_metadata.get(key) is not None:
                    metadata[key] = document_metadata.get(key)

            tags = document_metadata.get("tags")

            if tags:
                metadata["tags"] = tags

        return PreparedKnowledgeChunk(content=content, metadata=metadata)

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
