-- V006 — P4 classificações e pendências (Pacote B, doc 104/11/23).
--
-- Aditiva: nenhuma tabela/coluna existente é alterada.
-- Estados canônicos fechados (RQ-P4-03) — nenhum estado livre.
-- Sugestão (determinística/IA) é só recomendação: campos `suggested_*`
-- nunca promovem decisão; `confirmed_classification` exige ator humano.
-- Histórico via `closing_audit_event` (entity_type='closing_pendency')
-- com os eventos canônicos PENDENCY_* / CLASSIFICATION_*.

CREATE TABLE IF NOT EXISTS controllership_finance.closing_pendency (
    pendency_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id      uuid NOT NULL
        REFERENCES controllership_finance.monthly_competence (competence_id),
    snapshot_item_id   uuid
        REFERENCES controllership_finance.competence_checklist_item (snapshot_item_id),
    kind               text NOT NULL CHECK (kind IN (
                           'MISSING_EVIDENCE',
                           'VALIDATION_REJECTED',
                           'RECONCILIATION_DIVERGENCE',
                           'STRUCTURAL_CORRECTION',
                           'EXTERNAL_DEPENDENCY',
                           'OTHER')),
    title              text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 255),
    description        text,
    state              text NOT NULL DEFAULT 'OPEN' CHECK (state IN (
                           'OPEN',
                           'IN_ANALYSIS',
                           'WAITING_EXTERNAL',
                           'RESOLVED',
                           'DISMISSED')),
    queue              text,
    responsible_subject text,
    branch_scope       text NOT NULL DEFAULT 'BOTH' CHECK (branch_scope IN (
                           'MATRIX', 'BRANCH', 'BOTH')),
    suggested_classification   text,
    suggestion_rationale       text,
    suggestion_source          text CHECK (suggestion_source IN (
                                   'DETERMINISTIC', 'AI', 'MANUAL')),
    confirmed_classification   text,
    classification_reason      text,
    resolution_notes           text,
    dismiss_justification      text,
    revision           integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by         text NOT NULL,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS closing_pendency_competence_idx
    ON controllership_finance.closing_pendency (competence_id, state);

CREATE INDEX IF NOT EXISTS closing_pendency_item_idx
    ON controllership_finance.closing_pendency (snapshot_item_id)
    WHERE snapshot_item_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS closing_pendency_responsible_idx
    ON controllership_finance.closing_pendency (responsible_subject)
    WHERE state IN ('OPEN', 'IN_ANALYSIS', 'WAITING_EXTERNAL');
