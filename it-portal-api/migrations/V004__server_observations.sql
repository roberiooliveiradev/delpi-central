-- Portal de TI — E4.S1 (coleta automática Linux).
-- Observações técnicas do host, distintas do cadastro manual do servidor.
-- Migration aditiva: não altera tabelas/colunas da V001–V003 nem dados existentes.
-- Não guarda senhas, tokens, env vars, argumentos de processo nem mounts sensíveis.

CREATE TABLE it_portal.server_observations (
    id UUID PRIMARY KEY,
    server_id UUID NOT NULL REFERENCES it_portal.servers (id),
    run_id VARCHAR(64) NOT NULL,
    source VARCHAR(40) NOT NULL,
    collector_client_id VARCHAR(120) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    schema_version VARCHAR(16) NOT NULL,
    status VARCHAR(20) NOT NULL,
    summary JSONB NOT NULL,
    sections_status JSONB NOT NULL DEFAULT '{}'::jsonb,
    divergences JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT server_observations_source_chk CHECK (
        source IN ('linux_host_collector')
    ),
    CONSTRAINT server_observations_status_chk CHECK (
        status IN ('complete', 'partial', 'failed')
    ),
    CONSTRAINT server_observations_run_id_chk CHECK (
        char_length(btrim(run_id)) BETWEEN 8 AND 64
    ),
    CONSTRAINT server_observations_schema_version_chk CHECK (
        char_length(btrim(schema_version)) BETWEEN 1 AND 16
    )
);

CREATE UNIQUE INDEX server_observations_run_id_uq
    ON it_portal.server_observations (run_id);

CREATE INDEX server_observations_server_observed_idx
    ON it_portal.server_observations (server_id, observed_at DESC);
