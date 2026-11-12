-- Identificador da linha Questor (row.Id) necessário para baixar o XML da NF-e depois do cadastro.
-- Não guarda itens, XML nem snapshot da SA5. Schema: lancamento_notas_fiscais

ALTER TABLE lancamento_notas_fiscais.invoice_posting_danfe_attachments
    ADD COLUMN IF NOT EXISTS provider_entity_id VARCHAR(24);

ALTER TABLE lancamento_notas_fiscais.invoice_posting_danfe_attachments
    DROP CONSTRAINT IF EXISTS ck_lnf_danfe_provider_entity_id;

ALTER TABLE lancamento_notas_fiscais.invoice_posting_danfe_attachments
    ADD CONSTRAINT ck_lnf_danfe_provider_entity_id
    CHECK (provider_entity_id IS NULL OR provider_entity_id ~ '^[0-9a-f]{24}$');

COMMENT ON COLUMN lancamento_notas_fiscais.invoice_posting_danfe_attachments.provider_entity_id IS
    'row.Id do Questor (IdEntity do download de XML). Distinto de document_id, que continua sendo o XmlFilename do DANFE.';
