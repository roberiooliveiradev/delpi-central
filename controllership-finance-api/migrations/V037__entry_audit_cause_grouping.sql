-- T18/FA-4 — uma ocorrência por causa. Aditivo: colunas novas com
-- defaults que reproduzem o comportamento v1; V023–V036 permanecem.

ALTER TABLE controllership_finance.entry_audit_occurrence
    ADD COLUMN IF NOT EXISTS cause_id  TEXT  NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS items     JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS followers JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS entry_audit_occurrence_cause_idx
    ON controllership_finance.entry_audit_occurrence (analysis_id, cause_id);

-- Chave v2 calculada pela migração de status (comando explícito, FA-6);
-- a coluna v1 permanece a fonte até o comando rodar.
ALTER TABLE controllership_finance.entry_audit_status
    ADD COLUMN IF NOT EXISTS stable_key_v2 TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS entry_audit_status_v2_idx
    ON controllership_finance.entry_audit_status (stable_key_v2)
    WHERE stable_key_v2 <> '';
