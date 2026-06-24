# Estoque histórico estimado — `GET /supplies/stock-value`

## Visão geral

A rota `GET /supplies/stock-value` possui dois modos:

| Modo | Quando | Fonte |
|---|---|---|
| **Atual** | Sem `start_date` e sem `end_date` | `SB2010` — saldo corrente (`B2_VATU1`, `B2_QATU`) |
| **Histórico estimado** | Com `start_date` **e** `end_date` | `SB9010` + `SD3010` — ver método abaixo |

O modo histórico responde perguntas como *“qual era o valor do estoque em abril/2026?”* quando **não existe fechamento oficial** na `SB9010` para aquela data.

A resposta inclui o objeto `estimation` quando o modo histórico está ativo.

---

## Parâmetros

| Query | Obrigatório | Descrição |
|---|---|---|
| `branch` | Não | Filial (`01`, `02`, …). Omitido = consolidado. |
| `location` | Não | Local de estoque. **Somente no modo atual** (SB2). |
| `start_date` | Condicional | Início do período (inclusivo). Ex.: `2026-04-01`, `20260401`. |
| `end_date` | Condicional | Fim do período (inclusivo). Ex.: `2026-04-30`, `20260430`. |
| `top_limit` | Não | Top produtos por valor (default `10`, máx. `50`). Omitido no `summary_only`. |
| `summary_only` | Não | Quando `true`, retorna **apenas** `summary` (sem `by_branch`, `by_location`, `top_products`). Default `false`. |

Regras:

- Histórico exige **os dois** parâmetros de data.
- `start_date` não pode ser maior que `end_date`.
- Com datas, `location` filtra o fechamento SB9 e as movimentações SD3 por `B9_LOCAL` / `D3_LOCAL`.
- `by_location` e `top_products` usam agregação estimada por local e por produto (SB9 + SD3) — **indisponíveis** com `summary_only=true`.
- O **Strategic Indicators** e o **IDD** (`/inventory-turnover`) chamam sempre `summary_only=true` para o KPI consolidado.

---

## Método de cálculo (histórico)

### Conceito

```text
Valor estimado no fim do período =
  Valor do último fechamento real em SB9 (antes de start_date)
+ Movimentos SD3 entre o fechamento e start_date
+ Movimento líquido SD3 dentro do período [start_date, end_date]
```

Fórmula resumida:

```text
Estoque_final = SB9_base + SD3_ponte + SD3_período
```

### Tabelas

**`SB9010` — fechamento**

| Campo | Uso |
|---|---|
| `B9_FILIAL` | Filial |
| `B9_DATA` | Data do fechamento (`YYYYMMDD`) |
| `B9_QINI` | Quantidade no fechamento |
| `B9_VINI1` | Valor no fechamento |

Para cada filial, usa-se `MAX(B9_DATA)` com `B9_DATA < start_date` como base.

**`SD3010` — movimentações**

| Campo | Uso |
|---|---|
| `D3_FILIAL` | Filial |
| `D3_EMISSAO` | Data da movimentação |
| `D3_TM` | Tipo de movimento |
| `D3_QUANT` | Quantidade |
| `D3_CUSTO1` | Valor |

Regra entrada/saída:

```text
D3_TM < '500'  → entrada
D3_TM >= '500' → saída
```

Valor líquido:

```sql
CASE WHEN D3_TM < '500' THEN D3_CUSTO1 ELSE -D3_CUSTO1 END
```

### Intervalo de datas

- Período solicitado: `D3_EMISSAO >= start_date` e `D3_EMISSAO < (end_date + 1 dia)` em formato Protheus.
- Exemplo abril/2026: `start_date=20260401`, `end_date=20260430` → movimentos com emissão `>= 20260401` e `< 20260501`.

### Movimento entre fechamento e início do período

Entre `DATA_FECHAMENTO_BASE` e `start_date` (exclusive no início), aplica-se a mesma regra líquida de SD3 para “atualizar” a base até o primeiro dia do período analisado.

Na implementação SQL (jun/2026), **ponte** e **período** são obtidos numa **única varredura** de `SD3010`:

- Filtro indexável: `D3_EMISSAO > closing_base_date` **e** `D3_EMISSAO < end_date_exclusive`.
- Separação ponte vs. período via `CASE` usando `start_date` como fronteira.

