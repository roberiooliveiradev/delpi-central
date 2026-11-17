BEGIN;

-- Idempotency keys for governed change-request writes (DAVI W013-ACT).
-- A retried create/comment carrying the same key returns the already
-- committed row instead of duplicating the record after a timeout.

ALTER TABLE strategic_indicators.settings_change_requests
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(120) NULL;

ALTER TABLE strategic_indicators.settings_change_request_comments
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(120) NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_si_cr_idempotency_key
    ON strategic_indicators.settings_change_requests (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_si_cr_comments_idempotency_key
    ON strategic_indicators.settings_change_request_comments (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

COMMENT ON COLUMN strategic_indicators.settings_change_requests.idempotency_key IS
'Chave de idempotência do chamador (ex.: proposal id DAVI); replay com a mesma chave retorna o registro existente.';

COMMENT ON COLUMN strategic_indicators.settings_change_request_comments.idempotency_key IS
'Chave de idempotência do chamador (ex.: proposal id DAVI); replay com a mesma chave retorna o comentário existente.';

COMMIT;
