-- Transformômetro — views de leitura rápida (dashboard + api-delpi / Transforma+)
BEGIN;

CREATE OR REPLACE VIEW transformometro.dashboard_competencia_evolucao AS
SELECT
    d.competencia,
    d.codigo_filial,
    d.codigo_setor,
    d.filial_id,
    d.setor_id,
    COUNT(DISTINCT d.revisao_id) FILTER (
        WHERE d.cenario_tipo IN ('melhoria', 'automacao', 'correcao')
    ) AS solucoes_implementadas,
    COALESCE(SUM(d.economia_bruta), 0) AS economia_bruta,
    COALESCE(SUM(d.investimento_unico_mes), 0) AS investimento_unico_mes,
    COALESCE(SUM(d.custo_recorrente_mes), 0) AS custo_recorrente_mes,
    COALESCE(SUM(d.custo_recursos_compartilhados_mes), 0) AS custo_recursos_compartilhados_mes,
    COALESCE(
        SUM(
            COALESCE(d.investimento_unico_mes, 0)
          + COALESCE(d.custo_recorrente_mes, 0)
          + COALESCE(d.custo_recursos_compartilhados_mes, 0)
        ),
        0
    ) AS investimento_total_mes,
    COALESCE(SUM(d.economia_liquida_mes), 0) AS economia_liquida_mes,
    COALESCE(SUM(d.horas_economizadas_mes), 0) AS horas_economizadas_mes,
    MAX(d.calculated_at) AS calculated_at
FROM transformometro.dashboard_calculos d
GROUP BY
    d.competencia,
    d.codigo_filial,
    d.codigo_setor,
    d.filial_id,
    d.setor_id;

CREATE OR REPLACE VIEW transformometro.instancia_operacional_snapshot AS
WITH latest AS (
    SELECT MAX(competencia) AS competencia
    FROM transformometro.dashboard_calculos
),
cache_inst AS (
    SELECT
        d.instancia_id,
        d.processo_id,
        lc.competencia,
        MAX(d.codigo_filial) FILTER (WHERE d.codigo_filial IS NOT NULL AND d.codigo_filial <> '')
            AS codigo_filial,
        STRING_AGG(DISTINCT d.codigo_setor, ', ' ORDER BY d.codigo_setor)
            FILTER (WHERE d.codigo_setor IS NOT NULL AND d.codigo_setor <> '') AS codigos_setor,
        COALESCE(SUM(d.economia_bruta), 0) AS economia_bruta_mes,
        COALESCE(SUM(d.economia_liquida_mes), 0) AS economia_liquida_mes,
        COALESCE(
            SUM(
                COALESCE(d.investimento_unico_mes, 0)
              + COALESCE(d.custo_recorrente_mes, 0)
              + COALESCE(d.custo_recursos_compartilhados_mes, 0)
            ),
            0
        ) AS investimento_total_mes,
        EXTRACT(
            DAY FROM (
                (lc.competencia || '-01')::date
                + INTERVAL '1 month'
                - INTERVAL '1 day'
            )
        )::int AS dias_mes
    FROM transformometro.dashboard_calculos d
    CROSS JOIN latest lc
    WHERE d.competencia = lc.competencia
      AND d.cenario_tipo IN ('melhoria', 'automacao', 'correcao')
    GROUP BY d.instancia_id, d.processo_id, lc.competencia
)
SELECT
    pi.instancia_id,
    pi.processo_id,
    p.codigo_processo,
    p.nome_processo,
    p.status_processo,
    pi.todas_filiais_ativas,
    pi.filial_id,
    COALESCE(f.codigo_filial, ci.codigo_filial) AS codigo_filial,
    f.nome_filial,
    ci.codigos_setor AS codigo_setor,
    ci.codigos_setor AS setor_id,
    ci.competencia AS competencia_referencia,
    CASE
        WHEN ci.dias_mes > 0 THEN ci.economia_bruta_mes / ci.dias_mes
        ELSE 0
    END AS economia_diaria,
    CASE
        WHEN ci.economia_liquida_mes > 0 AND ci.investimento_total_mes > 0
            THEN ci.investimento_total_mes / ci.economia_liquida_mes
        ELSE NULL
    END AS payback_meses,
    rev_impl.data_implantacao
FROM transformometro.processo_instancias pi
JOIN transformometro.processos p
  ON p.processo_id = pi.processo_id
 AND p.deletado = FALSE
LEFT JOIN transformometro.filiais f
  ON f.filial_id = pi.filial_id
 AND f.deletado = FALSE
JOIN cache_inst ci
  ON ci.instancia_id = pi.instancia_id
LEFT JOIN LATERAL (
    SELECT MIN(COALESCE(r.data_implantacao, r.data_inicio_vigencia)) AS data_implantacao
    FROM transformometro.revisoes r
    WHERE r.instancia_id = pi.instancia_id
      AND r.deletado = FALSE
      AND r.cenario_tipo IN ('melhoria', 'automacao', 'correcao')
) rev_impl ON TRUE
WHERE pi.deletado = FALSE;

COMMENT ON VIEW transformometro.dashboard_competencia_evolucao IS
'Evolução mensal agregada sobre dashboard_calculos (filtro por codigo_filial/codigo_setor).';

COMMENT ON VIEW transformometro.instancia_operacional_snapshot IS
'Instâncias operacionais com métricas da última competência materializada — leitura rápida Transforma+/api-delpi.';

COMMIT;
