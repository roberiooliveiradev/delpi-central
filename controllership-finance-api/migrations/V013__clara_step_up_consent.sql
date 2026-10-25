-- V013 — CLARA step-up consent (CF-PROC0072-FULL-IMPLEMENTATION-RELEASE-001).
--
-- Consentimento verificável por superfície confiável: a proposta
-- governed single-op registra consent_record produzido SOMENTE pela
-- rota BFF /clara-proposals/{id}/consent, que exige token Keycloak
-- emitido DEPOIS do PREPARE (iat > created_at) — credencial que o
-- canal MCP não consegue fabricar porque o refresh token vive na
-- sessão do Portal, não no access token do assistente.
--
-- clara_batch já possui consent_record/consent_mode (V012); aqui só
-- a proposta ganha as colunas equivalentes. Não destrutiva.

BEGIN;

ALTER TABLE controllership_finance.clara_proposal
    ADD COLUMN IF NOT EXISTS consent_record JSONB NOT NULL
        DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS consented_at TIMESTAMPTZ;

-- Consentimento não pode coexistir com claim/consumo — invariante
-- defensiva: uma vez CLAIMED/consumed, nenhum consentimento novo.
CREATE INDEX IF NOT EXISTS clara_proposal_pending_consent_idx
    ON controllership_finance.clara_proposal (actor_sub, created_at DESC)
    WHERE consented_at IS NULL
      AND claimed_at IS NULL
      AND consumed_at IS NULL;

COMMIT;
