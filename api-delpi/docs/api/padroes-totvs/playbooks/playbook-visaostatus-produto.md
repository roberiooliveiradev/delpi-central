# Playbook Final DELPI — Visão Completa do Status de um Produto na Fábrica

## 1. Objetivo

Este playbook consolida a visão completa de um produto dentro da fábrica DELPI.

A visão deve responder:

- Qual é a estrutura vigente do produto?
- Quais intermediários fazem parte do produto?
- Quais matérias-primas compõem o produto?
- Quais matérias-primas são exclusivas desse produto?
- Existe estoque das matérias-primas?
- O PA e seus intermediários já começaram a ser produzidos?
- Quanto foi produzido?
- Quanto do PA já passou pela inspeção final?
- Quanto do PA já está liberado para expedição?
- Existem perdas na inspeção final?
- Quais OPs estão envolvidas?
- Qual o status real do produto na fábrica?

---

## 2. Regra-mãe da visão do produto

```text
Status fabril de um produto =
estrutura vigente
+ intermediários
+ matérias-primas
+ exclusividade das MPs
+ estoque das MPs
+ OPs do PA e dos PIs
+ apontamentos produtivos
+ apontamento do PA no CT de inspeção final
+ quantidade finalizada para expedição.
```

---

## 3. Tabelas usadas

### 3.1 Estrutura e cadastro

| Tabela | Função |
|---|---|
| `SG1010` | Estrutura do produto / BOM |
| `SB1010` | Cadastro de produtos |

Campos principais:

```text
SG1010.G1_COD     = Produto pai
SG1010.G1_COMP    = Componente
SG1010.G1_QUANT   = Quantidade
SG1010.G1_INI     = Início da vigência
SG1010.G1_FIM     = Fim da vigência

SB1010.B1_COD     = Código do produto
SB1010.B1_DESC    = Descrição
SB1010.B1_TIPO    = Tipo: PA, PI, MP
SB1010.B1_UM      = Unidade
SB1010.B1_GRUPO   = Grupo
```

---

### 3.2 Estoque

| Tabela | Função |
|---|---|
| `SB2010` | Saldos em estoque |

Campos principais:

```text
B2_FILIAL
B2_COD
B2_LOCAL
B2_QATU
B2_QEMP
B2_RESERVA
```

Quantidade disponível:

```sql
B2_QATU - B2_QEMP - B2_RESERVA
```

---

### 3.3 Produção

| Tabela | Função |
|---|---|
| `SC2010` | Ordens de produção |
| `SH6010` | Apontamentos reais de produção |
| `SH8010` | Operações alocadas da OP |
| `SH1010` | Recursos |
| `SHB010` | Centros de trabalho |

Campos principais da `SC2010`:

```text
C2_FILIAL
C2_OP
C2_NUM
C2_ITEM
C2_SEQUEN
C2_PRODUTO
C2_QUANT
C2_QUJE
C2_DATPRI
C2_DATPRF
C2_DATRF
C2_STATUS
```

Campos principais da `SH6010`:

```text
H6_FILIAL
H6_OP
H6_PRODUTO
H6_OPERAC
H6_RECURSO
H6_QTDPROD
H6_QTDPERD
H6_DATAINI
H6_HORAINI
H6_DATAFIN
H6_HORAFIN
H6_DTAPONT
```

Campos principais da `SH1010`:

```text
H1_FILIAL
H1_CODIGO
H1_DESCRI
H1_CTRAB
```

Campos principais da `SHB010`:

```text
HB_FILIAL
HB_COD
HB_NOME
HB_CC
```

---

## 4. Tipos de produto

| Tipo | Significado |
|---|---|
| `PA` | Produto acabado |
| `PI` | Produto intermediário |
| `MP` | Matéria-prima |

Regras:

```text
PA = produto final, pode ir para expedição.
PI = intermediário, pertence à produção.
MP = matéria-prima, deve ter estoque analisado.
```

---

## 5. Filtro obrigatório de registros ativos

Todas as consultas devem considerar:

```sql
D_E_L_E_T_ = ''
```

Nunca considerar registros deletados logicamente.

---

## 6. Filtro obrigatório de vigência da estrutura

Para estrutura atual:

```sql
AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
```

Para estrutura válida em uma data de referência:

```sql
AND (G1.G1_INI = '' OR G1.G1_INI <= @DATA_REF)
AND (G1.G1_FIM = '' OR G1.G1_FIM >= @DATA_REF)
```

---

## 7. Data de referência

Toda análise fabril deve considerar uma data.

```sql
DECLARE @DATA_REF VARCHAR(8);
SET @DATA_REF = '20260604';
```

Para usar a data atual:

```sql
SET @DATA_REF = CONVERT(CHAR(8), GETDATE(), 112);
```

Formato:

```text
AAAAMMDD
```

---

## 8. CTs de inspeção final confirmados

A tabela `SHB010` confirmou:

| Filial | CT | Nome |
|---|---|---|
| `01` | `CT-70` | `INSPEÇÃO FINAL` |
| `02` | `CT-99` | `INSPECAO FINAL` |

Regra dinâmica para localizar CT de inspeção final:

```sql
UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
```

Não fixar apenas `CT-70`, pois a filial 02 usa `CT-99`.

---

## 9. Conceitos principais da visão

### 9.1 Estrutura vigente

A estrutura vigente é a BOM aberta pela `SG1010`, em todos os níveis, filtrando vigência.

