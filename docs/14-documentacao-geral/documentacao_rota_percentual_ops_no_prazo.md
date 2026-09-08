## Documentação funcional e técnica — Rota de percentual de OPs no prazo

### Objetivo

Criar uma rota que apure o **percentual de ordens de produção entregues no prazo** dentro de uma faixa de datas, considerando como base a **data prevista de entrega** e a **data real de fim da OP**.

---

## Regra de negócio

Uma OP será considerada:

- **No prazo** quando `C2_DATRF <= C2_DATPRF`
- **Em atraso** quando `C2_DATRF > C2_DATPRF`

### Base de cálculo

A apuração deve ser feita por **OP distinta**, usando `C2_NUM`.

### Critérios de inclusão

Entram no cálculo apenas registros que atendam a todos os critérios abaixo:

- `D_E_L_E_T_ = ''`
- `C2_FILIAL = :FILIAL`
- `C2_DATPRF` dentro da faixa informada
- `C2_DATPRF IS NOT NULL`
- `C2_DATRF IS NOT NULL`

---

## Tabelas envolvidas

### SC2010 — Ordens de Produção

Tabela principal para cálculo do prazo de entrega.

#### Campos relevantes do schema

| Campo | Tipo | Tamanho | Dec | Descrição |
|---|---|---:|---:|---|
| `C2_FILIAL` | C | 2 | 0 | Filial do sistema |
| `C2_NUM` | C | 6 | 0 | Número da OP |
| `C2_ITEM` | C | 2 | 0 | Item da ordem de produção |
| `C2_SEQUEN` | C | 3 | 0 | Sequência |
| `C2_PRODUTO` | C | 15 | 0 | Código do produto |
| `C2_QUANT` | N | 13 | 3 | Quantidade da OP |
| `C2_QUJE` | N | 13 | 3 | Quantidade produzida |
| `C2_UM` | C | 2 | 0 | Unidade de medida |
| `C2_DATPRI` | D | 8 | 0 | Data prevista de início |
| `C2_DATPRF` | D | 8 | 0 | Data prevista de entrega |
| `C2_DATRF` | D | 8 | 0 | Data real de fim da OP |
| `C2_EMISSAO` | D | 8 | 0 | Data de emissão da OP |
| `C2_PRIOR` | C | 3 | 0 | Prioridade da OP |
| `C2_STATUS` | C | 1 | 0 | Situação da OP |
| `C2_UM` | C | 2 | 0 | Unidade |
| `D_E_L_E_T_` | C | — | — | Exclusão lógica |

### SB1010 — Cadastro de Produtos

Tabela auxiliar para detalhamento descritivo da OP.

#### Campos relevantes do schema

| Campo | Tipo | Tamanho | Dec | Descrição |
|---|---|---:|---:|---|
| `B1_FILIAL` | C | 2 | 0 | Filial |
| `B1_COD` | C | 15 | 0 | Código do produto |
| `B1_DESC` | C | 120 | 0 | Descrição do produto |
| `B1_TIPO` | C | 2 | 0 | Tipo de produto |
| `D_E_L_E_T_` | C | — | — | Exclusão lógica |

---

## Considerações de modelagem

### 1. Granularidade
A `SC2010` pode conter múltiplas linhas para a mesma OP (`C2_NUM`).  
Por isso, o cálculo do percentual deve usar:

```sql
DISTINCT C2_NUM
```

ou uma CTE que consolide a OP antes da contagem.

### 2. Faixa de datas
A faixa deve ser aplicada sobre:

```sql
C2_DATPRF
```

porque o indicador mede entrega no prazo com base na **data prevista de entrega**.

### 3. OPs consideradas
A rota deve considerar apenas OPs com data real de finalização preenchida:

```sql
C2_DATRF IS NOT NULL
```

Ou seja, a métrica representa **OPs finalizadas**.

---

## SQL 1 — Resumo percentual de OPs no prazo

