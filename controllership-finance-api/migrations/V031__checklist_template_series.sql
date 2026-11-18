BEGIN;

-- CF-CHECKLIST-LIVE-004 — Série/sequência de checklist (RQ-07)
-- Uma série é uma geração de numeração de versões de um template.
-- A série legada (series_no=1) é criada retroativamente por template e
-- recebe todas as versões existentes — identidade e histórico intactos.

CREATE TABLE IF NOT EXISTS controllership_finance.checklist_template_series (
    series_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id     UUID         NOT NULL
        REFERENCES controllership_finance.checklist_template (template_id)
        ON DELETE RESTRICT,
    series_no       INT          NOT NULL CHECK (series_no >= 1),
    status          VARCHAR(10)  NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'CLOSED')),
    start_reason    TEXT         NOT NULL DEFAULT '',
    started_by      UUID         NOT NULL,
    started_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    closed_by       UUID,
    closed_at       TIMESTAMPTZ,
    idempotency_key VARCHAR(80)  UNIQUE,
    UNIQUE (template_id, series_no)
);

-- No máximo uma série ACTIVE por template.
CREATE UNIQUE INDEX IF NOT EXISTS ck_template_series_one_active
    ON controllership_finance.checklist_template_series (template_id)
    WHERE status = 'ACTIVE';

-- Backfill da série legada: uma série 1 por template existente.
-- started_by usa o created_by do template (autor registrado, não
-- identidade fabricada).
INSERT INTO controllership_finance.checklist_template_series
    (template_id, series_no, status, start_reason, started_by)
SELECT t.template_id, 1, 'ACTIVE',
       'legacy_backfill', t.created_by
  FROM controllership_finance.checklist_template t
 WHERE NOT EXISTS (
       SELECT 1
         FROM controllership_finance.checklist_template_series s
        WHERE s.template_id = t.template_id AND s.series_no = 1
 );

ALTER TABLE controllership_finance.checklist_template_version
    ADD COLUMN IF NOT EXISTS series_id UUID
        REFERENCES controllership_finance.checklist_template_series
        (series_id) ON DELETE RESTRICT;

UPDATE controllership_finance.checklist_template_version v
   SET series_id = s.series_id
  FROM controllership_finance.checklist_template_series s
 WHERE v.series_id IS NULL
   AND s.template_id = v.template_id
   AND s.series_no = 1;

ALTER TABLE controllership_finance.checklist_template_version
    ALTER COLUMN series_id SET NOT NULL;

-- Numeração reinicia por série: unicidade passa a (series_id, version).
ALTER TABLE controllership_finance.checklist_template_version
    DROP CONSTRAINT checklist_template_version_template_id_version_key;
ALTER TABLE controllership_finance.checklist_template_version
    ADD CONSTRAINT checklist_template_version_series_version_key
    UNIQUE (series_id, version);

-- Um único DRAFT/REVIEW aberto por série (a série legada preserva a
-- mesma proteção que o índice por template garantia).
DROP INDEX IF EXISTS controllership_finance.ck_template_version_one_open;
CREATE UNIQUE INDEX IF NOT EXISTS ck_template_version_one_open
    ON controllership_finance.checklist_template_version (series_id)
    WHERE status IN ('DRAFT', 'REVIEW');

COMMIT;
