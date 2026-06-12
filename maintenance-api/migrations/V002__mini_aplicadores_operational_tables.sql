BEGIN;

CREATE TABLE IF NOT EXISTS maintenance.motivos (
    motivo_id SERIAL PRIMARY KEY,
    descricao VARCHAR(120) NOT NULL,
    excluido BOOLEAN NOT NULL DEFAULT FALSE,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_alteracao TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS maintenance.status_peca (
    status_id SERIAL PRIMARY KEY,
    descricao VARCHAR(60) NOT NULL,
    operador VARCHAR(4) NOT NULL CHECK (operador IN ('>=', '<', '>', '<=')),
    percentual INT NOT NULL CHECK (percentual >= 0 AND percentual <= 200),
    excluido BOOLEAN NOT NULL DEFAULT FALSE,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_alteracao TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS maintenance.reposicoes (
    reposicao_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filial VARCHAR(2) NOT NULL CHECK (filial IN ('01', '02')),
    codigo_ferramenta VARCHAR(40) NOT NULL,
    codigo_peca VARCHAR(40) NOT NULL,
    data_reposicao TIMESTAMPTZ NOT NULL,
    data_ultima_reposicao TIMESTAMPTZ,
    golpes BIGINT NOT NULL CHECK (golpes > 0),
    motivo_id INT NOT NULL REFERENCES maintenance.motivos (motivo_id),
    observacao TEXT,
    excluido BOOLEAN NOT NULL DEFAULT FALSE,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_alteracao TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS maintenance.audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entidade VARCHAR(60) NOT NULL,
    entidade_id TEXT NOT NULL,
    acao VARCHAR(20) NOT NULL,
    filial VARCHAR(2),
    payload JSONB,
    usuario_sub TEXT,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reposicoes_filial_ferramenta_peca_data
    ON maintenance.reposicoes (filial, codigo_ferramenta, codigo_peca, data_reposicao DESC)
    WHERE excluido = FALSE;

CREATE INDEX IF NOT EXISTS idx_reposicoes_excluido
    ON maintenance.reposicoes (excluido);

INSERT INTO maintenance.motivos (descricao)
SELECT v.descricao
FROM (VALUES ('QUEBRA'), ('DESGASTE'), ('PREVENTIVA'), ('AJUSTE')) AS v(descricao)
WHERE NOT EXISTS (SELECT 1 FROM maintenance.motivos);

INSERT INTO maintenance.status_peca (descricao, operador, percentual)
SELECT v.descricao, v.operador, v.percentual
FROM (
    VALUES ('CRÍTICO', '>=', 95),
           ('ATENÇÃO', '>=', 80),
           ('OK', '<', 80)
) AS v(descricao, operador, percentual)
WHERE NOT EXISTS (SELECT 1 FROM maintenance.status_peca);

COMMIT;
