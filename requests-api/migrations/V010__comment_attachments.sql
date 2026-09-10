BEGIN;

CREATE TABLE IF NOT EXISTS my_requests.request_comment_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES my_requests.requests(id) ON DELETE CASCADE,
    comment_id UUID NOT NULL REFERENCES my_requests.request_comments(id) ON DELETE CASCADE,
    original_name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    mime_type VARCHAR(120) NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
    checksum_sha256 VARCHAR(64) NOT NULL,
    created_by_user_id VARCHAR(100) NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_request_comment_attachments_comment
    ON my_requests.request_comment_attachments (comment_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_request_comment_attachments_request
    ON my_requests.request_comment_attachments (request_id, created_at DESC);

COMMIT;
