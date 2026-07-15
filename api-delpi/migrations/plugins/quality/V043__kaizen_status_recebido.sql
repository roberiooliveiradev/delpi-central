-- Renomeia status operacional em_andamento → recebido (sugestão pública / fila do gestor).

UPDATE quality.kaizens
   SET status = 'recebido'
 WHERE status = 'em_andamento';

UPDATE quality.kaizen_revisions
   SET version_status = 'recebido'
 WHERE version_status = 'em_andamento';

ALTER TABLE quality.kaizens
    ALTER COLUMN status SET DEFAULT 'recebido';

ALTER TABLE quality.kaizens
    DROP CONSTRAINT IF EXISTS ck_quality_kaizens_status;

ALTER TABLE quality.kaizens
    ADD CONSTRAINT ck_quality_kaizens_status CHECK (
        status IN (
            'recebido',
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
            'recebido',
            'aprovado',
            'implantado',
            'descontinuado',
            'cancelado',
            'substituido'
        )
    );
