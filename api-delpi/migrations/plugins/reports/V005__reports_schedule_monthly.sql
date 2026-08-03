-- Delpi Reports — agenda mensal (dia do mês)
-- Imutável após apply (checksum).

ALTER TABLE reports.report_schedules
    DROP CONSTRAINT IF EXISTS ck_reports_schedules_kind;

ALTER TABLE reports.report_schedules
    ADD CONSTRAINT ck_reports_schedules_kind
    CHECK (schedule_kind IN ('daily', 'weekly', 'weekdays', 'monthly'));

COMMENT ON CONSTRAINT ck_reports_schedules_kind ON reports.report_schedules IS
    'daily = todos os dias; weekly = um dia da semana; weekdays = seg–sex; monthly = dia do mês (cron DOM).';
