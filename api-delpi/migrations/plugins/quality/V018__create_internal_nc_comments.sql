CREATE TABLE IF NOT EXISTS quality.internal_nc_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    comment_type VARCHAR(50) NOT NULL DEFAULT 'general',
    content TEXT NOT NULL,
    is_internal BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_internal_nc_comments_nonconformity
        FOREIGN KEY (nonconformity_id)
        REFERENCES quality.internal_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);