-- Índice para lookup reverso NF → CT-e (número + série da nota vinculada).
-- Schema: lancamento_notas_fiscais
-- Não altera V009; apenas acelera JOIN por document_match_key + series.

CREATE INDEX IF NOT EXISTS ix_lnf_linked_invoices_document_series
    ON lancamento_notas_fiscais.invoice_posting_linked_invoices (
        document_match_key,
        series
    );

COMMENT ON INDEX lancamento_notas_fiscais.ix_lnf_linked_invoices_document_series IS
    'Lookup reverso: solicitação NF-e/NFS-e → CT-e(s) que a vinculam.';