Intermediários precisam ser abertos recursivamente.

---

### 9.2 Matéria-prima exclusiva

Uma MP é exclusiva quando aparece em apenas um PA válido.

Regra:

```text
MP exclusiva =
matéria-prima que aparece em apenas 1 produto acabado válido,
considerando todos os níveis da estrutura.
```

PAs de teste/amostra devem ser ignorados:

```sql
AND PA.B1_COD NOT LIKE '8000%'
AND PA.B1_COD NOT LIKE '8001%'
```

---

### 9.3 Estoque de matéria-prima

Estoque deve ser consultado pela `SB2010`.

Quantidade disponível:

```sql
B2_QATU - B2_QEMP - B2_RESERVA
```

---

### 9.4 Produção iniciada

Produção iniciada pode ser identificada por apontamento na `SH6010`.

Critério:

```text
Existe apontamento na SH6010 para o PA ou PI.
```

Fallback:

```text
Se não houver SH6010, mas SC2010.C2_QUJE > 0, existe produção registrada na OP.
```

---

### 9.5 Expedição

Expedição, pela regra operacional validada:

```text
PA apontado no CT de inspeção final = PA finalizado/liberado para expedição.
```

Quantidade em expedição:

```text
SUM(H6_QTDPROD) dos apontamentos do PA no CT de INSPEÇÃO FINAL.
```

Perda na inspeção:

```text
SUM(H6_QTDPERD) dos apontamentos do PA no CT de INSPEÇÃO FINAL.
```

Atenção:

```text
PI não entra em expedição.
Somente PA entra em expedição.
```

---

## 10. Query 1 — Estrutura completa vigente do produto

```sql
DECLARE @PRODUTO VARCHAR(30);
DECLARE @MAX_DEPTH INT;

SET @PRODUTO = '90261255';
SET @MAX_DEPTH = 50;

WITH ESTRUTURA AS (
    SELECT
        G1.G1_COD AS PRODUTO_PAI,
        G1.G1_COMP AS COMPONENTE,
        CAST(G1.G1_QUANT AS FLOAT) AS QTD_POR,
        CAST(G1.G1_QUANT AS FLOAT) AS QTD_ACUMULADA,
        1 AS NIVEL,
        CAST(G1.G1_COD + ' > ' + G1.G1_COMP AS VARCHAR(MAX)) AS CAMINHO
    FROM SG1010 G1 WITH (NOLOCK)
    WHERE
        G1.D_E_L_E_T_ = ''
        AND G1.G1_COD = @PRODUTO
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

    UNION ALL

    SELECT
        G1.G1_COD,
        G1.G1_COMP,
        CAST(G1.G1_QUANT AS FLOAT),
        CAST(E.QTD_ACUMULADA * CAST(G1.G1_QUANT AS FLOAT) AS FLOAT),
        E.NIVEL + 1,
        CAST(E.CAMINHO + ' > ' + G1.G1_COMP AS VARCHAR(MAX))
    FROM SG1010 G1 WITH (NOLOCK)
    INNER JOIN ESTRUTURA E
        ON E.COMPONENTE = G1.G1_COD
    WHERE
        G1.D_E_L_E_T_ = ''
        AND E.NIVEL < @MAX_DEPTH
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
)

SELECT
    E.NIVEL,
    E.PRODUTO_PAI,
    PAI.B1_DESC AS DESC_PRODUTO_PAI,
    E.COMPONENTE,
    COMP.B1_DESC AS DESC_COMPONENTE,
    COMP.B1_TIPO AS TIPO_COMPONENTE,
    COMP.B1_UM AS UNIDADE_COMPONENTE,
    COMP.B1_GRUPO AS GRUPO_COMPONENTE,
    CAST(E.QTD_POR AS VARCHAR(50)) AS QTD_POR,
    CAST(E.QTD_ACUMULADA AS VARCHAR(50)) AS QTD_ACUMULADA,
    E.CAMINHO
FROM ESTRUTURA E
LEFT JOIN SB1010 PAI WITH (NOLOCK)
    ON PAI.B1_COD = E.PRODUTO_PAI
   AND PAI.D_E_L_E_T_ = ''
LEFT JOIN SB1010 COMP WITH (NOLOCK)
    ON COMP.B1_COD = E.COMPONENTE
   AND COMP.D_E_L_E_T_ = ''
ORDER BY
    E.CAMINHO
OPTION (MAXRECURSION 0);
```

---

## 11. Query 2 — Estrutura com matérias-primas exclusivas

Esta query abre a estrutura do produto e marca as MPs exclusivas, considerando intermediários.

