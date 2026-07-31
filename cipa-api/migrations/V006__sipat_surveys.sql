BEGIN;

CREATE TABLE IF NOT EXISTS cipa.sipat_surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_code CHAR(2) NOT NULL
        CHECK (unit_code IN ('01', '02')),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'published', 'closed')),
    public_token TEXT UNIQUE,
    qr_filename TEXT,
    opens_at TIMESTAMPTZ,
    closes_at TIMESTAMPTZ,
    response_count INTEGER NOT NULL DEFAULT 0,
    created_by_user_id UUID,
    updated_by_user_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CHECK (closes_at IS NULL OR opens_at IS NULL OR closes_at >= opens_at)
);

CREATE INDEX IF NOT EXISTS idx_cipa_sipat_surveys_unit
    ON cipa.sipat_surveys (unit_code, status, created_at DESC)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_cipa_sipat_surveys_token
    ON cipa.sipat_surveys (public_token)
    WHERE public_token IS NOT NULL AND deleted_at IS NULL;

-- Tipos: single_choice, multi_choice, likert_5, yes_no, text_short, text_long
CREATE TABLE IF NOT EXISTS cipa.sipat_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID NOT NULL
        REFERENCES cipa.sipat_surveys (id) ON DELETE CASCADE,
    position INTEGER NOT NULL DEFAULT 0,
    question_type VARCHAR(40) NOT NULL,
    label TEXT NOT NULL,
    help_text TEXT,
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    options JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cipa_sipat_questions_survey
    ON cipa.sipat_questions (survey_id, position);

CREATE TABLE IF NOT EXISTS cipa.sipat_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID NOT NULL
        REFERENCES cipa.sipat_surveys (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cipa_sipat_responses_survey
    ON cipa.sipat_responses (survey_id, created_at DESC);

CREATE TABLE IF NOT EXISTS cipa.sipat_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL
        REFERENCES cipa.sipat_responses (id) ON DELETE CASCADE,
    question_id UUID NOT NULL
        REFERENCES cipa.sipat_questions (id) ON DELETE CASCADE,
    value_text TEXT,
    value_json JSONB,
    UNIQUE (response_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_cipa_sipat_answers_response
    ON cipa.sipat_answers (response_id);
CREATE INDEX IF NOT EXISTS idx_cipa_sipat_answers_question
    ON cipa.sipat_answers (question_id);

COMMIT;
