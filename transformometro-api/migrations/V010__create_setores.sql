-- Transformômetro — catálogo de setores com vínculo por filial
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.setores (
    setor_id VARCHAR(64) PRIMARY KEY,
    nome_setor VARCHAR(255) NOT NULL,
    status_setor VARCHAR(32) NOT NULL DEFAULT 'ativo',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_setores_status ON transformometro.setores (status_setor)
    WHERE deletado = FALSE;

CREATE TABLE IF NOT EXISTS transformometro.setor_filiais (
    setor_id VARCHAR(64) NOT NULL REFERENCES transformometro.setores (setor_id) ON DELETE CASCADE,
    filial_id VARCHAR(16) NOT NULL,
    PRIMARY KEY (setor_id, filial_id)
);

CREATE INDEX IF NOT EXISTS idx_setor_filiais_filial ON transformometro.setor_filiais (filial_id);

INSERT INTO transformometro.setores (setor_id, nome_setor) VALUES
    ('engenharia', 'Engenharia'),
    ('qualidade', 'Qualidade'),
    ('pcp', 'PCP'),
    ('producao', 'Produção'),
    ('comercial', 'Comercial'),
    ('compras', 'Compras'),
    ('almoxarifado', 'Almoxarifado')
ON CONFLICT (setor_id) DO NOTHING;

INSERT INTO transformometro.setor_filiais (setor_id, filial_id)
SELECT s.setor_id, f.filial_id
FROM transformometro.setores s
CROSS JOIN (VALUES ('01'), ('02')) AS f (filial_id)
ON CONFLICT DO NOTHING;

COMMIT;
