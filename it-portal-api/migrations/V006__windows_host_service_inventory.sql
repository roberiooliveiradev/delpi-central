-- #1576/P1: inventário Windows SCM, separado do cadastro de aplicações.
-- Não armazena binários, comandos, caminhos, contas de execução ou credenciais.
CREATE TABLE it_portal.host_service_runs (
    run_id UUID PRIMARY KEY,
    server_id UUID NOT NULL REFERENCES it_portal.servers(id),
    collector_client_id VARCHAR(120) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    batch_count SMALLINT NOT NULL CHECK (batch_count BETWEEN 1 AND 50),
    status VARCHAR(16) NOT NULL DEFAULT 'collecting'
        CHECK (status IN ('collecting', 'complete')),
    applied BOOLEAN NOT NULL DEFAULT false,
    service_count INTEGER NOT NULL DEFAULT 0 CHECK (service_count BETWEEN 0 AND 5000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX host_service_runs_server_idx
    ON it_portal.host_service_runs (server_id, created_at DESC);
CREATE TABLE it_portal.host_service_batches (
    run_id UUID NOT NULL REFERENCES it_portal.host_service_runs(run_id) ON DELETE CASCADE,
    batch_index SMALLINT NOT NULL CHECK (batch_index BETWEEN 0 AND 49),
    payload_sha256 CHAR(64) NOT NULL,
    services JSONB,
    PRIMARY KEY(run_id, batch_index)
);
CREATE TABLE it_portal.host_services (
    server_id UUID NOT NULL REFERENCES it_portal.servers(id),
    service_key VARCHAR(200) NOT NULL,
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(240) NOT NULL,
    description VARCHAR(500),
    state VARCHAR(32) NOT NULL,
    start_mode VARCHAR(16) NOT NULL,
    can_stop BOOLEAN NOT NULL,
    is_present BOOLEAN NOT NULL DEFAULT true,
    observed_at TIMESTAMPTZ NOT NULL,
    last_run_id UUID NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY(server_id, service_key)
);
CREATE INDEX host_services_lookup_idx
    ON it_portal.host_services (server_id, is_present, state);
CREATE TABLE it_portal.host_service_current (
    server_id UUID PRIMARY KEY REFERENCES it_portal.servers(id),
    run_id UUID NOT NULL REFERENCES it_portal.host_service_runs(run_id),
    observed_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    service_count INTEGER NOT NULL CHECK (service_count BETWEEN 0 AND 5000)
);
