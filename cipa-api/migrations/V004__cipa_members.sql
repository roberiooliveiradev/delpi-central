BEGIN;

CREATE TABLE IF NOT EXISTS cipa.members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_code CHAR(2) NOT NULL CHECK (unit_code IN ('01', '02')),
    user_id UUID NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    role VARCHAR(40) NOT NULL
        CHECK (role IN (
            'president', 'vice_president', 'secretary',
            'titular_member', 'alternate_member'
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

-- Um usuário ativo por filial (sem soft-delete).
CREATE UNIQUE INDEX IF NOT EXISTS uq_cipa_members_active_user
    ON cipa.members (unit_code, user_id)
    WHERE deleted_at IS NULL AND is_active = TRUE;

-- Um ocupante ativo por cargo de liderança.
CREATE UNIQUE INDEX IF NOT EXISTS uq_cipa_members_active_leadership
    ON cipa.members (unit_code, role)
    WHERE deleted_at IS NULL
      AND is_active = TRUE
      AND role IN ('president', 'vice_president', 'secretary');

CREATE INDEX IF NOT EXISTS idx_cipa_members_unit_active
    ON cipa.members (unit_code, sort_order, display_name)
    WHERE deleted_at IS NULL AND is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_cipa_members_unit_mandate
    ON cipa.members (unit_code, mandate_start, mandate_end)
    WHERE deleted_at IS NULL;

COMMIT;