Exemplo validado (abril/2026):

- Último fechamento SB9: `20260228`
- Período: março + abril até `20260430`
- Consolidado estimado: **R$ 8.273.236,494**

---

## Exemplo de requisição

```http
GET /supplies/stock-value?start_date=2026-04-01&end_date=2026-04-30
```

Filial específica:

```http
GET /supplies/stock-value?branch=01&start_date=2026-04-01&end_date=2026-04-30
```

Estoque atual (sem filtro de data):

```http
GET /supplies/stock-value?branch=02&location=01
```

---

## Exemplo de resposta (trecho)

```json
{
  "branch": "consolidated",
  "location": "all",
  "summary": {
    "total_stock_value": 8273236.494,
    "total_stock_quantity": 0
  },
  "by_branch": [
    {
      "branch": "01",
      "total_stock_value": 1718441.479,
      "closing_base_date": "20260228",
      "closing_base_value": 3474907.576,
      "bridge_value": -900946.94,
      "period_net_value": -855519.157,
      "official_closure_date": "20260228",
      "official_closure_value": 3474907.576,
      "official_closure_available": true,
      "official_closure_on_period_end": false
    }
  ],
  "by_location": [
    {
      "branch": "02",
      "location": "01",
      "total_stock_value": 1200000.0,
      "total_stock_quantity": 5000.0
    }
  ],
  "top_products": [
    {
      "product_code": "10080047",
      "product_description": "Produto exemplo",
      "total_stock_value": 250000.0,
      "total_stock_quantity": 120.0
    }
  ],
  "estimation": {
    "enabled": true,
    "method": "sb9_last_closure_plus_sd3_movements",
    "start_date": "20260401",
    "end_date": "20260430",
    "end_date_exclusive": "20260501",
    "closing_base_date": "20260228",
    "closing_base_value": 3474907.576,
    "bridge_value": -900946.94,
    "period_net_value": -855519.157,
    "official_closure_available": true,
    "official_closure_date": "20260228",
    "official_closure_value": 3474907.576,
    "official_closure_on_period_end": false,
    "data_quality_warning": "Último fechamento SB9 anterior ao fim do período; ...",
    "note": "Valor estimado a partir do último fechamento real em SB9010..."
  }
}
```

Campos de auditoria (W1, jun/2026): `closing_base_*`, `bridge_value`, `period_net_value`, `official_closure_*` e `data_quality_warning` quando a base SB9 é anterior a `end_date` sem fechamento na data do inventário.

---

## Limitações

- Resultado de **análise gerencial**, não substitui fechamento contábil oficial na SB9.
- Comparação com **Registro de Inventário** (MATR460): ver plano de correção em [playbook-correcao-estoque-supplies-inventario.md](../roadmaps/playbook-correcao-estoque-supplies-inventario.md) (ondas W0–W4, modo fechamento oficial, EM PROCESSO).
- Detalhamento por produto/local é estimado (não replica saldo SB2 linha a linha).
- Depende da consistência das movimentações SD3 e do último fechamento SB9 disponível.

Referência de validação interna: documento *Método de Cálculo do Valor de Estoque em Abril/2026* (cenários abril/2026 e março/2025).

---

## Uso no giro de estoque (IDD)

A rota `GET /supplies/inventory-turnover` reutiliza **o mesmo estoque** de `/supplies/stock-value`:

- Com `start_date` e `end_date`: estimativa SB9010 + SD3010 (fim do período).
- Sem datas no estoque: saldo atual SB2010 (o IDD ainda exige datas para o CPV).

Fórmulas do IDD (inalteradas):

```text
IDD (meses) = valor_estoque ÷ CPV_médio_mensal
Giro (vezes) = CPV_total ÷ valor_estoque
```

O CPV vem de `SD2010` no período (`SUM(D2_CUSTO1)`, `D2_EMISSAO`), com CFOPs Kardex `5101`, `5124`, `6101`, `6124` (`D2_CF`).

---

## Implementação SQL e performance (jun/2026)

### Onde está no código

| Artefato | Caminho |
|---|---|
| CTEs e templates SQL | `api-delpi/app/infrastructure/persistence/totvs/supplies_repositories/stock_value_historical_sql.py` |
| Repositório / cache | `stock_value_query_repository.py`, `stock_value_cache.py` |
| `operation_id` console | `get_supplies_stock_value` |

