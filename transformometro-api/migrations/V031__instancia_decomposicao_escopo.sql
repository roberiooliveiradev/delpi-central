-- Transformômetro — escopo WBS por instância (Playbook 20)

BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.instancia_decomposicao_escopo (
    instancia_id UUID PRIMARY KEY REFERENCES transformometro.processo_instancias(instancia_id) ON DELETE CASCADE,
    node_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    inherit_all BOOLEAN NOT NULL DEFAULT TRUE,
    include_descendants BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE transformometro.instancia_decomposicao_escopo IS
    'Subset de node_id da árvore WBS relevante para a instância operacional.';

COMMIT;
