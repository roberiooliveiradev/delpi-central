BEGIN;

CREATE TABLE IF NOT EXISTS my_requests.request_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(80) NOT NULL DEFAULT 'general',
    icon VARCHAR(80) NOT NULL DEFAULT 'file-text',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    version INT NOT NULL DEFAULT 1,
    presentation_mode VARCHAR(20) NOT NULL
        CHECK (presentation_mode IN ('schema_driven', 'specialized')),
    branch_scope VARCHAR(20) NOT NULL DEFAULT 'optional'
        CHECK (branch_scope IN ('required', 'optional', 'none')),
    form_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    ui_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    workflow_definition JSONB NOT NULL,
    destination_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    permission_prefix VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE SEQUENCE IF NOT EXISTS my_requests.request_number_seq;

CREATE TABLE IF NOT EXISTS my_requests.requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_number VARCHAR(32) NOT NULL UNIQUE,
    request_type_id UUID NOT NULL REFERENCES my_requests.request_types(id),
    status VARCHAR(40) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal'
        CHECK (priority IN ('normal', 'high', 'urgent')),
    branch_code VARCHAR(2),
    created_by_user_id VARCHAR(100) NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    return_reason TEXT,
    cancel_justification TEXT,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_requests_type_status_created
    ON my_requests.requests (request_type_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_requests_created_by
    ON my_requests.requests (created_by_user_id);

CREATE INDEX IF NOT EXISTS ix_requests_branch_status
    ON my_requests.requests (branch_code, status)
    WHERE branch_code IS NOT NULL;

CREATE TABLE IF NOT EXISTS my_requests.request_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES my_requests.requests(id) ON DELETE CASCADE,
    from_status VARCHAR(40),
    to_status VARCHAR(40) NOT NULL,
    action VARCHAR(80) NOT NULL,
    actor_user_id VARCHAR(100) NOT NULL,
    actor_name VARCHAR(200) NOT NULL,
    justification TEXT,
    changes JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_request_status_history_request_created
    ON my_requests.request_status_history (request_id, created_at DESC);

CREATE TABLE IF NOT EXISTS my_requests.request_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES my_requests.requests(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('processor', 'queue')),
    assignee_user_id VARCHAR(100),
    queue_code VARCHAR(80),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    released_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_request_assignments_request_active
    ON my_requests.request_assignments (request_id)
    WHERE released_at IS NULL;

CREATE TABLE IF NOT EXISTS my_requests.request_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES my_requests.requests(id) ON DELETE CASCADE,
    author_user_id VARCHAR(100) NOT NULL,
    author_name VARCHAR(200) NOT NULL,
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_request_comments_request_created
    ON my_requests.request_comments (request_id, created_at DESC);

COMMIT;
