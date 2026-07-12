CREATE INDEX IF NOT EXISTS idx_audit_5s_nc_audit_status_due
    ON quality.audit_5s_nonconformities (audit_id, status, due_date);