```sql
DECLARE @PRODUTO VARCHAR(30);
DECLARE @MAX_DEPTH INT;

SET @PRODUTO = '90261255';
SET @MAX_DEPTH = 50;

WITH ESTRUTURA_PRODUTO AS (
    SELECT
        G1.G1_COD AS PRODUTO_PAI,
        G1.G1_COMP AS COMPONENTE,
        G1.G1_QUANT AS QTD_POR,
        CAST(G1.G1_QUANT AS FLOAT) AS QTD_ACUMULADA,
        1 AS NIVEL,
        CAST(G1.G1_COD + ' > ' + G1.G1_COMP AS VARCHAR(MAX)) AS CAMINHO
    FROM SG1010 G1 WITH (NOLOCK)
    WHERE
        G1.D_E_L_E_T_ = ''
        AND G1.G1_COD = @PRODUTO
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

    UNION ALL

    SELECT
        G1.G1_COD,
        G1.G1_COMP,
        G1.G1_QUANT,
        CAST(EP.QTD_ACUMULADA * CAST(G1.G1_QUANT AS FLOAT) AS FLOAT),
        EP.NIVEL + 1,
        CAST(EP.CAMINHO + ' > ' + G1.G1_COMP AS VARCHAR(MAX))
    FROM SG1010 G1 WITH (NOLOCK)
    INNER JOIN ESTRUTURA_PRODUTO EP
        ON EP.COMPONENTE = G1.G1_COD
    WHERE
        G1.D_E_L_E_T_ = ''
        AND EP.NIVEL < @MAX_DEPTH
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
),

MATERIAS_PRIMAS_DO_PRODUTO AS (
    SELECT DISTINCT
        EP.COMPONENTE AS COD_MP
    FROM ESTRUTURA_PRODUTO EP
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = EP.COMPONENTE
       AND SB1.D_E_L_E_T_ = ''
    WHERE
        SB1.B1_TIPO = 'MP'
),

TODAS_ESTRUTURAS_VALIDAS AS (
    SELECT
        PA.B1_COD AS PA_RAIZ,
        PA.B1_DESC AS DESC_PA_RAIZ,
        G1.G1_COD AS PRODUTO_PAI,
        G1.G1_COMP AS COMPONENTE,
        1 AS NIVEL
    FROM SG1010 G1 WITH (NOLOCK)
    INNER JOIN SB1010 PA WITH (NOLOCK)
        ON PA.B1_COD = G1.G1_COD
       AND PA.D_E_L_E_T_ = ''
       AND PA.B1_TIPO = 'PA'
       AND PA.B1_COD NOT LIKE '8000%'
       AND PA.B1_COD NOT LIKE '8001%'
    WHERE
        G1.D_E_L_E_T_ = ''
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

    UNION ALL

    SELECT
        TE.PA_RAIZ,
        TE.DESC_PA_RAIZ,
        G1.G1_COD,
        G1.G1_COMP,
        TE.NIVEL + 1
    FROM TODAS_ESTRUTURAS_VALIDAS TE
    INNER JOIN SG1010 G1 WITH (NOLOCK)
        ON G1.G1_COD = TE.COMPONENTE
       AND G1.D_E_L_E_T_ = ''
       AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
    WHERE
        TE.NIVEL < @MAX_DEPTH
),

USO_MP_EM_PA AS (
    SELECT
        TE.COMPONENTE AS COD_MP,
        COUNT(DISTINCT TE.PA_RAIZ) AS TOTAL_PAS_VALIDOS
    FROM TODAS_ESTRUTURAS_VALIDAS TE
    INNER JOIN MATERIAS_PRIMAS_DO_PRODUTO MP
        ON MP.COD_MP = TE.COMPONENTE
    GROUP BY
        TE.COMPONENTE
)

SELECT
    EP.NIVEL,
    EP.PRODUTO_PAI,
    PAI.B1_DESC AS DESC_PRODUTO_PAI,
    EP.COMPONENTE,
    COMP.B1_DESC AS DESC_COMPONENTE,
    COMP.B1_TIPO AS TIPO_COMPONENTE,
    COMP.B1_UM AS UNIDADE_COMPONENTE,
    COMP.B1_GRUPO AS GRUPO_COMPONENTE,
    CAST(EP.QTD_POR AS VARCHAR(50)) AS QTD_POR,
    CAST(EP.QTD_ACUMULADA AS VARCHAR(50)) AS QTD_ACUMULADA,
    CASE
        WHEN COMP.B1_TIPO = 'MP' AND ISNULL(U.TOTAL_PAS_VALIDOS, 0) = 1 THEN 'SIM'
        WHEN COMP.B1_TIPO = 'MP' THEN 'NAO'
        ELSE NULL
    END AS MP_EXCLUSIVA,
    CASE
        WHEN COMP.B1_TIPO = 'MP' THEN ISNULL(U.TOTAL_PAS_VALIDOS, 0)
        ELSE NULL
    END AS TOTAL_PAS_VALIDOS_ONDE_MP_APARECE,
    EP.CAMINHO
FROM ESTRUTURA_PRODUTO EP
LEFT JOIN SB1010 PAI WITH (NOLOCK)
    ON PAI.B1_COD = EP.PRODUTO_PAI
   AND PAI.D_E_L_E_T_ = ''
LEFT JOIN SB1010 COMP WITH (NOLOCK)
    ON COMP.B1_COD = EP.COMPONENTE
   AND COMP.D_E_L_E_T_ = ''
LEFT JOIN USO_MP_EM_PA U
    ON U.COD_MP = EP.COMPONENTE
ORDER BY
    EP.CAMINHO
OPTION (MAXRECURSION 0);
```

---

## 12. Query 3 — Estoque das matérias-primas do produto

Esta query abre a estrutura, localiza as MPs e consulta o estoque de cada uma.

