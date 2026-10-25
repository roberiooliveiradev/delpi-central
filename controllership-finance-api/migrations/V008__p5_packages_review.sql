-- V008 — P5: recipient packages, PackageVersion, reviewer assignments,
-- decisions, clarifications, terminal rejection e notification outbox
-- (docs 12/37, contrato C2/P5-A..J/DEC-01..04).
--
-- Invariantes físicas:
-- - uma PackageVersion nunca é alterada após FINALIZED; correção cria
--   nova versão encadeada por previous_version_id (P5-09 / RQ-P5-09);
-- - aceites/rejeições são append-only — nenhum UPDATE/DELETE em
--   closing_review_decision (P5-B/G: aceite irreversível via UI e API);
-- - required_areas é snapshot JSONB congelado na submissão (P5-H);
-- - reatribuição desativa a linha anterior — substituto só age
--   futuramente; aceites passados preservam autoria (P5-F);
-- - notification outbox registra EMISSÃO do evento; entrega/ler é
--   capability Core Notifications (T02) — falha de e-mail nunca reverte
--   submissão (RQ-P5-07);
-- - recipient_area replica o CHECK do checklist (CONTABIL|FISCAL):
--   pacotes nascem por área destinataria com itens aplicáveis.

BEGIN;

CREATE TABLE IF NOT EXISTS controllership_finance.closing_package (
    package_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id   UUID NOT NULL
        REFERENCES controllership_finance.monthly_competence
            (competence_id) ON DELETE RESTRICT,
    recipient_area  VARCHAR(16) NOT NULL
        CHECK (recipient_area IN ('CONTABIL', 'FISCAL')),
    revision        INT NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by      UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (competence_id, recipient_area)
);

CREATE INDEX IF NOT EXISTS closing_package_competence_idx
    ON controllership_finance.closing_package (competence_id);

CREATE TABLE IF NOT EXISTS controllership_finance.closing_package_version (
    package_version_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id          UUID NOT NULL
        REFERENCES controllership_finance.closing_package (package_id)
            ON DELETE RESTRICT,
    version_no          INT NOT NULL CHECK (version_no >= 1),
    status              VARCHAR(16) NOT NULL
        CHECK (status IN ('DRAFT', 'FINALIZED', 'SUBMITTED')),
    -- snapshot imutável de composição: itens/versões de evidência
    -- validadas da área + resumo P3/P4 no instante da finalização.
    content             JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- áreas obrigatórias congeladas na submissão (P5-H).
    required_areas      JSONB,
    previous_version_id UUID
        REFERENCES controllership_finance.closing_package_version
            (package_version_id) ON DELETE RESTRICT,
    change_reason       TEXT,
    finalized_by        UUID,
    finalized_at        TIMESTAMPTZ,
    submitted_by        UUID,
    submitted_at        TIMESTAMPTZ,
    revision            INT NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by          UUID NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (package_id, version_no)
);

CREATE INDEX IF NOT EXISTS closing_package_version_pkg_idx
    ON controllership_finance.closing_package_version (package_id);

CREATE TABLE IF NOT EXISTS controllership_finance.closing_review_assignment (
    assignment_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id   UUID NOT NULL
        REFERENCES controllership_finance.monthly_competence
            (competence_id) ON DELETE RESTRICT,
    package_id      UUID
        REFERENCES controllership_finance.closing_package (package_id)
            ON DELETE RESTRICT,
    role            VARCHAR(16) NOT NULL
        CHECK (role IN ('REVIEWER', 'COORDINATOR')),
    area            VARCHAR(32),
    subject         UUID NOT NULL,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    assigned_by     UUID NOT NULL,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    deactivated_by  UUID,
    deactivated_at  TIMESTAMPTZ,
    deactivate_reason TEXT,
    -- REVIEWER sempre vinculado a pacote+área; COORDINATOR é da
    -- competência (rejeição terminal — DEC-01), sem pacote/área.
    CHECK (
        (role = 'REVIEWER' AND package_id IS NOT NULL
         AND area IS NOT NULL)
        OR (role = 'COORDINATOR' AND package_id IS NULL
            AND area IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS closing_review_assignment_pkg_idx
    ON controllership_finance.closing_review_assignment
        (package_id) WHERE active;

CREATE INDEX IF NOT EXISTS closing_review_assignment_subject_idx
    ON controllership_finance.closing_review_assignment
        (competence_id, subject) WHERE active;

CREATE TABLE IF NOT EXISTS controllership_finance.closing_review_decision (
    decision_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_version_id  UUID NOT NULL
        REFERENCES controllership_finance.closing_package_version
            (package_version_id) ON DELETE RESTRICT,
    area                VARCHAR(32) NOT NULL,
    outcome             VARCHAR(24) NOT NULL
        CHECK (outcome IN (
            'ACCEPTED', 'CHANGES_REQUESTED', 'REJECTED'
        )),
    actor_subject       UUID NOT NULL,
    note                TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS closing_review_decision_version_idx
    ON controllership_finance.closing_review_decision
        (package_version_id, area, created_at);

CREATE TABLE IF NOT EXISTS controllership_finance.closing_clarification (
    clarification_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_version_id  UUID NOT NULL
        REFERENCES controllership_finance.closing_package_version
            (package_version_id) ON DELETE RESTRICT,
    area                VARCHAR(32),
    state               VARCHAR(16) NOT NULL DEFAULT 'OPEN'
        CHECK (state IN ('OPEN', 'RESOLVED')),
    question            TEXT NOT NULL,
    response            TEXT,
    opened_by           UUID NOT NULL,
    opened_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_by         UUID,
    resolved_at         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS closing_clarification_version_idx
    ON controllership_finance.closing_clarification
        (package_version_id, state);

CREATE TABLE IF NOT EXISTS controllership_finance.closing_terminal_rejection (
    rejection_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id   UUID NOT NULL UNIQUE
        REFERENCES controllership_finance.monthly_competence
            (competence_id) ON DELETE RESTRICT,
    state           VARCHAR(16) NOT NULL DEFAULT 'ACTIVE'
        CHECK (state IN ('ACTIVE', 'REVERTED')),
    reason          TEXT NOT NULL,
    confirmed_by    UUID NOT NULL,
    confirmed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    reverted_by     UUID,
    reverted_at     TIMESTAMPTZ,
    revert_reason   TEXT
);

-- Outbox honesto: EMISSION registrada; entrega/canal pertencem a Core
-- Notifications (T02 TO_INVENTORY) — nunca evidência de estado de
-- negócio (RQ-P5-07).
CREATE TABLE IF NOT EXISTS controllership_finance.closing_notification_event (
    notification_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id       UUID NOT NULL
        REFERENCES controllership_finance.monthly_competence
            (competence_id) ON DELETE RESTRICT,
    event_type          VARCHAR(48) NOT NULL,
    recipient_subject   UUID NOT NULL,
    payload             JSONB NOT NULL DEFAULT '{}'::jsonb,
    delivery_state      VARCHAR(16) NOT NULL DEFAULT 'EMITTED'
        CHECK (delivery_state IN ('EMITTED', 'UNAVAILABLE')),
    emitted_by          UUID NOT NULL,
    emitted_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS closing_notification_recipient_idx
    ON controllership_finance.closing_notification_event
        (competence_id, recipient_subject);

COMMIT;
