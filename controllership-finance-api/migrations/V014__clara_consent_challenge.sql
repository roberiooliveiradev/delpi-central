-- V014 — CLARA consent challenge (CF-PROC0072-CLARA-CONSENT-FINAL-REWORK-001).
--
-- R-CLARA-01: consentimento comprovável — a aprovação humana deixa de
-- ser inferida apenas pela idade do JWT e passa a ser um objeto de
-- autorização de primeira classe, emitido pelo servidor no PREPARE e
-- vinculado de forma verificável a:
--   ator (actor_sub), alvo (batch_id | proposal_id), plano selado
--   (plan_hash + plan_version), expiração, origem autorizada
--   (origin='portal'), correlação e estado de consumo único
--   (PENDING → APPROVED → CONSUMED | EXPIRED | REVOKED).
--
-- A rota BFF de consentimento só grava consent_record depois de
-- aprovar o desafio em transação atômica; a execução verifica o
-- desafio APROVADO/CONSUMED — nem a chamada MCP, nem um JWT recente
-- isolado, nem um desafio de outro lote/ator/plano servem de prova.
-- Não destrutiva.

BEGIN;

CREATE TABLE IF NOT EXISTS controllership_finance.clara_consent_challenge (
    challenge_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind               TEXT NOT NULL CHECK (kind IN ('batch', 'proposal')),
    batch_id           UUID REFERENCES
        controllership_finance.clara_batch(batch_id)
        ON DELETE RESTRICT,
    proposal_id        UUID REFERENCES
        controllership_finance.clara_proposal(proposal_id)
        ON DELETE RESTRICT,
    actor_sub          TEXT NOT NULL,
    plan_hash          TEXT NOT NULL,
    plan_version       INTEGER NOT NULL DEFAULT 1
        CHECK (plan_version >= 1),
    status             TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN (
            'PENDING', 'APPROVED', 'CONSUMED', 'EXPIRED', 'REVOKED'
        )),
    origin             TEXT NOT NULL DEFAULT 'portal'
        CHECK (origin = 'portal'),
    correlation_id     TEXT,
    approved_by        TEXT,
    approved_token_jti TEXT,
    approved_token_iat TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at        TIMESTAMPTZ,
    consumed_at        TIMESTAMPTZ,
    expires_at         TIMESTAMPTZ NOT NULL,
    CHECK (num_nonnulls(batch_id, proposal_id) = 1)
);

-- Um desafio pendente por alvo: re-emissão não cria paralelos
-- (NULLs não colidem — cada kind usa apenas sua própria coluna).
CREATE UNIQUE INDEX IF NOT EXISTS clara_consent_challenge_pending_batch_idx
    ON controllership_finance.clara_consent_challenge (batch_id)
    WHERE status = 'PENDING';

CREATE UNIQUE INDEX IF NOT EXISTS clara_consent_challenge_pending_proposal_idx
    ON controllership_finance.clara_consent_challenge (proposal_id)
    WHERE status = 'PENDING';

CREATE INDEX IF NOT EXISTS clara_consent_challenge_batch_idx
    ON controllership_finance.clara_consent_challenge (batch_id, created_at DESC);

CREATE INDEX IF NOT EXISTS clara_consent_challenge_proposal_idx
    ON controllership_finance.clara_consent_challenge
        (proposal_id, created_at DESC);

COMMIT;
