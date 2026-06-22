-- Histórico completo maio/2026 ± contexto: 087, 102, 561, 2871
-- Objetivo: revisões, reaberturas, homolog, engenharia por revisão
SELECT
    RTRIM(A.AIJ_NROPOR) AS sale_number,
    RTRIM(A.AIJ_FILIAL) AS branch,
    A.AIJ_REVISA AS revision,
    A.AIJ_PROVEN AS process_code,
    A.AIJ_STAGE AS stage_code,
    A.AIJ_DTINIC AS start_date,
    A.AIJ_HRINIC AS start_time,
    A.AIJ_DTENCE AS end_date,
    A.AIJ_HRENCE AS end_time,
    RTRIM(A.AIJ_STATUS) AS status_code
FROM AIJ010 A
WHERE A.D_E_L_E_T_ = ''
  AND (
        (A.AIJ_NROPOR = '000087' AND A.AIJ_FILIAL = '02')
     OR (A.AIJ_NROPOR = '000102' AND A.AIJ_FILIAL = '02')
     OR (A.AIJ_NROPOR = '003561' AND A.AIJ_FILIAL = '01')
     OR (A.AIJ_NROPOR = '002871' AND A.AIJ_FILIAL = '01')
  )
  AND (
        (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003','000008','000012','000013'))
     OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003','000012','000002','000008','000013'))
  )
ORDER BY A.AIJ_NROPOR, A.AIJ_FILIAL, A.AIJ_DTINIC, A.AIJ_HRINIC, A.R_E_C_N_O_;
