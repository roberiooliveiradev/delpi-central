-- One-shot human confirmation challenges for Windows service control (MCP + API).
-- Does not enable control by itself; IT_PORTAL_WINDOWS_CONTROL_* flags remain required.
CREATE TABLE it_portal.host_service_confirmations (
    id UUID PRIMARY KEY,
    requester_subject UUID NOT NULL,
    server_id UUID NOT NULL,
    service_key VARCHAR(200) NOT NULL,
    service_name VARCHAR(200) NOT NULL,
    action VARCHAR(8) NOT NULL CHECK (action IN ('start', 'stop', 'restart')),
    state_before VARCHAR(24) NOT NULL,
    request_id UUID NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT host_service_confirmations_server_fk FOREIGN KEY (server_id)
        REFERENCES it_portal.servers (id) ON DELETE RESTRICT,
    CONSTRAINT host_service_confirmations_service_fk FOREIGN KEY (server_id, service_key)
        REFERENCES it_portal.host_services (server_id, service_key) ON DELETE RESTRICT,
    CONSTRAINT host_service_confirmations_ttl CHECK (expires_at > created_at),
    CONSTRAINT host_service_confirmations_consumed CHECK (
        consumed_at IS NULL OR consumed_at >= created_at
    )
);

CREATE INDEX host_service_confirmations_active_idx
    ON it_portal.host_service_confirmations (requester_subject, server_id, expires_at)
    WHERE consumed_at IS NULL;

ALTER TABLE it_portal.audit_events DROP CONSTRAINT audit_events_entity_type_chk;
ALTER TABLE it_portal.audit_events ADD CONSTRAINT audit_events_entity_type_chk CHECK (
    entity_type IN (
        'server', 'server_note', 'action_plan',
        'service', 'service_hosting', 'database_instance', 'database_consumer',
        'network', 'server_network_link', 'integration', 'service_dependency',
        'host_service_preference', 'host_service_action', 'workstation',
        'host_service_confirmation'
    )
);
