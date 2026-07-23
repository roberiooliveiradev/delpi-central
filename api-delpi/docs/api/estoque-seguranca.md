# Estoque de Segurança — API

Rotas de análise de matérias-primas (MP) versus estoque de segurança cadastrado (SBZ), saldos SB2 e cobertura futura por pedidos (SC7) e empenhos (SD4).

Plugin MFE: [plugins/estoque-seguranca/README.md](../../../plugins/estoque-seguranca/README.md).

---

## Base

`/apps/api-delpi/supplies/safety-stock`

Envelope padrão `{ success, message, data, meta }`. Empresa padrão nesta entrega: **01** (tabelas `*010`).

---

## Endpoints

| Método | Rota | `operationId` | Shape |
|--------|------|---------------|-------|
| GET | `/filters` | `get_supplies_safety_stock_filters` | scalar |
| GET | `/summary` | `get_supplies_safety_stock_summary` | scalar |
| GET | `/items` | `get_supplies_safety_stock_items` | paged_list |
| GET | `/items/{code}/details` | `get_supplies_safety_stock_item_details` | composite_analysis |
| GET | `/items/{code}/suppliers` | `get_supplies_safety_stock_item_suppliers` | list |
| GET | `/items/{code}/suppliers/{supplier_code}/purchase-price-history` | `get_supplies_safety_stock_supplier_purchase_price_history` | playbook_report |
| GET | `/consumption-analysis/summary` | `get_supplies_safety_stock_consumption_analysis_summary` | scalar |
| GET | `/consumption-analysis/items` | `get_supplies_safety_stock_consumption_analysis_items` | paged_list |
| GET | `/consumption-analysis/items/{code}` | `get_supplies_safety_stock_consumption_analysis_item_details` | composite_analysis |

Parâmetro comum: `branch` (`01` SC / `02` ES).

---

## Análise de consumo × ESTSEG sugerido

Responde à pergunta gerencial: **qual estoque de segurança cobre o lead time com base no consumo real?**

### Escopo

- Somente MPs com `BZ_ESTSEG <> 0`
- Somente produtos com pelo menos uma baixa elegível nos últimos **365 dias corridos** (janela inclusiva única no SQL e no denominador)
- Simulação **somente leitura** (não atualiza SBZ)

### Consumo (SD3)

Soma assinada de `D3_QUANT` com:

- `D_E_L_E_T_ = ''`
- mesma filial/produto
- `D3_LOCAL = '99'`
- OP preenchida (`D3_OP`)
- `D3_TM = '999'`

### Fórmulas

\[
\text{consumo médio diário útil} = \frac{\sum D3\_QUANT}{\text{dias úteis do período}}
\]

Dias úteis = segunda a sexta (feriados não descontados).

\[
\text{sugerido} = \lceil \text{consumo médio diário útil} \times \text{dias úteis no lead time} \rceil
\]

`BZ_PE` é lead time em **dias corridos**; a API converte a janela futura correspondente em dias úteis.

\[
\text{cobertura (dias úteis)} = \frac{\text{saldo } 01+98+99}{\text{consumo médio diário útil}}
\]

### Status gerenciais

| Status | Significado |
|--------|-------------|
| `below_suggested` | ESTSEG atual abaixo do sugerido |
| `above_suggested` | ESTSEG atual acima do sugerido |
| `adequate` | Dentro de 5% do sugerido |
| `inconsistent_data` | Consumo/lead time inválidos para recomendar |

### Cache e performance

- Namespace `safety-stock-consumption-analysis` no `query_cache` (TTL padrão)
- Agregação única por produto (sem N+1)
- Detalhe do item: série mensal dos últimos 12 meses + `annual_comparison` (Jan–Dez × 3 anos civis) numa única consulta SD3 a partir de 01/jan do primeiro ano
- Medição inicial (filial `01`, jul/2026): ~560 itens em ~1,8 s (SQL frio); use case aquecido via cache fica tipicamente &lt; 50 ms
- Índices candidatos a validar no TOTVS se a latência subir: SD3 `(D3_FILIAL, D3_LOCAL, D3_TM, D3_EMISSAO, D3_COD)` e SBZ `(BZ_FILIAL, BZ_COD)`

