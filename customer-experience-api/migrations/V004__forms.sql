-- Módulo Formulários (estilo Google Forms): formulários com perguntas
-- personalizáveis, respondidos publicamente por visitantes (nome + empresa).

CREATE TABLE IF NOT EXISTS customer_experience.forms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    public_token    TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    description     TEXT,
    qr_filename     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    response_count  INTEGER NOT NULL DEFAULT 0,
    created_by      TEXT,
    created_by_name TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tipos aceitos: rating, short_text, long_text, single_choice, multi_choice, yes_no
CREATE TABLE IF NOT EXISTS customer_experience.form_questions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id       UUID NOT NULL
        REFERENCES customer_experience.forms (id) ON DELETE CASCADE,
    position      INTEGER NOT NULL DEFAULT 0,
    question_type TEXT NOT NULL,
    label         TEXT NOT NULL,
    help_text     TEXT,
    is_required   BOOLEAN NOT NULL DEFAULT FALSE,
    options       JSONB,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cx_form_questions_form
    ON customer_experience.form_questions (form_id, position);

CREATE TABLE IF NOT EXISTS customer_experience.form_responses (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id            UUID NOT NULL
        REFERENCES customer_experience.forms (id) ON DELETE CASCADE,
    respondent_name    TEXT NOT NULL,
    respondent_company TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cx_form_responses_form
    ON customer_experience.form_responses (form_id, created_at DESC);

CREATE TABLE IF NOT EXISTS customer_experience.form_answers (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id    UUID NOT NULL
        REFERENCES customer_experience.form_responses (id) ON DELETE CASCADE,
    question_id    UUID NOT NULL
        REFERENCES customer_experience.form_questions (id) ON DELETE CASCADE,
    answer_text    TEXT,
    answer_rating  SMALLINT,
    answer_choices JSONB
);

CREATE INDEX IF NOT EXISTS idx_cx_form_answers_response
    ON customer_experience.form_answers (response_id);
CREATE INDEX IF NOT EXISTS idx_cx_form_answers_question
    ON customer_experience.form_answers (question_id);
