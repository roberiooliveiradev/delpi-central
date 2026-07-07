-- Layout avançado de formulários: páginas, imagens e modo passo a passo.

ALTER TABLE customer_experience.forms
    ADD COLUMN IF NOT EXISTS one_question_per_page BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS background_image_filename TEXT;

CREATE TABLE IF NOT EXISTS customer_experience.form_pages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id         UUID NOT NULL
        REFERENCES customer_experience.forms (id) ON DELETE CASCADE,
    position        INTEGER NOT NULL DEFAULT 0,
    title           TEXT,
    background_image_filename TEXT,
    point_image_filename      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cx_form_pages_form
    ON customer_experience.form_pages (form_id, position);

ALTER TABLE customer_experience.form_questions
    ADD COLUMN IF NOT EXISTS page_id UUID
        REFERENCES customer_experience.form_pages (id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS point_image_filename TEXT;
