-- Numeração diária MET-AAAAMMDD-NNN.
-- A data civil é America/Sao_Paulo em created_at, não o campo editável report_date.
-- Sequências acima de 999 abortam a migration; não há truncamento.
-- O contador anual permanece apenas como histórico e deixa de ser a fonte da numeração.

CREATE OR REPLACE FUNCTION engineering.metallographic_business_date(moment TIMESTAMPTZ)
RETURNS DATE
LANGUAGE sql
STABLE
AS $$
    SELECT (moment AT TIME ZONE 'America/Sao_Paulo')::date;
$$;

CREATE TABLE IF NOT EXISTS engineering.metallographic_report_day_counters (
    business_date DATE PRIMARY KEY,
    last_value INTEGER NOT NULL,
    CONSTRAINT ck_metallographic_report_day_counters_range
        CHECK (last_value >= 1 AND last_value <= 999)
);

CREATE TABLE IF NOT EXISTS engineering.metallographic_report_number_renames (
    report_id UUID PRIMARY KEY REFERENCES engineering.metallographic_reports (id),
    previous_number VARCHAR(32) NOT NULL,
    report_number VARCHAR(32) NOT NULL,
    migrated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
DECLARE
    overflow_days INTEGER;
BEGIN
    SELECT COUNT(*) INTO overflow_days
      FROM (
            SELECT 1
              FROM engineering.metallographic_reports
             GROUP BY engineering.metallographic_business_date(created_at)
            HAVING COUNT(*) > 999
           ) days;
    IF overflow_days > 0 THEN
        RAISE EXCEPTION 'metallographic daily sequence exceeds 999; renumber aborted';
    END IF;
END $$;

WITH ranked AS (
    SELECT
        id,
        report_number AS previous_number,
        'MET-' || to_char(engineering.metallographic_business_date(created_at), 'YYYYMMDD')
            || '-' || lpad(
                ROW_NUMBER() OVER (
                    PARTITION BY engineering.metallographic_business_date(created_at)
                    ORDER BY created_at, id
                )::text,
                3,
                '0'
            ) AS report_number
      FROM engineering.metallographic_reports
)
INSERT INTO engineering.metallographic_report_number_renames (
    report_id, previous_number, report_number
)
SELECT id, previous_number, report_number
  FROM ranked
 WHERE previous_number IS DISTINCT FROM report_number
ON CONFLICT (report_id) DO NOTHING;

WITH ranked AS (
    SELECT
        id,
        'MET-' || to_char(engineering.metallographic_business_date(created_at), 'YYYYMMDD')
            || '-' || lpad(
                ROW_NUMBER() OVER (
                    PARTITION BY engineering.metallographic_business_date(created_at)
                    ORDER BY created_at, id
                )::text,
                3,
                '0'
            ) AS report_number
      FROM engineering.metallographic_reports
)
UPDATE engineering.metallographic_reports AS reports
   SET report_number = ranked.report_number
  FROM ranked
 WHERE reports.id = ranked.id
   AND reports.report_number IS DISTINCT FROM ranked.report_number;

INSERT INTO engineering.metallographic_report_day_counters (business_date, last_value)
SELECT engineering.metallographic_business_date(created_at),
       MAX(CAST(substring(report_number FROM '[0-9]+$') AS INTEGER))
  FROM engineering.metallographic_reports
 GROUP BY engineering.metallographic_business_date(created_at)
ON CONFLICT (business_date) DO UPDATE
   SET last_value = GREATEST(
           engineering.metallographic_report_day_counters.last_value,
           EXCLUDED.last_value
       );

ALTER TABLE engineering.metallographic_reports
    DROP CONSTRAINT IF EXISTS ck_metallographic_reports_number_format;

ALTER TABLE engineering.metallographic_reports
    ADD CONSTRAINT ck_metallographic_reports_number_format
    CHECK (report_number ~ '^MET-[0-9]{8}-[0-9]{3}$');

COMMENT ON TABLE engineering.metallographic_report_counters IS
    'Histórico da numeração anual. A fonte vigente é metallographic_report_day_counters.';

COMMENT ON TABLE engineering.metallographic_report_day_counters IS
    'Último número reservado em cada dia civil de America/Sao_Paulo, inclusive relatórios excluídos.';

COMMENT ON TABLE engineering.metallographic_report_number_renames IS
    'Correspondência do número anual de teste para MET-AAAAMMDD-NNN. Não apaga relatório nem anexo.';
