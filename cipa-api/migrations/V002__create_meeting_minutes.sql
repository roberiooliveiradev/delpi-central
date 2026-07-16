BEGIN;

CREATE TABLE IF NOT EXISTS cipa.meeting_minutes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_code CHAR(2) NOT NULL CHECK (unit_code IN ('01', '02')),
    title VARCHAR(300) NOT NULL,
    minute_number VARCHAR(40) NOT NULL,
    meeting_type VARCHAR(40) NOT NULL DEFAULT 'ordinary'
        CHECK (meeting_type IN (
            'ordinary', 'extraordinary', 'installation', 'election', 'training', 'other'
        )),
    meeting_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    location VARCHAR(300),
    responsible_user_id UUID,
    responsible_name VARCHAR(200),
    president_name VARCHAR(200),
    secretary_name VARCHAR(200),
    status VARCHAR(40) NOT NULL DEFAULT 'draft'
        CHECK (status IN (
            'draft', 'in_review', 'awaiting_signatures', 'partially_signed',
            'signed', 'finalized', 'cancelled'
        )),
    current_version_id UUID,
    cancel_reason TEXT,
    submitted_for_signature_at TIMESTAMPTZ,
    finalized_at TIMESTAMPTZ,
    finalized_by_user_id UUID,
    cancelled_at TIMESTAMPTZ,
    cancelled_by_user_id UUID,
    final_pdf_path TEXT,
    final_content_hash VARCHAR(64),
    validation_code VARCHAR(64),
    created_by_user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_cipa_minutes_unit_number_active
    ON cipa.meeting_minutes (unit_code, minute_number)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_cipa_minutes_unit_status
    ON cipa.meeting_minutes (unit_code, status)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_cipa_minutes_unit_date
    ON cipa.meeting_minutes (unit_code, meeting_date DESC)
    WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS cipa.meeting_minute_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    minute_id UUID NOT NULL REFERENCES cipa.meeting_minutes(id) ON DELETE CASCADE,
    unit_code CHAR(2) NOT NULL,
    version_number INTEGER NOT NULL,
    title VARCHAR(300) NOT NULL,
    meeting_type VARCHAR(40) NOT NULL,
    meeting_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    location VARCHAR(300),
    agenda_html TEXT NOT NULL DEFAULT '',
    body_html TEXT NOT NULL DEFAULT '',
    decisions_html TEXT NOT NULL DEFAULT '',
    pending_html TEXT NOT NULL DEFAULT '',
    observations_html TEXT NOT NULL DEFAULT '',
    content_hash VARCHAR(64) NOT NULL,
    change_reason TEXT,
    created_by_user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (minute_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_cipa_versions_minute
    ON cipa.meeting_minute_versions (minute_id, version_number DESC);

CREATE TABLE IF NOT EXISTS cipa.meeting_minute_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    minute_id UUID NOT NULL REFERENCES cipa.meeting_minutes(id) ON DELETE CASCADE,
    unit_code CHAR(2) NOT NULL,
    user_id UUID,
    display_name VARCHAR(200) NOT NULL,
    role_in_meeting VARCHAR(40) NOT NULL DEFAULT 'other'
        CHECK (role_in_meeting IN (
            'president', 'vice_president', 'secretary', 'titular_member',
            'alternate_member', 'guest', 'action_owner', 'other'
        )),
    presence VARCHAR(20) NOT NULL DEFAULT 'present'
        CHECK (presence IN ('present', 'absent', 'justified')),
    is_external BOOLEAN NOT NULL DEFAULT FALSE,
    must_sign BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cipa_participants_minute
    ON cipa.meeting_minute_participants (minute_id, sort_order);

CREATE TABLE IF NOT EXISTS cipa.meeting_minute_signers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    minute_id UUID NOT NULL REFERENCES cipa.meeting_minutes(id) ON DELETE CASCADE,
    version_id UUID NOT NULL REFERENCES cipa.meeting_minute_versions(id) ON DELETE CASCADE,
    unit_code CHAR(2) NOT NULL,
    user_id UUID NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    sign_order INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending', 'viewed', 'signed', 'refused', 'invalidated', 'cancelled'
        )),
    viewed_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    refused_at TIMESTAMPTZ,
    refuse_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (version_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_cipa_signers_user_status
    ON cipa.meeting_minute_signers (user_id, status);

CREATE INDEX IF NOT EXISTS idx_cipa_signers_minute
    ON cipa.meeting_minute_signers (minute_id, version_id);

CREATE TABLE IF NOT EXISTS cipa.meeting_minute_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    minute_id UUID NOT NULL REFERENCES cipa.meeting_minutes(id) ON DELETE CASCADE,
    version_id UUID NOT NULL REFERENCES cipa.meeting_minute_versions(id) ON DELETE CASCADE,
    signer_id UUID NOT NULL REFERENCES cipa.meeting_minute_signers(id) ON DELETE CASCADE,
    unit_code CHAR(2) NOT NULL,
    user_id UUID NOT NULL,
    display_name_confirmed VARCHAR(200) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    image_path TEXT NOT NULL,
    terms_accepted BOOLEAN NOT NULL DEFAULT FALSE,
    client_ip VARCHAR(64),
    user_agent TEXT,
    session_id VARCHAR(128),
    idempotency_key VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (signer_id),
    UNIQUE (version_id, user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_cipa_signatures_idempotency
    ON cipa.meeting_minute_signatures (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS cipa.meeting_minute_action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    minute_id UUID NOT NULL REFERENCES cipa.meeting_minutes(id) ON DELETE CASCADE,
    unit_code CHAR(2) NOT NULL,
    title VARCHAR(400) NOT NULL,
    description TEXT,
    owner_user_id UUID,
    owner_name VARCHAR(200),
    due_date DATE,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal'
        CHECK (priority IN ('low', 'normal', 'high')),
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'done', 'cancelled')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cipa.meeting_minute_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    minute_id UUID NOT NULL REFERENCES cipa.meeting_minutes(id) ON DELETE CASCADE,
    unit_code CHAR(2) NOT NULL,
    file_name VARCHAR(300) NOT NULL,
    content_type VARCHAR(120) NOT NULL,
    size_bytes BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    uploaded_by_user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS cipa.meeting_minute_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    minute_id UUID REFERENCES cipa.meeting_minutes(id) ON DELETE SET NULL,
    unit_code CHAR(2) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id UUID,
    action VARCHAR(80) NOT NULL,
    actor_user_id UUID,
    before_data JSONB,
    after_data JSONB,
    client_ip VARCHAR(64),
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cipa_audit_minute
    ON cipa.meeting_minute_audit_logs (minute_id, created_at DESC);

CREATE TABLE IF NOT EXISTS cipa.meeting_minute_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    minute_id UUID NOT NULL REFERENCES cipa.meeting_minutes(id) ON DELETE CASCADE,
    unit_code CHAR(2) NOT NULL,
    version_id UUID REFERENCES cipa.meeting_minute_versions(id) ON DELETE SET NULL,
    author_user_id UUID NOT NULL,
    author_name VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

ALTER TABLE cipa.meeting_minutes
    DROP CONSTRAINT IF EXISTS fk_cipa_minutes_current_version;

ALTER TABLE cipa.meeting_minutes
    ADD CONSTRAINT fk_cipa_minutes_current_version
    FOREIGN KEY (current_version_id)
    REFERENCES cipa.meeting_minute_versions(id)
    DEFERRABLE INITIALLY DEFERRED;

COMMIT;
