# Portal Comercial — dono do escopo de clientes

> **Status:** canônico (ago/2026) · ADRs [ADR-001](./adr/ADR-001-commercial-api.md) · [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md)  
> **RBAC:** [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) — `commercial.access` / `commercial.manage` / `commercial.billing.notify`  
> **Diretriz Cursor:** `.cursor/rules/application-bounded-context-decoupling.mdc` + `.cursor/rules/mfe-own-api-no-direct-api-delpi.mdc` — MFE do Portal **nunca** chama api-delpi; regra/membership só em `commercial-api`.

## Princípio

| Camada | Responsabilidade |
|--------|------------------|
| **commercial-api** | Membership, escopo de clientes, CRUD carteira/avatar, BFF que aplica escopo **antes** do proxy TOTVS — **única** evolução de regra do Portal |
| **api-delpi** | SQL/views TOTVS (paths `totvs-*` / enrichment / billing sem membership Portal) — **não** dono de carteira do Portal |
| **PVA** (`/pedidos-venda-abertos/` + plugin) | Legado **isolado** — schema `pedidos_venda_abertos.*` apenas; **não** lê/escreve `commercial.*`. Congelado para regra nova (bug crítico / segurança). Remoção futura do app. |

**Uma fonte de escopo no Portal:** `ResolveCommercialCustomerScopeService`.

| Permissão | Semântica de escopo |
|-----------|---------------------|
| `commercial.seller-portfolios.manage` | Irrestrito (consolidado) |
| `commercial.accounts.team.view` | Irrestrito no Portal; pode filtrar por `portfolio_id` / `seller_id` (PK da carteira) |
| Demais (`accounts.view` etc.) **com** membership | Union dos clientes das carteiras do JWT; com **2+ carteiras** pode filtrar por PK **própria** (`portfolio_id` / `seller_id`) |
| Demais **sem** membership | Em **pedidos em aberto** / **listas MC / KPIs** → filtro ou consolidado conforme a superfície; **Conta detalhe** (par único: NF, avatar GET, contatos CUD, enrichment/billing com 1 par) → `accounts.view` **sem** `ensure_allows` |

### Conta fora da carteira (deep-link)

| Regra | Comportamento |
|-------|----------------|
| Gate MFE Conta | `accounts.view` (app); **não** exige `canAccessMyPortfolio` |
| Lista Minha Carteira / topnav MC | KEEP membership / team / manage |
| Topbar | Par ∉ carteiras do user e **sem** team/manage → item efêmero **Cliente** ativo; MC não ativa |
| Team/manage | Conta tratada como «dentro» (sem item Cliente) |
| API Conta (path `/{code}/{store}/*`) | Sem `ensure_allows`; contatos CUD liberados |
| Enrichment / billing-series | **1 par** = Conta (sem filter); **N pares** = lista (KEEP `filter_pairs`) |
| Pedidos na Conta | `GET /customers/{c}/{s}/open-orders` — TOTVS por par, **sem** membership |
| Oportunidades na Conta | `account_customer_code` no BFF analytics — **sem** membership de carteira |
| Pedidos / KPIs / lista MC | KEEP filtro membership |

## Matriz rota × dono da regra

| Superfície | Dono do escopo | Quem chama o quê |
|------------|----------------|------------------|
| CRUD `/seller-portfolios*` | commercial-api | MFE → commercial-api |
| `GET …/avatar` (Conta) | commercial-api (`accounts.view`, sem membership) | MFE → commercial-api |
| `PUT/DELETE …/avatar` | commercial-api (manage) | MFE → commercial-api |
| `POST /customers/enrichment` | 1 par Conta sem filter; N pares `filter_pairs` → api-delpi | MFE → commercial-api |
| `GET /customers/search` | Sem membership (Conta + manage/add); api-delpi aceita `accounts.view` | MFE → commercial-api → api-delpi |
| `GET /open-orders/` | commercial-api filtra resposta TOTVS | MFE → commercial-api → `GET …/totvs-open-orders` |
| `GET /customers/{c}/{s}/open-orders` | Conta 360 sem membership | MFE → commercial-api → `GET …/totvs-open-orders/{c}/{s}` |
| `GET /open-orders/ops-abertas` | Proxy (sem membership) | MFE → commercial-api → api-delpi |
| `POST /customers/billing-series` | 1 par Conta sem filter; N pares `filter_pairs` | MFE → commercial-api → api-delpi |
| `GET /customers/{c}/{s}/outbound-invoices` | commercial-api (`accounts.view`, sem membership) | MFE → commercial-api → `GET …/totvs-outbound-invoices/{c}/{s}` |
| Contatos `…/contacts*` | commercial-api (`accounts.view`, sem membership) | MFE → commercial-api |
| KPIs `/analytics/*`, OV, OTD | commercial-api (`seller_id`/`membership` → `customer_codes`) | MFE → commercial-api → `GET …/commercial/*` |
| `GET /analytics/open-portfolio-summary` | commercial-api filtra open-orders (summary só; sem `items`) | MFE → commercial-api → `GET …/totvs-open-orders` |
| Propostas ADY `/proposal-documents*` | commercial-api (RBAC) | MFE → commercial-api → api-delpi `commercial-proposals` |
| Production / products BFF | commercial-api (RBAC) | MFE → commercial-api → api-delpi production/products |
| `/interaction-rooms*` (sala P0) | commercial-api (membership da sala + `access`/`manage`) | MFE → commercial-api — **sem** api-delpi |
| PVA `GET /pedidos-venda-abertos/` | Legado: membership + **`for_open_orders`** (sem vínculo → consolidado) | Só plugin PVA |
| PVA `…/clientes/…/notas-fiscais` | Legado: `customer_allowed` / membership clássico | Só plugin PVA |

## Gate de PR (Portal)

- [ ] MFE `plugins/commercial` **nunca** chama `/apps/api-delpi` (grep zero: `apiDelpiUrl|API_DELPI_BASE|/apps/api-delpi` no `src/`).
- [ ] Rotas BFF do Portal aplicam `ResolveCommercialCustomerScopeService` (ou helper `resolve_portfolio_scope`) antes do gateway quando há membership.
- [ ] api-delpi / PVA **não** lê schema `commercial.*` (sem dual-read de carteira). Portal não depende do PVA.
- [ ] Portal usa paths TOTVS puros (`totvs-open-orders`, `totvs-outbound-invoices`) — rotas PVA com membership ficam só para o plugin PVA.
- [ ] Semântica `team.view` = irrestrito testada só na commercial-api.
- [ ] **Nenhuma** regra de negócio nova no PVA / `ResolvePortfolioScope` / `portfolio_access` “para alinhar com o Portal”.
- [ ] Sem import/shared module de regra entre `commercial-api` e `api-delpi`.

## Fora deste contrato

- Delete físico do plugin PVA (app) quando produto decidir; carteiras já estão desacopladas.
- Mover SQL Protheus para commercial-api.
