-- Eventos AIJ010 em maio/2026 para OVs divergentes do controle interno (amostra)
SELECT
    RTRIM(A.AIJ_NROPOR) AS sale_number,
    RTRIM(A.AIJ_FILIAL) AS branch,
    A.AIJ_REVISA AS revision,
    A.AIJ_PROVEN AS process_code,
    A.AIJ_STAGE AS stage_code,
    A.AIJ_DTINIC AS start_date,
    A.AIJ_DTENCE AS end_date,
    RTRIM(A.AIJ_STATUS) AS status_code,
    RTRIM(A.AIJ_HISTOR) AS history_flag
FROM AIJ010 A
WHERE A.D_E_L_E_T_ = ''
  AND A.AIJ_NROPOR IN ('000090','000094','003562','003578','000120','003563','003561')
  AND A.AIJ_DTINIC BETWEEN '20260501' AND '20260531'
  AND (
        (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003','000008','000012'))
     OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003','000012','000002','000008'))
  )
ORDER BY A.AIJ_NROPOR, A.AIJ_DTINIC, A.AIJ_HRINIC, A.R_E_C_N_O_;
