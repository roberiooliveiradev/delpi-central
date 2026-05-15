/* ============================================================
   1) EVENTOS DA OV ENRIQUECIDOS
   ============================================================ */
CREATE OR ALTER VIEW dbo.VW_DELPI_OV_EVENTOS_ENRIQUECIDOS
AS
WITH TodosEventosOV AS (
    SELECT
        A.AIJ_FILIAL AS branch,
        A.AIJ_NROPOR AS sale_number,
        A.AIJ_REVISA AS revision,
        A.AIJ_PROVEN AS process_code,
        A.AIJ_STAGE AS stage_code,
        A.AIJ_DTINIC AS start_date_raw,
        A.AIJ_HRINIC AS start_time_raw,
        A.AIJ_DTLIMI AS limit_date_raw,
        A.AIJ_HRLIMI AS limit_time_raw,
        A.AIJ_DTENCE AS end_date_raw,
        A.AIJ_HRENCE AS end_time_raw,
        A.AIJ_HISTOR AS history_text,
        A.AIJ_STATUS AS status_code,
        A.R_E_C_N_O_ AS recno,
        ROW_NUMBER() OVER (
            PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
            ORDER BY
                A.AIJ_REVISA,
                A.AIJ_DTINIC,
                A.AIJ_HRINIC,
                A.AIJ_STAGE,
                A.R_E_C_N_O_
        ) AS global_order
    FROM AIJ010 A
    WHERE A.D_E_L_E_T_ = ''
)
SELECT
    E.branch,
    E.sale_number,
    E.revision,
    E.process_code,
    E.stage_code,
    E.start_date_raw,
    E.start_time_raw,
    E.limit_date_raw,
    E.limit_time_raw,
    E.end_date_raw,
    E.end_time_raw,
    E.history_text,
    E.status_code,
    E.recno,
    E.global_order,
    NX.revision AS next_revision,
    NX.process_code AS next_process_code,
    NX.stage_code AS next_stage_code,
    NX.start_date_raw AS next_start_date_raw,
    NX.start_time_raw AS next_start_time_raw,
    NX.end_date_raw AS next_end_date_raw,
    NX.end_time_raw AS next_end_time_raw,
    NX.recno AS next_recno
FROM TodosEventosOV E
OUTER APPLY (
    SELECT TOP 1
        X.revision,
        X.process_code,
        X.stage_code,
        X.start_date_raw,
        X.start_time_raw,
        X.end_date_raw,
        X.end_time_raw,
        X.recno
    FROM TodosEventosOV X
    WHERE
        X.branch = E.branch
        AND X.sale_number = E.sale_number
        AND X.global_order > E.global_order
        AND (
            X.start_date_raw > E.start_date_raw
            OR (
                X.start_date_raw = E.start_date_raw
                AND ISNULL(X.start_time_raw, '') > ISNULL(E.start_time_raw, '')
            )
        )
    ORDER BY
        X.start_date_raw,
        X.start_time_raw,
        X.revision,
        X.stage_code,
        X.recno
) NX;
GO

/* ============================================================
   2) CABEÇALHO COMERCIAL DA OV
   ============================================================ */
CREATE OR ALTER VIEW dbo.VW_DELPI_OV_HEADER_BASE
AS
SELECT
    AD1.AD1_FILIAL AS branch,
    AD1.AD1_NROPOR AS sale_number,
    AD1.AD1_REVISA AS revision,
    AD1.AD1_DESCRI AS sale_description,
    AD1.AD1_CODCLI AS costumer_code,
    AD1.AD1_LOJCLI AS costumer_store,
    SA1.A1_NOME AS costumer_name,
    AD1.AD1_VEND AS seller_code,
    SA3.A3_NOME AS seller_name
FROM AD1010 AD1
LEFT JOIN SA1010 SA1
    ON SA1.A1_COD = AD1.AD1_CODCLI
   AND SA1.A1_LOJA = AD1.AD1_LOJCLI
   AND SA1.D_E_L_E_T_ = ''
