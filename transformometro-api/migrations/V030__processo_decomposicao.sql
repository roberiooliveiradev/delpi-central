-- Transformômetro — árvore de decomposição por processo-mestre (Playbook 20)

BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.processo_decomposicao (
    processo_id UUID PRIMARY KEY REFERENCES transformometro.processos(processo_id) ON DELETE CASCADE,
    conteudo JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE transformometro.processo_decomposicao IS
    'Árvore WBS decomposition_tree_v1 — um documento por processo-mestre (Playbook 20).';

COMMIT;
