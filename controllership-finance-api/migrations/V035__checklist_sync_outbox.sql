BEGIN;

-- CF-CHECKLIST-LIVE-004 — Outbox durável da sincronização (RQ-03/12)
-- Mesma forma canônica de closing_notification_event + dispatcher
-- SKIP LOCKED (doc 176 §4.7/§7). Evento conclui apenas quando todo run
-- está terminal E o read-back de convergência confirma (converged_at).

CREATE TABLE IF NOT EXISTS controllership_finance.checklist_sync_event (
    event_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_id      UUID         NOT NULL
        REFERENCES controllership_finance.checklist_version_revision
        (revision_id) ON DELETE RESTRICT,
    state            VARCHAR(10)  NOT NULL DEFAULT 'EMITTED'
        CHECK (state IN ('EMITTED','DISPATCHED','FAILED')),
    completion_state VARCHAR(26)
        CHECK (completion_state IS NULL OR completion_state IN (
            'CONVERGED','CONVERGED_WITH_EXCLUSIONS','INCOMPLETE')),
    converged_at     TIMESTAMPTZ,
    attempts         INT          NOT NULL DEFAULT 0,
    last_error       TEXT,
    emitted_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ck_sync_event_state_idx
    ON controllership_finance.checklist_sync_event (state)
    WHERE converged_at IS NULL;

CREATE TABLE IF NOT EXISTS controllership_finance.checklist_sync_run (
    run_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id      UUID         NOT NULL
        REFERENCES controllership_finance.checklist_sync_event
        (event_id) ON DELETE RESTRICT,
    competence_id UUID         NOT NULL
        REFERENCES controllership_finance.monthly_competence
        (competence_id) ON DELETE RESTRICT,
    revision_id   UUID         NOT NULL
        REFERENCES controllership_finance.checklist_version_revision
        (revision_id) ON DELETE RESTRICT,
    state         VARCHAR(24)  NOT NULL DEFAULT 'PENDING'
        CHECK (state IN ('PENDING','APPLYING','APPLIED',
                         'APPLIED_WITH_EXCLUSIONS','SKIPPED',
                         'PARTIAL','FAILED')),
    attempts      INT          NOT NULL DEFAULT 0,
    skip_reason   VARCHAR(40),
    exclusions    JSONB        NOT NULL DEFAULT '[]'::jsonb,
    last_error    TEXT,
    started_at    TIMESTAMPTZ,
    finished_at   TIMESTAMPTZ,
    UNIQUE (revision_id, competence_id)
);

CREATE INDEX IF NOT EXISTS ck_sync_run_event_idx
    ON controllership_finance.checklist_sync_run (event_id);
CREATE INDEX IF NOT EXISTS ck_sync_run_competence_idx
    ON controllership_finance.checklist_sync_run (competence_id);

COMMIT;
