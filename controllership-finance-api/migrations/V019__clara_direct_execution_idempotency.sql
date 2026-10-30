-- V019 — CLARA-MCP-SEMANTIC-002: execução direta por risco (doc 124)
--
-- Decisões de contrato (owner: controllership-finance-api):
--   * `idempotency_key` dedicada em clara_proposal: operations marcadas
--     DIRECT_ALLOWED executam PREPARE→CLAIM→ACT em uma única chamada,
--     sem consentimento — a proteção de repetição passa a ser uma
--     constraint física, não apenas semântica.
--   * Parcial e aditiva: índice único somente sobre linhas com key —
--     propostas governadas legadas (key NULL) não são afetadas e nenhum
--     dado existente muda de semântica.
--   * Mesma key + mesma capability + mesmo ator ⇒ replay do resultado
--     verificado; mesma key com conteúdo divergente é impossível porque
--     a key canônica deriva do próprio plano.
--
-- Reversível por drop da constraint/coluna; execução por
-- run_migrations_on_startup (mesmo gate das V011+).

BEGIN;

ALTER TABLE controllership_finance.clara_proposal
    ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS clara_proposal_idempotency_ux
    ON controllership_finance.clara_proposal
        (actor_sub, capability, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

COMMIT;
