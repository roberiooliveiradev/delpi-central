-- Transformômetro — escopo de nós do macro por instância operacional
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.instancia_diagrama_escopo (
    instancia_id UUID PRIMARY KEY
        REFERENCES transformometro.processo_instancias (instancia_id) ON DELETE CASCADE,
    node_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    inherit_all BOOLEAN NOT NULL DEFAULT TRUE,
    include_boundary_edges BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE transformometro.instancia_diagrama_escopo IS
    'Subset de node_id do diagrama macro relevante para a instância.';

COMMIT;