```sql
DECLARE @FILIAL VARCHAR(2);
DECLARE @DATA_INICIAL DATE;
DECLARE @DATA_FINAL DATE;

SET @FILIAL = '01';
SET @DATA_INICIAL = '2026-03-01';
SET @DATA_FINAL   = '2026-03-31';

WITH OPS_FINALIZADAS AS (
    SELECT DISTINCT
        OP.C2_NUM,
        OP.C2_DATPRF,
        OP.C2_DATRF
    FROM SC2010 OP
    WHERE
           OP.D_E_L_E_T_ = ''
       AND OP.C2_FILIAL = @FILIAL
       AND OP.C2_DATPRF BETWEEN @DATA_INICIAL AND @DATA_FINAL
       AND OP.C2_DATPRF IS NOT NULL
       AND OP.C2_DATRF IS NOT NULL
)
SELECT
    COUNT(*) AS TOTAL_OPS_FINALIZADAS,
    SUM(CASE WHEN C2_DATRF <= C2_DATPRF THEN 1 ELSE 0 END) AS OPS_NO_PRAZO,
    SUM(CASE WHEN C2_DATRF > C2_DATPRF THEN 1 ELSE 0 END) AS OPS_ATRASADAS,
    CAST(
        SUM(CASE WHEN C2_DATRF <= C2_DATPRF THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0)
        AS DECIMAL(10,2)
    ) AS PERCENTUAL_NO_PRAZO,
    CAST(
        SUM(CASE WHEN C2_DATRF > C2_DATPRF THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0)
        AS DECIMAL(10,2)
    ) AS PERCENTUAL_ATRASO
FROM OPS_FINALIZADAS;
```

### Finalidade
Retornar o indicador consolidado para a faixa informada.

### Saída esperada

| Campo | Descrição |
|---|---|
| `TOTAL_OPS_FINALIZADAS` | Total de OPs finalizadas no período |
| `OPS_NO_PRAZO` | Total de OPs entregues no prazo |
| `OPS_ATRASADAS` | Total de OPs entregues com atraso |
| `PERCENTUAL_NO_PRAZO` | Percentual de entregas no prazo |
| `PERCENTUAL_ATRASO` | Percentual de entregas em atraso |

---

## SQL 2 — Detalhamento por OP com classificação de prazo

```sql
DECLARE @FILIAL VARCHAR(2);
DECLARE @DATA_INICIAL DATE;
DECLARE @DATA_FINAL DATE;

SET @FILIAL = '01';
SET @DATA_INICIAL = '2026-03-01';
SET @DATA_FINAL   = '2026-03-31';

WITH OPS_FINALIZADAS AS (
    SELECT DISTINCT
        OP.C2_FILIAL,
        OP.C2_NUM,
        OP.C2_PRODUTO,
        OP.C2_DATPRF,
        OP.C2_DATRF
    FROM SC2010 OP
    WHERE
           OP.D_E_L_E_T_ = ''
       AND OP.C2_FILIAL = @FILIAL
       AND OP.C2_DATPRF BETWEEN @DATA_INICIAL AND @DATA_FINAL
       AND OP.C2_DATPRF IS NOT NULL
       AND OP.C2_DATRF IS NOT NULL
)
SELECT
    O.C2_FILIAL AS FILIAL,
    O.C2_NUM AS COD_OP,
    O.C2_PRODUTO AS COD_PRODUTO,
    P.B1_DESC AS DESCRICAO_PRODUTO,
    O.C2_DATPRF AS DATA_PREVISTA_ENTREGA,
    O.C2_DATRF AS DATA_REAL_FIM,
    DATEDIFF(DAY, O.C2_DATPRF, O.C2_DATRF) AS DIFERENCA_DIAS,
    CASE
        WHEN O.C2_DATRF <= O.C2_DATPRF THEN 'NO PRAZO'
        ELSE 'ATRASADA'
    END AS STATUS_PRAZO
FROM OPS_FINALIZADAS O
LEFT JOIN SB1010 P
    ON P.D_E_L_E_T_ = ''
   AND P.B1_COD = O.C2_PRODUTO
ORDER BY
    O.C2_DATPRF ASC,
    O.C2_NUM ASC;
```

