-- View agregada por processo + competência (leitura leve para chat/integrações)
BEGIN;

CREATE OR REPLACE VIEW transformometro.processo_competencia_snapshot AS
SELECT
    d.processo_id,
    p.codigo_processo,
    p.nome_processo,
    p.filial_id,
    p.setor_id,
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
    p.filial_id,
    p.setor_id,
    p.familia_processo,
    p.agrupador_ferramenta,
    d.competencia;

COMMENT ON VIEW transformometro.processo_competencia_snapshot IS
'Agregação mensal por processo sobre dashboard_calculos. Atualizada pelo recálculo do cache.';

COMMIT;
