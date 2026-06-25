-- Onda 7.3 — vínculo opcional plano PAC ↔ NC origem Auditoria 5S

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS linked_audit_5s_nc_id UUID;

ALTER TABLE quality.quality_action_plans
    DROP CONSTRAINT IF EXISTS fk_quality_action_plans_linked_audit_5s_nc;

ALTER TABLE quality.quality_action_plans
    ADD CONSTRAINT fk_quality_action_plans_linked_audit_5s_nc
        FOREIGN KEY (linked_audit_5s_nc_id)
        REFERENCES quality.audit_5s_nonconformities (id)
        ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_linked_audit_5s_nc
    ON quality.quality_action_plans (linked_audit_5s_nc_id)
    WHERE deleted_at IS NULL AND linked_audit_5s_nc_id IS NOT NULL;

COMMENT ON COLUMN quality.quality_action_plans.linked_audit_5s_nc_id IS
    'NC de Auditoria 5S que originou ou está associada ao plano PAC (Onda 7.3).';
