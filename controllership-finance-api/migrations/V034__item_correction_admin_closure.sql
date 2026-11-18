BEGIN;

-- CF-CHECKLIST-LIVE-004 — Encerramento administrativo de correções (RQ-11)
-- Novo estado terminal CLOSED_REQUIREMENT_RETIRED para encerramento por
-- retirada de catálogo; REJECTED permanece exclusivo de decisão humana.
-- VARCHAR(12) -> VARCHAR(32) (R6.1, doc 174 §3.2); zero reclassificação
-- de dados históricos.

ALTER TABLE controllership_finance.item_correction
    ALTER COLUMN status TYPE VARCHAR(32);

ALTER TABLE controllership_finance.item_correction
    DROP CONSTRAINT item_correction_status_check;
ALTER TABLE controllership_finance.item_correction
    ADD CONSTRAINT item_correction_status_check
    CHECK (status IN (
        'PENDING', 'APPROVED', 'REJECTED', 'CLOSED_REQUIREMENT_RETIRED'
    ));

ALTER TABLE controllership_finance.item_correction
    ADD COLUMN IF NOT EXISTS closure_reason VARCHAR(80),
    ADD COLUMN IF NOT EXISTS closed_by UUID,
    ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;

COMMIT;
