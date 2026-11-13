-- G2-S2: inventario observado de computadores, separado do cadastro curado.
-- A migracao e aditiva; nao instala agentes nem ativa ingestao.
CREATE TABLE it_portal.workstation_snapshots (
    id UUID PRIMARY KEY,
    workstation_id UUID NOT NULL REFERENCES it_portal.workstations(id) ON DELETE RESTRICT,
    run_id UUID NOT NULL,
    collector_client_id VARCHAR(100) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status VARCHAR(16) NOT NULL,
    payload JSONB NOT NULL,
    payload_sha256 CHAR(64) NOT NULL,
    CONSTRAINT workstation_snapshots_status_chk CHECK (status IN ('complete', 'partial', 'failed')),
    CONSTRAINT workstation_snapshots_digest_chk CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT workstation_snapshots_run_uq UNIQUE(workstation_id, run_id)
);

CREATE INDEX workstation_snapshots_latest_idx
    ON it_portal.workstation_snapshots
    (workstation_id, observed_at DESC, received_at DESC, id DESC);

COMMENT ON TABLE it_portal.workstation_snapshots IS
    'G2-S2: snapshots de inventario Windows, coletados por identidade S2S individual; nunca permitem acesso remoto.';
