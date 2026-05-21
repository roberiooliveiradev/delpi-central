-- Transformômetro — materialização do dashboard (Fase 2)
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.dashboard_calculos (
    dashboard_calculo_id VARCHAR(80) PRIMARY KEY,
    revisao_id UUID NOT NULL REFERENCES transformometro.revisoes (revisao_id),
    processo_id UUID NOT NULL REFERENCES transformometro.processos (processo_id),
    competencia CHAR(7) NOT NULL,
    filial_id VARCHAR(16),
    setor_id VARCHAR(64),
    cenario_tipo VARCHAR(32) NOT NULL,
    revisao_ativa BOOLEAN NOT NULL DEFAULT FALSE,
    economia_tempo NUMERIC(14, 2) NOT NULL DEFAULT 0,
    economia_retrabalho NUMERIC(14, 2) NOT NULL DEFAULT 0,
    economia_erros NUMERIC(14, 2) NOT NULL DEFAULT 0,
    economia_outros NUMERIC(14, 2) NOT NULL DEFAULT 0,
    economia_recursos_compartilhados NUMERIC(14, 2) NOT NULL DEFAULT 0,
    economia_bruta NUMERIC(14, 2) NOT NULL DEFAULT 0,
    investimento_unico_mes NUMERIC(14, 2) NOT NULL DEFAULT 0,
    custo_recorrente_mes NUMERIC(14, 2) NOT NULL DEFAULT 0,
    economia_liquida_mes NUMERIC(14, 2) NOT NULL DEFAULT 0,
    custo_recursos_compartilhados_mes NUMERIC(14, 2) NOT NULL DEFAULT 0,
    horas_economizadas_mes NUMERIC(14, 2) NOT NULL DEFAULT 0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dashboard_revisao_competencia
    ON transformometro.dashboard_calculos (revisao_id, competencia);

CREATE INDEX IF NOT EXISTS idx_dashboard_competencia
    ON transformometro.dashboard_calculos (competencia);

CREATE INDEX IF NOT EXISTS idx_dashboard_processo
    ON transformometro.dashboard_calculos (processo_id);

CREATE INDEX IF NOT EXISTS idx_dashboard_filial
    ON transformometro.dashboard_calculos (filial_id);

CREATE INDEX IF NOT EXISTS idx_dashboard_setor
    ON transformometro.dashboard_calculos (setor_id);

CREATE INDEX IF NOT EXISTS idx_dashboard_cenario
    ON transformometro.dashboard_calculos (cenario_tipo);

COMMIT;
