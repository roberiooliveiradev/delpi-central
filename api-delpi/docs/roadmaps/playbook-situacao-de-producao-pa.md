# Playbook DELPI — Situação de Produção de um Produto Considerando PA, PI, OP e Apontamentos

## 1. Objetivo

Este playbook define como avaliar a situação produtiva de um produto no Protheus DELPI.

A análise responde perguntas como:

- O produto já começou a ser produzido?
- Algum intermediário dele já começou?
- Quais OPs existem para o PA e para os PIs?
- Quanto já foi produzido?
- Houve apontamento hoje ou até uma data de referência?
- Quanto a produção dos PIs representa para montar 1 PA?
- Qual a rota produtiva real considerando estrutura, OP e apontamento?

---

## 2. Conceito principal

Para avaliar a situação de produção de um produto, não basta olhar somente o PA.

É obrigatório considerar:

- O produto acabado analisado;
- Todos os intermediários `PI` dentro da estrutura;
- As OPs desses produtos;
- Os apontamentos reais de produção;
- Uma data de avaliação.

Regra-mãe:

```text
Situação produtiva de um produto = PA + PIs da estrutura + OPs da SC2010 + apontamentos da SH6010, avaliados em uma data de referência.
```

---

## 3. Tabelas envolvidas

### 3.1 SG1010 — Estrutura do produto

Usada para abrir a estrutura do produto e localizar os intermediários.

Campos principais:

| Campo | Uso |
|---|---|
| `G1_COD` | Produto pai |
| `G1_COMP` | Componente filho |
| `G1_QUANT` | Quantidade do componente |
| `G1_INI` | Data inicial de vigência |
| `G1_FIM` | Data final de vigência |
| `D_E_L_E_T_` | Exclusão lógica |

---

### 3.2 SB1010 — Cadastro de produtos

Usada para identificar descrição, tipo e unidade.

Campos principais:

| Campo | Uso |
|---|---|
| `B1_COD` | Código do produto |
| `B1_DESC` | Descrição |
| `B1_TIPO` | Tipo: PA, PI, MP etc. |
| `B1_UM` | Unidade |
| `D_E_L_E_T_` | Exclusão lógica |

Tipos importantes:

| Tipo | Significado |
|---|---|
| `PA` | Produto acabado |
| `PI` | Produto intermediário |
| `MP` | Matéria-prima |

---

### 3.3 SC2010 — Ordens de Produção

Tabela principal das OPs.

Campos principais:

| Campo | Uso |
|---|---|
| `C2_FILIAL` | Filial |
| `C2_NUM` | Número da OP |
| `C2_ITEM` | Item da OP |
| `C2_SEQUEN` | Sequência da OP |
| `C2_OP` | Ordem de Produção completa |
| `C2_PRODUTO` | Produto da OP |
| `C2_QUANT` | Quantidade planejada da OP |
| `C2_QUJE` | Quantidade já produzida na OP |
| `C2_EMISSAO` | Data de emissão |
| `C2_DATPRI` | Data prevista de início |
| `C2_DATPRF` | Data prevista de fim |
| `C2_DATRF` | Data real de fim |
| `C2_STATUS` | Status da OP |
| `D_E_L_E_T_` | Exclusão lógica |

Observação:

```text
C2_NUM é o número da OP, mas C2_OP é o campo mais seguro para cruzar com apontamentos.
```

---

### 3.4 SH6010 — Movimentação da Produção

Tabela de apontamentos/movimentações da produção.

Campos principais:

| Campo | Uso |
|---|---|
| `H6_FILIAL` | Filial do apontamento |
| `H6_OP` | OP apontada |
| `H6_PRODUTO` | Produto apontado |
| `H6_OPERAC` | Operação |
| `H6_RECURSO` | Recurso |
| `H6_DATAINI` | Data inicial do apontamento |
| `H6_HORAINI` | Hora inicial |
| `H6_DATAFIN` | Data final |
| `H6_HORAFIN` | Hora final |
| `H6_QTDPROD` | Quantidade produzida |
| `H6_QTDPERD` | Quantidade perdida |
| `H6_DTAPONT` | Data do apontamento |
| `H6_PT` | Produção parcial ou total |
| `D_E_L_E_T_` | Exclusão lógica |

---

