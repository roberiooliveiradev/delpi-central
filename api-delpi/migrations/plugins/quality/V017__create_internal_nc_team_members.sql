CREATE TABLE IF NOT EXISTS quality.internal_nc_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    role_in_case VARCHAR(100) NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_internal_nc_team_members_nonconformity
        FOREIGN KEY (nonconformity_id)
        REFERENCES quality.internal_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT uq_internal_nc_team_member_unique
        UNIQUE (nonconformity_id, user_id, role_in_case)
);