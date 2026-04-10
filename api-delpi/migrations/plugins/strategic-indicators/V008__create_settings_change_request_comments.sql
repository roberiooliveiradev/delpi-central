BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.settings_change_request_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    change_request_id UUID NOT NULL,
    comment_text TEXT NOT NULL,

    created_by_user_id UUID NULL,
    created_by_email VARCHAR(255) NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_si_settings_change_request_comments_request
        FOREIGN KEY (change_request_id)
        REFERENCES strategic_indicators.settings_change_requests (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_si_settings_change_request_comments_request_id
    ON strategic_indicators.settings_change_request_comments (change_request_id);

CREATE INDEX IF NOT EXISTS idx_si_settings_change_request_comments_created_at
    ON strategic_indicators.settings_change_request_comments (created_at DESC);

COMMENT ON TABLE strategic_indicators.settings_change_request_comments IS
'Comentários administrativos vinculados às solicitações de alteração do Strategic Indicators.';

COMMENT ON COLUMN strategic_indicators.settings_change_request_comments.comment_text IS
'Texto do comentário registrado no fluxo administrativo da solicitação.';

COMMIT;