## 4. Sobre a tabela SH46010

Durante a validação, a tabela `SH46010` não foi confirmada no dicionário.

A tabela validada para apontamentos/movimentação da produção foi:

```text
SH6010 — Movimentação da Produção
```

Portanto, para este playbook, a tabela correta é:

```text
SH6010
```

---

## 5. Data de referência

Toda análise produtiva deve ter uma data.

Sem data, a consulta mistura OPs históricas com produção atual.

Usar:

```sql
DECLARE @DATA_REF VARCHAR(8);
SET @DATA_REF = '20260604';
```

Para usar a data atual do banco:

```sql
SET @DATA_REF = CONVERT(CHAR(8), GETDATE(), 112);
```

Formato obrigatório:

```text
AAAAMMDD
```

Exemplo:

```text
20260604
```

---

## 6. Regras de avaliação por data

### 6.1 Estrutura válida na data

A estrutura deve ser válida na data de referência:

```sql
AND (G1.G1_INI = '' OR G1.G1_INI <= @DATA_REF)
AND (G1.G1_FIM = '' OR G1.G1_FIM >= @DATA_REF)
```

---

### 6.2 OPs consideradas

Para visão histórica até a data:

```sql
AND SC2.C2_EMISSAO <= @DATA_REF
```

Para visão de produção do dia, usar apontamentos do dia na `SH6010`:

```sql
AND H6.H6_DTAPONT = @DATA_REF
```

---

### 6.3 Apontamentos considerados

Para saber tudo que foi apontado até a data:

```sql
AND H6.H6_DTAPONT <= @DATA_REF
```

Para saber somente o que foi apontado no dia:

```sql
AND H6.H6_DTAPONT = @DATA_REF
```

---

## 7. Relação entre SC2010 e SH6010

A ligação pode ocorrer por duas formas.

Forma principal:

```sql
SH6.H6_OP = SC2.C2_OP
```

Forma alternativa observada pelo dicionário:

```sql
SH6.H6_OP = SC2.C2_NUM + SC2.C2_ITEM + SC2.C2_SEQUEN
```

Ligação recomendada:

```sql
AND (
    SH6.H6_OP = SC2.C2_OP
    OR SH6.H6_OP = SC2.C2_NUM + SC2.C2_ITEM + SC2.C2_SEQUEN
)
```

Também cruzar filial e produto:

```sql
SH6.H6_FILIAL = SC2.C2_FILIAL
SH6.H6_PRODUTO = SC2.C2_PRODUTO
```

---

## 8. Indicadores principais

| Indicador | Como calcular |
|---|---|
| Produção iniciada | Existe apontamento na SH6010 |
| Quantidade apontada | Soma de `H6_QTDPROD` |
| Quantidade perdida | Soma de `H6_QTDPERD` |
| Quantidade produzida na OP | `C2_QUJE` |
| Percentual da OP | `H6_QTDPROD / C2_QUANT * 100` |
| Quantidade necessária para 1 PA | Quantidade acumulada da estrutura |
| Equivalente em PA | `H6_QTDPROD / QTD_NECESSARIA_PARA_1_PA` |
| Percentual para 1 PA | `Equivalente em PA * 100` |

---

## 9. Interpretação do status de produção

### 9.1 Produção iniciada pela SH6010

```text
Há apontamento real de produção.
```

Critério:

```sql
TOTAL_APONTAMENTOS > 0
```

Resultado:

```text
PRODUCAO_INICIADA = SIM
```

---

### 9.2 Produção indicada apenas pela SC2010

Pode acontecer de a SH6010 não trazer apontamentos, mas a SC2010 ter quantidade produzida.

Critério:

```sql
C2_QUJE > 0
```

Resultado sugerido:

```text
PRODUCAO_INICIADA = SIM_SC2
```

Interpretação:

```text
A OP indica produção realizada, mas o apontamento detalhado não foi localizado na SH6010.
```

---

### 9.3 Produção não iniciada

Critério:

```text
Sem apontamento na SH6010 e C2_QUJE = 0
```

Resultado:

```text
PRODUCAO_INICIADA = NAO
```

---

## 10. Query — Visão completa até uma data de referência

Esta query avalia o PA e seus PIs, considerando OPs até uma data e apontamentos até a data.

Trocar:

