BEGIN;

CREATE TABLE IF NOT EXISTS comite_etica.members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    role VARCHAR(40) NOT NULL
        CHECK (role IN (
            'president', 'secretary', 'member', 'guest'
        )),
    mandate_start DATE NOT NULL,
    mandate_end DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_by_user_id UUID NOT NULL,
    updated_by_user_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CHECK (mandate_end IS NULL OR mandate_end >= mandate_start)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_cec_members_active_user
    ON comite_etica.members (user_id)
    WHERE deleted_at IS NULL AND is_active = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_cec_members_active_leadership
    ON comite_etica.members (role)
    WHERE deleted_at IS NULL
      AND is_active = TRUE
      AND role IN ('president', 'secretary');

CREATE INDEX IF NOT EXISTS idx_cec_members_active
    ON comite_etica.members (sort_order, display_name)
    WHERE deleted_at IS NULL AND is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_cec_members_mandate
    ON comite_etica.members (mandate_start, mandate_end)
    WHERE deleted_at IS NULL;

COMMIT;
