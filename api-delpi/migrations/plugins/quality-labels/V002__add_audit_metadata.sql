-- Snapshot auditável de OP/produto (estrutura, roteiro, inspeção TOTVS) no registro.
ALTER TABLE quality_labels.inspection_labels
    ADD COLUMN IF NOT EXISTS audit_metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_quality_labels_audit_metadata_gin
    ON quality_labels.inspection_labels USING gin (audit_metadata);
