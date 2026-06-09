ALTER TABLE quality.audit_5s_nonconformities
    ADD COLUMN IF NOT EXISTS root_cause TEXT,
    ADD COLUMN IF NOT EXISTS corrective_action TEXT,
    ADD COLUMN IF NOT EXISTS priority VARCHAR(20);

ALTER TABLE quality.audit_5s_nonconformities
    DROP CONSTRAINT IF EXISTS ck_audit_5s_nc_priority;

ALTER TABLE quality.audit_5s_nonconformities
    ADD CONSTRAINT ck_audit_5s_nc_priority
    CHECK (priority IS NULL OR priority IN ('high', 'medium', 'low'));
