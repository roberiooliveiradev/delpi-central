-- Lançamento de Notas Fiscais — CT-e (frete) e notas vinculadas.
-- Não altera V007; a constraint de modelo é recriada aqui.

ALTER TABLE lancamento_notas_fiscais.invoice_posting_requests
    DROP CONSTRAINT IF EXISTS ck_lnf_requests_fiscal_model;

ALTER TABLE lancamento_notas_fiscais.invoice_posting_requests
    ADD CONSTRAINT ck_lnf_requests_fiscal_model
    CHECK (fiscal_model IS NULL OR fiscal_model IN ('nfe', 'nfse', 'cte'));

COMMENT ON COLUMN lancamento_notas_fiscais.invoice_posting_requests.fiscal_model IS
    'Modelo da nota na solicitação: nfe (NF-e), nfse (NFS-e) ou cte (CT-e / frete).';

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_linked_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL
        REFERENCES lancamento_notas_fiscais.invoice_posting_requests(id) ON DELETE CASCADE,
    document_number VARCHAR(9) NOT NULL,
    document_match_key VARCHAR(9) NOT NULL,
    series VARCHAR(3) NOT NULL,
    position INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE lancamento_notas_fiscais.invoice_posting_linked_invoices IS
    'Notas amarradas a uma solicitação de CT-e. Vazio nos demais tipos.';

CREATE UNIQUE INDEX IF NOT EXISTS uq_lnf_linked_invoices_request_document
    ON lancamento_notas_fiscais.invoice_posting_linked_invoices (
        request_id,
        document_match_key,
        series
    );

CREATE INDEX IF NOT EXISTS ix_lnf_linked_invoices_request_id
    ON lancamento_notas_fiscais.invoice_posting_linked_invoices (request_id, position);
