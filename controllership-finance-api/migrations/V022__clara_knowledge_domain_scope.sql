-- V022 — CLARA F7-R4: domínio de knowledge (controllership | LNF).
-- Corpus já publicado permanece controllership via DEFAULT.
-- Não reescreve itens; só adiciona coluna filtrável.

BEGIN;

ALTER TABLE controllership_finance.clara_knowledge_item
    ADD COLUMN IF NOT EXISTS domain_scope TEXT NOT NULL DEFAULT 'controllership';

ALTER TABLE controllership_finance.clara_knowledge_item
    DROP CONSTRAINT IF EXISTS clara_knowledge_item_domain_scope_check;

ALTER TABLE controllership_finance.clara_knowledge_item
    ADD CONSTRAINT clara_knowledge_item_domain_scope_check
    CHECK (domain_scope IN (
        'controllership',
        'lancamento-notas-fiscais'
    ));

CREATE INDEX IF NOT EXISTS clara_knowledge_item_domain_scope_idx
    ON controllership_finance.clara_knowledge_item (domain_scope, status);

COMMIT;
