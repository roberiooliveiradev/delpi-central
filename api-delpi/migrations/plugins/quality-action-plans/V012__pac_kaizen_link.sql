-- Onda 7.2 — vínculo opcional plano PAC ↔ kaizen PostgreSQL

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS linked_kaizen_id UUID;

ALTER TABLE quality.quality_action_plans
    DROP CONSTRAINT IF EXISTS fk_quality_action_plans_linked_kaizen;

ALTER TABLE quality.quality_action_plans
    ADD CONSTRAINT fk_quality_action_plans_linked_kaizen
        FOREIGN KEY (linked_kaizen_id)
        REFERENCES quality.kaizens (id)
        ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_linked_kaizen
    ON quality.quality_action_plans (linked_kaizen_id)
    WHERE deleted_at IS NULL AND linked_kaizen_id IS NOT NULL;

COMMENT ON COLUMN quality.quality_action_plans.linked_kaizen_id IS
    'Kaizen operacional vinculado ao fechamento do ciclo de melhoria (Onda 7.2).';
