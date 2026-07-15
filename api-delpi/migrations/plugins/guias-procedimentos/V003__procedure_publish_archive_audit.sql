-- Guias e Procedimentos — auditoria de publicação e arquivamento (V003)

ALTER TABLE guias_procedimentos.procedures
    ADD COLUMN IF NOT EXISTS published_by_user_id VARCHAR(100);

ALTER TABLE guias_procedimentos.procedures
    ADD COLUMN IF NOT EXISTS published_by_name VARCHAR(200);

ALTER TABLE guias_procedimentos.procedures
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

ALTER TABLE guias_procedimentos.procedures
    ADD COLUMN IF NOT EXISTS archived_by_user_id VARCHAR(100);

ALTER TABLE guias_procedimentos.procedures
    ADD COLUMN IF NOT EXISTS archived_by_name VARCHAR(200);
