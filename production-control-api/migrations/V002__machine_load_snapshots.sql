-- Snapshot congelado da carga máquina (sequenciamento SH8 por filial + janela).
-- Status HZA não é fonte de verdade aqui: o GET reenriquece ao vivo.

CREATE TABLE IF NOT EXISTS production_control.machine_load_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch VARCHAR(2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    payload_json JSONB NOT NULL,
    schema_version SMALLINT NOT NULL DEFAULT 1,
    source VARCHAR(40) NOT NULL DEFAULT 'api-delpi',
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    refreshed_by VARCHAR(120),
    CONSTRAINT uq_pc_machine_load_snapshots_scope
        UNIQUE (branch, start_date, end_date)
);

COMMENT ON TABLE production_control.machine_load_snapshots IS
    'Fila de carga máquina congelada pelo PCP; regenera só via POST /machine-load/refresh.';

CREATE INDEX IF NOT EXISTS ix_pc_machine_load_snapshots_refreshed
    ON production_control.machine_load_snapshots (refreshed_at DESC);
