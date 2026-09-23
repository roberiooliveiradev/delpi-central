# Suprimentos — saldos de estoque por armazém

Rotas de **controle de estoque** (quantidade de produtos e valor por `B2_LOCAL`), alinhadas ao Power BI de estoque.

**Não confundir** com:

| Rota | Papel |
|------|--------|
| [`/supplies/stock-value`](./supplies-estoque-historico.md) | KPI consolidado (`B2_VATU1`) + histórico/MATR460 |
| [`/supplies/safety-stock/*`](./estoque-seguranca.md) | Estoque de segurança / cobertura |
| `/products/{code}/stock` | Saldo de **um** produto (sem valor R$) |

Padrão TOTVS: [padroes-totvs/armazem-custo.md](./padroes-totvs/armazem-custo.md) § *Valoração de saldo por armazém*.

## Endpoints

| Método | Path | operationId | shape |
|--------|------|-------------|-------|
| `GET` | `/supplies/stock-balances/summary` | `get_supplies_stock_balances_summary` | `playbook_report` |
| `GET` | `/supplies/stock-balances/items` | `get_supplies_stock_balances_items` | `paged_list` |

Permissão: `api-delpi.access` ou `dashboard-supplies.view` (`KPI_SUPPLIES_ACCESS`), ou S2S `supplies-api`.

## Tabelas e colunas

| Tabela | Colunas |
|--------|---------|
| `SB2010` | `B2_FILIAL`, `B2_COD`, `B2_LOCAL`, `B2_QATU`, `B2_CM1`, `B2_VATU1`, `D_E_L_E_T_` |
| `SB1010` | `B1_COD`, `B1_DESC`, `B1_UM`, `D_E_L_E_T_` |

## Valoração

```text
stock_value      = B2_QATU × B2_CM1     -- CM1 do mesmo B2_LOCAL
product_count    = COUNT(DISTINCT B2_COD)
total_quantity   = SUM(B2_QATU)         -- preservado por compatibilidade
total_stock_value = SUM(B2_QATU × B2_CM1)
```

Opcional na resposta (conferência): `total_stock_value_vatu1 = SUM(B2_VATU1)`.

Residual conhecido (`VALUATION_RESIDUAL`): valoração canônica permanece `QATU × CM1` (não `B2_VATU1`).

## Filtros

| Param | Default | Comportamento |
|-------|---------|----------------|
| `branch` | omitido | Consolidado (sem predicado `B2_FILIAL`) — legacy |
| `branch=all` | — | Idem consolidado (legacy) |
| `branch=01` / `branch=02` | — | Filial concreta |
| `branch=01&branch=02` | — | Multi-filial explícita no **mesmo** dataset (`IN (?, ?)`); ordem normalizada para `01,02`; duplicatas removidas |
| `branch=all&branch=01` | — | **Rejeitado** (ambíguo) — HTTP 400 |
| `warehouse` | vazio | Todos os armazéns; alias `location` (aceito, fora do OpenAPI/TV) |
| `only_positive` | `true` | `B2_QATU > 0` (default legado — não alterar sem migração de consumers) |
| `only_positive=false` | — | Inclui saldo zero e negativo (sem predicado `B2_QATU > 0`) |
| `product_codes` | omitido | Só em `/items`. Repetível ou CSV; `B2_COD IN (...)`. Omitido = todos os produtos; informado sem código válido = nenhum produto (`1 = 0`), nunca "todos" |
| `page` / `page_size` | `1` / `50` | Paginação; `page_size` máx. **500** |
| `sort` | `stock_value_desc` | Ordenação da listagem |

Códigos de filial aceitos: somente `01` e `02`. Qualquer outro valor concreto é rejeitado.

Multi-filial **não** é `summary(01) + summary(02)`: `product_count` / `warehouse_count` usam `COUNT(DISTINCT …)` no conjunto filtrado.

Quem precisa do saldo de uma lista fechada de materiais (cockpits de necessidade, por exemplo) combina `product_codes` com `warehouse` e `only_positive=false`, para distinguir saldo zero de saldo negativo em vez de receber a linha ausente.

## Respostas

**summary:** `summary` + `by_warehouse[]` (`warehouse`, `warehouse_label`, `branch`, `product_count`, `total_quantity`, `total_stock_value`).

`by_warehouse` preserva o grão `branch + warehouse` (não colapsa o mesmo `B2_LOCAL` de filiais distintas).

**items:** `items[]` (`product_code`, `description`, `unit_of_measure`, `branch`, `warehouse`, `warehouse_label`, `quantity`, `unit_cost`, `stock_value`) + `pagination`.

| Campo | Fonte |
|-------|--------|
| `unit_of_measure` | `SB1.B1_UM` (aditivo). Ausência de SB1 / UM vazia → `null` (não inventar UM). |
| `warehouse_label` | catálogo `WAREHOUSE_LABELS_PT`; desconhecido → `null` (registro permanece). |

## SQL

`app/infrastructure/persistence/totvs/supplies_repositories/stock_balances_sql.py`
