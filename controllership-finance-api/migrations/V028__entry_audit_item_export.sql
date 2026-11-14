-- Comparativo item a item e notas com itens agrupados/desmembrados,
-- para as abas da skill que faltavam no export. Aditivo; V023–V027
-- permanecem.

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_item_comparison (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id     UUID        NOT NULL
        REFERENCES controllership_finance.entry_audit_run (id) ON DELETE CASCADE,
    payload    JSONB       NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS entry_audit_item_comparison_run_idx
    ON controllership_finance.entry_audit_item_comparison (run_id);

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_grouped_note (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id     UUID        NOT NULL
        REFERENCES controllership_finance.entry_audit_run (id) ON DELETE CASCADE,
    payload    JSONB       NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS entry_audit_grouped_note_run_idx
    ON controllership_finance.entry_audit_grouped_note (run_id);

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_excluded_item (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id     UUID        NOT NULL
        REFERENCES controllership_finance.entry_audit_run (id) ON DELETE CASCADE,
    payload    JSONB       NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS entry_audit_excluded_item_run_idx
    ON controllership_finance.entry_audit_excluded_item (run_id);
