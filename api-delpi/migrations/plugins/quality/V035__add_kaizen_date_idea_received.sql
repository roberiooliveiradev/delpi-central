-- Data em que a ideia de kaizen foi recebida/registrada (antes da implantação).

ALTER TABLE quality.kaizens
    ADD COLUMN IF NOT EXISTS date_idea_received DATE;

CREATE INDEX IF NOT EXISTS ix_quality_kaizens_date_idea_received
    ON quality.kaizens (date_idea_received)
    WHERE deleted_at IS NULL;