---

## Detalhe do produto — contrato

`GET /items/{code}/details?branch=01`

Blocos em `data`:

| Bloco | Conteúdo |
|-------|----------|
| `product` | Identificação / cadastro |
| `stock` | Saldos 01/98/99, ESTSEG, déficit **físico** |
| `peer_branch_stock` | Saldo disponível na outra filial (01↔02) + `last_consumption_date` (última baixa elegível), se o usuário tiver permissão de visualização |
| `purchase_coverage` | Cobertura do déficit físico só com SC7 elegível |
| `open_purchase_orders` | `{ items, total }` pedidos abertos |
| `open_commitments` | `{ items, total, summary }` empenhos SD4 com `D4_QUANT > 0` |
| `stock_projection` | `{ items, total, summary }` extrato cronológico consolidado |
| `monthly_consumption` | Série mensal (12 meses) + `period_consumption` para o gráfico |
| `annual_comparison` | Pivot Jan–Dez × 3 anos civis (comparativo sazonal) |

`meta.sections` lista `open_purchase_orders`, `open_commitments`, `stock_projection`, `monthly_consumption` e `annual_comparison`.

### Regras de negócio

- Déficit físico: `ESTSEG − saldo(01+98+99)`. Pedidos e empenhos **não** alteram esse valor.
- Empenho aberto: `D_E_L_E_T_ = ''` e `D4_QUANT > 0`. Quantidade projetada = `D4_QUANT` (não `QTDEORI − QUANT`).
- Campo original Protheus: `D4_QTDEORI` (não `D4_QTDORI`).
- Data da projeção do empenho: `SC2.C2_DATPRI` da OP do empenho (`D4_OP` → SC2). `D4_DATA` fica só como `empenho_recorded_date` (registro do empenho). Sem `C2_DATPRI`, o evento fica sem data confiável.
- Produto acabado no extrato/empenhos: OP do empenho (`D4_OP`) → OP mãe `LEFT(D4_OP, 6) + '01001'` → `SC2.C2_PRODUTO` (`finished_product_code`) e `SC2.C2_OBS` (`finished_order_observation`).
- Extrato consolidado 01+98+99; cada linha mantém armazém de origem.
- Projeção: saldo atual + SC7 elegível − SD4 elegível, com saídas antes de entradas no mesmo dia.
- Unidade incompatível fica listada, mas fora da projeção/cobertura.

### Exemplo

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: estoque-seguranca" \
     "http://localhost/apps/api-delpi/supplies/safety-stock/items/10020113/details?branch=01" \
  | jq '.meta.operationId, .meta.sections, .data.stock_projection.summary.status'
