-- Transformômetro — dashboard_calculos com PK UUID e FKs de instância/filial/setor (Playbook 18 S6)
-- Cache derivado: TRUNCATE + recalc após migration.
BEGIN;

DROP VIEW IF EXISTS transformometro.processo_competencia_snapshot;

DROP TABLE IF EXISTS transformometro.dashboard_calculos;

CREATE TABLE transformometro.dashboard_calculos (
    dashboard_calculo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revisao_id UUID NOT NULL REFERENCES transformometro.revisoes (revisao_id) ON DELETE CASCADE,
    processo_id UUID NOT NULL REFERENCES transformometro.processos (processo_id) ON DELETE CASCADE,
    instancia_id UUID REFERENCES transformometro.processo_instancias (instancia_id),
    competencia CHAR(7) NOT NULL,
    filial_id UUID REFERENCES transformometro.filiais (filial_id),
    setor_id UUID REFERENCES transformometro.setores (setor_id),
    codigo_filial VARCHAR(16),
    codigo_setor VARCHAR(64),
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
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dashboard_revisao_competencia UNIQUE (revisao_id, competencia)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_competencia
    ON transformometro.dashboard_calculos (competencia);

CREATE INDEX IF NOT EXISTS idx_dashboard_processo
    ON transformometro.dashboard_calculos (processo_id);

CREATE INDEX IF NOT EXISTS idx_dashboard_instancia
    ON transformometro.dashboard_calculos (instancia_id);

CREATE INDEX IF NOT EXISTS idx_dashboard_filial_uuid
    ON transformometro.dashboard_calculos (filial_id);

CREATE INDEX IF NOT EXISTS idx_dashboard_setor_uuid
    ON transformometro.dashboard_calculos (setor_id);

CREATE INDEX IF NOT EXISTS idx_dashboard_codigo_filial
    ON transformometro.dashboard_calculos (codigo_filial);

CREATE INDEX IF NOT EXISTS idx_dashboard_codigo_setor
    ON transformometro.dashboard_calculos (codigo_setor);

CREATE INDEX IF NOT EXISTS idx_dashboard_cenario
    ON transformometro.dashboard_calculos (cenario_tipo);

CREATE OR REPLACE VIEW transformometro.processo_competencia_snapshot AS
SELECT
    d.processo_id,
    p.codigo_processo,
    p.nome_processo,
    d.codigo_filial AS filial_id,
    d.codigo_setor AS setor_id,
    d.instancia_id,
    p.familia_processo,
    p.agrupador_ferramenta,
    d.competencia,
    COUNT(DISTINCT d.revisao_id) AS revisoes_no_mes,
    SUM(d.economia_bruta) AS economia_bruta,
    SUM(d.economia_liquida_mes) AS economia_liquida_mes,
    SUM(d.investimento_unico_mes) AS investimento_unico_mes,
    SUM(d.custo_recorrente_mes) AS custo_recorrente_mes,
    SUM(d.custo_recursos_compartilhados_mes) AS custo_recursos_compartilhados_mes,
    SUM(
        COALESCE(d.investimento_unico_mes, 0)
      + COALESCE(d.custo_recorrente_mes, 0)
      + COALESCE(d.custo_recursos_compartilhados_mes, 0)
    ) AS investimento_total_mes,
    SUM(d.horas_economizadas_mes) AS horas_economizadas_mes,
    MAX(d.calculated_at) AS calculated_at
FROM transformometro.dashboard_calculos d
JOIN transformometro.processos p
  ON p.processo_id = d.processo_id
 AND p.deletado = FALSE
WHERE d.cenario_tipo IN ('melhoria', 'automacao', 'correcao')
GROUP BY
    d.processo_id,
    p.codigo_processo,
    p.nome_processo,
    d.codigo_filial,
    d.codigo_setor,
    d.instancia_id,
    p.familia_processo,
    p.agrupador_ferramenta,
    d.competencia;

COMMENT ON VIEW transformometro.processo_competencia_snapshot IS
'Agregação mensal por processo sobre dashboard_calculos (filial/setor = codigo_* denormalizado).';

COMMIT;
