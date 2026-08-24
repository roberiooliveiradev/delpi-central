-- Snapshot congelado do mapa de entrega (OPs PA com saldo por filial).
-- Regenera só via POST /delivery-map/refresh; MP-OK e CT ficam no payload.

CREATE TABLE IF NOT EXISTS production_control.delivery_map_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch VARCHAR(2) NOT NULL,
    horizon_end DATE NOT NULL,
    payload_json JSONB NOT NULL,
    schema_version SMALLINT NOT NULL DEFAULT 1,
    source VARCHAR(40) NOT NULL DEFAULT 'api-delpi',
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    refreshed_by VARCHAR(120),
    CONSTRAINT uq_pc_delivery_map_snapshots_branch UNIQUE (branch)
);

COMMENT ON TABLE production_control.delivery_map_snapshots IS
    'Mapa de entrega congelado pelo PCP: uma fila por filial, regenerada só via POST /delivery-map/refresh.';

COMMENT ON COLUMN production_control.delivery_map_snapshots.horizon_end IS
    'Fim da janela de entrega prevista puxada no último refresh (hoje + N dias).';

CREATE INDEX IF NOT EXISTS ix_pc_delivery_map_snapshots_refreshed
    ON production_control.delivery_map_snapshots (refreshed_at DESC);
