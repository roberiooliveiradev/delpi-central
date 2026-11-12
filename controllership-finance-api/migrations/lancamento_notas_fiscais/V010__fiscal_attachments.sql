-- Anexos fiscais genéricos (XML de NFS-e). Não altera a tabela legada de DANFE.
-- Schema: lancamento_notas_fiscais

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_fiscal_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    document_type VARCHAR(8) NOT NULL,
    attachment_type VARCHAR(32) NOT NULL,
    provider_document_id VARCHAR(24) NOT NULL,
    provider_document_number VARCHAR(40) NOT NULL,
    provider_document_key VARCHAR(120),
    branch_code VARCHAR(2) NOT NULL,
    stored_name VARCHAR(120) NOT NULL,
    original_name VARCHAR(120) NOT NULL,
    content_type VARCHAR(80) NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_lnf_fiscal_attachment_request
        FOREIGN KEY (request_id)
        REFERENCES lancamento_notas_fiscais.invoice_posting_requests (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_lnf_fiscal_attachment_document_type
        CHECK (document_type IN ('nfe', 'nfse', 'cte')),

    CONSTRAINT ck_lnf_fiscal_attachment_type
        CHECK (attachment_type IN ('danfe', 'xml_original', 'xml_standard', 'dacte')),

    CONSTRAINT ck_lnf_fiscal_attachment_branch
        CHECK (branch_code IN ('01', '02')),

    CONSTRAINT ck_lnf_fiscal_attachment_document_id
        CHECK (provider_document_id ~ '^[0-9a-f]{24}$'),

    CONSTRAINT ck_lnf_fiscal_attachment_size
        CHECK (size_bytes > 0),

    CONSTRAINT uq_lnf_fiscal_attachment_request_type
        UNIQUE (request_id, attachment_type)
);

COMMENT ON TABLE lancamento_notas_fiscais.invoice_posting_fiscal_attachments IS
    'Metadado de anexos fiscais gravados no volume do lançamento. O DANFE legado permanece em invoice_posting_danfe_attachments.';
