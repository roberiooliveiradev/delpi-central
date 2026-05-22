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
| `top_limit` | Não | Top produtos por valor (default `10`, máx. `50`). **Somente no modo atual**. |

Regras:

- Histórico exige **os dois** parâmetros de data.
- `start_date` não pode ser maior que `end_date`.
- Com datas, `location` filtra o fechamento SB9 e as movimentações SD3 por `B9_LOCAL` / `D3_LOCAL`.
- `by_location` e `top_products` usam agregação estimada por local e por produto (SB9 + SD3).

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
      "period_net_value": -855519.157
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
    "end_date_exclusive": "20260501",
    "note": "Valor estimado a partir do último fechamento real em SB9010..."
  }
}
```

---

## Limitações

- Resultado de **análise gerencial**, não substitui fechamento contábil oficial na SB9.
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