### Finalidade
Retornar a listagem detalhada das OPs consideradas no cálculo, com a classificação individual de prazo.

### Saída esperada

| Campo | Descrição |
|---|---|
| `FILIAL` | Filial da OP |
| `COD_OP` | Número da ordem de produção |
| `COD_PRODUTO` | Código do produto |
| `DESCRICAO_PRODUTO` | Descrição do produto |
| `DATA_PREVISTA_ENTREGA` | Data prevista de entrega |
| `DATA_REAL_FIM` | Data real de conclusão |
| `DIFERENCA_DIAS` | Diferença em dias entre previsto e realizado |
| `STATUS_PRAZO` | `NO PRAZO` ou `ATRASADA` |

---

## Sugestão de rota

### Endpoint
```http
GET /production/orders/on-time-delivery
```

### Parâmetros
| Parâmetro | Tipo | Obrigatório | Exemplo |
|---|---|---|---|
| `branch` | string | sim | `01` |
| `start_date` | date | sim | `2026-03-01` |
| `end_date` | date | sim | `2026-03-31` |
| `include_details` | boolean | não | `true` |

---

## Comportamento esperado da rota

### Sem detalhamento
A rota retorna apenas o resumo percentual.

### Com detalhamento
A rota retorna:

- resumo percentual
- lista de OPs consideradas no cálculo

---

## Exemplo de resposta JSON

```json
{
  "success": true,
  "message": "Percentual de OPs no prazo calculado com sucesso.",
  "data": {
    "branch": "01",
    "start_date": "2026-03-01",
    "end_date": "2026-03-31",
    "total_ops_finalizadas": 100,
    "ops_no_prazo": 74,
    "ops_atrasadas": 26,
    "percentual_no_prazo": 74.00,
    "percentual_atraso": 26.00
  }
}
```

### Exemplo com detalhamento

```json
{
  "success": true,
  "message": "Percentual de OPs no prazo calculado com sucesso.",
  "data": {
    "branch": "01",
    "start_date": "2026-03-01",
    "end_date": "2026-03-31",
    "total_ops_finalizadas": 100,
    "ops_no_prazo": 74,
    "ops_atrasadas": 26,
    "percentual_no_prazo": 74.00,
    "percentual_atraso": 26.00,
    "details": [
      {
        "filial": "01",
        "cod_op": "243614",
        "cod_produto": "90300026",
        "descricao_produto": "CHICOTE DE LIGACAO",
        "data_prevista_entrega": "2026-03-02",
        "data_real_fim": "2026-03-03",
        "diferenca_dias": 1,
        "status_prazo": "ATRASADA"
      }
    ]
  }
}
```

---

## Regras técnicas recomendadas

- Sempre filtrar `D_E_L_E_T_ = ''`
- Sempre trabalhar com **OP distinta**
- Não calcular percentual sobre linhas brutas da `SC2010`
- Aplicar `NULLIF(COUNT(*), 0)` para evitar divisão por zero
- Usar `LEFT JOIN SB1010` apenas para enriquecimento descritivo
- Não usar `B1_FILIAL = C2_FILIAL` no join sem validação prévia do ambiente, para não reduzir indevidamente o retorno

---

## Resumo de implementação

A rota deve:

1. Receber filial e faixa de datas
2. Buscar OPs finalizadas na `SC2010`
3. Consolidar OP distinta por `C2_NUM`
4. Classificar cada OP como:
   - no prazo
   - atrasada
5. Calcular percentuais
6. Retornar resumo e, opcionalmente, detalhamento

**Fonte:** API DELPI — schema real de `SC2010` e `SB1010` consultado no ambiente.