```sql
SET @PRODUTO = '90261255';
SET @DATA_REF = '20260604';
```

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
        CAST(G1.G1_QUANT AS FLOAT) AS QTD_POR,
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
        CAST(G1.G1_QUANT AS FLOAT),
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
        E.COMPONENTE AS CODIGO,
        E.QTD_NECESSARIA_PARA_1_PA,
        E.CAMINHO
    FROM ESTRUTURA E
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = E.COMPONENTE
       AND SB1.D_E_L_E_T_ = ''
    WHERE
        SB1.B1_TIPO IN ('PI', 'PA')
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
        CAST(SC2.C2_QUANT AS FLOAT) AS C2_QUANT,
        CAST(SC2.C2_QUJE AS FLOAT) AS C2_QUJE,
        SC2.C2_EMISSAO,
        SC2.C2_DATPRI,
        SC2.C2_DATPRF,
        SC2.C2_DATRF,
        SC2.C2_STATUS
    FROM ESCOPO_PRODUCAO EP
    LEFT JOIN SC2010 SC2 WITH (NOLOCK)
        ON SC2.C2_PRODUTO = EP.CODIGO
       AND SC2.D_E_L_E_T_ = ''
       AND SC2.C2_EMISSAO <= @DATA_REF
),

APONTAMENTOS AS (
    SELECT
        H6_FILIAL,
        H6_OP,
        H6_PRODUTO,
        SUM(CAST(H6_QTDPROD AS FLOAT)) AS QTD_APONTADA_SH6,
        SUM(CAST(H6_QTDPERD AS FLOAT)) AS QTD_PERDIDA_SH6,
        MIN(H6_DATAINI) AS PRIMEIRO_INICIO_APONTAMENTO,
        MIN(H6_HORAINI) AS PRIMEIRA_HORA_INICIO,
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
    O.C2_NUM AS NUM_OP,
    O.C2_ITEM AS ITEM_OP,
    O.C2_SEQUEN AS SEQUENCIA_OP,

    CAST(ISNULL(O.C2_QUANT, 0) AS VARCHAR(50)) AS QTD_OP,
    CAST(ISNULL(O.C2_QUJE, 0) AS VARCHAR(50)) AS QTD_PRODUZIDA_SC2,

    CAST(ISNULL(A.QTD_APONTADA_SH6, 0) AS VARCHAR(50)) AS QTD_APONTADA_SH6,
    CAST(ISNULL(A.QTD_PERDIDA_SH6, 0) AS VARCHAR(50)) AS QTD_PERDIDA_SH6,

    A.PRIMEIRO_INICIO_APONTAMENTO,
    A.PRIMEIRA_HORA_INICIO,
    A.ULTIMO_APONTAMENTO,
    ISNULL(A.TOTAL_APONTAMENTOS, 0) AS TOTAL_APONTAMENTOS,

    CASE
        WHEN ISNULL(A.TOTAL_APONTAMENTOS, 0) > 0 THEN 'SIM'
        WHEN ISNULL(O.C2_QUJE, 0) > 0 THEN 'SIM_SC2'
        ELSE 'NAO'
    END AS PRODUCAO_INICIADA,

    CAST(CASE
        WHEN ISNULL(O.C2_QUANT, 0) > 0
            THEN (ISNULL(A.QTD_APONTADA_SH6, ISNULL(O.C2_QUJE, 0)) / O.C2_QUANT) * 100
        ELSE 0
    END AS VARCHAR(50)) AS PERCENTUAL_DA_OP_PRODUZIDO,

    CAST(CASE
        WHEN O.QTD_NECESSARIA_PARA_1_PA > 0
            THEN ISNULL(A.QTD_APONTADA_SH6, ISNULL(O.C2_QUJE, 0)) / O.QTD_NECESSARIA_PARA_1_PA
        ELSE 0
    END AS VARCHAR(50)) AS EQUIVALENTE_EM_PA,

    CAST(CASE
        WHEN O.QTD_NECESSARIA_PARA_1_PA > 0
            THEN (ISNULL(A.QTD_APONTADA_SH6, ISNULL(O.C2_QUJE, 0)) / O.QTD_NECESSARIA_PARA_1_PA) * 100
        ELSE 0
    END AS VARCHAR(50)) AS PERCENTUAL_PARA_1_PA,

    O.C2_EMISSAO AS DATA_EMISSAO_OP,
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

## 11. Query — Identificar produtos produzidos em uma data

Antes de testar uma visão produtiva, pode-se localizar produtos com apontamento na data.

```sql
DECLARE @DATA_REF VARCHAR(8);
SET @DATA_REF = '20260604';

SELECT TOP 10
    H6.H6_PRODUTO AS PRODUTO,
    SB1.B1_DESC AS DESCRICAO,
    SB1.B1_TIPO AS TIPO,
    SB1.B1_UM AS UNIDADE,
    COUNT(*) AS TOTAL_APONTAMENTOS,
    SUM(CAST(H6.H6_QTDPROD AS FLOAT)) AS QTD_APONTADA,
    SUM(CAST(H6.H6_QTDPERD AS FLOAT)) AS QTD_PERDIDA,
    MIN(H6.H6_DATAINI) AS PRIMEIRO_INICIO,
    MAX(H6.H6_DTAPONT) AS ULTIMO_APONTAMENTO
FROM SH6010 H6 WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = H6.H6_PRODUTO
   AND SB1.D_E_L_E_T_ = ''
WHERE
    H6.D_E_L_E_T_ = ''
    AND H6.H6_DTAPONT = @DATA_REF
GROUP BY
    H6.H6_PRODUTO,
    SB1.B1_DESC,
    SB1.B1_TIPO,
    SB1.B1_UM
ORDER BY
    TOTAL_APONTAMENTOS DESC,
    QTD_APONTADA DESC;
```

---

## 12. Query — Visão somente do que foi produzido no dia

Esta query mostra PA e PIs da estrutura que tiveram apontamento exatamente na data de referência.

Ela é ideal para responder:

```text
O que começou/foi produzido hoje para este produto e seus intermediários?
```

Trocar:

```sql
SET @PRODUTO = '90260951';
SET @DATA_REF = '20260604';
```

```sql
DECLARE @PRODUTO VARCHAR(30);
DECLARE @DATA_REF VARCHAR(8);
DECLARE @MAX_DEPTH INT;

SET @PRODUTO = '90260951';
SET @DATA_REF = '20260604';
SET @MAX_DEPTH = 50;

WITH ESTRUTURA AS (
    SELECT
        G1.G1_COD AS PRODUTO_PAI,
        G1.G1_COMP AS COMPONENTE,
        CAST(G1.G1_QUANT AS FLOAT) AS QTD_POR,
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
        CAST(G1.G1_QUANT AS FLOAT),
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
        SB1.B1_TIPO IN ('PI', 'PA')
),

APONTAMENTOS_DIA AS (
    SELECT
        H6.H6_FILIAL,
        H6.H6_OP,
        H6.H6_PRODUTO,
        SUM(CAST(H6.H6_QTDPROD AS FLOAT)) AS QTD_APONTADA_DIA,
        SUM(CAST(H6.H6_QTDPERD AS FLOAT)) AS QTD_PERDIDA_DIA,
        MIN(H6.H6_DATAINI) AS PRIMEIRO_INICIO_DIA,
        MIN(H6.H6_HORAINI) AS PRIMEIRA_HORA_DIA,
        MAX(H6.H6_DATAFIN) AS ULTIMO_FIM_DIA,
        MAX(H6.H6_HORAFIN) AS ULTIMA_HORA_DIA,
        COUNT(*) AS TOTAL_APONTAMENTOS_DIA
    FROM SH6010 H6 WITH (NOLOCK)
    WHERE
        H6.D_E_L_E_T_ = ''
        AND H6.H6_DTAPONT = @DATA_REF
    GROUP BY
        H6.H6_FILIAL,
        H6.H6_OP,
        H6.H6_PRODUTO
),

OPS_DO_DIA AS (
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
        CAST(SC2.C2_QUANT AS FLOAT) AS C2_QUANT,
        CAST(SC2.C2_QUJE AS FLOAT) AS C2_QUJE,
        SC2.C2_DATPRI,
        SC2.C2_DATPRF,
        SC2.C2_DATRF,
        SC2.C2_STATUS,

        A.QTD_APONTADA_DIA,
        A.QTD_PERDIDA_DIA,
        A.PRIMEIRO_INICIO_DIA,
        A.PRIMEIRA_HORA_DIA,
        A.ULTIMO_FIM_DIA,
        A.ULTIMA_HORA_DIA,
        A.TOTAL_APONTAMENTOS_DIA
    FROM ESCOPO_PRODUCAO EP
    INNER JOIN APONTAMENTOS_DIA A
        ON A.H6_PRODUTO = EP.CODIGO
    LEFT JOIN SC2010 SC2 WITH (NOLOCK)
        ON SC2.D_E_L_E_T_ = ''
       AND SC2.C2_PRODUTO = EP.CODIGO
       AND SC2.C2_FILIAL = A.H6_FILIAL
       AND (
            A.H6_OP = SC2.C2_OP
            OR A.H6_OP = SC2.C2_NUM + SC2.C2_ITEM + SC2.C2_SEQUEN
       )
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
    O.C2_NUM AS NUM_OP,
    O.C2_ITEM AS ITEM_OP,
    O.C2_SEQUEN AS SEQUENCIA_OP,

    CAST(ISNULL(O.C2_QUANT, 0) AS VARCHAR(50)) AS QTD_OP,
    CAST(ISNULL(O.C2_QUJE, 0) AS VARCHAR(50)) AS QTD_PRODUZIDA_SC2_TOTAL_OP,

    CAST(ISNULL(O.QTD_APONTADA_DIA, 0) AS VARCHAR(50)) AS QTD_APONTADA_HOJE,
    CAST(ISNULL(O.QTD_PERDIDA_DIA, 0) AS VARCHAR(50)) AS QTD_PERDIDA_HOJE,

    O.TOTAL_APONTAMENTOS_DIA,
    O.PRIMEIRO_INICIO_DIA,
    O.PRIMEIRA_HORA_DIA,
    O.ULTIMO_FIM_DIA,
    O.ULTIMA_HORA_DIA,

    'SIM' AS PRODUCAO_INICIADA_HOJE,

    CAST(CASE
        WHEN ISNULL(O.C2_QUANT, 0) > 0
            THEN (ISNULL(O.QTD_APONTADA_DIA, 0) / O.C2_QUANT) * 100
        ELSE 0
    END AS VARCHAR(50)) AS PERCENTUAL_DA_OP_APONTADO_HOJE,

    CAST(CASE
        WHEN O.QTD_NECESSARIA_PARA_1_PA > 0
            THEN ISNULL(O.QTD_APONTADA_DIA, 0) / O.QTD_NECESSARIA_PARA_1_PA
        ELSE 0
    END AS VARCHAR(50)) AS EQUIVALENTE_EM_PA_HOJE,

    CAST(CASE
        WHEN O.QTD_NECESSARIA_PARA_1_PA > 0
            THEN (ISNULL(O.QTD_APONTADA_DIA, 0) / O.QTD_NECESSARIA_PARA_1_PA) * 100
        ELSE 0
    END AS VARCHAR(50)) AS PERCENTUAL_PARA_1_PA_HOJE,

    O.C2_DATPRI AS DATA_PREV_INICIO_OP,
    O.C2_DATPRF AS DATA_PREV_FIM_OP,
    O.C2_DATRF AS DATA_REAL_FIM_OP,
    O.C2_STATUS AS STATUS_OP,

    O.CAMINHO
FROM OPS_DO_DIA O
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = O.CODIGO
   AND SB1.D_E_L_E_T_ = ''
ORDER BY
    O.NIVEL,
    O.CAMINHO,
    O.C2_OP
OPTION (MAXRECURSION 0);
```

---

## 13. Resultado validado — produto produzido em 20260604

Produto identificado com apontamento no dia:

```text
90260951 — CHICOTE DE LIGACAO
```

Resumo encontrado na SH6010:

| Produto | Tipo | Total apontamentos | Qtd. apontada | Qtd. perdida |
|---|---|---:|---:|---:|
| `90260951` | PA | 16 | 0.092 | 0.023 |

Estrutura produtiva considerada:

| Nível | Produto | Tipo | Descrição | Qtd. necessária para 1 PA |
|---:|---|---|---|---:|
| 0 | `90260951` | PA | CHICOTE DE LIGACAO | 1 |
| 1 | `50220562` | PI | CF18CINZ-06820/10/10-0000-6500 | 1 |

OPs do PA apontadas no dia:

| Produto | OP | Qtd. OP | Qtd. apontada hoje | Qtd. perdida hoje | Apontamentos | Início | Fim | % OP |
|---|---|---:|---:|---:|---:|---|---|---:|
| `90260951` | `24531901001` | 0.003 | 0.012 | 0.003 | 5 | 10:02 | 15:48 | 400% |
| `90260951` | `24556901001` | 0.010 | 0.040 | 0.010 | 6 | 09:36 | 15:50 | 400% |
| `90260951` | `24557001001` | 0.010 | 0.040 | 0.010 | 5 | 09:10 | 15:49 | 400% |

OPs do PI apontadas no dia:

| PI | OP | Qtd. OP | Qtd. apontada hoje | Apontamentos | Início | Fim | % OP |
|---|---|---:|---:|---:|---|---|---:|
| `50220562` | `24531901002` | 0.003 | 0.003 | 1 | 14:24 | 14:30 | 100% |
| `50220562` | `24556901002` | 0.010 | 0.010 | 1 | 14:12 | 14:23 | 100% |
| `50220562` | `24557001002` | 0.010 | 0.010 | 1 | 13:40 | 13:47 | 100% |

Conclusão validada:

```text
Para o produto 90260951 em 20260604, houve produção iniciada tanto no PA quanto no PI 50220562.
```

Alerta validado:

```text
O PA teve apontamento de 400% em relação à quantidade da OP em três OPs.
Isso indica múltiplos apontamentos no mesmo PA/OP ou regra operacional que precisa ser interpretada com cuidado.
```

---

## 14. Como interpretar percentual maior que 100%

Se `PERCENTUAL_DA_OP_APONTADO_HOJE > 100`, investigar:

- Se existem múltiplos apontamentos parciais somando mais que a OP;
- Se `H6_QTDPROD` está em unidade diferente da `C2_QUANT`;
- Se a OP tem lote/fracionamento;
- Se há apontamento em mais de uma operação para o mesmo produto;
- Se há reapontamento ou correção;
- Se a perda também compõe parte do processo.

Não concluir erro automaticamente sem olhar o contexto operacional.

---

## 15. Modelo de resposta esperado

Ao executar a visão para um produto, responder assim:

```text
Consulta executada para [PRODUTO] — [DESCRIÇÃO].

Data avaliada: [AAAAMMDD]
Fonte: SC2010 + SH6010 + SG1010 + SB1010

Resumo:
- Produção iniciada no PA: SIM/NAO
- Produção iniciada em PIs: SIM/NAO
- Total de OPs encontradas: N
- Total de apontamentos: N
- Quantidade apontada: N
- Quantidade perdida: N

Tabela 1 — Rota produtiva considerada
Tabela 2 — OPs do PA
Tabela 3 — OPs dos PIs
Tabela 4 — Alertas

Conclusão:
[texto direto com a leitura produtiva]
```

---

## 16. Checklist técnico

Antes de considerar a visão válida:

- [ ] Usou `SG1010` para abrir a estrutura;
- [ ] Filtrou estrutura vigente pela data de referência;
- [ ] Considerou o PA raiz;
- [ ] Considerou todos os PIs da estrutura;
- [ ] Usou `SC2010` para OPs;
- [ ] Usou `SH6010` para apontamentos;
- [ ] Cruzou por filial;
- [ ] Cruzou por produto;
- [ ] Tentou cruzar `H6_OP = C2_OP`;
- [ ] Tentou cruzar `H6_OP = C2_NUM + C2_ITEM + C2_SEQUEN`;
- [ ] Filtrou `D_E_L_E_T_ = ''` em todas as tabelas;
- [ ] Considerou a data da análise;
- [ ] Calculou quantidade apontada;
- [ ] Calculou quantidade perdida;
- [ ] Calculou percentual da OP;
- [ ] Calculou equivalente em PA;
- [ ] Apontou alertas quando percentual passou de 100%.

---

## 17. Resumo da regra-mãe

```text
Para saber a situação produtiva de um produto, abra a estrutura vigente na data, pegue o PA e seus PIs, encontre suas OPs na SC2010 e seus apontamentos na SH6010, sempre usando uma data de referência.
```