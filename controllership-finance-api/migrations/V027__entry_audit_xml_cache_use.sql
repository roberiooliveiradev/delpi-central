-- Uso do cache de XML já criado na V023: última leitura e
-- cancelamento. A V023 não é reescrita. XML cancelado não é
-- servido como autorizado. A limpeza usa last_used_at.

ALTER TABLE controllership_finance.entry_audit_xml_cache
    ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS cancelled BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS entry_audit_xml_cache_last_used_idx
    ON controllership_finance.entry_audit_xml_cache (last_used_at);
