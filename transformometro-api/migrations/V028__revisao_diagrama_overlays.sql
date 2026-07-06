-- Transformômetro — overlay as-is/to-be por revisão
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.revisao_diagrama_overlays (
    revisao_id UUID PRIMARY KEY
        REFERENCES transformometro.revisoes (revisao_id) ON DELETE CASCADE,
    conteudo JSONB NOT NULL DEFAULT '{}'::jsonb,
    mermaid_cached TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE transformometro.revisao_diagrama_overlays IS
    'Overlay flowchart_overlay_v1 — estado visual as-is/to-be da revisão.';

COMMIT;