```sql
DECLARE @PRODUTO VARCHAR(30);
DECLARE @MAX_DEPTH INT;

SET @PRODUTO = '90261255';
SET @MAX_DEPTH = 50;

WITH ESTRUTURA AS (
    SELECT
        G1.G1_COD AS PRODUTO_PAI,
        G1.G1_COMP AS COMPONENTE,
        CAST(G1.G1_QUANT AS FLOAT) AS QTD_ACUMULADA,
        1 AS NIVEL
    FROM SG1010 G1 WITH (NOLOCK)
    WHERE
        G1.D_E_L_E_T_ = ''
        AND G1.G1_COD = @PRODUTO
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

    UNION ALL

    SELECT
        G1.G1_COD,
        G1.G1_COMP,
        CAST(E.QTD_ACUMULADA * CAST(G1.G1_QUANT AS FLOAT) AS FLOAT),
        E.NIVEL + 1
    FROM SG1010 G1 WITH (NOLOCK)
    INNER JOIN ESTRUTURA E
        ON E.COMPONENTE = G1.G1_COD
    WHERE
        G1.D_E_L_E_T_ = ''
        AND E.NIVEL < @MAX_DEPTH
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
),

MPS AS (
    SELECT DISTINCT
        E.COMPONENTE AS COD_MP,
        SUM(E.QTD_ACUMULADA) AS QTD_NECESSARIA_PARA_1_PA
    FROM ESTRUTURA E
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = E.COMPONENTE
       AND SB1.D_E_L_E_T_ = ''
       AND SB1.B1_TIPO = 'MP'
    GROUP BY
        E.COMPONENTE
),

ESTOQUE AS (
    SELECT
        B2.B2_COD,
        B2.B2_FILIAL,
        B2.B2_LOCAL,
        SUM(CAST(B2.B2_QATU AS FLOAT)) AS QTD_ATUAL,
        SUM(CAST(B2.B2_QEMP AS FLOAT)) AS QTD_EMPENHADA,
        SUM(CAST(B2.B2_RESERVA AS FLOAT)) AS QTD_RESERVADA,
        SUM(CAST(B2.B2_QATU - B2.B2_QEMP - B2.B2_RESERVA AS FLOAT)) AS QTD_DISPONIVEL
    FROM SB2010 B2 WITH (NOLOCK)
    WHERE
        B2.D_E_L_E_T_ = ''
    GROUP BY
        B2.B2_COD,
        B2.B2_FILIAL,
        B2.B2_LOCAL
)

SELECT
    MP.COD_MP,
    SB1.B1_DESC AS DESC_MP,
    SB1.B1_UM AS UNIDADE,
    SB1.B1_GRUPO AS GRUPO,
    CAST(MP.QTD_NECESSARIA_PARA_1_PA AS VARCHAR(50)) AS QTD_NECESSARIA_PARA_1_PA,
    E.B2_FILIAL AS FILIAL,
    E.B2_LOCAL AS ARMAZEM,
    CAST(ISNULL(E.QTD_ATUAL, 0) AS VARCHAR(50)) AS QTD_ATUAL,
    CAST(ISNULL(E.QTD_EMPENHADA, 0) AS VARCHAR(50)) AS QTD_EMPENHADA,
    CAST(ISNULL(E.QTD_RESERVADA, 0) AS VARCHAR(50)) AS QTD_RESERVADA,
    CAST(ISNULL(E.QTD_DISPONIVEL, 0) AS VARCHAR(50)) AS QTD_DISPONIVEL,
    CASE
        WHEN ISNULL(E.QTD_DISPONIVEL, 0) >= MP.QTD_NECESSARIA_PARA_1_PA THEN 'SIM'
        ELSE 'NAO'
    END AS TEM_ESTOQUE_PARA_1_PA
FROM MPS MP
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = MP.COD_MP
   AND SB1.D_E_L_E_T_ = ''
LEFT JOIN ESTOQUE E
    ON E.B2_COD = MP.COD_MP
ORDER BY
    MP.COD_MP,
    E.B2_FILIAL,
    E.B2_LOCAL
OPTION (MAXRECURSION 0);
```

---

## 13. Query 4 — Status produtivo do PA e intermediários

Esta query mostra se o PA e seus PIs já começaram a ser produzidos.

