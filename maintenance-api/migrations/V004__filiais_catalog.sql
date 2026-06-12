BEGIN;

CREATE TABLE IF NOT EXISTS maintenance.filiais (
    filial_id SERIAL PRIMARY KEY,
    codigo_filial VARCHAR(2) NOT NULL UNIQUE,
    nome_filial VARCHAR(120) NOT NULL,
    status_filial VARCHAR(20) NOT NULL DEFAULT 'ativo'
        CHECK (status_filial IN ('ativo', 'inativo')),
    excluido BOOLEAN NOT NULL DEFAULT FALSE,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_alteracao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT filiais_codigo_filial_format CHECK (codigo_filial ~ '^[0-9]{2}$')
);

INSERT INTO maintenance.filiais (codigo_filial, nome_filial, status_filial)
VALUES ('01', 'Matriz', 'ativo'),
       ('02', 'ES', 'ativo')
ON CONFLICT (codigo_filial) DO NOTHING;

ALTER TABLE maintenance.reposicoes
    DROP CONSTRAINT IF EXISTS reposicoes_filial_check;

ALTER TABLE maintenance.motivos
    DROP CONSTRAINT IF EXISTS motivos_filial_check;

ALTER TABLE maintenance.status_peca
    DROP CONSTRAINT IF EXISTS status_peca_filial_check;

ALTER TABLE maintenance.reposicoes
    ADD CONSTRAINT fk_reposicoes_filial
        FOREIGN KEY (filial) REFERENCES maintenance.filiais (codigo_filial);

ALTER TABLE maintenance.motivos
    ADD CONSTRAINT fk_motivos_filial
        FOREIGN KEY (filial) REFERENCES maintenance.filiais (codigo_filial);

ALTER TABLE maintenance.status_peca
    ADD CONSTRAINT fk_status_peca_filial
        FOREIGN KEY (filial) REFERENCES maintenance.filiais (codigo_filial);

CREATE INDEX IF NOT EXISTS idx_filiais_ativo
    ON maintenance.filiais (codigo_filial)
    WHERE excluido = FALSE AND status_filial = 'ativo';

COMMIT;
