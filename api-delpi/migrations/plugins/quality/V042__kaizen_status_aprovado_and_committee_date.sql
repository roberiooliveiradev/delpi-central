-- Status "aprovado" (comitê) + data de aprovação no comitê.
-- Quantidade mensal passa a incluir aprovado; ganhos financeiros seguem só com implantado.

ALTER TABLE quality.kaizens
    ADD COLUMN IF NOT EXISTS date_committee_approved DATE;

CREATE INDEX IF NOT EXISTS ix_quality_kaizens_date_committee_approved
    ON quality.kaizens (date_committee_approved)
    WHERE deleted_at IS NULL;

ALTER TABLE quality.kaizens
    DROP CONSTRAINT IF EXISTS ck_quality_kaizens_status;

ALTER TABLE quality.kaizens
    ADD CONSTRAINT ck_quality_kaizens_status CHECK (
        status IN (
            'em_andamento',
            'aprovado',
            'implantado',
            'descontinuado',
            'cancelado'
        )
    );

ALTER TABLE quality.kaizen_revisions
    DROP CONSTRAINT IF EXISTS ck_kaizen_revision_version_status;

ALTER TABLE quality.kaizen_revisions
    ADD CONSTRAINT ck_kaizen_revision_version_status CHECK (
        version_status IN (
            'em_andamento',
            'aprovado',
            'implantado',
            'descontinuado',
            'cancelado',
            'substituido'
        )
    );