```sql
DECLARE @PRODUTO VARCHAR(30);
DECLARE @DATA_REF VARCHAR(8);
DECLARE @MAX_DEPTH INT;

SET @PRODUTO = '90261255';
SET @DATA_REF = '20260604';
SET @MAX_DEPTH = 50;

WITH ESTRUTURA AS (
    SELECT
        G1.G1_COD AS PRODUTO_PAI,
        G1.G1_COMP AS COMPONENTE,
        CAST(G1.G1_QUANT AS FLOAT) AS QTD_NECESSARIA_PARA_1_PA,
        1 AS NIVEL,
        CAST(G1.G1_COD + ' > ' + G1.G1_COMP AS VARCHAR(MAX)) AS CAMINHO
    FROM SG1010 G1 WITH (NOLOCK)
    WHERE
        G1.D_E_L_E_T_ = ''
        AND G1.G1_COD = @PRODUTO
        AND (G1.G1_INI = '' OR G1.G1_INI <= @DATA_REF)
        AND (G1.G1_FIM = '' OR G1.G1_FIM >= @DATA_REF)

    UNION ALL

    SELECT
        G1.G1_COD,
        G1.G1_COMP,
        CAST(E.QTD_NECESSARIA_PARA_1_PA * CAST(G1.G1_QUANT AS FLOAT) AS FLOAT),
        E.NIVEL + 1,
        CAST(E.CAMINHO + ' > ' + G1.G1_COMP AS VARCHAR(MAX))
    FROM SG1010 G1 WITH (NOLOCK)
    INNER JOIN ESTRUTURA E
        ON E.COMPONENTE = G1.G1_COD
    WHERE
        G1.D_E_L_E_T_ = ''
        AND E.NIVEL < @MAX_DEPTH
        AND (G1.G1_INI = '' OR G1.G1_INI <= @DATA_REF)
        AND (G1.G1_FIM = '' OR G1.G1_FIM >= @DATA_REF)
),

ESCOPO_PRODUCAO AS (
    SELECT
        0 AS NIVEL,
        @PRODUTO AS CODIGO,
        CAST(1 AS FLOAT) AS QTD_NECESSARIA_PARA_1_PA,
        CAST(@PRODUTO AS VARCHAR(MAX)) AS CAMINHO

    UNION

    SELECT
        E.NIVEL,
        E.COMPONENTE,
        E.QTD_NECESSARIA_PARA_1_PA,
        E.CAMINHO
    FROM ESTRUTURA E
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = E.COMPONENTE
       AND SB1.D_E_L_E_T_ = ''
    WHERE
        SB1.B1_TIPO IN ('PA', 'PI')
),

OPS AS (
    SELECT
        EP.NIVEL,
        EP.CODIGO,
        EP.QTD_NECESSARIA_PARA_1_PA,
        EP.CAMINHO,
        SC2.C2_FILIAL,
        SC2.C2_OP,
        SC2.C2_NUM,
        SC2.C2_ITEM,
        SC2.C2_SEQUEN,
        SC2.C2_PRODUTO,
        CAST(SC2.C2_QUANT AS FLOAT) AS QTD_OP,
        CAST(SC2.C2_QUJE AS FLOAT) AS QTD_PRODUZIDA_SC2,
        SC2.C2_DATPRI,
        SC2.C2_DATPRF,
        SC2.C2_DATRF,
        SC2.C2_STATUS
    FROM ESCOPO_PRODUCAO EP
    LEFT JOIN SC2010 SC2 WITH (NOLOCK)
        ON SC2.C2_PRODUTO = EP.CODIGO
       AND SC2.D_E_L_E_T_ = ''
),

APONTAMENTOS AS (
    SELECT
        H6_FILIAL,
        H6_OP,
        H6_PRODUTO,
        SUM(CAST(H6_QTDPROD AS FLOAT)) AS QTD_APONTADA,
        SUM(CAST(H6_QTDPERD AS FLOAT)) AS QTD_PERDIDA,
        MIN(H6_DATAINI) AS PRIMEIRO_INICIO,
        MIN(H6_HORAINI) AS PRIMEIRA_HORA,
        MAX(H6_DTAPONT) AS ULTIMO_APONTAMENTO,
        COUNT(*) AS TOTAL_APONTAMENTOS
    FROM SH6010 WITH (NOLOCK)
    WHERE
        D_E_L_E_T_ = ''
        AND H6_DTAPONT <= @DATA_REF
    GROUP BY
        H6_FILIAL,
        H6_OP,
        H6_PRODUTO
)

SELECT
    O.NIVEL,
    O.CODIGO AS PRODUTO_ROTA,
    SB1.B1_DESC AS DESCRICAO,
    SB1.B1_TIPO AS TIPO,
    SB1.B1_UM AS UNIDADE,
    CAST(O.QTD_NECESSARIA_PARA_1_PA AS VARCHAR(50)) AS QTD_NECESSARIA_PARA_1_PA,
    O.C2_FILIAL AS FILIAL,
    O.C2_OP AS OP,
    CAST(ISNULL(O.QTD_OP, 0) AS VARCHAR(50)) AS QTD_OP,
    CAST(ISNULL(O.QTD_PRODUZIDA_SC2, 0) AS VARCHAR(50)) AS QTD_PRODUZIDA_SC2,
    CAST(ISNULL(A.QTD_APONTADA, 0) AS VARCHAR(50)) AS QTD_APONTADA_SH6,
    CAST(ISNULL(A.QTD_PERDIDA, 0) AS VARCHAR(50)) AS QTD_PERDIDA_SH6,
    ISNULL(A.TOTAL_APONTAMENTOS, 0) AS TOTAL_APONTAMENTOS,
    CASE
        WHEN ISNULL(A.TOTAL_APONTAMENTOS, 0) > 0 THEN 'SIM'
        WHEN ISNULL(O.QTD_PRODUZIDA_SC2, 0) > 0 THEN 'SIM_SC2'
        ELSE 'NAO'
    END AS PRODUCAO_INICIADA,
    CAST(CASE
        WHEN ISNULL(O.QTD_OP, 0) > 0 THEN (ISNULL(A.QTD_APONTADA, ISNULL(O.QTD_PRODUZIDA_SC2, 0)) / O.QTD_OP) * 100
        ELSE 0
    END AS VARCHAR(50)) AS PERCENTUAL_DA_OP_PRODUZIDO,
    CAST(CASE
        WHEN O.QTD_NECESSARIA_PARA_1_PA > 0 THEN ISNULL(A.QTD_APONTADA, ISNULL(O.QTD_PRODUZIDA_SC2, 0)) / O.QTD_NECESSARIA_PARA_1_PA
        ELSE 0
    END AS VARCHAR(50)) AS EQUIVALENTE_EM_PA,
    O.C2_DATPRI AS DATA_PREV_INICIO_OP,
    O.C2_DATPRF AS DATA_PREV_FIM_OP,
    O.C2_DATRF AS DATA_REAL_FIM_OP,
    O.C2_STATUS AS STATUS_OP,
    O.CAMINHO
FROM OPS O
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = O.CODIGO
   AND SB1.D_E_L_E_T_ = ''
LEFT JOIN APONTAMENTOS A
    ON A.H6_FILIAL = O.C2_FILIAL
   AND A.H6_PRODUTO = O.C2_PRODUTO
   AND (
        A.H6_OP = O.C2_OP
        OR A.H6_OP = O.C2_NUM + O.C2_ITEM + O.C2_SEQUEN
   )
ORDER BY
    O.NIVEL,
    O.CAMINHO,
    O.C2_FILIAL,
    O.C2_OP
OPTION (MAXRECURSION 0);
```

