# Commercial billing portfolio — previsto × realizado

Família de rotas simples que devolvem **receita prevista** (carteira SC5/SC6 por `C6_ENTREG`) e **receita realizada** (NF/ROL por `D2_EMISSAO`) no mesmo contrato.

Regra TOTVS: [padroes-totvs/carteira-semanal-previsto-realizado.md](./padroes-totvs/carteira-semanal-previsto-realizado.md).  
Índice comercial: [commercial-analysis-routes.md](./commercial-analysis-routes.md).

## Rotas

| Método | Path | operationId | Shape |
|--------|------|-------------|-------|
| GET | `/commercial/billing-portfolio/summary` | `get_billing_portfolio_summary` | scalar |
| GET | `/commercial/billing-portfolio/series` | `get_billing_portfolio_series` | scalar |
| GET | `/commercial/billing-portfolio/by-customer` | `get_billing_portfolio_by_customer` | paged_list |
| GET | `/commercial/billing-portfolio/by-branch` | `get_billing_portfolio_by_branch` | paged_list |

Permissão: `KPI_COMMERCIAL_ACCESS`.

## Query comum

| Param | Default | Notas |
|-------|---------|-------|
| `start_date` / `end_date` | obrigatórios | ISO / YYYYMMDD |
| `branch` | omitido = consolidado | `01` \| `02` |
| `customer_segment` | — | `weg` \| `new_business` |
| `customer_codes` / `customer_names` | — | CSV |
| `exclude_customer_codes` / `exclude_customer_names` | — | CSV |
| `customer_centers` | — | CSV SA7.A7_XCENT |
| `nature` | `order_gross` | também `rol` |
| `quantity_basis` | `planned` | também `open` |
| `granularity` | (só series) | `day` \| `week` \| `month` \| `year` |
| `page` / `page_size` | (só by-customer) | paginação |

## Contrato `data` (sempre)

```text
forecast_value
realized_value
variance_value          # realized − forecast
nature
quantity_basis
forecast_date_basis     # C6_ENTREG
realized_date_basis     # D2_EMISSAO
as_of                   # live
```

| Rota | Extra |
|------|-------|
| summary | `by_branch[]` com a tríade por filial |
| series | `granularity`, `truncated`, `points[]` (tríade + sort_key/start/end) |
| by-customer | `items[]` (customer_* + tríade), `pagination`, `summary` |
| by-branch | `items[]` (branch + tríade), `summary` |

## Realizado por `nature`

| `nature` | Fonte |
|----------|-------|
| `order_gross` | `FinancialRepository.get_rol` → `gross_revenue` |
| `rol` | `FinancialRepository.get_rol` → `rol` |

`/commercial/rol/*` permanece intacta (realizado isolado). Não misturar com OTD (`/sales-order-otd/*`).

## Limites do MVP

- `as_of=live` — sem snapshot histórico persistido.
- Sem rota composta; sem `include=portfolio`.
- Sem series-by-customer / panel SC6 / meta SI neste MVP.
- Chat Action Catalog / MFE fora do escopo desta entrega.

## Referências de código

- Use cases: `app/application/use_cases/commercial/get_billing_portfolio_*_use_case.py`
- Repo forecast: `CommercialWeeklyPortfolioRepository`
- Composer: `build_get_billing_portfolio_*_use_case` em `commercial_composer.py`
