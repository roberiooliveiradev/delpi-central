BEGIN;

-- CF-CHECKLIST-LIVE-004 — Revisões internas da versão publicada (RQ-08/09)
-- Cabeçalho + changes (Modelo A, doc 176 §4.2): histórico append-only,
-- reversão por revisão compensatória (reverts_revision_id na NOVA
-- revisão; a revisão alvo nunca é atualizada).

CREATE TABLE IF NOT EXISTS controllership_finance.checklist_version_revision (
    revision_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id           UUID         NOT NULL
        REFERENCES controllership_finance.checklist_template_version
        (version_id) ON DELETE RESTRICT,
    revision_no          INT          NOT NULL CHECK (revision_no >= 1),
    fingerprint          VARCHAR(64)  NOT NULL,
    reason               TEXT         NOT NULL,
    idempotency_key      VARCHAR(80)  NOT NULL UNIQUE,
    reverts_revision_id  UUID
        REFERENCES controllership_finance.checklist_version_revision
        (revision_id) ON DELETE RESTRICT,
    created_by           UUID         NOT NULL,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (version_id, revision_no)
);

CREATE TABLE IF NOT EXISTS controllership_finance.checklist_version_revision_change (
    change_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_id  UUID         NOT NULL
        REFERENCES controllership_finance.checklist_version_revision
        (revision_id) ON DELETE RESTRICT,
    seq          INT          NOT NULL,
    item_key     VARCHAR(32)  NOT NULL,
    op           VARCHAR(10)  NOT NULL
        CHECK (op IN ('ADD','UPDATE','RETIRE','REORDER','REACTIVATE')),
    before_state JSONB,
    after_state  JSONB,
    UNIQUE (revision_id, seq)
);

CREATE INDEX IF NOT EXISTS ck_revision_change_revision_idx
    ON controllership_finance.checklist_version_revision_change
    (revision_id);

-- Retirada lógica dos itens do catálogo (tombstone — nunca DELETE).
ALTER TABLE controllership_finance.checklist_template_item
    ADD COLUMN IF NOT EXISTS item_state VARCHAR(10)
        NOT NULL DEFAULT 'ACTIVE'
        CHECK (item_state IN ('ACTIVE','RETIRED')),
    ADD COLUMN IF NOT EXISTS retired_revision_id UUID
        REFERENCES controllership_finance.checklist_version_revision
        (revision_id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS retired_by UUID,
    ADD COLUMN IF NOT EXISTS retired_at TIMESTAMPTZ;

-- Proveniência tipada do cancelamento no snapshot (RQ-05): autoridade
-- exclusiva para comprovar retirada por catálogo e autorizar reativação.
ALTER TABLE controllership_finance.competence_checklist_item
    ADD COLUMN IF NOT EXISTS cancel_origin VARCHAR(14)
        CHECK (cancel_origin IS NULL
               OR cancel_origin IN ('MANUAL','CATALOG_RETIRE')),
    ADD COLUMN IF NOT EXISTS cancelled_revision_id UUID
        REFERENCES controllership_finance.checklist_version_revision
        (revision_id) ON DELETE RESTRICT;

COMMIT;
