CREATE SCHEMA IF NOT EXISTS customer_experience;

CREATE TABLE IF NOT EXISTS customer_experience.participants (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    public_token      TEXT NOT NULL UNIQUE,
    full_name         TEXT NOT NULL,
    company_name      TEXT NOT NULL,
    visit_date        DATE NOT NULL,
    participant_info  TEXT,
    photo_filename    TEXT,
    photo_mime        TEXT,
    qr_filename       TEXT,
    thank_you_message TEXT,
    view_count        INTEGER NOT NULL DEFAULT 0,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    created_by        TEXT,
    created_by_name   TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cx_participants_visit_date
    ON customer_experience.participants (visit_date DESC);

CREATE INDEX IF NOT EXISTS idx_cx_participants_company
    ON customer_experience.participants (company_name);
