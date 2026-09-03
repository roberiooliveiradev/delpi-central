-- Hierarquia de áreas 5S (agregadora → subáreas; profundidade 1).
-- Writes de hierarquia restritos à filial 02 na API; coluna é genérica.

ALTER TABLE quality.audit_5s_areas
    ADD COLUMN IF NOT EXISTS parent_area_id UUID NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'fk_audit_5s_areas_parent'
    ) THEN
        ALTER TABLE quality.audit_5s_areas
            ADD CONSTRAINT fk_audit_5s_areas_parent
            FOREIGN KEY (parent_area_id)
            REFERENCES quality.audit_5s_areas (id)
            ON UPDATE RESTRICT
            ON DELETE RESTRICT;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'ck_audit_5s_areas_parent_not_self'
    ) THEN
        ALTER TABLE quality.audit_5s_areas
            ADD CONSTRAINT ck_audit_5s_areas_parent_not_self
            CHECK (parent_area_id IS DISTINCT FROM id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_audit_5s_areas_branch_parent
    ON quality.audit_5s_areas (branch_code, parent_area_id);
