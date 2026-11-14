-- Customer satisfaction survey — first release (campaigns, recipients, responses).
-- Questionnaire catalog is versioned in application code; tables store the version id only.
-- Gated: applied only when COMMERCIAL_SATISFACTION_SURVEY_ENABLED is on (migration runner).

CREATE TABLE IF NOT EXISTS commercial.satisfaction_campaigns (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    TEXT NOT NULL,
    starts_at               TIMESTAMPTZ NOT NULL,
    ends_at                 TIMESTAMPTZ NOT NULL,
    questionnaire_version   TEXT NOT NULL,
    invite_subject          TEXT NOT NULL DEFAULT '',
    invite_body             TEXT NOT NULL DEFAULT '',
    created_by_user_id      TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version                 INT NOT NULL DEFAULT 1,
    CONSTRAINT satisfaction_campaigns_window_chk CHECK (starts_at < ends_at)
);

CREATE INDEX IF NOT EXISTS idx_satisfaction_campaigns_starts_at_desc
    ON commercial.satisfaction_campaigns (starts_at DESC);

CREATE TABLE IF NOT EXISTS commercial.satisfaction_recipients (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id             UUID NOT NULL
        REFERENCES commercial.satisfaction_campaigns (id) ON DELETE RESTRICT,
    customer_code           TEXT NOT NULL,
    customer_store          TEXT NOT NULL,
    customer_name_snapshot  TEXT,
    contact_name            TEXT,
    contact_email           TEXT,
    token_hash              TEXT NOT NULL,
    token_ciphertext        TEXT NOT NULL,
    created_by_user_id      TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version                 INT NOT NULL DEFAULT 1,
    CONSTRAINT satisfaction_recipients_campaign_customer_uq
        UNIQUE (campaign_id, customer_code, customer_store),
    CONSTRAINT satisfaction_recipients_token_hash_uq
        UNIQUE (token_hash)
);

CREATE INDEX IF NOT EXISTS idx_satisfaction_recipients_campaign
    ON commercial.satisfaction_recipients (campaign_id);

CREATE INDEX IF NOT EXISTS idx_satisfaction_recipients_token_hash
    ON commercial.satisfaction_recipients (token_hash);

CREATE TABLE IF NOT EXISTS commercial.satisfaction_responses (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id            UUID NOT NULL
        REFERENCES commercial.satisfaction_recipients (id) ON DELETE RESTRICT,
    overall_score           SMALLINT NOT NULL,
    recommendation_score    SMALLINT NOT NULL,
    dimensions              JSONB NOT NULL,
    strengths               TEXT,
    improvements            TEXT,
    unmet_needs             TEXT,
    questionnaire_version   TEXT NOT NULL,
    submitted_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT satisfaction_responses_recipient_uq UNIQUE (recipient_id),
    CONSTRAINT satisfaction_responses_overall_chk
        CHECK (overall_score BETWEEN 1 AND 5),
    CONSTRAINT satisfaction_responses_recommendation_chk
        CHECK (recommendation_score BETWEEN 0 AND 10)
);

CREATE INDEX IF NOT EXISTS idx_satisfaction_responses_submitted_at
    ON commercial.satisfaction_responses (submitted_at DESC);
