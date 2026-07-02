-- Evidências do processo do kaizen (anexos, incl. registro Antes/Depois).
-- Metadado no Postgres + binário em volume persistente (KAIZEN_EVIDENCE_UPLOAD_DIR).

CREATE TABLE IF NOT EXISTS quality.kaizen_evidences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kaizen_id UUID NOT NULL,
    type VARCHAR(30) NOT NULL DEFAULT 'attachment',
    stage VARCHAR(20) NOT NULL DEFAULT 'geral',
    file_name VARCHAR(500),
    stored_name VARCHAR(200),
    mime_type VARCHAR(150),
    size_bytes BIGINT,
    description TEXT,
    external_url VARCHAR(1000),
    uploaded_by_user_id VARCHAR(100) NOT NULL,
    uploaded_by_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    CONSTRAINT fk_kaizen_evidences_kaizen
        FOREIGN KEY (kaizen_id)
        REFERENCES quality.kaizens (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_kaizen_evidences_type CHECK (
        type IN ('attachment', 'photo', 'document', 'link')
    ),

    CONSTRAINT ck_kaizen_evidences_stage CHECK (
        stage IN ('antes', 'depois', 'geral')
    )
);

CREATE INDEX IF NOT EXISTS ix_kaizen_evidences_kaizen
    ON quality.kaizen_evidences (kaizen_id)
    WHERE deleted_at IS NULL;
