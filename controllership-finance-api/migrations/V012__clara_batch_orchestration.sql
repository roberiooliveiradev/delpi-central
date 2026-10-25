-- V012 — CLARA batch orchestration (CF-PROC0072-CLARA-BATCH-RELEASE-001).
--
-- Execução multiação governada: um pedido → plano ordenado por
-- dependências → consentimento consolidado → claim atômico por
-- operação → execução delegada às regras canônicas → read-back
-- independente → relatório honesto. Não destrutiva.
--
-- Máquina de estados por operação:
--   PREPARED → CLAIMED → APPLIED → VERIFIED
--                    ↘ FAILED | UNKNOWN | BLOCKED
-- CLAIMED é durável ANTES do efeito — duas ACTs concorrentes têm
-- exatamente um vencedor; efeito desconhecido nunca é repetido.

BEGIN;

-- 1) Proposal ganha claim durável e estado de execução ---------------

ALTER TABLE controllership_finance.clara_proposal
    ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS execution_state TEXT NOT NULL
        DEFAULT 'PREPARED'
        CHECK (execution_state IN (
            'PREPARED', 'CLAIMED', 'APPLIED', 'VERIFIED',
            'FAILED', 'UNKNOWN'
        )),
    ADD COLUMN IF NOT EXISTS batch_operation_id UUID;

-- consumed_at permanece: marca a proposta como encerrada
-- (terminal). claimed_at marca o vencedor da corrida antes do efeito.

-- 2) Lote de operações ------------------------------------------------

CREATE TABLE IF NOT EXISTS controllership_finance.clara_batch (
    batch_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handle_hash       TEXT NOT NULL UNIQUE,
    actor_sub         TEXT NOT NULL,
    plan              JSONB NOT NULL,
    plan_hash         TEXT NOT NULL,
    consent_mode      TEXT NOT NULL DEFAULT 'NONE'
        CHECK (consent_mode IN (
            'NONE', 'CONSOLIDATED', 'HOST_ATTESTED'
        )),
    consent_record    JSONB NOT NULL DEFAULT '{}'::jsonb,
    status            TEXT NOT NULL DEFAULT 'PREPARED'
        CHECK (status IN (
            'PREPARED', 'CONFIRMED', 'EXECUTING',
            'COMPLETED', 'COMPLETED_WITH_FAILURES',
            'BLOCKED', 'EXPIRED'
        )),
    correlation_id    TEXT,
    expires_at        TIMESTAMPTZ NOT NULL,
    confirmed_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    result            JSONB
);

CREATE INDEX IF NOT EXISTS clara_batch_actor_idx
    ON controllership_finance.clara_batch (actor_sub, created_at DESC);

-- 3) Operação do lote -------------------------------------------------

CREATE TABLE IF NOT EXISTS controllership_finance.clara_batch_operation (
    operation_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id          UUID NOT NULL REFERENCES
        controllership_finance.clara_batch(batch_id)
        ON DELETE RESTRICT,
    seq               INTEGER NOT NULL,
    idempotency_key   TEXT NOT NULL,
    capability        TEXT NOT NULL,
    resource_type     TEXT NOT NULL,
    resource_key      TEXT NOT NULL,
    params            JSONB NOT NULL,
    depends_on        JSONB NOT NULL DEFAULT '[]'::jsonb,
    state             TEXT NOT NULL DEFAULT 'PREPARED'
        CHECK (state IN (
            'PREPARED', 'CLAIMED', 'APPLIED', 'VERIFIED',
            'FAILED', 'BLOCKED', 'UNKNOWN'
        )),
    proposal_id       UUID REFERENCES
        controllership_finance.clara_proposal(proposal_id),
    result            JSONB,
    error_code        TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (batch_id, seq),
    UNIQUE (batch_id, idempotency_key)
);

ALTER TABLE controllership_finance.clara_proposal
    ADD CONSTRAINT clara_proposal_batch_operation_fk
    FOREIGN KEY (batch_operation_id)
    REFERENCES controllership_finance.clara_batch_operation(operation_id)
    ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS clara_batch_operation_batch_idx
    ON controllership_finance.clara_batch_operation
        (batch_id, seq);

COMMIT;
