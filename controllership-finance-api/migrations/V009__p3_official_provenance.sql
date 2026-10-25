-- V009 — P3: distingue conciliação DECLARED (valor informado pelo
-- operador) de OFFICIAL (comprovada por artefato oficial anexado e
-- validado na competência). Controle pendente do Pacote B: conclusão
-- mensal não pode depender somente de disponibilidade declarada.

BEGIN;

ALTER TABLE controllership_finance.closing_reconciliation
    ADD COLUMN provenance_kind VARCHAR(12) NOT NULL DEFAULT 'DECLARED'
        CHECK (provenance_kind IN ('DECLARED', 'OFFICIAL')),
    ADD COLUMN official_document_id UUID
        REFERENCES controllership_finance.closing_document (document_id)
            ON DELETE RESTRICT,
    ADD CONSTRAINT closing_reconciliation_official_doc_check
        CHECK (
            provenance_kind = 'DECLARED'
            OR official_document_id IS NOT NULL
        );

COMMIT;