### Pipeline histórico (CTE compartilhado)

```text
ultima_data_sb9     → MAX(B9_DATA) por filial antes de start_date
fechamento_base     → saldo SB9010 na data de fechamento (por filial/local/produto)
movimentos_sd3      → uma leitura SD3010; CASE separa ponte e período
item_totals         → UNION ALL + GROUP BY (summary_only; evita item_keys + LEFT JOIN duplo)
item_keys           → UNION das chaves (fechamento + movimentos) — só bundle
estoque_item        → LEFT JOINs; soma base + ponte + período por item — só bundle
```

### Caminhos de execução

| Caller | `summary_only` | SQL | Observação |
|---|---|---|---|
| SI, IDD, dashboard KPI | `true` | `HISTORICAL_STOCK_SUMMARY_SQL` | `item_totals` (rollup); consolidado sem filial → **fan-out 01+02** com cache por filial |
| Chat / MFE detalhe (`StockPage`) | `false` | `HISTORICAL_STOCK_BUNDLE_BATCH_SQL` | Materializa `#Delpi_StockItems` uma vez; 4 SELECTs de breakdown |
| Estoque atual (sem datas) | `summary_only` consolidado | `SB2010` + fan-out | KPI leve; breakdown continua no bundle completo |

Chaves de cache (`stock_value_cache_key`): incluem `branch`, datas, `top_limit` e sufixo `summary` vs `full` (TTL: `QUERY_CACHE_TTL_SECONDS`, default 300 s).

Tabelas SB9010 e SD3010 no bundle histórico usam `WITH (NOLOCK)` para reduzir contenção em leituras analíticas (jun/2026).

### Observabilidade (console Saúde SQL)

Duas hashes para a mesma operação são **esperadas**:

| Variante | Causa típica | Latência relativa |
|---|---|---|
| Com `branch=01/02` | Filtro em SB9/SD3 | Menor |
| Consolidado (sem `branch`) | Todas as filiais em uma varredura | **Fan-out 01+02** em `summary_only` (jun/2026) ou maior latência no bundle completo |

Alertas `slow_sql` (> 2500 ms) no modo histórico consolidado indicam volume TOTVS ou cache frio — validar aba **Cache** e índices abaixo antes de alterar regra de negócio.

### Índices recomendados (DBA / SQL Server)

```sql
-- Fechamento por filial/data
CREATE NONCLUSTERED INDEX IX_SB9010_Filial_Data
ON SB9010 (B9_FILIAL, B9_DATA)
INCLUDE (B9_LOCAL, B9_COD, B9_QINI, B9_VINI1)
WHERE D_E_L_E_T_ = '';

-- Movimentações Kardex por filial/emissão
CREATE NONCLUSTERED INDEX IX_SD3010_Filial_Emissao
ON SD3010 (D3_FILIAL, D3_EMISSAO)
INCLUDE (D3_LOCAL, D3_COD, D3_TM, D3_QUANT, D3_CUSTO1)
WHERE D_E_L_E_T_ = '';
```

Validar com plano de execução antes/depois; nomes podem variar por ambiente Protheus.

### Histórico de otimizações (jun/2026)

| Commit / tema | Mudança | Efeito |
|---|---|---|
| Refatoração CTE único | Unificação `movimentos_sd3`; `UNION`+`LEFT JOIN` no lugar de `FULL OUTER JOIN`; `summary_only` sem temp table | Menos I/O em SD3010; SI/IDD mais leves |
| Summary rollup + fan-out | `item_totals` (UNION ALL); consolidado `summary_only` por filial 01/02 + cache | Reduz alertas `slow_sql` em `get_supplies_stock_value` |
| Filtro em intervalo | `OR` (ponte \| período) → range `(closing_base_date, end_date_exclusive)` | Melhor chance de index seek em SD3010 |

A **semântica** (`sb9_last_closure_plus_sd3_movements`) e os totais validados (ex.: consolidado abril/2026) permanecem os mesmos.

### Backlog residual

- Turnover ainda invoca stock-value separadamente no mesmo snapshot SI (duplicata HTTP; ver `SI_BOTTLENECK_MAP.md` §5.2).
- Fast path só para `total_stock_value` / `total_stock_quantity` (sem `COUNT DISTINCT`) se indicadores deixarem de exigir `total_products` no IDD.