---

## 14. Query 5 — Quanto do PA já está finalizado na expedição

Esta query calcula quanto do PA foi apontado no CT de inspeção final.

```sql
DECLARE @PRODUTO VARCHAR(30);
DECLARE @DATA_INI VARCHAR(8);
DECLARE @DATA_FIM VARCHAR(8);

SET @PRODUTO = '90260951';
SET @DATA_INI = '20260604';
SET @DATA_FIM = '20260605';

WITH CTS_INSPECAO AS (
    SELECT
        HB_FILIAL AS FILIAL,
        HB_COD AS CT_INSPECAO,
        HB_NOME AS NOME_CT_INSPECAO
    FROM SHB010 WITH (NOLOCK)
    WHERE
        D_E_L_E_T_ = ''
        AND UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
),

APONTAMENTO_PA_INSPECAO AS (
    SELECT
        H6.H6_FILIAL AS FILIAL,
        H6.H6_PRODUTO AS PRODUTO,
        SB1.B1_DESC AS DESCRICAO,
        SB1.B1_TIPO AS TIPO,
        SB1.B1_UM AS UNIDADE,
        H6.H6_OP AS OP,
        H6.H6_OPERAC AS OPERACAO,
        H6.H6_RECURSO AS RECURSO,
        SH1.H1_DESCRI AS NOME_RECURSO,
        SH1.H1_CTRAB AS CT,
        CT.NOME_CT_INSPECAO,
        SUM(CAST(H6.H6_QTDPROD AS FLOAT)) AS QTD_FINALIZADA_EXPEDICAO,
        SUM(CAST(H6.H6_QTDPERD AS FLOAT)) AS QTD_PERDIDA_INSPECAO,
        COUNT(*) AS TOTAL_APONTAMENTOS,
        MIN(H6.H6_DATAINI) AS PRIMEIRO_INICIO,
        MIN(H6.H6_HORAINI) AS PRIMEIRA_HORA,
        MAX(H6.H6_DATAFIN) AS ULTIMO_FIM,
        MAX(H6.H6_HORAFIN) AS ULTIMA_HORA,
        MAX(H6.H6_DTAPONT) AS ULTIMO_APONTAMENTO
    FROM SH6010 H6 WITH (NOLOCK)
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = H6.H6_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
       AND SB1.B1_TIPO = 'PA'
    INNER JOIN SH1010 SH1 WITH (NOLOCK)
        ON SH1.H1_FILIAL = H6.H6_FILIAL
       AND SH1.H1_CODIGO = H6.H6_RECURSO
       AND SH1.D_E_L_E_T_ = ''
    INNER JOIN CTS_INSPECAO CT
        ON CT.FILIAL = H6.H6_FILIAL
       AND CT.CT_INSPECAO = SH1.H1_CTRAB
    WHERE
        H6.D_E_L_E_T_ = ''
        AND H6.H6_PRODUTO = @PRODUTO
        AND H6.H6_DTAPONT >= @DATA_INI
        AND H6.H6_DTAPONT < @DATA_FIM
    GROUP BY
        H6.H6_FILIAL,
        H6.H6_PRODUTO,
        SB1.B1_DESC,
        SB1.B1_TIPO,
        SB1.B1_UM,
        H6.H6_OP,
        H6.H6_OPERAC,
        H6.H6_RECURSO,
        SH1.H1_DESCRI,
        SH1.H1_CTRAB,
        CT.NOME_CT_INSPECAO
)

SELECT
    FILIAL,
    PRODUTO,
    DESCRICAO,
    TIPO,
    UNIDADE,
    OP,
    OPERACAO,
    RECURSO,
    NOME_RECURSO,
    CT,
    NOME_CT_INSPECAO,
    CAST(QTD_FINALIZADA_EXPEDICAO AS VARCHAR(50)) AS QTD_FINALIZADA_EXPEDICAO,
    CAST(QTD_PERDIDA_INSPECAO AS VARCHAR(50)) AS QTD_PERDIDA_INSPECAO,
    TOTAL_APONTAMENTOS,
    PRIMEIRO_INICIO,
    PRIMEIRA_HORA,
    ULTIMO_FIM,
    ULTIMA_HORA,
    ULTIMO_APONTAMENTO
FROM APONTAMENTO_PA_INSPECAO
ORDER BY
    FILIAL,
    OP,
    OPERACAO,
    RECURSO;
```

---

## 15. Query 6 — Ranking de PAs finalizados para expedição no período

