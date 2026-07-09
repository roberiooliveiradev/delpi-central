# OTD de pedidos de venda — `/commercial/sales-order-otd`

**Última atualização:** 2026-07-09  
**Operação OpenAPI:** `get_sales_order_otd`  
**Repositório:** `app/infrastructure/persistence/totvs/commercial_repositories/sales_order_otd_repository.py`  
**SQL:** `sales_order_otd_sql.py`

## Objetivo

Calcular o percentual de linhas de pedido de venda (SC6) atendidas no prazo em relação à data prometida (`C6_ENTREG`), considerando **linhas faturadas e não faturadas**.

## Endpoint

```http
GET /commercial/sales-order-otd?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&branch=02&customer_segment=weg
```

| Parâmetro | Descrição |
|-----------|-----------|
| `start_date` / `end_date` | Filtra linhas pela **data prometida** (`C6_ENTREG`). |
| `branch` | Filial TOTVS (`01`, `02`, …). |
| `customer_segment` | `weg` (cliente `000001`) ou `new_business` (demais clientes). |

## Fonte TOTVS

| Tabela | Papel |
|--------|-------|
| `SC6010` (C6) | Itens do pedido de venda |
| `SC5010` (C5) | Cabeçalho do pedido (cliente, segmento) |

Leitura analítica com `WITH (NOLOCK)`.

## Linhas elegíveis (denominador)

Entram linhas que atendem **todos** os critérios:

| Regra | Campo |
|-------|-------|
| Registro ativo | `C6.D_E_L_E_T_ = ''` e `C5.D_E_L_E_T_ = ''` |
| Quantidade vendida | `C6_QTDVEN > 0` |
| Data prometida preenchida | `C6_ENTREG` não nula/vazia |
| Sem bloqueio | `C6_BLOQUEI` e `C6_BLQ` vazios |
| Período | `C6_ENTREG` entre `start_date` e `end_date` |
| Filial / segmento | Quando informados na query |

**Não exige** faturamento (`C6_DATFAT`) nem entrega total (`C6_QTDENT >= C6_QTDVEN`).

## Classificação no prazo vs. atrasado

| Situação | Regra |
|----------|-------|
| **Faturada** (`C6_DATFAT` preenchida) | **No prazo** se `C6_DATFAT <= C6_ENTREG`; **atrasada** se `C6_DATFAT > C6_ENTREG`. |
| **Não faturada** | **No prazo** se a data de referência `<= C6_ENTREG`; **atrasada** se a data de referência `> C6_ENTREG`. |

**Data de referência** para linhas não faturadas: `end_date` da requisição; se omitida, `GETDATE()` (data corrente no SQL Server).

## Resposta (`data`)

| Campo | Descrição |
|-------|-----------|
| `total_lines` | Total de linhas elegíveis |
| `on_time_lines` | Linhas no prazo |
| `late_lines` | Linhas atrasadas |
| `sales_order_otd_pct` | `on_time_lines / total_lines × 100` (2 casas decimais) |

Metas do Indicadores Estratégicos: `source_key` = `commercial_sales_order_otd`.

## Consumidores

- Dashboard Comercial (`plugins/dashboard-commercial`)
- Strategic Indicators API (`commercial-sales-order-otd`)
- Chat / agente (`get_sales_order_otd`)

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-07-09 | Passa a incluir linhas **não faturadas**; atraso de abertas medido por `end_date` vs. `C6_ENTREG`. |
| Anterior | Considerava apenas linhas faturadas e totalmente entregues. |
