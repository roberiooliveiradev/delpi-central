-- Transformômetro — diagrama macro por processo-mestre (Playbook 19)
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.processo_diagramas (
    processo_id UUID PRIMARY KEY
        REFERENCES transformometro.processos (processo_id) ON DELETE CASCADE,
    conteudo JSONB NOT NULL DEFAULT '{}'::jsonb,
    mermaid_cached TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE transformometro.processo_diagramas IS
    'Diagrama-macro flowchart_v1 — mapa canônico do processo-mestre.';

COMMIT;
