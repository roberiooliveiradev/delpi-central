CREATE TABLE IF NOT EXISTS quality.internal_nc_root_causes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    analysis_method VARCHAR(50),
    cause_dimension VARCHAR(100),
    category VARCHAR(100),
    why_level INTEGER,
    description TEXT NOT NULL,
    is_root_cause BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_internal_nc_root_causes_nonconformity
        FOREIGN KEY (nonconformity_id)
        REFERENCES quality.internal_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_internal_nc_root_causes_why_level
        CHECK (why_level IS NULL OR why_level BETWEEN 1 AND 10)
);