-- Onda 6.1 — embeddings pgvector para busca semântica em quality_case_similarity_index

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE quality.quality_case_similarity_index
    ADD COLUMN IF NOT EXISTS search_embedding vector(1024);

COMMENT ON COLUMN quality.quality_case_similarity_index.search_embedding IS
    'Embedding de search_text (dim 1024) para busca semântica PAC — populado de forma assíncrona.';

COMMENT ON COLUMN quality.quality_case_similarity_index.embedding_vector IS
    'Legado MVP (BYTEA). Preferir search_embedding (pgvector).';

CREATE INDEX IF NOT EXISTS ix_quality_case_similarity_index_search_embedding
    ON quality.quality_case_similarity_index
    USING hnsw (search_embedding vector_cosine_ops);
