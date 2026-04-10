BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.settings_change_request_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    change_request_id UUID NOT NULL,
    comment_text TEXT NOT NULL,

    created_by_user_id UUID NULL,
    created_by_email VARCHAR(255) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_si_change_request_comments_request
        FOREIGN KEY (change_request_id)
        REFERENCES strategic_indicators.settings_change_requests (id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_si_change_request_comments_request_id
    ON strategic_indicators.settings_change_request_comments (change_request_id);

CREATE INDEX IF NOT EXISTS idx_si_change_request_comments_created_at
    ON strategic_indicators.settings_change_request_comments (created_at ASC);

COMMENT ON TABLE strategic_indicators.settings_change_request_comments IS
'Comentários internos associados às solicitações administrativas do Strategic Indicators.';

COMMIT;