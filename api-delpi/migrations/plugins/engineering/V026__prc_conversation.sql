-- PRC-CONVERSATION — conversa governada do caso (Issue #207, task
-- EVA-PRC-CONVERSATION-P0-P1). Comentários e anexos da conversa vivem
-- no schema engineering (owner Engineering API) — nunca nas tabelas
-- do My Requests. Autor = principal autenticado (snapshot de nome);
-- storage_key privado, nunca exposto em DTO.

CREATE TABLE IF NOT EXISTS engineering.product_registration_comments (
    id uuid PRIMARY KEY,
    request_id uuid NOT NULL
        REFERENCES engineering.product_registration_requests (id),
    author_subject text NOT NULL,
    author_display_name text,
    body text NOT NULL,
    row_version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT prc_comment_body_nonempty CHECK (length(btrim(body)) > 0)
);

CREATE INDEX IF NOT EXISTS prc_comments_request_chrono_idx
    ON engineering.product_registration_comments (request_id, created_at, id);

COMMENT ON TABLE engineering.product_registration_comments IS
    'PRC-CONVERSATION: mensagens da conversa do caso; autor é snapshot do principal — identidade nunca vem do payload.';

CREATE TABLE IF NOT EXISTS engineering.product_registration_comment_attachments (
    id uuid PRIMARY KEY,
    request_id uuid NOT NULL
        REFERENCES engineering.product_registration_requests (id),
    comment_id uuid NOT NULL
        REFERENCES engineering.product_registration_comments (id),
    original_file_name text NOT NULL,
    media_type text NOT NULL,
    size_bytes bigint NOT NULL CHECK (size_bytes > 0),
    sha256 text NOT NULL,
    storage_key text NOT NULL,
    state text NOT NULL DEFAULT 'AVAILABLE',
    uploaded_by_subject text NOT NULL,
    uploaded_by_display_name text,
    uploaded_by_email text,
    correlation_id text,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT prc_comment_attachment_state_check CHECK (
        state IN ('PENDING_SCAN','AVAILABLE','REJECTED','QUARANTINED','DELETED')
    )
);

CREATE INDEX IF NOT EXISTS prc_comment_attachments_comment_idx
    ON engineering.product_registration_comment_attachments (comment_id);

CREATE INDEX IF NOT EXISTS prc_comment_attachments_request_idx
    ON engineering.product_registration_comment_attachments (request_id);

CREATE INDEX IF NOT EXISTS prc_comment_attachments_dedup_idx
    ON engineering.product_registration_comment_attachments
        (comment_id, sha256, original_file_name);

COMMENT ON TABLE engineering.product_registration_comment_attachments IS
    'PRC-CONVERSATION: metadado/estado de anexos da conversa; bytes no storage dedicado (mesmo volume PRC).';
