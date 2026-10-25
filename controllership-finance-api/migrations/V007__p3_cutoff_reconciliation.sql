-- V007 — P3 cutoff humano governado, revalidação e conciliação (doc 10/15.1).
--
-- Aditiva. Regras canônicas preservadas:
--   - cutoff é confirmação humana única por competência (UNIQUE);
--   - readiness NUNCA é derivada só de valores zerados;
--   - divergência tolerada = exatamente R$ 0,00 (numeric(19,2));
--   - source indisponível permanece explícita — nunca vira zero;
--   - `closing_stock_state` só reflete estado canônico do owner quando
--     uma fonte real o sincronizar; linha ausente = UNAVAILABLE honesto,
--     nunca fallback manual silencioso (RQ-P3-08);
--   - nenhuma escrita TOTVS/ERP (RQ-P3-07).
-- Histórico via `closing_audit_event` (entity_type='closing_p3'/'closing_reconciliation').

CREATE TABLE IF NOT EXISTS controllership_finance.closing_cutoff (
    cutoff_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id   uuid NOT NULL UNIQUE
        REFERENCES controllership_finance.monthly_competence (competence_id),
    confirmed_by    text NOT NULL,
    confirmed_at    timestamptz NOT NULL DEFAULT now(),
    notes           text,
    revision        integer NOT NULL DEFAULT 1 CHECK (revision >= 1)
);

CREATE TABLE IF NOT EXISTS controllership_finance.closing_reconciliation (
    reconciliation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id   uuid NOT NULL
        REFERENCES controllership_finance.monthly_competence (competence_id),
    domain          text NOT NULL CHECK (domain IN (
                        'ENTRADAS_SAIDAS', 'P7', 'H02')),
    source_state    text NOT NULL DEFAULT 'UNAVAILABLE' CHECK (source_state IN (
                        'AVAILABLE', 'STALE', 'UNAVAILABLE',
                        'PARTIAL', 'ERROR')),
    expected_amount numeric(19, 2),
    reported_amount numeric(19, 2),
    fetched_at      timestamptz,
    rule_version    text,
    provenance      jsonb,
    input_fingerprint text,
    revision        integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (competence_id, domain)
);

CREATE TABLE IF NOT EXISTS controllership_finance.closing_revalidation (
    revalidation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id   uuid NOT NULL
        REFERENCES controllership_finance.monthly_competence (competence_id),
    validated_by    text NOT NULL,
    validated_at    timestamptz NOT NULL DEFAULT now(),
    result          text NOT NULL CHECK (result IN (
                        'VALID', 'STALE_INPUT')),
    input_fingerprint text NOT NULL,
    notes           text
);

CREATE INDEX IF NOT EXISTS closing_revalidation_competence_idx
    ON controllership_finance.closing_revalidation (competence_id, validated_at);

-- Estado canônico de fechamento do estoque conforme o owner.
-- Preenchido somente por sincronização com fonte autorizada (T03);
-- ausência de linha = estado indisponível (honesto).
CREATE TABLE IF NOT EXISTS controllership_finance.closing_stock_state (
    competence_id   uuid PRIMARY KEY
        REFERENCES controllership_finance.monthly_competence (competence_id),
    canonical_state text NOT NULL CHECK (canonical_state IN (
                        'OPEN', 'CLOSED')),
    source          text,
    fetched_at      timestamptz
);
