-- Guias e Procedimentos — mídias e anexos (V004)

CREATE TABLE IF NOT EXISTS guias_procedimentos.procedure_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    procedure_id UUID NOT NULL
        REFERENCES guias_procedimentos.procedures (id)
        ON DELETE RESTRICT,
    media_kind VARCHAR(32) NOT NULL,
    title VARCHAR(300) NOT NULL DEFAULT '',
    alt_text VARCHAR(500) NOT NULL DEFAULT '',
    original_filename VARCHAR(500),
    stored_name VARCHAR(200),
    mime_type VARCHAR(120),
    size_bytes BIGINT,
    storage_subdir VARCHAR(32),
    external_url TEXT,
    external_provider VARCHAR(40),
    order_index INTEGER NOT NULL DEFAULT 0,
    archived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_user_id VARCHAR(100),
    created_by_name VARCHAR(200),
    updated_by_user_id VARCHAR(100),
    updated_by_name VARCHAR(200),

    CONSTRAINT ck_guias_procedure_media_kind
        CHECK (media_kind IN ('image', 'video_file', 'video_external')),
    CONSTRAINT ck_guias_procedure_media_file_vs_external
        CHECK (
            (
                media_kind IN ('image', 'video_file')
                AND stored_name IS NOT NULL
                AND char_length(btrim(stored_name)) > 0
                AND mime_type IS NOT NULL
                AND size_bytes IS NOT NULL
                AND size_bytes > 0
                AND storage_subdir IS NOT NULL
                AND external_url IS NULL
                AND external_provider IS NULL
            )
            OR (
                media_kind = 'video_external'
                AND external_url IS NOT NULL
                AND char_length(btrim(external_url)) > 0
                AND external_provider IS NOT NULL
                AND stored_name IS NULL
                AND storage_subdir IS NULL
                AND size_bytes IS NULL
            )
        ),
    CONSTRAINT ck_guias_procedure_media_subdir
        CHECK (
            storage_subdir IS NULL
            OR storage_subdir IN ('images', 'videos')
        ),
    CONSTRAINT ck_guias_procedure_media_size
        CHECK (size_bytes IS NULL OR size_bytes > 0)
);

CREATE TABLE IF NOT EXISTS guias_procedimentos.procedure_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    procedure_id UUID NOT NULL
        REFERENCES guias_procedimentos.procedures (id)
        ON DELETE RESTRICT,
    title VARCHAR(300) NOT NULL DEFAULT '',
    original_filename VARCHAR(500) NOT NULL,
    stored_name VARCHAR(200) NOT NULL,
    mime_type VARCHAR(120) NOT NULL,
    size_bytes BIGINT NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 0,
    archived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_user_id VARCHAR(100),
    created_by_name VARCHAR(200),
    updated_by_user_id VARCHAR(100),
    updated_by_name VARCHAR(200),

    CONSTRAINT ck_guias_procedure_attachments_filename_not_blank
        CHECK (char_length(btrim(original_filename)) > 0),
    CONSTRAINT ck_guias_procedure_attachments_stored_not_blank
        CHECK (char_length(btrim(stored_name)) > 0),
    CONSTRAINT ck_guias_procedure_attachments_mime_not_blank
        CHECK (char_length(btrim(mime_type)) > 0),
    CONSTRAINT ck_guias_procedure_attachments_size
        CHECK (size_bytes > 0)
);

CREATE INDEX IF NOT EXISTS idx_guias_procedure_media_procedure_active
    ON guias_procedimentos.procedure_media (procedure_id, order_index, created_at)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_guias_procedure_attachments_procedure_active
    ON guias_procedimentos.procedure_attachments (procedure_id, order_index, created_at)
    WHERE archived_at IS NULL;
