SET NOCOUNT ON;
-- SA5 dictionary entry
SELECT * FROM SX2010 WHERE X2_CHAVE='SA5';
-- SA5 full field metadata (empresa 01)
SELECT X3_ORDEM,X3_CAMPO,X3_TIPO,X3_TAMANHO,X3_DECIMAL,X3_TITULO,X3_DESCRIC,X3_PICTURE,
       X3_VALID,X3_RELACAO,X3_F3,X3_CBOX,X3_WHEN,X3_OBRIGAT,X3_USADO,X3_PROPRI,X3_CONDSQL
FROM SX3010 WHERE X3_ARQUIVO='SA5' AND D_E_L_E_T_<>'*' ORDER BY X3_ORDEM;
-- SA5 indexes
SELECT * FROM SIX010 WHERE INDICE='SA5' AND D_E_L_E_T_<>'*' ORDER BY ORDEM;
-- physical indexes on SA2010 and SA5010
SELECT t.name AS tbl, i.name AS idx, i.is_unique, i.is_primary_key,
       STUFF((SELECT ','+c.name FROM sys.index_columns ic JOIN sys.columns c
              ON c.object_id=ic.object_id AND c.column_id=ic.column_id
              WHERE ic.object_id=i.object_id AND ic.index_id=i.index_id
              ORDER BY ic.key_ordinal FOR XML PATH('')),1,1,'') AS cols
FROM sys.indexes i JOIN sys.tables t ON t.object_id=i.object_id
WHERE t.name IN ('SA2010','SA5010') AND i.type>0 ORDER BY t.name, i.index_id;
-- field list diff empresa 01 vs 03 for SA2
SELECT 'only_01' side, X3_CAMPO, X3_TITULO FROM SX3010 WHERE X3_ARQUIVO='SA2' AND D_E_L_E_T_<>'*'
  AND X3_CAMPO NOT IN (SELECT X3_CAMPO FROM SX3030 WHERE X3_ARQUIVO='SA2' AND D_E_L_E_T_<>'*')
UNION ALL
SELECT 'only_03', X3_CAMPO, X3_TITULO FROM SX3030 WHERE X3_ARQUIVO='SA2' AND D_E_L_E_T_<>'*'
  AND X3_CAMPO NOT IN (SELECT X3_CAMPO FROM SX3010 WHERE X3_ARQUIVO='SA2' AND D_E_L_E_T_<>'*')
ORDER BY 1,2;
-- diff 01 vs 05
SELECT 'only_01' side, X3_CAMPO FROM SX3010 WHERE X3_ARQUIVO='SA2' AND D_E_L_E_T_<>'*'
  AND X3_CAMPO NOT IN (SELECT X3_CAMPO FROM SX3050 WHERE X3_ARQUIVO='SA2' AND D_E_L_E_T_<>'*')
UNION ALL
SELECT 'only_05', X3_CAMPO FROM SX3050 WHERE X3_ARQUIVO='SA2' AND D_E_L_E_T_<>'*'
  AND X3_CAMPO NOT IN (SELECT X3_CAMPO FROM SX3010 WHERE X3_ARQUIVO='SA2' AND D_E_L_E_T_<>'*')
ORDER BY 1,2;
