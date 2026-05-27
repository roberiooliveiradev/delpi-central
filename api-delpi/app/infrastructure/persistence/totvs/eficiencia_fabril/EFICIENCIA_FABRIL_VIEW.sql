/* ============================================================
   Eficiência Fabril — queries de referência (Fase 0)
   View: dbo.vw_Apontamentos_Eficiencia
   Uso: validação manual (SSMS) ou script validate_eficiencia_fabril_view.py
   ============================================================ */

/* ------------------------------------------------------------
   0) Smoke — view existe e retorna linhas
   ------------------------------------------------------------ */
SELECT TOP 100
    FILIAL,
    OP,
    PRODUTO,
    CENTRO_TRABALHO,
    OPERACAO,
    COD_OPERADOR,
    LOGIN_OPERADOR,
    NOME_OPERADOR,
    DATA_PRODUCAO,
    HORA_INICIO,
    HORA_FINAL,
    TEMPO_ORIGINAL,
    QTD_APONTADA,
    QTD_TOTAL_OP,
    TEMPO_REAL_HORAS,
    TEMPO_PREVISTO_HORAS,
    EFICIENCIA_PERCENTUAL,
    VALOR_MOD_HORA,
    TEMPO_GANHO_PERDIDO_HORAS,
    RESULTADO_MOD,
    LUCRO_MOD,
    PREJUIZO_MOD,
    STATUS_MOD,
    STATUS_RESULTADO_MOD,
    STATUS_REGISTRO
FROM dbo.vw_Apontamentos_Eficiencia
ORDER BY DATA_PRODUCAO DESC, HORA_INICIO DESC, HORA_FINAL DESC;


/* ------------------------------------------------------------
   1) Literais — STATUS_REGISTRO
   ------------------------------------------------------------ */
SELECT
    STATUS_REGISTRO,
    COUNT(*) AS total
FROM dbo.vw_Apontamentos_Eficiencia
GROUP BY STATUS_REGISTRO
ORDER BY total DESC;


/* ------------------------------------------------------------
   2) Literais — STATUS_MOD
   ------------------------------------------------------------ */
SELECT
    STATUS_MOD,
    COUNT(*) AS total
FROM dbo.vw_Apontamentos_Eficiencia
GROUP BY STATUS_MOD
ORDER BY total DESC;


/* ------------------------------------------------------------
   3) Literais — STATUS_RESULTADO_MOD
   ------------------------------------------------------------ */
SELECT
    STATUS_RESULTADO_MOD,
    COUNT(*) AS total
FROM dbo.vw_Apontamentos_Eficiencia
GROUP BY STATUS_RESULTADO_MOD
ORDER BY total DESC;


/* ------------------------------------------------------------
   4) Filiais presentes na view
   ------------------------------------------------------------ */
SELECT
    FILIAL,
    COUNT(*) AS total,
    MIN(DATA_PRODUCAO) AS data_min,
    MAX(DATA_PRODUCAO) AS data_max
FROM dbo.vw_Apontamentos_Eficiencia
GROUP BY FILIAL
ORDER BY FILIAL;


/* ------------------------------------------------------------
   5) Volume — últimos 30 dias (por dia)
   ------------------------------------------------------------ */
SELECT
    DATA_PRODUCAO,
    COUNT(*) AS linhas_dia
FROM dbo.vw_Apontamentos_Eficiencia
WHERE DATA_PRODUCAO >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
GROUP BY DATA_PRODUCAO
ORDER BY DATA_PRODUCAO DESC;


/* ------------------------------------------------------------
   6) Volume — últimos 12 meses (por mês)
   ------------------------------------------------------------ */
SELECT
    YEAR(DATA_PRODUCAO) AS ano,
    MONTH(DATA_PRODUCAO) AS mes,
    COUNT(*) AS linhas_mes
FROM dbo.vw_Apontamentos_Eficiencia
WHERE DATA_PRODUCAO >= DATEADD(MONTH, -12, CAST(GETDATE() AS DATE))
GROUP BY YEAR(DATA_PRODUCAO), MONTH(DATA_PRODUCAO)
ORDER BY ano DESC, mes DESC;


/* ------------------------------------------------------------
   7) KPI de referência — eficiência ponderada (últimos 7 dias, somente OK)
   ------------------------------------------------------------ */
SELECT
    COUNT(*) AS appointment_count,
    SUM(CASE WHEN STATUS_REGISTRO <> 'OK' THEN 1 ELSE 0 END) AS invalid_record_count,
    CASE
        WHEN SUM(TEMPO_REAL_HORAS) > 0
        THEN ROUND(SUM(TEMPO_PREVISTO_HORAS) / SUM(TEMPO_REAL_HORAS) * 100.0, 2)
        ELSE NULL
    END AS weighted_efficiency_pct,
    ROUND(SUM(RESULTADO_MOD), 2) AS total_mod_result,
    ROUND(SUM(LUCRO_MOD), 2) AS total_mod_profit,
    ROUND(SUM(PREJUIZO_MOD), 2) AS total_mod_loss,
    ROUND(SUM(TEMPO_GANHO_PERDIDO_HORAS), 6) AS total_hours_gained_lost
FROM dbo.vw_Apontamentos_Eficiencia
WHERE DATA_PRODUCAO >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
  AND STATUS_REGISTRO = 'OK';


/* ------------------------------------------------------------
   8) Sanidade — CT-00 não deve aparecer
   ------------------------------------------------------------ */
SELECT COUNT(*) AS ct00_count
FROM dbo.vw_Apontamentos_Eficiencia
WHERE CENTRO_TRABALHO = 'CT-00';


/* ------------------------------------------------------------
   9) Sanidade — tempo real zero (impacto na agregação)
   ------------------------------------------------------------ */
SELECT
    STATUS_REGISTRO,
    COUNT(*) AS total
FROM dbo.vw_Apontamentos_Eficiencia
WHERE TEMPO_REAL_HORAS = 0 OR TEMPO_REAL_HORAS IS NULL
GROUP BY STATUS_REGISTRO
ORDER BY total DESC;


/* ------------------------------------------------------------
   10) Consulta sugerida para o dashboard (filtro por período)
   ------------------------------------------------------------ */
SELECT
    FILIAL,
    OP,
    PRODUTO,
    CENTRO_TRABALHO,
    OPERACAO,
    COD_OPERADOR,
    LOGIN_OPERADOR,
    NOME_OPERADOR,
    DATA_PRODUCAO,
    HORA_INICIO,
    HORA_FINAL,
    TEMPO_REAL_HORAS,
    TEMPO_PREVISTO_HORAS,
    EFICIENCIA_PERCENTUAL,
    VALOR_MOD_HORA,
    TEMPO_GANHO_PERDIDO_HORAS,
    RESULTADO_MOD,
    LUCRO_MOD,
    PREJUIZO_MOD,
    STATUS_RESULTADO_MOD,
    STATUS_REGISTRO
FROM dbo.vw_Apontamentos_Eficiencia
WHERE DATA_PRODUCAO BETWEEN @date_start AND @date_end
  AND (@branch IS NULL OR FILIAL = @branch)
  AND (@status_ok_only = 0 OR STATUS_REGISTRO = 'OK')
ORDER BY DATA_PRODUCAO DESC, HORA_INICIO DESC, HORA_FINAL DESC;
