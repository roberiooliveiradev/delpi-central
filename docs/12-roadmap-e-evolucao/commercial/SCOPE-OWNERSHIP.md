# Portal Comercial — dono do escopo de clientes

> **Status:** canônico (ago/2026) · ADRs [ADR-001](./adr/ADR-001-commercial-api.md) · [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md)  
> **Diretriz Cursor:** `.cursor/rules/application-bounded-context-decoupling.mdc` + `.cursor/rules/mfe-own-api-no-direct-api-delpi.mdc` — MFE do Portal **nunca** chama api-delpi; regra/membership só em `commercial-api`.

## Princípio

| Camada | Responsabilidade |
|--------|------------------|
| **commercial-api** | Membership, escopo de clientes, CRUD carteira/avatar, BFF que aplica escopo **antes** do proxy TOTVS — **única** evolução de regra do Portal |
| **api-delpi** | SQL/views TOTVS (paths `totvs-*` / enrichment / billing sem membership Portal) — **não** dono de carteira do Portal |
| **PVA** (`/pedidos-venda-abertos/` + plugin) | Legado **congelado** para regra de negócio nova (só bug crítico / segurança até F2c) |

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
| KPIs `/analytics/*`, OV, OTD | commercial-api (`seller_id`/`membership` → `customer_codes`) | MFE → commercial-api → `GET …/commercial/*` |
| Propostas ADY `/proposal-documents*` | commercial-api (RBAC) | MFE → commercial-api → api-delpi `commercial-proposals` |
| Production / products BFF | commercial-api (RBAC) | MFE → commercial-api → api-delpi production/products |
| PVA `GET /pedidos-venda-abertos/` | Legado: membership + **`for_open_orders`** (sem vínculo → consolidado) | Só plugin PVA |
| PVA `…/clientes/…/notas-fiscais` | Legado: `customer_allowed` / membership clássico | Só plugin PVA |

## Gate de PR (Portal)

- [ ] MFE `plugins/commercial` **nunca** chama `/apps/api-delpi` (grep zero: `apiDelpiUrl|API_DELPI_BASE|/apps/api-delpi` no `src/`).
- [ ] Rotas BFF do Portal aplicam `ResolveCommercialCustomerScopeService` (ou helper `resolve_portfolio_scope`) antes do gateway quando há membership.
- [ ] api-delpi **não** reintroduz `list_by_user_id` / dual-read commercial em enrichment, billing-series, avatar ou NF para o path do Portal.
- [ ] Portal usa paths TOTVS puros (`totvs-open-orders`, `totvs-outbound-invoices`) — rotas PVA com membership ficam só para o plugin PVA.
- [ ] Semântica `team.view` = irrestrito testada só na commercial-api.
- [ ] **Nenhuma** regra de negócio nova no PVA / `ResolvePortfolioScope` / `portfolio_access` “para alinhar com o Portal”.
- [ ] Sem import/shared module de regra entre `commercial-api` e `api-delpi`.

## Fora deste contrato

- Delete físico PVA / dual-read completo (F2c).
- Mover SQL Protheus para commercial-api.
