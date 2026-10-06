SET NOCOUNT ON;
-- triggers on SA2010 / SA5010
SELECT 'trigger' k, t.name tbl, tr.name trg, tr.is_disabled
FROM sys.triggers tr JOIN sys.tables t ON t.object_id=tr.parent_id
WHERE t.name IN ('SA2010','SA5010','SA2010_TTAT_LOG','SA5010_TTAT_LOG');

-- TTAT_LOG structure (audit trail)
SELECT 'ttat_cols' k, c.name FROM sys.columns c JOIN sys.tables t ON c.object_id=t.object_id
WHERE t.name='SA2010_TTAT_LOG' ORDER BY c.column_id;
SELECT 'ttat_count' k, COUNT(*) v FROM SA2010_TTAT_LOG WITH (NOLOCK);

-- SXE sequence generator for SA2
SELECT 'SXE' k, * FROM SXE010 WHERE XE_ALIAS='SA2' AND D_E_L_E_T_<>'*';

-- SXE table columns context
SELECT 'sxe_cols' k, c.name FROM sys.columns c JOIN sys.tables t ON c.object_id=t.object_id
WHERE t.name='SXE010' ORDER BY c.column_id;

-- custom/Z tables physically present mentioning supplier
SELECT 'ztables' k, t.name, s.X2_NOME FROM sys.tables t
LEFT JOIN SX2010 s ON s.X2_CHAVE = LEFT(t.name,3)
WHERE (t.name LIKE 'Z%' OR t.name LIKE '[A-Z][A-Z0-9]X%')
AND t.name NOT LIKE '%\_BKP' ESCAPE '\' AND t.name NOT LIKE '%TTAT%' AND t.name NOT LIKE 'SIXX%' AND t.name NOT LIKE 'SX_X%' AND t.name NOT LIKE '%X31%' AND t.name NOT LIKE '%XNQ%'
ORDER BY t.name;

-- SA5 sample structure values (top fields, no PII)
SELECT 'sa5_loja' k, A5_LOJA d, COUNT(*) v FROM SA5010 WITH (NOLOCK) WHERE D_E_L_E_T_<>'*' GROUP BY A5_LOJA;
SELECT 'sa5_filial' k, A5_FILIAL d, COUNT(*) v FROM SA5010 WITH (NOLOCK) WHERE D_E_L_E_T_<>'*' GROUP BY A5_FILIAL;

-- SX5 tables used by SA2 validations/lookups
SELECT 'sx5_used' k, X5_TABELA, COUNT(*) v FROM SX5010 WITH (NOLOCK)
WHERE D_E_L_E_T_<>'*' AND X5_FILIAL='  ' AND X5_TABELA IN ('12','T3','Y7','58','48','MF','83','GRU','74','B9','H4','01','55','0I')
GROUP BY X5_TABELA ORDER BY X5_TABELA;
