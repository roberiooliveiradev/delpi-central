CREATE TABLE IF NOT EXISTS quality.external_nc_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID,
    action_id UUID,
    effectiveness_check_id UUID,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(150),
    size_bytes BIGINT NOT NULL,
    storage_provider VARCHAR(50) NOT NULL,
    storage_path TEXT NOT NULL,
    checksum VARCHAR(255),
    uploaded_by_user_id VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_external_nc_attachments_nonconformity
        FOREIGN KEY (nonconformity_id)
        REFERENCES quality.external_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_external_nc_attachments_action
        FOREIGN KEY (action_id)
        REFERENCES quality.external_nc_actions (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_external_nc_attachments_effectiveness_check
        FOREIGN KEY (effectiveness_check_id)
        REFERENCES quality.external_nc_effectiveness_checks (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_external_nc_attachments_size_bytes
        CHECK (size_bytes >= 0),

    CONSTRAINT ck_external_nc_attachments_target
        CHECK (
            nonconformity_id IS NOT NULL
            OR action_id IS NOT NULL
            OR effectiveness_check_id IS NOT NULL
        )
);