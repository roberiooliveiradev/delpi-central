# Portal Comercial — dono do escopo de clientes

> **Status:** canônico (ago/2026) · ADRs [ADR-001](./adr/ADR-001-commercial-api-bounded-context.md) · [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md)

## Princípio

| Camada | Responsabilidade |
|--------|------------------|
| **commercial-api** | Membership, escopo de clientes, CRUD carteira/avatar, BFF que aplica escopo **antes** do proxy TOTVS |
| **api-delpi** | SQL/views TOTVS (pedidos, NF, billing, enrichment, KPIs) **sem** montar «carteira do usuário» a partir de JWT + membership commercial para o Portal |

**Uma fonte de escopo no Portal:** `ResolveCommercialCustomerScopeService`.

| Permissão | Semântica de escopo |
|-----------|---------------------|
| `commercial.seller-portfolios.manage` | Irrestrito (consolidado) |
| `commercial.accounts.team.view` | Irrestrito no Portal; pode filtrar por `portfolio_id` / `seller_id` (PK da carteira) |
| Demais (`accounts.view` etc.) **com** membership | Union dos clientes das carteiras do JWT |
| Demais **sem** membership | Em **pedidos em aberto** → consolidado (todos os clientes); demais superfícies (NF/billing/avatar) seguem `ensure_allows` / filter_pairs |

## Matriz rota × dono da regra

| Superfície | Dono do escopo | Quem chama o quê |
|------------|----------------|------------------|
| CRUD `/seller-portfolios*` | commercial-api | MFE → commercial-api |
| `GET/PUT/DELETE …/avatar` | commercial-api (`ensure_allows`) | MFE → commercial-api |
| `POST /customers/enrichment` | commercial-api (filter_pairs) → api-delpi TOTVS | MFE → commercial-api |
| `GET /customers/search` | Sem membership (manage/add) | MFE → commercial-api → api-delpi |
| `GET /open-orders/` | commercial-api filtra resposta TOTVS | MFE → commercial-api → `GET …/totvs-open-orders` |
| `GET /open-orders/ops-abertas` | Proxy (sem membership) | MFE → commercial-api → api-delpi |
| `POST /customers/billing-series` | commercial-api (filter_pairs) | MFE → commercial-api → api-delpi (path TOTVS sem gate PVA) |
| `GET /customers/{c}/{s}/outbound-invoices` | commercial-api (`ensure_allows`) | MFE → commercial-api → `GET …/totvs-outbound-invoices/{c}/{s}` |
| KPIs `/commercial/*`, propostas, production | Sem membership de carteira | MFE → api-delpi (OK) |
| PVA `GET /pedidos-venda-abertos/` + `…/clientes/…/notas-fiscais` | Legado: `ResolvePortfolioScope` na api-delpi até F2c | Só plugin PVA — **não** alterar regras para o Portal |

## Gate de PR (Portal)

- [ ] MFE `plugins/commercial` **não** chama `billing-series` / open-orders / NF **direto** na api-delpi (só via `/apps/commercial-api`).
- [ ] Rotas BFF do Portal aplicam `ResolveCommercialCustomerScopeService` (ou helper `_customer_scope_for_request`) antes do gateway.
- [ ] api-delpi **não** reintroduz `list_by_user_id` / dual-read commercial em enrichment, billing-series, avatar ou NF para o path do Portal.
- [ ] Portal usa paths TOTVS puros (`totvs-open-orders`, `totvs-outbound-invoices`) — rotas PVA com membership ficam só para o plugin PVA.
- [ ] Semântica `team.view` = irrestrito testada só na commercial-api.

## Fora deste contrato

- Delete físico PVA / dual-read completo (F2c).
- Migrar KPIs `/commercial/*` para commercial-api.
- Mover SQL Protheus para commercial-api.
