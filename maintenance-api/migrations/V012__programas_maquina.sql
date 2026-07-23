BEGIN;

CREATE TABLE IF NOT EXISTS maintenance.programas_maquina_produtos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filial VARCHAR(2) NOT NULL CHECK (filial IN ('01', '02')),
    codigo_intermediario VARCHAR(40) NOT NULL,
    codigo_produto_acabado VARCHAR(40),
    codigo_ct_corte VARCHAR(40),
    nome_programa VARCHAR(120),
    observacao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    excluido BOOLEAN NOT NULL DEFAULT FALSE,
    usuario_sub TEXT,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_alteracao TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_programas_maquina_produtos_ativo
    ON maintenance.programas_maquina_produtos (
        filial,
        codigo_intermediario,
        (COALESCE(nome_programa, ''))
    )
    WHERE excluido = FALSE;

CREATE INDEX IF NOT EXISTS idx_programas_maquina_produtos_filial_ativo
    ON maintenance.programas_maquina_produtos (filial, ativo)
    WHERE excluido = FALSE;

COMMENT ON TABLE maintenance.programas_maquina_produtos IS
    'Produtos (PI) cadastrados para programas de máquina — submódulo Manutenção.';

COMMIT;
