-- Transformômetro — tabelas cadastrais (Fase 1)
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.processos (
    processo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_processo VARCHAR(32) NOT NULL,
    nome_processo VARCHAR(500) NOT NULL,
    descricao_processo TEXT,
    filial_id VARCHAR(16) NOT NULL,
    setor_id VARCHAR(64) NOT NULL,
    gestor_responsavel VARCHAR(255),
    objetivo_processo TEXT,
    status_processo VARCHAR(32) NOT NULL DEFAULT 'ativo',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_processos_codigo UNIQUE (codigo_processo)
);

CREATE INDEX IF NOT EXISTS idx_processos_filial ON transformometro.processos (filial_id)
    WHERE deletado = FALSE;
CREATE INDEX IF NOT EXISTS idx_processos_setor ON transformometro.processos (setor_id)
    WHERE deletado = FALSE;
CREATE INDEX IF NOT EXISTS idx_processos_status ON transformometro.processos (status_processo)
    WHERE deletado = FALSE;

CREATE TABLE IF NOT EXISTS transformometro.revisoes (
    revisao_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processo_id UUID NOT NULL REFERENCES transformometro.processos (processo_id),
    versao_revisao VARCHAR(32) NOT NULL,
    chave_unica_processo_revisao VARCHAR(128) NOT NULL,
    descricao_revisao TEXT,
    motivo_revisao TEXT,
    cenario_tipo VARCHAR(32) NOT NULL,
    data_implantacao DATE,
    data_inicio_vigencia DATE NOT NULL,
    data_fim_vigencia DATE,
    revisao_ativa BOOLEAN NOT NULL DEFAULT FALSE,
    observacoes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_revisoes_processo_versao UNIQUE (processo_id, versao_revisao),
    CONSTRAINT uq_revisoes_chave UNIQUE (chave_unica_processo_revisao)
);

CREATE INDEX IF NOT EXISTS idx_revisoes_processo ON transformometro.revisoes (processo_id)
    WHERE deletado = FALSE;
CREATE INDEX IF NOT EXISTS idx_revisoes_cenario ON transformometro.revisoes (cenario_tipo)
    WHERE deletado = FALSE;

CREATE TABLE IF NOT EXISTS transformometro.medicoes (
    medicao_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revisao_id UUID NOT NULL REFERENCES transformometro.revisoes (revisao_id),
    volume_mensal NUMERIC(14, 4) NOT NULL DEFAULT 0,
    tempo_medio_execucao_min NUMERIC(14, 4) NOT NULL DEFAULT 0,
    tempo_retrabalho_min NUMERIC(14, 4) NOT NULL DEFAULT 0,
    percentual_retrabalho NUMERIC(10, 4) NOT NULL DEFAULT 0,
    percentual_erro NUMERIC(10, 4) NOT NULL DEFAULT 0,
    quantidade_erros_mes NUMERIC(14, 4) NOT NULL DEFAULT 0,
    custo_hora_mao_obra NUMERIC(14, 2) NOT NULL DEFAULT 0,
    custo_unitario_erro NUMERIC(14, 2) NOT NULL DEFAULT 0,
    custo_unitario_retrabalho NUMERIC(14, 2) NOT NULL DEFAULT 0,
    custo_outros_desperdicios NUMERIC(14, 2) NOT NULL DEFAULT 0,
    base_referencia_mes VARCHAR(16),
    observacoes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_medicoes_revisao UNIQUE (revisao_id)
);

CREATE TABLE IF NOT EXISTS transformometro.investimentos (
    investimento_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revisao_id UUID NOT NULL REFERENCES transformometro.revisoes (revisao_id),
    tipo_investimento VARCHAR(32) NOT NULL,
    categoria_investimento VARCHAR(64),
    descricao_item VARCHAR(500) NOT NULL,
    quantidade NUMERIC(14, 4) NOT NULL DEFAULT 1,
    valor_unitario NUMERIC(14, 2) NOT NULL DEFAULT 0,
    valor_total NUMERIC(14, 2) NOT NULL DEFAULT 0,
    data_investimento DATE,
    recorrencia VARCHAR(32) NOT NULL DEFAULT 'unico',
    meses_vigencia INTEGER,
    centro_custo VARCHAR(64),
    observacoes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_investimentos_revisao ON transformometro.investimentos (revisao_id)
    WHERE deletado = FALSE;

CREATE TABLE IF NOT EXISTS transformometro.recursos_compartilhados (
    recurso_compartilhado_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_recurso VARCHAR(32) NOT NULL,
    nome_recurso VARCHAR(255) NOT NULL,
    categoria_recurso VARCHAR(64),
    fornecedor VARCHAR(255),
    tipo_custo VARCHAR(32) NOT NULL,
    recorrencia VARCHAR(32) NOT NULL,
    valor_total_recorrente NUMERIC(14, 2) NOT NULL DEFAULT 0,
    data_inicio_vigencia DATE,
    data_fim_vigencia DATE,
    centro_custo VARCHAR(64),
    criterio_rateio VARCHAR(32) NOT NULL DEFAULT 'igualitario',
    status_recurso VARCHAR(32) NOT NULL DEFAULT 'ativo',
    observacoes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_recursos_codigo UNIQUE (codigo_recurso)
);

CREATE TABLE IF NOT EXISTS transformometro.revisao_recursos_compartilhados (
    vinculo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revisao_id UUID NOT NULL REFERENCES transformometro.revisoes (revisao_id),
    recurso_compartilhado_id UUID NOT NULL REFERENCES transformometro.recursos_compartilhados (recurso_compartilhado_id),
    data_inicio_uso DATE,
    data_fim_uso DATE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    peso_rateio NUMERIC(10, 4),
    observacoes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_vinculos_revisao ON transformometro.revisao_recursos_compartilhados (revisao_id)
    WHERE deletado = FALSE;
CREATE INDEX IF NOT EXISTS idx_vinculos_recurso ON transformometro.revisao_recursos_compartilhados (recurso_compartilhado_id)
    WHERE deletado = FALSE;

CREATE TABLE IF NOT EXISTS transformometro.audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(64) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(32) NOT NULL,
    user_id VARCHAR(128),
    user_email VARCHAR(255),
    payload_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_entity ON transformometro.audit_logs (entity_type, entity_id);

COMMIT;
