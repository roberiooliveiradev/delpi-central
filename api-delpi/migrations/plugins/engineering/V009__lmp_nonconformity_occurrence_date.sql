-- Data de ocorrência da NC (= quando o problema foi encontrado).
-- Distinto de registered_at (timestamp de entrada no sistema Delpi).

ALTER TABLE engineering.lmp_nonconformities
    ADD COLUMN IF NOT EXISTS occurrence_date DATE;

UPDATE engineering.lmp_nonconformities
   SET occurrence_date = registered_at::date
 WHERE occurrence_date IS NULL;

ALTER TABLE engineering.lmp_nonconformities
    ALTER COLUMN occurrence_date SET DEFAULT CURRENT_DATE;

ALTER TABLE engineering.lmp_nonconformities
    ALTER COLUMN occurrence_date SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_occurrence_date
    ON engineering.lmp_nonconformities (occurrence_date DESC);

COMMENT ON COLUMN engineering.lmp_nonconformities.occurrence_date IS
    'Data em que o problema foi encontrado (ocorrência da NC).';
COMMENT ON COLUMN engineering.lmp_nonconformities.registered_at IS
    'Data/hora de entrada do registro no sistema Delpi (auditoria).';
