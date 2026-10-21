-- Integration execution tracking — api-delpi owned Protheus write audit.
-- Owner: api-delpi (postgres-plugins, schema integration_tracking).
-- Records the lifecycle of logical write operations forwarded to upstream
-- integrations (TOTVS Protheus REST). Never stores secrets; payloads are
-- sanitized JSONB with a documented redaction policy.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS integration_tracking;

CREATE TABLE IF NOT EXISTS integration_tracking.integration_operations (
    operation_id UUID PRIMARY KEY,
    correlation_id VARCHAR(120),
    request_id VARCHAR(120),
    idempotency_key VARCHAR(200),
    schema_version INTEGER NOT NULL DEFAULT 1,
    integration VARCHAR(60) NOT NULL,
    resource VARCHAR(60) NOT NULL,
    action VARCHAR(20) NOT NULL,
    resource_key VARCHAR(60),
    environment_key VARCHAR(120),
    company_scope VARCHAR(40),
    caller_app VARCHAR(120),
    actor_subject VARCHAR(120),
    protheus_user_id VARCHAR(20),
    authorization_context VARCHAR(300),
    request_payload JSONB,
    outbound_payload JSONB,
    response_payload JSONB,
    request_hash CHAR(64),
    outbound_hash CHAR(64),
    payload_schema_version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(30) NOT NULL,
    http_status INTEGER,
    upstream_error_code VARCHAR(120),
    error_details JSONB,
    confirmation_evidence JSONB,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    send_started_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT integration_operations_status_chk CHECK (
        status IN (
            'CREATED',
            'SENDING',
            'ACKNOWLEDGED',
            'CONFIRMED',
            'REJECTED',
            'FAILED_PRE_SEND',
            'UNKNOWN',
            'RECONCILIATION_REQUIRED'
        )
    ),
    CONSTRAINT integration_operations_action_chk CHECK (
        action IN ('create', 'update', 'delete', 'post')
    ),
    CONSTRAINT integration_operations_attempt_count_chk CHECK (attempt_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_integration_operations_status
    ON integration_tracking.integration_operations (status);

CREATE INDEX IF NOT EXISTS idx_integration_operations_caller_actor
    ON integration_tracking.integration_operations (caller_app, actor_subject);

CREATE INDEX IF NOT EXISTS idx_integration_operations_resource
    ON integration_tracking.integration_operations (integration, resource, action);

CREATE INDEX IF NOT EXISTS idx_integration_operations_correlation
    ON integration_tracking.integration_operations (correlation_id);

CREATE INDEX IF NOT EXISTS idx_integration_operations_created_at
    ON integration_tracking.integration_operations (created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_integration_operations_idem_key
    ON integration_tracking.integration_operations (caller_app, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS integration_tracking.integration_operation_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id UUID NOT NULL,
    sequence_number INTEGER NOT NULL,
    event_type VARCHAR(60) NOT NULL,
    status_from VARCHAR(30),
    status_to VARCHAR(30),
    event_data JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id VARCHAR(120),
    CONSTRAINT fk_integration_operation_events_operation
        FOREIGN KEY (operation_id)
        REFERENCES integration_tracking.integration_operations (operation_id)
        ON DELETE RESTRICT,
    CONSTRAINT uq_integration_operation_events_seq
        UNIQUE (operation_id, sequence_number)
);

CREATE INDEX IF NOT EXISTS idx_integration_operation_events_op
    ON integration_tracking.integration_operation_events (operation_id, sequence_number);
