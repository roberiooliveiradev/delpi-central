-- #1585. Canal de acoes Windows controlado, com fila curta, resposta e auditoria.
-- Registros sao persistentes para rastreabilidade, sem payloads ou comandos arbitrarios.
CREATE TABLE it_portal.host_service_actions (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL,
    server_id UUID NOT NULL,
    service_key VARCHAR(200) NOT NULL,
    service_name VARCHAR(200) NOT NULL,
    action VARCHAR(8) NOT NULL CHECK (action IN ('start', 'stop', 'restart')),
    state_before VARCHAR(24) NOT NULL,
    status VARCHAR(12) NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'timeout')),
    state_after VARCHAR(24),
    error_code VARCHAR(64),
    lease_sha256 CHAR(64),
    claimed_by VARCHAR(100),
    requested_by_id UUID NOT NULL,
    requested_by_name VARCHAR(200) NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    claimed_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    CONSTRAINT host_service_actions_server_fk FOREIGN KEY (server_id)
        REFERENCES it_portal.servers (id) ON DELETE RESTRICT,
    CONSTRAINT host_service_actions_service_fk FOREIGN KEY (server_id, service_key)
        REFERENCES it_portal.host_services (server_id, service_key) ON DELETE RESTRICT,
    CONSTRAINT host_service_actions_request_unique UNIQUE (server_id, requested_by_id, request_id)
);

-- Nao permite duas acoes simultaneas no mesmo servico, nem mesmo por usuarios diferentes.
CREATE UNIQUE INDEX host_service_actions_single_active_idx
    ON it_portal.host_service_actions (server_id, service_key)
    WHERE status IN ('queued', 'running');
CREATE INDEX host_service_actions_claim_idx
    ON it_portal.host_service_actions (server_id, requested_at)
    WHERE status='queued';
CREATE INDEX host_service_actions_recent_idx
    ON it_portal.host_service_actions (server_id, requested_at DESC);

ALTER TABLE it_portal.audit_events DROP CONSTRAINT audit_events_entity_type_chk;
ALTER TABLE it_portal.audit_events ADD CONSTRAINT audit_events_entity_type_chk CHECK (
    entity_type IN (
        'server', 'server_note', 'action_plan',
        'service', 'service_hosting', 'database_instance', 'database_consumer',
        'network', 'server_network_link', 'integration', 'service_dependency',
        'host_service_preference', 'host_service_action'
    )
);
