-- Delpi Reports Fase 4 — claim de agenda + trigger event
-- Não editar V001 (checksum imutável).

-- Uma agenda por definição (mantém a mais antiga em caso de duplicata).
DELETE FROM reports.report_schedules a
      USING reports.report_schedules b
 WHERE a.definition_id = b.definition_id
   AND a.created_at > b.created_at;

CREATE UNIQUE INDEX IF NOT EXISTS uq_reports_schedules_definition
    ON reports.report_schedules (definition_id);

ALTER TABLE reports.report_schedules
    ADD COLUMN IF NOT EXISTS last_claimed_at TIMESTAMPTZ;

ALTER TABLE reports.report_runs
    DROP CONSTRAINT IF EXISTS ck_reports_runs_trigger;

ALTER TABLE reports.report_runs
    ADD CONSTRAINT ck_reports_runs_trigger
    CHECK (trigger IN ('manual', 'schedule', 'event'));