```sql
DECLARE @DATA_INI VARCHAR(8);
DECLARE @DATA_FIM VARCHAR(8);

SET @DATA_INI = '20260604';
SET @DATA_FIM = '20260605';

WITH CTS_INSPECAO AS (
    SELECT
        HB_FILIAL AS FILIAL,
        HB_COD AS CT_INSPECAO,
        HB_NOME AS NOME_CT_INSPECAO
    FROM SHB010 WITH (NOLOCK)
    WHERE
        D_E_L_E_T_ = ''
        AND UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
),

APONTAMENTO_PA_INSPECAO AS (
    SELECT
        H6.H6_FILIAL AS FILIAL,
        H6.H6_PRODUTO AS PRODUTO,
        SB1.B1_DESC AS DESCRICAO,
        SB1.B1_UM AS UNIDADE,
        H6.H6_OP AS OP,
        H6.H6_OPERAC AS OPERACAO,
        H6.H6_RECURSO AS RECURSO,
        SH1.H1_DESCRI AS NOME_RECURSO,
        SH1.H1_CTRAB AS CT,
        CT.NOME_CT_INSPECAO,
        SUM(CAST(H6.H6_QTDPROD AS FLOAT)) AS QTD_FINALIZADA_EXPEDICAO,
        SUM(CAST(H6.H6_QTDPERD AS FLOAT)) AS QTD_PERDIDA_INSPECAO,
        COUNT(*) AS TOTAL_APONTAMENTOS,
        MIN(H6.H6_DATAINI) AS PRIMEIRO_INICIO,
        MIN(H6.H6_HORAINI) AS PRIMEIRA_HORA,
        MAX(H6.H6_DATAFIN) AS ULTIMO_FIM,
        MAX(H6.H6_HORAFIN) AS ULTIMA_HORA,
        MAX(H6.H6_DTAPONT) AS ULTIMO_APONTAMENTO
    FROM SH6010 H6 WITH (NOLOCK)
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = H6.H6_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
       AND SB1.B1_TIPO = 'PA'
    INNER JOIN SH1010 SH1 WITH (NOLOCK)
        ON SH1.H1_FILIAL = H6.H6_FILIAL
       AND SH1.H1_CODIGO = H6.H6_RECURSO
       AND SH1.D_E_L_E_T_ = ''
    INNER JOIN CTS_INSPECAO CT
        ON CT.FILIAL = H6.H6_FILIAL
       AND CT.CT_INSPECAO = SH1.H1_CTRAB
    WHERE
        H6.D_E_L_E_T_ = ''
        AND H6.H6_DTAPONT >= @DATA_INI
        AND H6.H6_DTAPONT < @DATA_FIM
    GROUP BY
        H6.H6_FILIAL,
        H6.H6_PRODUTO,
        SB1.B1_DESC,
        SB1.B1_UM,
        H6.H6_OP,
        H6.H6_OPERAC,
        H6.H6_RECURSO,
        SH1.H1_DESCRI,
        SH1.H1_CTRAB,
        CT.NOME_CT_INSPECAO
)

SELECT TOP 20
    FILIAL,
    PRODUTO,
    DESCRICAO,
    UNIDADE,
    OP,
    OPERACAO,
    RECURSO,
    NOME_RECURSO,
    CT,
    NOME_CT_INSPECAO,
    CAST(QTD_FINALIZADA_EXPEDICAO AS VARCHAR(50)) AS QTD_FINALIZADA_EXPEDICAO,
    CAST(QTD_PERDIDA_INSPECAO AS VARCHAR(50)) AS QTD_PERDIDA_INSPECAO,
    TOTAL_APONTAMENTOS,
    PRIMEIRO_INICIO,
    PRIMEIRA_HORA,
    ULTIMO_FIM,
    ULTIMA_HORA,
    ULTIMO_APONTAMENTO
FROM APONTAMENTO_PA_INSPECAO
ORDER BY
    QTD_FINALIZADA_EXPEDICAO DESC,
    QTD_PERDIDA_INSPECAO DESC,
    PRODUTO,
    OP;
```

---

## 16. Modelo de visão final do produto

A resposta final ao usuário deve ter esta estrutura:

```text
Produto: [código] — [descrição]
Data de referência: [AAAAMMDD]

1. Estrutura vigente
- Total de componentes
- Total de PIs
- Total de MPs

2. Intermediários
- Lista de PIs
- Quantidade necessária para 1 PA
- Status produtivo de cada PI

3. Matérias-primas
- Lista de MPs
- Quantidade necessária para 1 PA
- Estoque atual
- Estoque disponível
- Se atende 1 PA

4. Matérias-primas exclusivas
- MPs exclusivas = SIM
- Total de PAs onde cada MP aparece

5. Produção
- OPs do PA
- OPs dos PIs
- Produção iniciada SIM/NAO
- Quantidade apontada
- Quantidade perdida
- Equivalente em PA

6. Expedição
- Quantidade do PA apontada no CT de inspeção final
- Quantidade perdida na inspeção final
- CT usado
- OPs finalizadas

7. Conclusão
- Status fabril consolidado
```

---

## 17. Regras de status consolidado

### 17.1 Produto sem estrutura

```text
STATUS = SEM ESTRUTURA VIGENTE
```

Quando não há registros vigentes na `SG1010`.

---

### 17.2 Produto com estrutura, mas sem OP

```text
STATUS = ESTRUTURA OK, SEM OP LOCALIZADA
```

Quando existe BOM, mas não há OP na `SC2010`.

---

### 17.3 Produto com OP, mas sem apontamento

```text
STATUS = OP ABERTA / NÃO INICIADO
```

Quando existe OP, mas não há apontamento na `SH6010` e `C2_QUJE = 0`.

---

### 17.4 Produto iniciado

```text
STATUS = PRODUÇÃO INICIADA
```

Quando existe apontamento na `SH6010` para PA ou PI.

---

