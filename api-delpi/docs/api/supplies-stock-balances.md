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

Permissão: `api-delpi.access` ou `dashboard-supplies.view` (`KPI_SUPPLIES_ACCESS`).

## Tabelas e colunas

| Tabela | Colunas |
|--------|---------|
| `SB2010` | `B2_FILIAL`, `B2_COD`, `B2_LOCAL`, `B2_QATU`, `B2_CM1`, `B2_VATU1`, `D_E_L_E_T_` |
| `SB1010` | `B1_COD`, `B1_DESC`, `D_E_L_E_T_` |

## Valoração

```text
stock_value      = B2_QATU × B2_CM1     -- CM1 do mesmo B2_LOCAL
product_count    = COUNT(DISTINCT B2_COD) WHERE B2_QATU > 0
total_quantity   = SUM(B2_QATU)
total_stock_value = SUM(B2_QATU × B2_CM1)
```

Opcional na resposta (conferência): `total_stock_value_vatu1 = SUM(B2_VATU1)`.

## Filtros

| Param | Default | Comportamento |
|-------|---------|----------------|
| `branch` | vazio | Consolidado (todas as filiais) |
| `warehouse` | vazio | Todos os armazéns; alias `location` (aceito, fora do OpenAPI/TV) |
| `only_positive` | `true` | `B2_QATU > 0` |
| `page` / `page_size` | `1` / `50` | Paginação; `page_size` máx. **500** |
| `sort` | `stock_value_desc` | Ordenação da listagem |

## Respostas

**summary:** `summary` + `by_warehouse[]` (`warehouse`, `warehouse_label`, `branch`, `product_count`, `total_quantity`, `total_stock_value`).

**items:** `items[]` (`product_code`, `description`, `branch`, `warehouse`, `quantity`, `unit_cost`, `stock_value`) + `pagination`.

## SQL

`app/infrastructure/persistence/totvs/supplies_repositories/stock_balances_sql.py`
