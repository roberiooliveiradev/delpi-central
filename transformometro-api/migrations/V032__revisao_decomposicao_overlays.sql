-- Transformômetro — overlay de decomposição por revisão (Playbook 20)

BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.revisao_decomposicao_overlays (
    revisao_id UUID PRIMARY KEY REFERENCES transformometro.revisoes(revisao_id) ON DELETE CASCADE,
    conteudo JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE transformometro.revisao_decomposicao_overlays IS
    'Overlay as-is/to-be decomposition_overlay_v1 sobre escopo da instância.';

COMMIT;