### 17.5 Intermediários produzidos, PA não finalizado

```text
STATUS = INTERMEDIÁRIOS EM PRODUÇÃO / PA NÃO FINALIZADO
```

Quando PIs têm apontamento, mas PA ainda não foi apontado na inspeção final.

---

### 17.6 PA produzido, mas sem inspeção final

```text
STATUS = PA PRODUZIDO / AGUARDANDO INSPEÇÃO FINAL
```

Quando PA tem apontamento produtivo, mas não tem apontamento no CT de inspeção final.

---

### 17.7 PA passou inspeção com perda

```text
STATUS = PA INSPECIONADO COM PERDA
```

Quando há apontamento no CT de inspeção final com:

```text
H6_QTDPROD = 0
H6_QTDPERD > 0
```

---

### 17.8 PA finalizado para expedição

```text
STATUS = PA FINALIZADO / LIBERADO PARA EXPEDIÇÃO
```

Quando há apontamento no CT de inspeção final com:

```text
H6_QTDPROD > 0
```

---

## 18. Indicadores finais recomendados

| Indicador | Cálculo |
|---|---|
| `TOTAL_PIS` | Quantidade de componentes tipo PI na estrutura |
| `TOTAL_MPS` | Quantidade de componentes tipo MP na estrutura |
| `TOTAL_MPS_EXCLUSIVAS` | MPs com `MP_EXCLUSIVA = SIM` |
| `TOTAL_MPS_SEM_ESTOQUE` | MPs com disponível <= 0 |
| `TOTAL_OPS_PA` | OPs do PA |
| `TOTAL_OPS_PI` | OPs dos PIs |
| `QTD_PA_PRODUZIDA` | Soma de apontamentos do PA na SH6010 |
| `QTD_PI_PRODUZIDA` | Soma de apontamentos dos PIs na SH6010 |
| `QTD_PA_EXPEDICAO` | Soma de H6_QTDPROD do PA no CT de inspeção final |
| `QTD_PERDA_INSPECAO` | Soma de H6_QTDPERD do PA no CT de inspeção final |
| `STATUS_FABRIL` | Classificação consolidada |

---

## 19. Checklist técnico final

Antes de responder a visão de um produto:

- [ ] Consultar cadastro do produto na `SB1010`;
- [ ] Confirmar se é PA, PI ou MP;
- [ ] Abrir estrutura vigente pela `SG1010`;
- [ ] Abrir todos os níveis recursivamente;
- [ ] Identificar PIs;
- [ ] Identificar MPs;
- [ ] Calcular quantidade acumulada por componente;
- [ ] Verificar exclusividade das MPs;
- [ ] Ignorar PAs `8000%` e `8001%` na exclusividade;
- [ ] Consultar estoque das MPs na `SB2010`;
- [ ] Calcular disponível: atual - empenhado - reservado;
- [ ] Consultar OPs do PA e PIs na `SC2010`;
- [ ] Consultar apontamentos na `SH6010`;
- [ ] Cruzar OP por `C2_OP` ou `C2_NUM + C2_ITEM + C2_SEQUEN`;
- [ ] Consultar recursos na `SH1010`;
- [ ] Consultar CTs de inspeção final na `SHB010`;
- [ ] Somar apenas PA no CT de inspeção final para expedição;
- [ ] Não considerar PI como expedição;
- [ ] Separar quantidade boa e perda;
- [ ] Gerar status fabril consolidado.

---

## 20. Resumo executivo da regra final

```text
Para saber o status completo de um produto na fábrica, abra sua estrutura vigente, identifique PIs e MPs, avalie estoque e exclusividade das MPs, consulte OPs e apontamentos do PA e dos PIs, e considere como expedição somente a quantidade do PA apontada no CT de inspeção final.
```

---

## 21. Fontes de verdade por pergunta

| Pergunta | Fonte principal |
|---|---|
| Qual é a estrutura? | `SG1010` + `SB1010` |
| Quais são os intermediários? | `SG1010` + `SB1010.B1_TIPO = PI` |
| Quais são as MPs? | `SG1010` + `SB1010.B1_TIPO = MP` |
| MP é exclusiva? | `SG1010` recursiva de todos os PAs válidos |
| Tem estoque de MP? | `SB2010` |
| PA/PI começou produção? | `SH6010` |
| Existe OP? | `SC2010` |
| Quanto foi produzido? | `SH6010.H6_QTDPROD` |
| Quanto foi perdido? | `SH6010.H6_QTDPERD` |
| Qual CT é inspeção final? | `SHB010.HB_NOME LIKE '%INSPE%FINAL%'` |
| Quanto está na expedição? | `SH6010.H6_QTDPROD` do PA no CT de inspeção final |
| Intermediário entra em expedição? | Não |

---

## 22. Modelo de conclusão final

```text
Conclusão:

O produto [PA] possui estrutura vigente com [N] intermediários e [N] matérias-primas.
Foram encontradas [N] matérias-primas exclusivas.
Das matérias-primas, [N] possuem estoque disponível e [N] estão sem saldo suficiente para 1 PA.

Na produção, o PA possui [N] OPs e os intermediários possuem [N] OPs.
A produção está [não iniciada / iniciada / parcialmente iniciada / finalizada].

Na expedição, foram finalizados [QTD] [UNIDADE] do PA, com [QTD] de perda na inspeção final.
O CT de inspeção final utilizado foi [CT] — [NOME_CT].

Status fabril consolidado:
[STATUS]
```