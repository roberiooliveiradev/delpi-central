-- Status admin: auditoria encerrada sem tratar NCs em aberto

ALTER TABLE quality.audit_5s_audits
    DROP CONSTRAINT IF EXISTS ck_audit_5s_audits_status;

ALTER TABLE quality.audit_5s_audits
    ADD CONSTRAINT ck_audit_5s_audits_status CHECK (
        status IN (
            'draft',
            'evaluation_complete',
            'nc_in_progress',
            'closed',
            'closed_without_nc_treatment'
        )
    );
