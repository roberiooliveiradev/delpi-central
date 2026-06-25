-- Vínculo opcional entre evidência e ação do plano (contenção/corretiva/etc.)

ALTER TABLE quality.quality_problem_evidences
    ADD COLUMN IF NOT EXISTS action_id UUID NULL;

ALTER TABLE quality.quality_problem_evidences
    DROP CONSTRAINT IF EXISTS fk_quality_problem_evidences_action;

ALTER TABLE quality.quality_problem_evidences
    ADD CONSTRAINT fk_quality_problem_evidences_action
        FOREIGN KEY (action_id)
        REFERENCES quality.quality_actions (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_quality_problem_evidences_action
    ON quality.quality_problem_evidences (action_id)
    WHERE action_id IS NOT NULL;

COMMENT ON COLUMN quality.quality_problem_evidences.action_id IS
    'Ação do plano vinculada à evidência (opcional).';