LEFT JOIN SA3010 SA3
    ON SA3.A3_COD = AD1.AD1_VEND
   AND SA3.D_E_L_E_T_ = ''
WHERE AD1.D_E_L_E_T_ = '';
GO

/* ============================================================
   3) PRODUTOS BASE DA LMP
   ============================================================ */
CREATE OR ALTER VIEW dbo.VW_DELPI_LMP_PRODUTOS_BASE
AS
SELECT DISTINCT
    ADJ.ADJ_FILIAL AS branch,
    ADJ.ADJ_NROPOR AS sale_number,
    ADJ.ADJ_REVISA AS revision,
    ADJ.ADJ_PROD AS product_code,
    SB1.B1_GRUPO AS group_code,
    SB1.B1_COD AS code,
    SB1.B1_DESC AS description,
    SB1.B1_TIPO AS type,
    SB1.B1_REFEREN AS reference
FROM ADJ010 ADJ
INNER JOIN AD1010 AD1
    ON AD1.AD1_FILIAL = ADJ.ADJ_FILIAL
   AND AD1.AD1_NROPOR = ADJ.ADJ_NROPOR
   AND AD1.AD1_REVISA = ADJ.ADJ_REVISA
   AND AD1.D_E_L_E_T_ = ''
INNER JOIN SB1010 SB1
    ON SB1.B1_COD = ADJ.ADJ_PROD
   AND SB1.D_E_L_E_T_ = ''
WHERE ADJ.D_E_L_E_T_ = '';
GO

/* ============================================================
   4) CADASTRO BASE DE PRODUTOS
   ============================================================ */
CREATE OR ALTER VIEW dbo.VW_DELPI_PRODUTOS_BASE
AS
SELECT
    SB1.B1_COD AS code,
    SB1.B1_DESC AS description,
    SB1.B1_GRUPO AS group_code,
    SB1.B1_TIPO AS type,
    SB1.B1_REFEREN AS reference,
    SB1.B1_UM AS unit
FROM SB1010 SB1
WHERE SB1.D_E_L_E_T_ = '';
GO

/* ============================================================
   5) ARESTAS ATIVAS DA BOM
   ============================================================ */
CREATE OR ALTER VIEW dbo.VW_DELPI_BOM_ARESTAS_ATIVAS
AS
SELECT
    G.G1_COD AS parent_code,
    G.G1_COMP AS component_code,
    G.G1_QUANT AS quantity,
    SB1.B1_UM AS unit,
    G.G1_INI AS start_validity,
    G.G1_FIM AS end_validity
FROM SG1010 G
LEFT JOIN SB1010 SB1
    ON SB1.B1_COD = G.G1_COMP
   AND SB1.D_E_L_E_T_ = ''
WHERE
    G.D_E_L_E_T_ = ''
    AND G.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112);
GO

/* ============================================================
   6) RELAÇÃO PRODUTO ↔ RAIZ POR REFERÊNCIA
   ============================================================ */
CREATE OR ALTER VIEW dbo.VW_DELPI_PRODUTO_REFERENCIA_RAIZ
AS
SELECT DISTINCT
    P.code AS product_code,
    P.reference AS product_reference,
    R.code AS root_code,
    R.type AS root_type,
    R.reference AS root_reference
FROM dbo.VW_DELPI_PRODUTOS_BASE P
INNER JOIN dbo.VW_DELPI_PRODUTOS_BASE R
    ON R.reference = P.reference
WHERE ISNULL(P.reference, '') <> '';
GO

/* ============================================================
   7) RESUMO BASE DA LMP
   ============================================================ */
CREATE OR ALTER VIEW dbo.VW_DELPI_LMP_RESUMO_BASE
AS
SELECT DISTINCT
    H.branch,
    H.sale_number,
    H.revision,
    H.sale_description,
    H.costumer_code,
    H.costumer_store,
    H.costumer_name,
    H.seller_code,
    H.seller_name
FROM dbo.VW_DELPI_OV_HEADER_BASE H;
GO