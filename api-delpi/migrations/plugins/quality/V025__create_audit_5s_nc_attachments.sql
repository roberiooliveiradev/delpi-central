CREATE TABLE IF NOT EXISTS quality.audit_5s_nc_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    attachment_type VARCHAR(20) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(120),
    size_bytes BIGINT NOT NULL DEFAULT 0,
    uploaded_by_user_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_audit_5s_nc_attachments_nc
        FOREIGN KEY (nonconformity_id)
        REFERENCES quality.audit_5s_nonconformities (id)
        ON DELETE CASCADE,
    CONSTRAINT ck_audit_5s_nc_attachment_type
        CHECK (attachment_type IN ('before', 'after')),
    CONSTRAINT uq_audit_5s_nc_attachment_slot
        UNIQUE (nonconformity_id, attachment_type)
);

CREATE INDEX IF NOT EXISTS idx_audit_5s_nc_attachments_nc_id
    ON quality.audit_5s_nc_attachments (nonconformity_id);
