from app.domain.services.text_chunker_service import TextChunkerService
from app.infrastructure.config.settings import Settings


class KnowledgeAdaptiveChunkerService:
    def __init__(
        self,
        *,
        min_chunk_size: int | None = None,
        max_chunk_size: int | None = None,
        overlap: int | None = None,
        fallback_chunker: TextChunkerService | None = None,
    ):
        self.min_chunk_size = min_chunk_size or Settings.KNOWLEDGE_CHUNK_MIN_SIZE
        self.max_chunk_size = max_chunk_size or Settings.KNOWLEDGE_CHUNK_SIZE
        self.overlap = overlap or Settings.KNOWLEDGE_CHUNK_OVERLAP
        self.fallback_chunker = fallback_chunker or TextChunkerService(
            chunk_size=self.max_chunk_size,
            overlap=self.overlap,
        )

    def chunk(self, text: str) -> tuple[list[str], str]:
        normalized = str(text or "").strip()

        if not normalized:
            return [], "empty"

        if len(normalized) <= self.min_chunk_size:
            return [normalized], "single"

        paragraphs = [part.strip() for part in normalized.split("\n\n") if part.strip()]

        if len(paragraphs) > 1:
            packed = self._pack_paragraphs(paragraphs)

            if packed:
                return packed, "paragraph"

        return self.fallback_chunker.chunk(normalized), "sliding"

    def _pack_paragraphs(self, paragraphs: list[str]) -> list[str]:
        chunks: list[str] = []
        buffer = ""

        for paragraph in paragraphs:
            candidate = paragraph if not buffer else f"{buffer}\n\n{paragraph}"

            if len(candidate) <= self.max_chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(buffer)

            if len(paragraph) <= self.max_chunk_size:
                buffer = paragraph
                continue

            chunks.extend(self.fallback_chunker.chunk(paragraph))
            buffer = ""

        if buffer:
            chunks.append(buffer)

        return chunks