```

---

## Fornecedores vinculados — contrato

`GET /items/{code}/suppliers?branch=01`

Endpoint auxiliar do modal: carrega independentemente do detalhe composto, para que falha/vazio dos fornecedores não oculte saldos e projeção.

`data` retorna `{ items, total }`. Cada item:

| Campo | Origem |
|-------|--------|
| `supplier_code` / `supplier_store` | SA5 (`A5_FORNECE` / `A5_LOJA`) |
| `supplier_part_number` | SA5 (`A5_CODPRF` — partnumber do produto no fornecedor) |
| `trade_name` / `legal_name` / `document` | SA2 (`A2_NREDUZ` / `A2_NOME` / `A2_CGC`) |
| `has_last_purchase` | `true` quando existe NF em SD1 |
| `last_purchase_date` | SD1 `D1_DTDIGIT` (ISO `YYYY-MM-DD`) |
| `last_unit_price` | SD1 `D1_VUNIT` |
| `last_quantity` | SD1 `D1_QUANT` |
| `last_total_value` | SD1 `D1_TOTAL` |
| `last_invoice_number` / `last_invoice_series` | SD1 `D1_DOC` / `D1_SERIE` |

### Regras de negócio

- Amarração em SA5 (filial da consulta ou cadastro compartilhado em branco); um registro por produto + fornecedor + loja.
- Última compra: `ROW_NUMBER()` em SD1 particionado por produto/fornecedor/loja, ordenado por `D1_DTDIGIT DESC`, `D1_EMISSAO DESC`, `R_E_C_N_O_ DESC`.
- SD1: `D_E_L_E_T_ = ''`, `D1_TIPO = 'N'`, `D1_QUANT > 0`, filtrado por filial e produto.
- Fornecedor sem compra permanece na lista com `has_last_purchase = false` e campos de compra nulos.
- Fornecedores internos DELPI (`000052`, `000972` — transferência entre filiais) são excluídos da lista (`safety_stock_supplier_scope_service.INTERNAL_TRANSFER_SUPPLIER_CODES`).
- Ordenação: última compra mais recente primeiro; fornecedores sem compra ao final (desempate por nome e código).

### Exemplo

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: estoque-seguranca" \
     "http://localhost/apps/api-delpi/supplies/safety-stock/items/10020113/suppliers?branch=01" \
  | jq '.meta.operationId, .data.total, .data.items[0]'
```

---

## Histórico de preço por fornecedor — contrato

`GET /items/{code}/suppliers/{supplier_code}/purchase-price-history?branch=01&supplierStore=01`

Carga sob demanda ao selecionar um fornecedor no modal. Intervalo móvel dos últimos 12 meses com base em `D1_DTDIGIT`.

`data` retorna:

| Campo | Conteúdo |
|-------|----------|
| `items` | Pontos cronológicos (ASC): data, `D1_VUNIT`, quantidade, total, NF/série |
| `total` | Quantidade de compras no período |
| `summary` | `min_unit_price`, `max_unit_price`, `first_unit_price`, `last_unit_price`, `variation_percent` |
| `date_start` / `date_end_exclusive` | Intervalo Protheus `YYYYMMDD` |

### Regras de negócio

- Uma compra = um ponto (sem média mensal).
- Filtros: filial, produto, fornecedor, loja, `D_E_L_E_T_ = ''`, `D1_TIPO = 'N'`, `D1_QUANT > 0` e exclusão canônica de fornecedores internos/transporte.
- Empate de data: `D1_EMISSAO`, `R_E_C_N_O_`.

### Exemplo

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: estoque-seguranca" \
     "http://localhost/apps/api-delpi/supplies/safety-stock/items/10020113/suppliers/F001/purchase-price-history?branch=01&supplierStore=01" \
  | jq '.meta.operationId, .data.summary, .data.items[0]'
```

---

## RBAC

| Permissão | Escopo |
|-----------|--------|
| `estoque-seguranca.access` | Acesso ao módulo |
| `estoque-seguranca.view.filial-sc` | Filial `01` |
| `estoque-seguranca.view.filial-es` | Filial `02` |

Gate de filial no router antes do use case (`branch_access_error`).

---

## Performance SQL (SD4 / SA5 / SD1)

- Consulta parametrizada por `D4_FILIAL` + `D4_COD`, `WITH (NOLOCK)`, sem função nas colunas do `WHERE`.
- Fornecedores: uma query com CTEs (SA5 + SA2 + SD1); medir no Protheus tempo/plano; índices úteis `A5_PRODUTO`, `D1_FILIAL+D1_COD+D1_FORNECE+D1_LOJA+D1_DTDIGIT`.
- Medir no Protheus: tempo, linhas e plano; avaliar índice em `C7_FILIAL+C7_PRODUTO` / `D4_FILIAL+D4_COD` se ultrapassar alerta de SQL lento.
