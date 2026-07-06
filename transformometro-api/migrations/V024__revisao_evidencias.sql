-- Transformômetro — evidências por revisão (metadado Postgres + binário em volume)
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.revisao_evidencias (
    evidencia_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revisao_id UUID NOT NULL
        REFERENCES transformometro.revisoes (revisao_id) ON DELETE CASCADE,
    tipo VARCHAR(30) NOT NULL DEFAULT 'anexo',
    nome_arquivo VARCHAR(512),
    nome_armazenado VARCHAR(512),
    tipo_mime VARCHAR(128),
    tamanho_bytes BIGINT,
    descricao TEXT,
    url_externa VARCHAR(1000),
    enviado_por_id VARCHAR(100),
    enviado_por_nome VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_revisao_evidencias_revisao
    ON transformometro.revisao_evidencias (revisao_id)
    WHERE deleted_at IS NULL;

COMMIT;
