CREATE TABLE IF NOT EXISTS customer_experience.feedback (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id UUID NOT NULL
        REFERENCES customer_experience.participants (id) ON DELETE CASCADE,
    rating         SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    liked_most     TEXT,
    suggestions    TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cx_feedback_participant UNIQUE (participant_id)
);

CREATE INDEX IF NOT EXISTS idx_cx_feedback_participant
    ON customer_experience.feedback (participant_id);
