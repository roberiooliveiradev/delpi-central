-- Lançamento de Notas Fiscais — modelo da nota informado na solicitação.
-- NULL permanece só nas solicitações anteriores a esta coluna.

ALTER TABLE lancamento_notas_fiscais.invoice_posting_requests
    ADD COLUMN IF NOT EXISTS fiscal_model VARCHAR(8);

ALTER TABLE lancamento_notas_fiscais.invoice_posting_requests
    DROP CONSTRAINT IF EXISTS ck_lnf_requests_fiscal_model;

ALTER TABLE lancamento_notas_fiscais.invoice_posting_requests
    ADD CONSTRAINT ck_lnf_requests_fiscal_model
    CHECK (fiscal_model IS NULL OR fiscal_model IN ('nfe', 'nfse'));

COMMENT ON COLUMN lancamento_notas_fiscais.invoice_posting_requests.fiscal_model IS
    'Modelo da nota na solicitação: nfe (NF-e) ou nfse (NFS-e).';
