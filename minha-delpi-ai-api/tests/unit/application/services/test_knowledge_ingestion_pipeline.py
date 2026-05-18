from app.application.services.knowledge_adaptive_chunker_service import (
    KnowledgeAdaptiveChunkerService,
)
from app.application.services.knowledge_chunk_deduplicator_service import (
    KnowledgeChunkDeduplicatorService,
)
from app.application.services.knowledge_content_cleaner_service import (
    KnowledgeContentCleanerService,
)
from app.application.services.knowledge_ingestion_pipeline_service import (
    KnowledgeIngestionPipelineService,
)
from app.domain.services.text_chunker_service import TextChunkerService


def test_content_cleaner_removes_control_chars_and_collapses_blank_lines():
    cleaner = KnowledgeContentCleanerService()

    cleaned = cleaner.clean("Linha 1\x00\n\n\nLinha 2   com   espaços")

    assert "\x00" not in cleaned
    assert "Linha 1" in cleaned
    assert "Linha 2 com espaços" in cleaned
    assert "\n\n\n" not in cleaned


def test_chunk_deduplicator_removes_exact_duplicates():
    deduplicator = KnowledgeChunkDeduplicatorService()

    unique, removed = deduplicator.dedupe(
        ["Mesmo conteúdo", "mesmo   conteúdo", "Outro trecho"],
    )

    assert removed == 1
    assert len(unique) == 2


def test_adaptive_chunker_uses_paragraph_strategy_for_long_text():
    chunker = KnowledgeAdaptiveChunkerService(
        min_chunk_size=100,
        max_chunk_size=500,
    )

    content = "\n\n".join([f"Parágrafo {index} " + ("texto " * 40) for index in range(4)])
    chunks, strategy = chunker.chunk(content)

    assert strategy == "paragraph"
    assert len(chunks) >= 2


def test_text_chunker_normalizes_with_real_newlines():
    chunker = TextChunkerService(chunk_size=50, overlap=10)

    chunks = chunker.chunk("Linha A\n\nLinha B")

    assert len(chunks) == 1
    assert "\\n" not in chunks[0]
    assert "Linha A" in chunks[0]
    assert "Linha B" in chunks[0]


def test_pipeline_enriches_chunk_metadata_and_stats():
    pipeline = KnowledgeIngestionPipelineService()

    result = pipeline.prepare(
        "Primeiro parágrafo.\n\nSegundo parágrafo.\n\nPrimeiro parágrafo.",
        title="Doc",
        source_type="manual",
        source_ref="global:test",
        document_metadata={"scope": "global", "category": "faq"},
    )

    assert result.stats["chunksBeforeDedup"] >= result.stats["chunksAfterDedup"]
    assert result.stats["chunksAfterDedup"] >= 1
    assert result.content_hash
    assert result.chunks[0].metadata["category"] == "faq"
    assert result.chunks[0].metadata["pipelineVersion"] == "1"
