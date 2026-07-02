-- Transformômetro — views com média por instância (regra jul/2026).
-- Cada instância é um ambiente isolado (baseline/parâmetros próprios); o processo
-- consolidado é a MÉDIA das instâncias ativas no mês. Agregação em 2 níveis:
--   inst_lvl: soma as revisões dentro de cada instância (grão instância × competência);
--   proc_lvl: média entre instâncias ativas (grão processo × competência).
-- Espelha DashboardCalculatorService / calc_rules.prorate_dashboard_row_for_period e
-- DashboardCalculoRepository._instance_average_cte. Mantém o contrato de colunas das views.
BEGIN;

DROP VIEW IF EXISTS transformometro.processo_competencia_snapshot;
DROP VIEW IF EXISTS transformometro.dashboard_competencia_evolucao;

CREATE VIEW transformometro.processo_competencia_snapshot AS
WITH inst_lvl AS (
    SELECT
        d.processo_id,
        d.competencia,
        COALESCE(d.instancia_id::text, d.processo_id::text) AS instancia_key,
        MAX(d.instancia_id::text) AS instancia_id,
        MAX(d.filial_id::text) AS filial_id,
        MAX(d.setor_id::text) AS setor_id,
        SUM(COALESCE(d.economia_bruta, 0)) AS economia_bruta,
        SUM(COALESCE(d.economia_liquida_mes, 0)) AS economia_liquida_mes,
        SUM(COALESCE(d.investimento_unico_mes, 0)) AS investimento_unico_mes,
        SUM(COALESCE(d.custo_recorrente_mes, 0)) AS custo_recorrente_mes,
        SUM(COALESCE(d.custo_recursos_compartilhados_mes, 0)) AS custo_recursos_compartilhados_mes,
        SUM(COALESCE(d.horas_economizadas_mes, 0)) AS horas_economizadas_mes,
        COUNT(DISTINCT d.revisao_id) AS revisoes,
        MAX(d.calculated_at) AS calculated_at
    FROM transformometro.dashboard_calculos d
    WHERE d.cenario_tipo IN ('melhoria', 'automacao', 'correcao')
    GROUP BY d.processo_id, d.competencia, COALESCE(d.instancia_id::text, d.processo_id::text)
),
proc_lvl AS (
    SELECT
        processo_id,
        competencia,
        MAX(instancia_id) AS instancia_id,
        MAX(filial_id) AS filial_id,
        MAX(setor_id) AS setor_id,
        AVG(economia_bruta) AS economia_bruta,
        AVG(economia_liquida_mes) AS economia_liquida_mes,
        AVG(investimento_unico_mes) AS investimento_unico_mes,
        AVG(custo_recorrente_mes) AS custo_recorrente_mes,
        AVG(custo_recursos_compartilhados_mes) AS custo_recursos_compartilhados_mes,
        AVG(horas_economizadas_mes) AS horas_economizadas_mes,
        SUM(revisoes) AS revisoes,
        MAX(calculated_at) AS calculated_at
    FROM inst_lvl
    GROUP BY processo_id, competencia
)
SELECT
    pl.processo_id,
    p.codigo_processo,
    p.nome_processo,
    pl.filial_id::uuid AS filial_id,
    pl.setor_id::uuid AS setor_id,
    pl.instancia_id::uuid AS instancia_id,
    p.familia_processo,
    p.agrupador_ferramenta,
    pl.competencia,
    pl.revisoes AS revisoes_no_mes,
    pl.economia_bruta,
    pl.economia_liquida_mes,
    pl.investimento_unico_mes,
    pl.custo_recorrente_mes,
    pl.custo_recursos_compartilhados_mes,
    (
        COALESCE(pl.investimento_unico_mes, 0)
      + COALESCE(pl.custo_recorrente_mes, 0)
      + COALESCE(pl.custo_recursos_compartilhados_mes, 0)
    ) AS investimento_total_mes,
    pl.horas_economizadas_mes,
    pl.calculated_at
FROM proc_lvl pl
JOIN transformometro.processos p
  ON p.processo_id = pl.processo_id
 AND p.deletado = FALSE;

