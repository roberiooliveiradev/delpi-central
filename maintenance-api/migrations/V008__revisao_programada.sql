BEGIN;

CREATE TABLE IF NOT EXISTS maintenance.revisao_programada (
    revisao_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filial VARCHAR(2) NOT NULL,
    codigo_ferramenta VARCHAR(40) NOT NULL,
    intervalo_meses INT NOT NULL CHECK (intervalo_meses >= 1 AND intervalo_meses <= 120),
    data_ultima_revisao TIMESTAMPTZ,
    observacao TEXT,
    excluido BOOLEAN NOT NULL DEFAULT FALSE,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_alteracao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_revisao_programada_filial
        FOREIGN KEY (filial) REFERENCES maintenance.filiais (codigo_filial)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_revisao_programada_filial_ferramenta_ativa
    ON maintenance.revisao_programada (filial, codigo_ferramenta)
    WHERE excluido = FALSE;

CREATE INDEX IF NOT EXISTS idx_revisao_programada_filial_ativa
    ON maintenance.revisao_programada (filial, codigo_ferramenta)
    WHERE excluido = FALSE;

CREATE OR REPLACE VIEW maintenance.vw_revisao_programada_ativos AS
SELECT
    revisao_id,
    filial,
    codigo_ferramenta,
    intervalo_meses,
    data_ultima_revisao,
    observacao,
    data_criacao,
    data_alteracao
FROM maintenance.revisao_programada
WHERE excluido = FALSE;

COMMENT ON TABLE maintenance.revisao_programada IS
    'Agenda de revisão periódica por ferramenta (ex.: a cada 3 meses).';
COMMENT ON VIEW maintenance.vw_revisao_programada_ativos IS
    'Programações de revisão ativas por filial.';

COMMIT;
