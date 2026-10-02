-- DANFE anexado à solicitação de lançamento. Binário fica no volume persistente.
-- Schema: lancamento_notas_fiscais

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_danfe_attachments (
    request_id UUID PRIMARY KEY,
    document_id VARCHAR(24) NOT NULL,
    access_key VARCHAR(44) NOT NULL,
    stored_name VARCHAR(80) NOT NULL,
    original_name VARCHAR(80) NOT NULL,
    size_bytes INTEGER NOT NULL,
    content_type VARCHAR(40) NOT NULL DEFAULT 'application/pdf',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_lnf_danfe_request
        FOREIGN KEY (request_id)
        REFERENCES lancamento_notas_fiscais.invoice_posting_requests (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_lnf_danfe_document_id
        CHECK (document_id ~ '^[0-9a-f]{24}$'),

    CONSTRAINT ck_lnf_danfe_access_key
        CHECK (access_key ~ '^[0-9]{44}$'),

    CONSTRAINT ck_lnf_danfe_size
        CHECK (size_bytes > 0),

    CONSTRAINT ck_lnf_danfe_content_type
        CHECK (content_type = 'application/pdf')
);

COMMENT ON TABLE lancamento_notas_fiscais.invoice_posting_danfe_attachments IS
    'Metadado do DANFE PDF gravado no volume do lançamento. Um arquivo por solicitação.';
