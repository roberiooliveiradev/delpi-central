-- V011 — CLARA (CF-PROC0072-CLARA-COMPLETE-001): base de conhecimento
-- própria, persistente, consultável, versionada e rastreável + store de
-- propostas governadas (PREPARE/ACT, padrão TÉO owner-local).
--
-- A base de conhecimento NÃO substitui sistemas de registro: cada item
-- carrega proveniência (source_id, versão, hash, autoridade) e locator de
-- citação. Sem permission nova — CLARA herda access/manage do Portal.
-- Proposals são handles opacos vinculados ao ator — nunca autorizam por si.

BEGIN;

-- 1) Fontes autorizadas do corpus ----------------------------------------

CREATE TABLE IF NOT EXISTS controllership_finance.clara_knowledge_source (
    source_id          TEXT PRIMARY KEY,
    source_type        TEXT NOT NULL CHECK (source_type IN (
        'DOCUMENT', 'VIDEO_OBSERVATION', 'VIDEO_TRANSCRIPT',
        'MATRIX', 'INVENTORY', 'REPORT_SAMPLE', 'CONTRACT',
        'CODE_EVIDENCE', 'TEST_EVIDENCE'
    )),
    name               TEXT NOT NULL,
    source_version     TEXT,
    source_hash        TEXT,
    origin_authority   TEXT NOT NULL DEFAULT 'TO_INVENTORY',
    description        TEXT,
    registered_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata           JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- 2) Itens de conhecimento (segmentos) ------------------------------------

CREATE TABLE IF NOT EXISTS controllership_finance.clara_knowledge_item (
    knowledge_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id              TEXT NOT NULL REFERENCES
        controllership_finance.clara_knowledge_source(source_id),
    process_id             TEXT NOT NULL DEFAULT 'PROC-0072',
    topic                  TEXT NOT NULL,
    business_step          TEXT,
    related_report_ids     JSONB NOT NULL DEFAULT '[]'::jsonb,
    origin_authority       TEXT NOT NULL DEFAULT 'TO_INVENTORY',
    evidence_classification TEXT NOT NULL DEFAULT 'OWNER_REPORTED_VIA_PO'
        CHECK (evidence_classification IN (
            'PROVEN_SCREENSHOT', 'PROVEN_CODE', 'PROVEN_TEST',
            'OWNER_REPORTED_VIA_PO', 'TO_INVENTORY', 'TARGET',
            'APPROVED_RULE', 'CURRENT_IMPLEMENTATION'
        )),
    valid_from             TIMESTAMPTZ,
    indexed_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_verified_at       TIMESTAMPTZ,
    access_scope           TEXT NOT NULL DEFAULT 'PORTAL_ACCESS'
        CHECK (access_scope IN (
            'PORTAL_ACCESS', 'PORTAL_MANAGE', 'INTERNAL_ONLY'
        )),
    citation_locator       JSONB NOT NULL DEFAULT '{}'::jsonb,
    supersedes             UUID REFERENCES
        controllership_finance.clara_knowledge_item(knowledge_id),
    status                 TEXT NOT NULL DEFAULT 'PUBLISHED'
        CHECK (status IN ('PUBLISHED', 'SUPERSEDED', 'RETRACTED')),
    title                  TEXT NOT NULL,
    content                TEXT NOT NULL,
    content_hash           TEXT NOT NULL,
    content_tsv            TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('portuguese',
            coalesce(title, '') || ' ' || coalesce(business_step, '')
            || ' ' || coalesce(topic, '') || ' ' || coalesce(content, ''))
    ) STORED
);

CREATE INDEX IF NOT EXISTS clara_knowledge_item_tsv_idx
    ON controllership_finance.clara_knowledge_item
    USING GIN (content_tsv);
CREATE INDEX IF NOT EXISTS clara_knowledge_item_topic_idx
    ON controllership_finance.clara_knowledge_item (topic, status);
CREATE INDEX IF NOT EXISTS clara_knowledge_item_step_idx
    ON controllership_finance.clara_knowledge_item (business_step, status);

-- 3) Versões publicadas do corpus ------------------------------------------

CREATE TABLE IF NOT EXISTS controllership_finance.clara_corpus_version (
    corpus_version_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    published_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_by       TEXT NOT NULL,
    item_count         INTEGER NOT NULL,
    source_count       INTEGER NOT NULL,
    manifest           JSONB NOT NULL DEFAULT '{}'::jsonb,
    status             TEXT NOT NULL DEFAULT 'PUBLISHED'
        CHECK (status IN ('PUBLISHED', 'RETRACTED'))
);

-- 4) Propostas governadas (PREPARE → ACT) ----------------------------------
-- Payload selado server-side; handle opaco = sha256 do segredo, nunca o
-- segredo em si. Consumo atômico via consumed_at (single-use).

CREATE TABLE IF NOT EXISTS controllership_finance.clara_proposal (
    proposal_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handle_hash        TEXT NOT NULL UNIQUE,
    actor_sub          TEXT NOT NULL,
    capability         TEXT NOT NULL,
    resource_type      TEXT NOT NULL,
    resource_key       TEXT NOT NULL,
    payload            JSONB NOT NULL,
    expected_state     JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at         TIMESTAMPTZ NOT NULL,
    consumed_at        TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    result             JSONB
);

CREATE INDEX IF NOT EXISTS clara_proposal_actor_idx
    ON controllership_finance.clara_proposal (actor_sub, created_at DESC);

COMMIT;