-- Evolução mensal CONSOLIDADA (empresa) com média por instância ativa.
-- Recortes por unidade/setor são calculados no grão de linha por
-- DashboardCalculoRepository.query_evolucao (o filtro precisa vir antes da média).
CREATE VIEW transformometro.dashboard_competencia_evolucao AS
WITH inst_lvl AS (
    SELECT
        d.processo_id,
        d.competencia,
        COALESCE(d.instancia_id::text, d.processo_id::text) AS instancia_key,
        SUM(COALESCE(d.economia_bruta, 0)) AS economia_bruta,
        SUM(COALESCE(d.economia_liquida_mes, 0)) AS economia_liquida_mes,
        SUM(COALESCE(d.investimento_unico_mes, 0)) AS investimento_unico_mes,
        SUM(COALESCE(d.custo_recorrente_mes, 0)) AS custo_recorrente_mes,
        SUM(COALESCE(d.custo_recursos_compartilhados_mes, 0)) AS custo_recursos_compartilhados_mes,
        SUM(COALESCE(d.horas_economizadas_mes, 0)) AS horas_economizadas_mes,
        COUNT(DISTINCT d.revisao_id) AS revisoes,
        MAX(d.calculated_at) AS calculated_at
    FROM transformometro.dashboard_calculos d
    WHERE d.cenario_tipo IN ('melhoria', 'automacao', 'correcao')
    GROUP BY d.processo_id, d.competencia, COALESCE(d.instancia_id::text, d.processo_id::text)
),
proc_lvl AS (
    SELECT
        processo_id,
        competencia,
        AVG(economia_bruta) AS economia_bruta,
        AVG(economia_liquida_mes) AS economia_liquida_mes,
        AVG(investimento_unico_mes) AS investimento_unico_mes,
        AVG(custo_recorrente_mes) AS custo_recorrente_mes,
        AVG(custo_recursos_compartilhados_mes) AS custo_recursos_compartilhados_mes,
        AVG(horas_economizadas_mes) AS horas_economizadas_mes,
        SUM(revisoes) AS revisoes,
        MAX(calculated_at) AS calculated_at
    FROM inst_lvl
    GROUP BY processo_id, competencia
)
SELECT
    competencia,
    NULL::text AS codigo_filial,
    NULL::text AS codigo_setor,
    NULL::uuid AS filial_id,
    NULL::uuid AS setor_id,
    SUM(revisoes) AS solucoes_implementadas,
    COALESCE(SUM(economia_bruta), 0) AS economia_bruta,
    COALESCE(SUM(investimento_unico_mes), 0) AS investimento_unico_mes,
    COALESCE(SUM(custo_recorrente_mes), 0) AS custo_recorrente_mes,
    COALESCE(SUM(custo_recursos_compartilhados_mes), 0) AS custo_recursos_compartilhados_mes,
    COALESCE(
        SUM(
            COALESCE(investimento_unico_mes, 0)
          + COALESCE(custo_recorrente_mes, 0)
          + COALESCE(custo_recursos_compartilhados_mes, 0)
        ),
        0
    ) AS investimento_total_mes,
    COALESCE(SUM(economia_liquida_mes), 0) AS economia_liquida_mes,
    COALESCE(SUM(horas_economizadas_mes), 0) AS horas_economizadas_mes,
    MAX(calculated_at) AS calculated_at
FROM proc_lvl
GROUP BY competencia;

COMMENT ON VIEW transformometro.processo_competencia_snapshot IS
'Agregação mensal por processo sobre dashboard_calculos com MÉDIA por instância ativa (regra jul/2026). Colunas filial_id/setor_id/instancia_id refletem instância única (MAX) — para multi-instância use o recorte por unidade no cálculo em tempo real. Atualizada pelo recálculo do cache.';

COMMENT ON VIEW transformometro.dashboard_competencia_evolucao IS
'Evolução mensal CONSOLIDADA (empresa) com média por instância ativa. Recortes por unidade/setor: DashboardCalculoRepository.query_evolucao (filtro no grão de linha).';

COMMIT;
