BEGIN;

CREATE TABLE IF NOT EXISTS maintenance.revisao_programada_realizacao (
    realizacao_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revisao_id UUID NOT NULL,
    filial VARCHAR(2) NOT NULL,
    codigo_ferramenta VARCHAR(40) NOT NULL,
    data_revisao TIMESTAMPTZ NOT NULL,
    intervalo_meses INT NOT NULL CHECK (intervalo_meses >= 1 AND intervalo_meses <= 120),
    observacao TEXT,
    data_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_revisao_realizacao_revisao
        FOREIGN KEY (revisao_id) REFERENCES maintenance.revisao_programada (revisao_id),
    CONSTRAINT fk_revisao_realizacao_filial
        FOREIGN KEY (filial) REFERENCES maintenance.filiais (codigo_filial)
);

CREATE INDEX IF NOT EXISTS idx_revisao_realizacao_filial_ferramenta
    ON maintenance.revisao_programada_realizacao (filial, codigo_ferramenta, data_revisao DESC);

COMMENT ON TABLE maintenance.revisao_programada_realizacao IS
    'Histórico de revisões programadas marcadas como feitas por ferramenta.';

COMMIT;
