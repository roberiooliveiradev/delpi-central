-- PRC-REF-023 — metadado de documentos opcionais de apoio técnico.
-- Bytes ficam no storage governado (volume dedicado); aqui apenas o
-- vínculo request ↔ attachment, estado e auditoria. Sem storage_key
-- exposto em API; coluna mantida privada para o adapter.

CREATE TABLE IF NOT EXISTS engineering.product_registration_attachments (
    id uuid PRIMARY KEY,
    request_id uuid NOT NULL
        REFERENCES engineering.product_registration_requests (id),
    original_file_name text NOT NULL,
    media_type text NOT NULL,
    size_bytes bigint NOT NULL CHECK (size_bytes > 0),
    sha256 text NOT NULL,
    storage_key text NOT NULL,
    state text NOT NULL DEFAULT 'PENDING_SCAN',
    uploaded_by_subject text NOT NULL,
    uploaded_by_display_name text,
    uploaded_by_email text,
    correlation_id text,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT prc_attachment_state_check CHECK (
        state IN ('PENDING_SCAN','AVAILABLE','REJECTED','QUARANTINED','DELETED')
    )
);

CREATE INDEX IF NOT EXISTS prc_attachments_request_idx
    ON engineering.product_registration_attachments (request_id);

CREATE INDEX IF NOT EXISTS prc_attachments_dedup_idx
    ON engineering.product_registration_attachments
        (request_id, sha256, original_file_name);

COMMENT ON TABLE engineering.product_registration_attachments IS
    'PRC-REF-023: metadado/estado de documentos de apoio do caso; bytes no storage dedicado.';
