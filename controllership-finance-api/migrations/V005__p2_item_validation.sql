-- V005 — P2 validação humana, N/A, item excepcional e correção estrutural
--
-- RQ-P2-02..RQ-P2-12 (doc 09 §Validação/N-A/Item excepcional/Correção):
--
--   * `competence_checklist_item` ganha `validation_scope`
--     (PER_ATTACHMENT | WHOLE_SET), `exceptional` (item só da
--     competência — nunca altera template), `revision` (OCC) e
--     `state_reason` (justificativa de N/A e cancelamento). Estados de
--     completude: EXPECTED → ACCEPTED | NOT_APPLICABLE | CANCELLED —
--     `CANCELLED != DELETED != NOT_APPLICABLE`; rejeição de evidência
--     NÃO vira estado do item (REPLACEMENT_REQUIRED é derivação).
--   * `checklist_template_item` ganha `validation_scope` para a
--     administração P6 propagar ao snapshot na abertura.
--   * `evidence_decision` é append-only: cada decisão
--     (ACCEPTED/REJECTED/REVERSED) é um fato imutável; o estado
--     corrente é o último registro. REJECTED exige `reason_code` do
--     catálogo canônico (`OTHER` exige comentário); REVERSED exige
--     justificativa + `result_state` + a decisão revertida — a mesma
--     validação nunca é reescrita nem apagada.
--   * `item_correction` implementa ACCESS REQUEST → MANAGE REVIEW →
--     APPROVE/REJECT (RQ-P2-09): aprovação cria nova `revision` do
--     item preservando histórico; revisão sobre revisão obsoleta é
--     `stale_revision`.

BEGIN;

ALTER TABLE controllership_finance.checklist_template_item
    ADD COLUMN validation_scope VARCHAR(14) NOT NULL DEFAULT 'PER_ATTACHMENT'
        CHECK (validation_scope IN ('PER_ATTACHMENT', 'WHOLE_SET'));

ALTER TABLE controllership_finance.competence_checklist_item
    DROP CONSTRAINT competence_checklist_item_state_check,
    ADD CONSTRAINT competence_checklist_item_state_check
        CHECK (state IN (
            'EXPECTED', 'ACCEPTED', 'NOT_APPLICABLE', 'CANCELLED'
        )),
    ADD COLUMN validation_scope VARCHAR(14) NOT NULL DEFAULT 'PER_ATTACHMENT'
        CHECK (validation_scope IN ('PER_ATTACHMENT', 'WHOLE_SET')),
    ADD COLUMN exceptional  BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN revision     INT     NOT NULL DEFAULT 1 CHECK (revision >= 1),
    ADD COLUMN state_reason TEXT,
    -- RQ-P2-07: item excepcional não tem origem de template — a
    -- proveniência NOT NULL só se aplica a itens do snapshot.
    ALTER COLUMN source_template_item_id DROP NOT NULL,
    ALTER COLUMN source_version_id DROP NOT NULL,
    ADD CONSTRAINT competence_checklist_item_provenance_check
        CHECK (
            (exceptional AND source_template_item_id IS NULL
             AND source_version_id IS NULL)
            OR (NOT exceptional AND source_template_item_id IS NOT NULL
                AND source_version_id IS NOT NULL)
        );

CREATE TABLE IF NOT EXISTS controllership_finance.evidence_decision (
    decision_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id       UUID         NOT NULL
        REFERENCES controllership_finance.monthly_competence (competence_id)
        ON DELETE RESTRICT,
    snapshot_item_id    UUID
        REFERENCES controllership_finance.competence_checklist_item
            (snapshot_item_id) ON DELETE RESTRICT,
    document_id         UUID
        REFERENCES controllership_finance.closing_document (document_id)
        ON DELETE RESTRICT,
    document_version_id UUID
        REFERENCES controllership_finance.document_version
            (document_version_id) ON DELETE RESTRICT,
    scope               VARCHAR(14)  NOT NULL
        CHECK (scope IN ('PER_ATTACHMENT', 'WHOLE_SET')),
    composition         JSONB        NOT NULL DEFAULT '[]'::jsonb,
    decision            VARCHAR(16)  NOT NULL
        CHECK (decision IN ('ACCEPTED', 'REJECTED', 'REVERSED')),
    reason_code         VARCHAR(40)
        CHECK (reason_code IS NULL OR reason_code IN (
            'WRONG_COMPETENCE', 'INCOMPLETE', 'ILLEGIBLE',
            'DIVERGENT', 'WRONG_DOCUMENT', 'OTHER'
        )),
    comment             TEXT,
    result_state        VARCHAR(16)
        CHECK (result_state IS NULL
               OR result_state IN ('UNDER_REVIEW', 'ACCEPTED')),
    reverses_decision_id UUID
        REFERENCES controllership_finance.evidence_decision (decision_id)
        ON DELETE RESTRICT,
    decided_by          UUID         NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CHECK (decision <> 'REJECTED' OR reason_code IS NOT NULL),
    CHECK (reason_code IS NULL OR reason_code <> 'OTHER'
           OR NULLIF(BTRIM(comment), '') IS NOT NULL),
    CHECK (decision <> 'REVERSED' OR (
        result_state IS NOT NULL
        AND reverses_decision_id IS NOT NULL
        AND NULLIF(BTRIM(comment), '') IS NOT NULL
    ))
);

CREATE INDEX IF NOT EXISTS evidence_decision_document_idx
    ON controllership_finance.evidence_decision (document_id);
CREATE INDEX IF NOT EXISTS evidence_decision_item_idx
    ON controllership_finance.evidence_decision (snapshot_item_id);
CREATE INDEX IF NOT EXISTS evidence_decision_version_idx
    ON controllership_finance.evidence_decision (document_version_id);

CREATE TABLE IF NOT EXISTS controllership_finance.item_correction (
    correction_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id   UUID         NOT NULL
        REFERENCES controllership_finance.monthly_competence (competence_id)
        ON DELETE RESTRICT,
    snapshot_item_id UUID        NOT NULL
        REFERENCES controllership_finance.competence_checklist_item
            (snapshot_item_id) ON DELETE RESTRICT,
    item_revision   INT          NOT NULL,
    changes         JSONB        NOT NULL,
    justification   TEXT         NOT NULL,
    status          VARCHAR(12)  NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    requested_by    UUID         NOT NULL,
    requested_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    reviewed_by     UUID,
    reviewed_at     TIMESTAMPTZ,
    review_reason   TEXT
);

CREATE INDEX IF NOT EXISTS item_correction_item_idx
    ON controllership_finance.item_correction (snapshot_item_id);

COMMIT;
