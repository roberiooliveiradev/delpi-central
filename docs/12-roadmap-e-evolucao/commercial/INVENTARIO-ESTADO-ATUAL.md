# Inventário de Estado Atual — Portal Comercial (Fase 1)

> **Tipo:** inventário factual de Current State (código + fontes canônicas do repositório)  
> **Não é:** plano de melhoria, redesign, backlog executável nem prova de runtime/produção  
> **Data da análise (Fase 1):** 2026-09-14T14:23:45-03:00  
> **Fase 1R (residuais técnicos):** 2026-09-14 — § 19 · baseline `47e4c595c`  
> **Baseline Git:** ver § 1  
> **Relação com docs existentes:**
> - [PARCIAL-INVENTARIO.md](./PARCIAL-INVENTARIO.md) — backlog / parcial / bloqueado (não misturar com § Current State)
> - [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md) — baseline histórico de ativos (parcialmente desatualizado; ver conflitos § 13)
> - [SCOPE-OWNERSHIP.md](./SCOPE-OWNERSHIP.md) — decisão de ownership (intenção/contrato)
> - [API-ROUTES.md](./API-ROUTES.md) — catálogo documental (não substitui routers reais)
> - [DATA-MODEL.md](./DATA-MODEL.md) — modelo + especificação futura (só migrations/repos provam implementado)
> - [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) — catálogo RBAC condensado (alinhado ao código nos 3 codes)

---

## Legenda de classificação de evidência

| Tag | Significado |
|-----|-------------|
| `PROVEN_CODE` | Implementação estática no repositório |
| `PROVEN_DOC` | Afirmação só na documentação |
| `PROVEN_TEST_EXISTENCE` | Arquivo de teste existe (não prova verde) |
| `PROVEN_CONFIG` | Compose / nginx / env template / manifest |
| `PLANNED` | Planejado em docs de roadmap/ADR |
| `BACKLOG` | Item de backlog documental |
| `BLOCKED` | Bloqueado por diretriz/doc |
| `OUT_OF_SCOPE` | Fora do bounded context Comercial |
| `TO_INVENTORY` | Ainda precisa inventário adicional no repo |
| `INFERENCE` | Inferência (não tratar como fato) |
| `RUNTIME_REQUIRED` | Só confirmável com evidência externa |

---

## 1. Baseline técnico

| Campo | Valor | Evidência |
|-------|-------|-----------|
| Repository | `roberiooliveiradev/delpi-central` | `git remote` → `git@github.com:roberiooliveiradev/delpi-central.git` |
| Branch | `main` | `git branch --show-current` |
| HEAD inicial | `6038ec5c841a4f03206b8fa342466dfecb68ef63` | `git rev-parse HEAD` no início |
| HEAD esperado (pedido) | `6038ec5c841a4f03206b8fa342466dfecb68ef63` | Pedido Fase 1 |
| Divergência HEAD (início) | **Nenhuma** no início | HEAD inicial = esperado |
| HEAD durante/final da análise | `10f874c84f4a661b9851a9179be8d1418e029a2a` | Avanço externo: `feat(tv-dashboard-api): Custom GPT Actions OAuth façade (TV-GPI-002)` — **sem checkout/reset nesta execução** |
| Impacto no inventário Comercial | Diff `6038ec5..10f874c` em `plugins/commercial`, `commercial-api`, `docs/.../commercial` = **vazio** | Inventário Comercial permanece válido no HEAD final |
| Working tree inicial | **Suja** (alterações **não** relacionadas ao Comercial) | `git status` — ver lista abaixo |
| Data/hora da análise | `2026-09-14T14:23:45-03:00` | `date -Iseconds` |

### Working tree inicial (preservar — não limpar)

Alterações locais presentes no início (nenhuma sob `plugins/commercial/**` ou `commercial-api/**` no status observado):

- Modificados: docs DÉLIA, `minha-delpi-ai-api/*`, `tv-dashboard-api/*`
- Untracked: evidências LLM, testes production-pulse, `tv-dashboard-api` gpt-actions / migrations / scripts

**Ação desta Fase 1:** apenas documentação em `docs/12-roadmap-e-evolucao/commercial/**`. Nenhum arquivo da working tree alheia foi sobrescrito.

---

## 2. Classificação das fontes documentais lidas

| Documento | Classificação | Observação |
|-----------|---------------|------------|
| `README.md` | estado atual (parcial) + planejamento | Status set/2026; misturar com cuidado |
| `SCOPE-OWNERSHIP.md` | decisão / contrato | Matriz ownership; **drift** em nomes de permission codes (ver § 13) |
| `PERFIS-E-PERMISSOES.md` | contrato / decisão | 3 codes alinhados ao código |
| `API-ROUTES.md` | contrato / catálogo documental | Não prova endpoints sem cruzar routers |
| `DATA-MODEL.md` | contrato + planejamento | Mix migrations aplicadas + entidades futuras M3–M5 |
| `PARCIAL-INVENTARIO.md` | backlog / parcial / bloqueado / homolog | Fonte canônica de backlog |
| `INVENTARIO-ATIVOS.md` | histórico / baseline | Desatualizado em permissões e telas |
| `ATA-MAPA-NECESSIDADES.md` | histórico + backlog | Ata × Portal |
| `ATA-ALINHAMENTO-AGO2026-2.md` | histórico / decisão | Ata alinhamento 2 |
| `ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md` | histórico + backlog | Follow-up |
| `F2C-CUTOVER-RUNBOOK.md` | runbook | F2c; config possível, não runtime |
| `GESTAO-A-VISTA.md` | planejamento / norte | Consolidação nativa |
| `WIREFRAMES.md` | intenção / UX | Não prova implementação |
| `IMPLEMENTATION-PLAN.md` | planejamento | Fases F0–F2 |
| `PLAYBOOK-MODULO-COMERCIAL.md` | planejamento | Playbook mestre |
| `PLAYBOOK-01-fronteiras-api-delpi.md` | decisão / fronteira | Ownership TOTVS × Delpi |
| `HOMOLOGACAO-*.md` | homolog / checklist | Não prova uso real |
| `MANUAL-USUARIO-*.md` / `TREINAMENTO-*.md` | intenção / treinamento | Processo humano não comprovado |
| `ROADMAP-INTERACTION-ROOM.md` | histórico + estado documentado | Sala E1–E7 |
| `UX-E-TASKS-EVOLUTION.md` | histórico + backlog | P3 reminder backlog |
| `DESIGN-IA-COMERCIAL.md` | planejamento / UX | |
| `KPI-FICHAS.md` | contrato KPI / homolog | |
| `GAV-TV-FEED.md` | decisão / OUT_OF_SCOPE TV | GR no TV Dashboard |
| `HELP-COVERAGE.md` | estado documental help | |
| ADRs `adr/ADR-001`, `ADR-002` | decisão | |

---

## 3. Arquitetura atual comprovada

```text
Portal host (Module Federation)
  └─ plugins/commercial  (basePath /apps/commercial)
       ├─ HTTP  → /apps/commercial-api/*     (gateway nginx → commercial-api:8000)
       ├─ HTTP  → /core-api/me (+ directory) (perfil/sessão; directory lookup)
       └─ WS    → /apps/commercial-api/commercial/realtime/ws

commercial-api (FastAPI, root_path /apps/commercial-api)
  ├─ Postgres schema commercial          (PLUGINS_DB_*)
  ├─ Volumes arquivo                     (avatars / attachments / user avatars)
  ├─ Gateway HTTP → api-delpi            (DELPI_API_URL, Bearer + X-Delpi-Caller-App)
  ├─ Gateway HTTP → core-api             (directory, person-profile, notifications S2S)
  ├─ Scheduler integration jobs          (ready_to_invoice + task_due)
  ├─ Outbox/checkpoints                  (integration_outbox / integration_checkpoints)
  └─ Realtime hub                        (WebSocket fan-out)

api-delpi
  └─ SQL/views TOTVS (+ paths commercial / pedidos / propostas / production)

core-api
  └─ JWT/RBAC load, directory, notifications, person-profile

dashboard-commercial (legado coexistente — fora do MFE commercial)
  └─ consome api-delpi /commercial/*  (PROVEN_DOC + plugin existe; não inventariado em profundidade nesta fase)
```

### Ligações com evidência arquivo → consumidor → contrato

| Ligação | Evidência | Status |
|---------|-----------|--------|
| Host → MFE commercial | `plugins/commercial/commercial.manifest.json` (`basePath`, `entry`, `type=microfrontend`); Compose service `commercial` | `PROVEN_CONFIG` + `PROVEN_CODE` |
| MFE → commercial-api | `plugins/commercial/src/api/httpClient.ts` → `COMMERCIAL_API_BASE = "/apps/commercial-api"` | `PROVEN_CODE` |
| MFE → core-api `/me` | `plugins/commercial/src/api/meApi.ts` | `PROVEN_CODE` |
| MFE → WS commercial-api | `plugins/commercial/src/constants/realtime.ts` + `CommercialRealtimeProvider.tsx` | `PROVEN_CODE` |
| Gateway → commercial-api | `gateway/nginx.conf` / `nginx.dev.conf` `location ^~ /apps/commercial-api/` | `PROVEN_CONFIG` |
| commercial-api → Postgres | Compose `PLUGINS_DB_*`; migrations `commercial-api/migrations/V001…V022` | `PROVEN_CONFIG` + `PROVEN_CODE` |
| commercial-api → api-delpi | `DelpiCommercialGateway` + Compose `DELPI_API_URL=http://delpi-api-delpi:8000` | `PROVEN_CODE` + `PROVEN_CONFIG` |
| commercial-api → core-api | `CoreApiPortalAccessPort`, `CommercialPortalNotificationService`; Compose `CORE_API_BASE_URL`, `CORE_API_INTEGRATIONS_SERVICE_TOKEN` | `PROVEN_CODE` + `PROVEN_CONFIG` |
| Scheduler | `main.py` lifespan → `start_integration_jobs_scheduler`; flag `COMMERCIAL_INTEGRATION_JOBS_SCHEDULER_ENABLED` | `PROVEN_CODE` + `PROVEN_CONFIG` |
| Realtime | `realtime_routes` WS `/commercial/realtime/ws`; hub no lifespan | `PROVEN_CODE` |
| MFE **não** chama api-delpi direto | gate `plugins/commercial/src/api/noDirectApiDelpi.test.mjs` + grep estrutural | `PROVEN_TEST_EXISTENCE` + `PROVEN_CODE` (padrão nos clients) |

**Não comprovado por este inventário:** SHA implantado, migrations aplicadas em produção, tokens reais, uso por usuários (`RUNTIME_REQUIRED`).

---

## 4. Inventário de telas e rotas (MFE)

**Bootstrap:** `bootstrap.tsx` → `App.tsx` → `resolvePluginRoute` (`pluginRoutes.ts`) — path-based próprio (sem React Router).  
**Manifest:** `commercial.manifest.json` v`0.4.0`.  
**Nav shell:** `content/shellNav.ts` (filtrada por capabilities) — distinta do menu Portal (`showInMenu` só na raiz).

| Área | Rota (relativa a `/apps/commercial`) | View/página | Permissão (manifest / gate MFE) | Dados principais | APIs consumidas | Tipo rota | Evidência |
|------|--------------------------------------|------------|----------------------------------|------------------|-----------------|-----------|-----------|
| Início | `` | `HomePage` | `commercial.access` | favoritos, atalhos, métricas hero | `homeFavoritesApi`, `openOrdersApi` | manifest | `PROVEN_CODE` |
| Visão geral | `overview` | `OverviewPage` | access + `canViewAnalytics` | KPIs ROL/OTD/carteira/IDD | `analyticsApi` | manifest | `PROVEN_CODE` |
| Visão geral | `analytics` | `OverviewPage` | idem | idem | idem | alias legado | `PROVEN_CODE` |
| Visão geral | `gestao` | `OverviewPage` | idem | idem | idem | alias legado PT | `PROVEN_CODE` |
| Minhas tarefas | `my-tasks` | `MyDayPage` | access + `canViewWorklist` | worklist/tasks | `worklistApi`, `attachmentsApi`, groups/portfolio | manifest | `PROVEN_CODE` |
| Minhas tarefas | `my-day` | `MyDayPage` | idem | idem | idem | alias (manifest + SPA) | `PROVEN_CODE` |
| Meus pedidos | `open-orders` | `OpenOrdersPage` | access | pedidos abertos / kanban | `openOrdersTotvsApi` via BFF | manifest | `PROVEN_CODE` |
| Detalhe linha | `open-orders/:branch/:order/:line` | `OpenOrderLineDetailPage` | (SPA; access app) | linha pedido | open-orders BFF | SPA internal | `PROVEN_CODE` |
| Detalhe OP | `…/op/:productionOrder` | `OpenOrderOpDetailPage` | SPA | OP | open-orders / production BFF | SPA internal | `PROVEN_CODE` |
| Sala interação | `interaction-rooms` | `InteractionRoomWorkspace` | access (sem gate extra em App) | inbox/salas | `interactionRoomsApi` | manifest | `PROVEN_CODE` |
| Sala detalhe | `interaction-rooms/:roomId` | `InteractionRoomWorkspace` | SPA | thread | `interactionRoomsApi` | SPA internal | `PROVEN_CODE` |
| Minha Carteira | `customers` | `CustomersPage` | access + `canAccessMyPortfolio` | clientes in-scope | `customersInScopeApi`, enrichment, analytics | manifest | `PROVEN_CODE` |
| Conta 360 | `customers/:codigo/:loja` | `CustomerDetailPage` | SPA; **sem** exigir portfolio gate | conta, pedidos, billing, contatos, opp | portfolio/open-orders/billing/contacts/audit/worklist/analytics | SPA internal | `PROVEN_CODE` |
| Pedido da Conta | `customers/…/orders/:branch/:order` | `CustomerOrderDetailPage` | SPA | pedido na conta | BFF open-orders conta | SPA internal | `PROVEN_CODE` |
| NF da Conta | `…/outbound-invoices/:branch/:number/:series` | `CustomerInvoiceDetailPage` | SPA | NF saída | `customerBillingApi` | SPA internal | `PROVEN_CODE` |
| Propostas (ADY) | `proposals` | `ProposalsPage` | access + `canViewProposals` | propostas documento | `commercialProposalsApi` | manifest | `PROVEN_CODE` |
| Detalhe proposta | `proposals/:id` | `ProposalDetailPage` | gate proposals | detalhe/PDF | proposals + contacts | SPA internal | `PROVEN_CODE` |
| Propostas | `propostas`, `propostas/:id` | mesmas | — | — | — | alias legado PT | `PROVEN_CODE` |
| OTD | `analytics/otd` | `AnalyticsOtdPage` | access + analytics gate | painel OTD | `analyticsApi` OTD | manifest | `PROVEN_CODE` |
| Detalhe OTD | `analytics/otd/:b/:o/:l` | `AnalyticsOtdLineDetailPage` | SPA + gate | linha OTD | OTD line detail | SPA internal | `PROVEN_CODE` |
| OTD | `gestao/otd…` | mesmas | — | — | — | alias legado PT | `PROVEN_CODE` |
| Oportunidades | `analytics/opportunities` | `AnalyticsOpportunitiesPage` | access + gate | OV/propostas analytics | `analyticsApi` proposals | manifest | `PROVEN_CODE` |
| Detalhe oportunidade | `analytics/opportunities/:n` | `AnalyticsOpportunityDetailPage` | SPA + gate | OV + produção | analytics + `productionExtrasApi` | SPA internal | `PROVEN_CODE` |
| Oportunidades | `gestao/oportunidades…` | mesmas | — | — | — | alias legado PT | `PROVEN_CODE` |
| Equipe (analytics) | `analytics/team` | `AnalyticsTeamRedirect` | manage | — | redirect → `administration` | manifest + **redirect** | `PROVEN_CODE` |
| Equipe | `gestao/equipe` | `AnalyticsTeamRedirect` | — | — | redirect | alias + redirect | `PROVEN_CODE` |
| Administração | `administration` | `AdministrationHomePage` | manage | hub admin | local | manifest | `PROVEN_CODE` |
| Carteiras | `administration/seller-portfolios` | `SellerPortfoliosPage` | manage | carteiras | `commercialPortfolioApi` | manifest | `PROVEN_CODE` |
| Carteiras | `seller-portfolios` | `SellerPortfoliosPage` | manage | idem | idem | alias (manifest + SPA) | `PROVEN_CODE` |
| Detalhe carteira | `…/seller-portfolios/:id` | `SellerPortfolioDetailPage` | manage | membros/clientes | portfolio API | SPA internal | `PROVEN_CODE` |
| Equipe admin | `administration/team` | `AdministrationTeamPage` | manage | roster | `administrationTeamApi`, groups, portfolio | manifest | `PROVEN_CODE` |
| Equipe | `administration/members` | `AdministrationTeamPage` | — | — | — | alias legado | `PROVEN_CODE` |
| Grupos | `administration/groups` | `AdministrationGroupsPage` | manage | grupos | `commercialGroupsApi` | manifest | `PROVEN_CODE` |
| SLAs | `administration/slas` | `AdministrationSlasPage` | manage | políticas SLA | `slaPoliciesApi` | manifest | `PROVEN_CODE` |
| Perfil | `users/:userId` | `UserProfilePage` | **fora do manifest** | perfil/foto | `meApi`, `userProfileApi` | SPA internal | `PROVEN_CODE` |
| Ajuda | `help` | `UserManualPage` | access | conteúdo local | local / catalogs | manifest | `PROVEN_CODE` |
| 404 | path inválido | `NotFoundPage` | — | — | — | SPA | `PROVEN_CODE` |

**Observação:** `AnalyticsTeamPage.tsx` existe no disco mas o router usa apenas `AnalyticsTeamRedirect` (`PROVEN_CODE` — página residual).

---

## 5. Inventário de APIs do `commercial-api` (routers reais)

**Fonte de verdade:** `commercial_app/main.py` + `interface/http/routes/*` (não `API-ROUTES.md`).  
**RBAC canônico:** `commercial.access` / `commercial.manage` / `commercial.billing.notify` em `commercial_permissions.py`.  
**Superadmin:** `is_superadmin` bypass em `has_any_permission`.  
Paths relativos ao app FastAPI (gateway prefixa `/apps/commercial-api`).

### 5.1 Health / ready

| Method | Path | Router | Handler | Permissão | Escopo | Owner dado | Repo/gateway | Write? | Auditado? | Status |
|--------|------|--------|---------|-----------|--------|------------|--------------|--------|-----------|--------|
| GET | `/health` | `main.py` | `health` | public | n/a | — | — | N | N | `PROVEN_CODE` |
| GET | `/ready` | `main.py` | `ready` | public | n/a | migrations | PluginBaseRepository | N | N | `PROVEN_CODE` |

### 5.2 Seller portfolios (`seller_portfolio_routes.py`)

Owner: Postgres `commercial.seller_*` (+ portal access Core). UC: `ManageSellerPortfolioUseCase`.

| Method | Path | Handler | Permissão | Escopo | Write? | Auditado? |
|--------|------|---------|-----------|--------|--------|-----------|
| GET | `/seller-portfolios/me` | `get_my_seller_portfolio` | access | membership self | N | N |
| GET | `/seller-portfolios/coverage-audit` | `get_seller_portfolios_coverage_audit` | manage | unrestricted | N | N |
| POST | `/seller-portfolios/customer-coverage` | `lookup_…` | access | membership | N | N |
| GET | `/seller-portfolios/load-summary` | `get_…_load_summary` | manage | unrestricted + Delpi metrics | N | N |
| GET | `/seller-portfolios` | `list_seller_portfolios` | manage | unrestricted | N | N |
| POST | `/seller-portfolios` | `create_seller_portfolio` | manage | portal_access | Y | Y |
| GET | `/seller-portfolios/{id}` | `get_seller_portfolio` | access | membership/manage | N | N |
| GET | `/seller-portfolios/{id}/audit` | `list_seller_portfolio_audit` | access | membership/manage | N | N (lê) |
| PATCH | `/seller-portfolios/{id}` | `update_seller_portfolio` | manage | manage | Y | Y |
| DELETE | `/seller-portfolios/{id}` | `deactivate_seller_portfolio` | manage | manage | Y | Y |
| DELETE | `/seller-portfolios/{id}/permanent` | `purge_seller_portfolio` | manage | manage | Y | Y |
| PUT/POST/DELETE | `…/customers*` | replace/add/remove | manage | manage | Y | Y |
| PUT/POST/DELETE | `…/members*` | replace/add/remove | manage | portal_access / manage | Y | Y |
| POST | `…/owner` | `set_seller_portfolio_owner` | manage | portal_access | Y | Y |
| POST | `/seller-portfolios/transfer` | `transfer_seller_customers` | manage | manage | Y | Y |
| POST | `/seller-portfolios/transfer-customers-bulk` | `transfer_seller_customers_bulk` | manage | manage | Y | Y |

### 5.3 Customers (`customer_routes.py`)

| Method | Path | Handler | Permissão | Escopo | Owner | Write? | Auditado? |
|--------|------|---------|-----------|--------|-------|--------|-----------|
| GET | `/customers/search` | `search_active_customers` | access\|manage | n/a | api-delpi | N | N |
| GET | `/customers/in-scope` | `list_customers_in_scope` | access\|manage | membership | commercial + Delpi metrics | N | N |
| POST | `/customers/enrichment` | `enrich_portfolio_customers` | access\|manage | membership filter | api-delpi | N* | N |
| POST | `/customers/billing-series` | billing series | access\|manage | membership / multi-pair | api-delpi | N | N |
| GET | `…/outbound-invoices` (+ detalhe) | list/get NF | access\|manage | account-pair | api-delpi | N | N |
| GET | `…/open-orders` | open orders conta | access\|manage | account-pair | api-delpi | N | N |
| GET | `…/contacts-bundle` | contacts bundle | access\|manage | account-pair | Postgres + Delpi SA1 | N | N |
| GET | `…/audit` | account audit | access | account | audit_log | N | N |
| POST/PATCH/DELETE | `…/contacts*` | CUD contacts | access\|manage | account | Postgres | Y | Y |
| GET/PUT/DELETE | `…/avatar` | avatar | access | account | Postgres + volume | Y (PUT/DEL) | Y (writes) |

\*POST enrichment = proxy read-ish para api-delpi (sem write local canônico).

### 5.4 Open orders (`open_orders_routes.py`)

| Method | Path | Handler | Permissão | Escopo | Gateway | Write? | Auditado? |
|--------|------|---------|-----------|--------|---------|--------|-----------|
| GET | `/open-orders/` | list | access\|manage | membership filter | Delpi + kanban enrich | N | N |
| GET | `/open-orders/recently-closed` | recently closed | access\|manage | membership | Delpi | N | N |
| GET | `/open-orders/ops-abertas` | ops abertas | access\|manage | membership | Delpi | N | N |

### 5.5 Analytics (`analytics_routes.py`) — BFF → api-delpi `/commercial/*`, `/dashboard/*`

Todos **read**; permissão típica `access` (exceto `portfolio-billing-share` → **manage**). Escopo via `resolve_analytics_portfolio_scope`.

Endpoints comprovados:  
`/analytics/portfolio-billing-share`, `portfolio-billing-ranking`, `open-portfolio-summary`, `open-portfolio-horizon`, `rol/summary`, `weg-rol-target-pct`, `new-business-rol-target-pct`, `department-idd`, `department-indicators`, `closing-rate`, `closing-rate/series`, `sales-order-otd`, `new-business-rol-pct`, `rol/series`, `rol/by-product`, `rol/by-customer`, `proposals`, `opportunity-collaborator-summary`, `proposals/{n}`, `proposals/{n}/history/events`, `sales-order-otd/panel`, `sales-order-otd/series`, `sales-order-otd/lines/{branch}/{order}/{line}`.

### 5.6 Proposal documents / Production BFF

| Method | Path | Permissão | Destino | Write? |
|--------|------|-----------|---------|--------|
| GET | `/proposal-documents/` | access | api-delpi commercial-proposals | N |
| GET | `/proposal-documents/{id}` | access | idem | N |
| GET/POST | `/proposal-documents/{id}/pdf` | access | idem (POST gera PDF) | N* |
| GET | `/production/orders/by-op/{op}` | access | api-delpi production | N |
| GET | `/production/appointments/by-op` | access | api-delpi | N |
| GET | `/products/{code}/factory-status` | access | api-delpi | N |
| GET | `/products/{code}/structure` | access | api-delpi | N |

### 5.7 Worklist / tasks / activities / favorites / SLA / attachments / profiles / groups / admin / jobs

| Área | Paths principais | Permissão | Persistência | Write? | Auditado? |
|------|------------------|-----------|--------------|--------|-----------|
| Worklist | `GET /me/worklist`, `/me/worklist/done` | access (+ team se manage) | tasks | N | N |
| Tasks | `GET/POST /tasks`, `PATCH/DELETE /tasks/{id}`, complete/defer/reassign | access + ACL tarefa | Postgres tasks* | Y | N |
| Activities | `POST/GET /activities` | access | activities | Y/N | N |
| Favorites | `GET/PUT /me/home-favorites` | access self | home_favorites | Y | N |
| SLA | `GET/POST/PATCH/DELETE /settings/sla-policies` | GET access; writes manage | sla_policies | Y | N |
| Attachments | `/attachments*` | access | attachments + volume | Y | N |
| User profile | `/users/{id}/profile*` | access (self writes) | commercial_user_profiles + Core mirror | Y | N |
| Groups | `/groups*` | manage | commercial_groups* | Y | Y (writes) |
| Admin | `GET /administration/team-roster` | manage | Core directory + local | N | N |
| Jobs | `POST /integrations/jobs/ready-to-invoice-scan`, `task-due-scan` | manage | outbox → Core notify | Y | N |

### 5.8 Interaction rooms + Realtime

| Method | Path | Permissão | Write? | Auditado? |
|--------|------|-----------|--------|-----------|
| CRUD salas/membros/mensagens/reações/pins/shared/tasks-from-message | `/interaction-rooms*` | `commercial.access` (+ ACL room) | misto | soft-delete/rename/members Y |
| WEBSOCKET | `/commercial/realtime/ws` | JWT + `commercial.access` no handler | fan-out N | N |

**Status agregado APIs:** inventário dos routers registrados em `main.py` = `PROVEN_CODE`. Paridade linha-a-linha com `API-ROUTES.md` = `TO_INVENTORY` (diff documental completo não fechado nesta fase).

---

## 6. Dados e modelo persistente

### 6.1 Tabelas comprovadas por migrations (schema `commercial`)

| Entidade/tabela | Migration(s) | Repository (quando identificado) | Owner | Fonte canônica | Relações principais | Runtime? |
|-----------------|--------------|----------------------------------|-------|----------------|---------------------|----------|
| `seller_portfolios` | V001, V005, V013 | `PostgresSellerPortfolioRepository` | commercial-api | Postgres | members, customers | sim p/ contagens |
| `seller_customers` | V001 | idem | commercial-api | Postgres | → ref TOTVS code+store | sim |
| `seller_portfolio_members` | V005 | idem | commercial-api | Postgres | N:N user↔portfolio | sim |
| `audit_log` | V001 | `PostgresAuditLogRepository` | commercial-api | Postgres | portfolio/contacts/groups/… | sim |
| `customer_avatars` | V002 | `PostgresCustomerAvatarRepository` | commercial-api | Postgres + volume | code+store | sim |
| `tasks` | V003, V007, V012, V020, V022 | `PostgresTaskRepository` | commercial-api | Postgres | assignees, groups, message source | sim |
| `activities` | V003 | Task/activity repos | commercial-api | Postgres | customer refs | sim |
| `attachments` | V004, V019 | `PostgresAttachmentRepository` | commercial-api | Postgres + volume | owner_type | sim |
| `task_assignees` / `task_customers` | V007 | task repo | commercial-api | Postgres | tasks | sim |
| `task_assignee_groups` | V012 | task repo | commercial-api | Postgres | groups | sim |
| `home_favorites` | V006 | `PostgresHomeFavoritesRepository` | commercial-api | Postgres | user | sim |
| `commercial_user_profiles` | V008, V015 | `PostgresUserProfileRepository` | commercial-api (+ mirror Core) | Postgres + volume | user | sim |
| `account_contacts` | V009 | `PostgresAccountContactRepository` | commercial-api | Postgres | code+store | sim |
| `commercial_groups` / `commercial_group_members` | V010, V011 | `PostgresCommercialGroupRepository` | commercial-api | Postgres | members | sim |
| `integration_outbox` / `integration_checkpoints` | V014 | outbox/checkpoint repos | commercial-api | Postgres | jobs notify | sim |
| `sla_policies` | V017 | `PostgresSlaPolicyRepository` | commercial-api | Postgres | policies | sim |
| interaction rooms/members/messages/mentions/reactions/pins | V019, V021 | interaction repos | commercial-api | Postgres | rooms | sim |
| `forecast_declarations` | V016 create / **V018 drop** | — | — | **removida** | — | n/a |

### 6.2 Distinções obrigatórias

| Classe | Exemplos | Evidência |
|--------|----------|-----------|
| Persistidos pelo Comercial | carteiras, membership, tasks, salas, contatos, SLA, outbox, avatars metadados | migrations + repos `PROVEN_CODE` |
| Referências a TOTVS | `customer_code`+`customer_store`, order keys | campos nas tabelas; dados vivem no Protheus |
| Obtidos via api-delpi | open-orders, ROL, OTD, OV, NF, ADY PDF, production | `DelpiCommercialGateway` |
| Obtidos via core-api | directory lookup, person-profile, notifications | `CoreApiPortalAccessPort` / notify service |
| Arquivos/blob | avatars, attachments, user photos | volumes Compose + storage classes |
| Outbox/checkpoints | ready_to_invoice, task due | V014 + jobs |
| **Futuro em DATA-MODEL (não migrado como entidade viva)** | opportunities CRM nativas, forecast cycles, samples, order confirmations, reference_* | `DATA-MODEL.md` diagrama M3–M5 = `PLANNED` |

Legado opcional: `COMMERCIAL_PORTFOLIO_SOURCE=legacy` lê schema PVA (`LegacyPostgres*`) — Compose default **`commercial`** (`PROVEN_CONFIG`).

---

## 7. Integrações

| Origem | Destino | Contrato | Direção | Autenticação | Finalidade | R/W | Fallback | Evidência |
|--------|---------|----------|---------|--------------|------------|-----|----------|-----------|
| MFE commercial | commercial-api | REST `/apps/commercial-api/*` | sync | Bearer user JWT + `X-Delpi-Caller-App: commercial` | UX | R/W | — | `httpClient.ts` |
| MFE commercial | core-api | `GET /core-api/me`, directory | sync | Bearer | perfil/RBAC raw / directory | R | — | `meApi.ts`, portfolio directory |
| MFE commercial | commercial-api WS | `/commercial/realtime/ws` | realtime | JWT query `token` | fan-out eventos | R | reconnect client | realtime provider |
| commercial-api | api-delpi | paths pedidos/commercial/proposals/production/products/dashboard | sync HTTP | Bearer + `X-Delpi-Caller-App: commercial-api` | TOTVS read (+ PDF gen) | R (+POST pdf) | — | `delpi_commercial_gateway.py` |
| commercial-api | core-api directory | lookup/search/person-profiles | sync S2S | Bearer service token | portal access / roster / mentions | R | **Permissive** se não configured | `core_api_portal_access.py` |
| commercial-api | core-api person-profile | PATCH/PUT/DELETE `/me/person-profile*` | sync | JWT usuário | espelho perfil | W | exige CORE_API_BASE_URL | idem |
| commercial-api | core-api notifications | `POST /integrations/notifications` | sync (via outbox publish) | S2S token | notif faturamento/tarefas | W | — | `commercial_portal_notification_service.py` |
| commercial-api | Postgres plugins | schema `commercial` | sync | DB creds | estado Delpi | R/W | — | Compose + repos |
| commercial-api | filesystem volumes | avatar/attachment/user dirs | sync | path local | blobs | R/W | — | Compose volumes |
| Scheduler | self use cases | ready_to_invoice + task_due scans | async loop | internal | enqueue outbox | W | flag disable | `integration_jobs_scheduler.py` |
| Gateway nginx | commercial-api:8000 | rewrite `/apps/commercial-api/` | proxy | — | roteamento | — | — | `gateway/nginx*.conf` |

### 7.1 `PermissivePortalAccessPort`

| Aspecto | Evidência | Status |
|---------|-----------|--------|
| Definição | `infrastructure/security/permissive_portal_access.py` — batch sempre `True` | `PROVEN_CODE` |
| Seleção | `build_portal_access_port()` em `commercial_composer.py`: se `CoreApiPortalAccessPort.configured()` (base_url **e** service_token) → Core; senão → Permissive | `PROVEN_CODE` |
| Fluxos via `build_portal_access_port()` | `ManageSellerPortfolioUseCase`, `ManageCommercialGroupsUseCase` (validação de acesso portal ao incluir membros/owner) | `PROVEN_CODE` |
| Fluxos Core **direto** (sem fallback Permissive no builder citado) | user profile / team roster / directory em mentions/inbox wiring | `PROVEN_CODE` |
| Compose | `CORE_API_BASE_URL` default `http://core-api:8000`; token `CORE_API_INTEGRATIONS_SERVICE_TOKEN` (fallback env `API_DELPI_INTERNAL_SERVICE_TOKEN`) | `PROVEN_CONFIG` |
| Produção usa Core ou Permissive? | **Não comprovável** só com GitHub | `RUNTIME_REQUIRED` |

Não classificado como vulnerabilidade neste inventário (falta evidência de runtime).

---

## 8. Permissões e escopo

### 8.1 Codes canônicos (código + manifest)

| Código | Manifest | Backend | MFE capabilities | Escopo concedido |
|--------|----------|---------|------------------|------------------|
| `commercial.access` | sim | produto / salas / BFF reads / worklist | `capabilities.access` | uso do Portal; membership filtra carteira quando aplicável |
| `commercial.manage` | sim | admin CRUD, team scope, share ranking consolidado, jobs | `capabilities.manage` / `is_admin` | irrestrito + Administração |
| `commercial.billing.notify` | sim | audiência notificação ready_to_invoice | `capabilities.billing_notify` | **não** libera telas; filtra toast WS | 

Evidência: `commercial.manifest.json`, `commercial_permissions.py`, `PortfolioScopeContext.tsx`, `PERFIS-E-PERMISSOES.md` → `PROVEN_CODE` + `PROVEN_DOC`.

### 8.2 Separação rigorosa

| Camada | O que é | Onde |
|--------|---------|------|
| RBAC | 3 codes (+ `is_superadmin`) | JWT/RBAC Core carregado no middleware |
| Membership carteira | `seller_portfolio_members` | `ResolveCommercialCustomerScopeService` |
| Grupos operacionais | `commercial_groups` | admin + assignees de tarefa; **≠** RBAC |
| Diretório/Core | lookup `has_app_access` app=`commercial` | `CoreApiPortalAccessPort` |
| Conta fora da carteira | deep-link Conta sem `ensure_allows` membership | documentado em `SCOPE-OWNERSHIP.md` + rotas customer |

### 8.3 Legado residual (busca)

| Achado | Onde | Classificação |
|--------|------|---------------|
| Nomes `commercial.seller-portfolios.manage`, `commercial.accounts.team.view` | `SCOPE-OWNERSHIP.md` tabela semântica | `PROVEN_DOC` **desalinhado** do catálogo de 3 codes |
| Helpers `can_view_accounts_team` etc. | `commercial_permissions.py` — **aliases de função** mapeados para `manage`/`access`, sem codes string legados | `PROVEN_CODE` |
| Doc proíbe dual-read de codes antigos | `PERFIS-E-PERMISSOES.md` | `PROVEN_DOC` |
| `INVENTARIO-ATIVOS.md` ainda cita `commercial.accounts.view` / `seller-portfolios.manage` | doc ativos | **conflito doc×código** (§ 13) |
| Strings legadas em docs comerciais (atas/KPI/etc.) | vários md | `PROVEN_DOC` histórico; não prova RBAC runtime |

Busca residual **não** prova ausência global de codes legados em Core/produção (`RUNTIME_REQUIRED`).

---

## 9. Funcionalidades existentes (comprovadas)

| Capacidade | Frontend | Backend | Persistência | Integrações | Permissão | Evidência |
|------------|----------|---------|--------------|-------------|-----------|-----------|
| Carteiras | admin + detalhe | seller-portfolio routes | seller_* | Core portal access; Delpi metrics | manage (CRUD); access (me) | `PROVEN_CODE` |
| Membership | UI membros | members endpoints | seller_portfolio_members | Core access check | manage | `PROVEN_CODE` |
| Clientes / Minha Carteira | CustomersPage | in-scope + enrichment | refs + metrics | api-delpi | access + membership | `PROVEN_CODE` |
| Conta 360 | CustomerDetailPage | customers/* account | contacts/avatar/audit | api-delpi | access | `PROVEN_CODE` |
| Pedidos | OpenOrders* | open-orders BFF | — | api-delpi | access + scope | `PROVEN_CODE` |
| Produção | OP detail / extras | production BFF | — | api-delpi | access | `PROVEN_CODE` |
| Faturamento/NF | Conta billing | outbound-invoices + series | — | api-delpi | access | `PROVEN_CODE` |
| Analytics / Overview | OverviewPage | `/analytics/*` | — | api-delpi (+ SI via dashboard paths) | access; share=manage | `PROVEN_CODE` |
| OTD | AnalyticsOtd* | OTD endpoints | — | api-delpi | access | `PROVEN_CODE` |
| Oportunidades (OV) | AnalyticsOpportunities* | analytics proposals | — | api-delpi | access | `PROVEN_CODE` |
| Propostas ADY | Proposals* | proposal-documents | — | api-delpi | access | `PROVEN_CODE` |
| Tarefas/worklist | MyDayPage | worklist/tasks | tasks* | notif Core | access | `PROVEN_CODE` |
| Atividades | Conta | `/activities` | activities | — | access | `PROVEN_CODE` |
| Contatos | Conta | contacts CUD | account_contacts | Delpi SA1 read | access | `PROVEN_CODE` |
| Anexos | tasks/UI | attachments | attachments + volume | — | access | `PROVEN_CODE` |
| Grupos | Admin groups | `/groups*` | commercial_groups | Core access | manage | `PROVEN_CODE` |
| SLAs | Admin slas | `/settings/sla-policies` | sla_policies | — | manage writes | `PROVEN_CODE` (consumo operacional banner = backlog parcial) |
| Perfis | UserProfilePage | user profile routes | commercial_user_profiles | Core mirror | access | `PROVEN_CODE` |
| Sala interação | InteractionRoomWorkspace | interaction-rooms | V019+ | realtime | access | `PROVEN_CODE` |
| Notificações | toast WS + Core prefs | outbox + jobs | outbox | Core notifications | billing.notify / envolvidos tasks | `PROVEN_CODE` |
| Auditoria | Conta/carteira | audit endpoints | audit_log | — | access | `PROVEN_CODE` |
| Realtime | CommercialRealtimeProvider | WS hub | — | — | access | `PROVEN_CODE` |
| Forecast nativo | — | — | tabela dropada V018 | — | — | **não** (removido) |
| GR TV / GAV N1 no MFE | — | — | — | tv-dashboard | — | `OUT_OF_SCOPE` / backlog |

**Existência ≠ adoção** (`RUNTIME_REQUIRED` para uso real).

---

## 10. Processos suportados pelo software (técnicos)

> Estes são fluxos que o **código consegue** executar. **Não** são o processo humano real do Comercial.

| Processo técnico | Gatilho técnico conhecido | Telas | APIs | Dados | Resultado técnico | O que NÃO sabemos (humano) |
|------------------|---------------------------|-------|------|-------|-------------------|----------------------------|
| Gerenciar carteira | Admin manage + CRUD HTTP | Carteiras / detalhe | `/seller-portfolios*` | seller_* | carteira/membros/clientes persistidos | quem decide composição; frequência |
| Consultar contexto cliente | deep-link Conta | Conta 360 | customers/* + analytics | mix Delpi+TOTVS | tela composta | ritual pré-reunião real |
| Acompanhar pedido | nav Meus pedidos / Conta | open-orders + detalhes | open-orders BFF | TOTVS | lista/kanban/detalhe | handoffs Apoio/PCP |
| Consultar produção vinculada | detalhe OP / opp | OP / opportunity | production BFF | TOTVS | status fábrica | processo chão de fábrica |
| Consultar faturamento | Conta NF / billing series | Conta | billing/NF BFF | TOTVS | séries/NF | processo financeiro |
| Consultar oportunidades/OV | Oportunidades | analytics opp | analytics proposals | TOTVS | lista/detalhe | funil CRM real SIGATEC |
| Consultar proposta ADY | Propostas | proposals | proposal-documents | TOTVS | PDF/detalhe | ciclo comercial ADY |
| Criar/concluir tarefa | My day / Conta / sala | my-tasks | tasks* | Postgres | task state + notif | priorização humana |
| Colaborar em sala | inbox/thread | interaction-rooms | rooms/messages + WS | Postgres | mensagens/pins | adoção vs Teams/WhatsApp |
| Administrar equipe/grupos/SLA | Admin | team/groups/slas | admin/groups/settings | Postgres + Core | roster/policies | quem opera no dia a dia |
| Receber notificação faturamento | job/scheduler/outbox | toast + Core | jobs + Core notify | outbox | notificação despachada | destinatários reais ativos |

---

## 11. Backlog conhecido (documental)

Fonte canônica: [PARCIAL-INVENTARIO.md](./PARCIAL-INVENTARIO.md). Consolidação resumida (não reimplementar):

| ID | Tema | Status documentado | Fonte | Evidência de código? | Observação |
|----|------|--------------------|-------|----------------------|------------|
| P-CART-ROL | Soma ROL+carteira | BLOCKED | PARCIAL | UI única proibida | gate ficha |
| P-OFF-SLA | SLA operacional consumo | PARTIAL | PARCIAL | CRUD SLA **Existe**; banner/alertas consumo **não** inventariado como completo | |
| P-OFF-AGG / AGE / FU / FILT-ADV | Ofertas avançadas | BACKLOG | PARCIAL | parcial/ausente | W2 |
| P-CLI-ATIVO / CLASS | KPI cliente ativo | BLOCKED | PARCIAL | — | ficha |
| P-SEG | Segmentação | BACKLOG | PARCIAL | — | ADR |
| P-CLI-FILT | Filtros família/grupo | PARTIAL | PARCIAL | parcial Conta Opp | |
| P-PLACE-DATE / LEAD / CYCLE | Datas ciclo CRM | BACKLOG CRM | PARCIAL | dado não homologado | |
| P-OTD-FLOW / VAR / CAUSE / MARCOS / FNE / FAT-EMB / PRAZO | OTD avançado | BACKLOG | PARCIAL | OTD base Existe | W4 |
| P-GAV-N1 / RANK-BI / IA / VIS-INT | GAV/home gerencial | BACKLOG | PARCIAL | overview base Existe | W5 |
| P-GR-TV | GR no MFE commercial | BLOCKED / OUT_OF_SCOPE | PARCIAL · GAV-TV | — | TV Dashboard |
| P-CAP-PCP | Cockpit PCP | BLOCKED | PARCIAL | — | Produção |
| P-HOME-PERS | Home orçamentista/faturamento | DELIVERED (doc) | PARCIAL | atalhos Home | validar papéis runtime |
| P-NOTIF / P-SALA | Notif + sala | DELIVERED (doc) | PARCIAL | código Existe | adoção `RUNTIME_REQUIRED` |
| H-YOY | Preferência visual YoY | HOMOLOG | PARCIAL | overlay Existe | |
| D-HIT | Hit rate ficha | DELIVERED DOC / homolog regra | PARCIAL · KPI-FICHAS | — | `em_validacao` |
| E7 UX (mapa/AI/inbox e-mail) | BACKLOG | UX-E-TASKS | — | futuro |
| P3 reminder tarefas | BACKLOG | UX-E-TASKS | — | |

Itens W0 marcados **Existe** no PARCIAL foram tratados como entregues documentais; revalidação completa item-a-item contra código = parcialmente coberta por esta Fase 1 (features § 9), restante `TO_INVENTORY` se auditoria pontual for exigida.

---

## 12. Testes

| Área | Arquivos | Tipo | Contrato protegido (amostra) |
|------|----------|------|------------------------------|
| commercial-api | **97** `tests/test_*.py` | unit/API (existência) | RBAC, BFF, portfolios, rooms, outbox, SLA, realtime, … |
| plugins/commercial `src/` | **197** `*.test.*` / `*.spec.*` | vitest/node structural | noDirectApiDelpi, rotas, RBAC gates, rooms, deep links, … |

| Campo | Valor |
|-------|-------|
| Classificação | `PROVEN_TEST_EXISTENCE` |
| Execução nesta fase | **EXECUTION_NOT_PERFORMED** |
| Motivo | inventário estático; evitar risco a serviços externos; working tree suja alheia |

---

## 13. Conflitos documentação × código

| # | Documentação | Código | Classificação |
|---|--------------|--------|---------------|
| C1 | `SCOPE-OWNERSHIP.md` lista `commercial.seller-portfolios.manage` e `commercial.accounts.team.view` como se fossem codes | Catálogo real = 3 codes; helpers mapeiam team/manage → `commercial.manage` | **DRIFT** doc×código |
| C2 | `INVENTARIO-ATIVOS.md` cita `commercial.accounts.view` / `seller-portfolios.manage` | Manifest/API usam `access`/`manage`/`billing.notify` | **DRIFT** |
| C3 | `DATA-MODEL.md` diagrama inclui opportunities/forecast/samples como modelo | Migrations M3+ não criam essas tabelas; forecast dropada V018 | Doc = mix estado + **PLANNED** |
| C4 | `DATA-MODEL.md` header “M1 aplicado… M2 parcial” incompleto vs V004–V022 | Migrations V001–V022 presentes | Doc **atrasado** vs código |
| C5 | `INVENTARIO-ATIVOS` telas resumidas (“Home, open-orders…”) | MFE tem overview, tasks, rooms, proposals, admin, OTD, opp, help, perfil | Doc **incompleto** |
| C6 | `API-ROUTES.md` catálogo extenso | Routers reais em `interface/http/routes` | Possível drift de cobertura — paridade total `TO_INVENTORY` |
| C7 | `PERFIS-E-PERMISSOES` alinhado aos 3 codes | Código alinhado | **Sem conflito** neste eixo |

Conflitos registrados; **não** corrigidos nesta fase (exceto documentação de inventário que os declara).

---

## 14. TO_INVENTORY

### Fechados nesta Fase 1R (ver § 19)

- Paridade `API-ROUTES.md` ↔ handlers (com contagens e divergências)
- Inventário profundo `dashboard-commercial`
- Residuais api-delpi / PVA deprecated (consumidores no repo)
- Help coverage por tela vs `HELP-COVERAGE.md`
- Cadeia SI/IDD Overview (até strategic-indicators-api)

### Ainda abertos (técnicos menores / runtime)

- Confirmar se `AnalyticsTeamPage.tsx` residual é dead code total além do não-roteamento (`PROVEN_CODE` parcial)
- Variáveis env de produção efetivas (sem secrets) vs templates Compose — `RUNTIME_REQUIRED`
- Contagem/amostra de dados reais — `RUNTIME_REQUIRED`
- Uso real de `dashboard-commercial` e de rotas PVA sellers ainda registradas na api-delpi — `RUNTIME_REQUIRED`

---

## 15. Evidências externas necessárias

### Runtime/deploy

- SHA implantado (MFE commercial, commercial-api, api-delpi, core-api)
- Versões/containers em execução; health/readiness reais
- Migrations aplicadas no Postgres plugins
- OpenAPI/runtime real; gateway efetivo
- Config real: `COMMERCIAL_PORTFOLIO_SOURCE`, scheduler enabled, `CORE_API_*` (sem secrets)
- Confirmar se `PermissivePortalAccessPort` está ativo ou não

### Usuários/permissões

- Usuários com app commercial (IDs pseudonimizados)
- Roles/codes efetivos; memberships; admins; destinatários `billing.notify`

### Uso real

- Acessos por tela; usuários ativos; tasks; salas/mensagens; notificações; uso por papel/unidade/filial

### Dados reais

- Qtd carteiras/clientes/cobertura membership; tasks/grupos/salas/contatos; erros integração; frescor TOTVS; amostras reconciliadas

### Processo comercial real

Entrevistar/observar: vendedor, apoio, orçamentista, faturamento, gestão (e outros). Por processo: gatilho, entrada, atividade, decisão, handoff, espera, sistemas (Portal/TOTVS/planilha/WhatsApp/Teams/e-mail), resultado, medição. **Não selecionar filial silenciosamente.**

---

## 16. Residual search (esta fase)

| Busca | Resultado relevante | Limitação |
|-------|---------------------|-----------|
| `commercial.(access\|manage\|billing.notify)` em commercial-api | catálogo 3 codes + testes | não prova Core prod |
| `PermissivePortalAccessPort` | composer fallback | runtime `configured()` desconhecido |
| `api-delpi` / `API_DELPI` em `plugins/commercial/src` | apenas comentários/testes estruturais proibitivos | grep ≠ prova dinâmica |
| Codes legados em docs commercial | vários docs históricos + SCOPE/INVENTARIO-ATIVOS | docs ≠ RBAC vivo |
| `docker-compose` commercial/commercial-api | services + env + volumes | config possível |
| gateway `commercial-api` | nginx location + WS headers | não prova deploy |
| migrations `V*.sql` | 22 arquivos V001–V022 | não prova DB prod |

**Limitação geral:** busca zero ≠ ausência; runtime e Core RBAC fora do GitHub.

---

## 17. Owners e fronteiras (preservadas nesta análise)

| Superfície | Owner tratado | Evidência de consumo |
|------------|---------------|----------------------|
| `plugins/commercial` | experiência web / MFE | manifest + pages + clients |
| `commercial-api` | regras/escopo/estado/composição Comercial | routers + UCs + repos |
| `api-delpi` | integração/dados DELPI/TOTVS | gateway Delpi nos BFFs |
| `core-api` | identidade/diretório/notif/perfil | meApi + CoreApiPortalAccess + notifications |
| Postgres `commercial` | estado persistente Comercial | migrations + repos |

Dependências atribuídas por consumidores reais (MFE→commercial-api→…), não por conveniência.

---

## 18. Invariantes desta Fase 1

Nenhuma melhoria proposta; nenhum código funcional alterado; backlog separado de Current State; hipóteses/runtime explicitamente marcados.

---

## 19. Residual técnico — fechamento Fase 1R

> **Execução:** 2026-09-14 · HEAD baseline pedido `47e4c595cd080660408dde160942d40cba57c3df`  
> **HEAD ao concluir análise:** `58c51651240044e00e99ecdea2dd24e16e2f8570` (commit externo TV Dashboard; diff scoped commercial/api-delpi/dashboard-commercial/docs commercial vs `47e4c595c` = **vazio**)  
> **Escopo:** R1–R5 inventário factual apenas · **sem** correção de código/docs contratuais históricos  
> **Método R1:** parse das tabelas §3 de `API-ROUTES.md` × rotas extraídas de `interface/http/routes/*.py` com `include_router` em `main.py` (cadeia handler→router→app). Health/ready incluídos de `main.py`.

### 19.1 R1 — API contracts (`API-ROUTES.md` × código)

**Resumo quantitativo (linhas de catálogo §3 + endpoints de código não casados):**

```text
DOC_AND_CODE:          36
CODE_ONLY:             60
DOC_ONLY:              96
DOC_DRIFT:             36
ROUTER_NOT_REGISTERED:  0
UNCERTAIN:              0  (nenhum caso marcado; ruído de parse absorvido em DOC_ONLY)
```

**Leitura dos números (não confundir com “faltam 96 features”):**

| Fatia | Qtd (aprox.) | Significado factual |
|-------|--------------|---------------------|
| `DOC_ONLY` fases futuras F6/F7/M5/prospects/forecast/samples/… | ~87 | Catálogo especifica fases **não** implementadas — esperado |
| `DOC_ONLY` residual / ruído de tabela | ~9 | Ex.: `/me/summary`, `GET /tasks/{id}`, transfer path legado `{seller_id}/customers/transfer`, células multi-método mal parseadas |
| `DOC_DRIFT` | 36 | Endpoint existe nos dois lados, mas **permissão documental legada** e/ou **nome de path param** diverge |
| `CODE_ONLY` | 60 | Implementado/registrado sem linha correspondente clara no catálogo §3 (muitos são BFF analytics, ADY, production, jobs, favorites, members/owner, contacts) |
| `ROUTER_NOT_REGISTERED` | 0 | Todos os routers de `routes/*.py` usados no extract estão no `include_router` de `main.py` |

**Permission drift (material, repetido):**

Doc §3 ainda cita codes históricos (`commercial.accounts.view`, `commercial.analytics.view`, `commercial.seller-portfolios.manage`, `commercial.worklist.view`, `commercial.followups.manage`, `commercial.home.view`, atalhos `accounts.view` / `analytics.view` / `manage`).  
Código canônico: apenas `commercial.access` / `commercial.manage` / `commercial.billing.notify` (`commercial_permissions.py`).  
→ classificado como **`DOC_DRIFT`** onde o path casa; **não** corrigido nesta fase.

**Path drift (amostra):**

| Doc | Código | Classe |
|-----|--------|--------|
| `/seller-portfolios/{seller_id}` | `/seller-portfolios/{portfolio_id}` | `DOC_DRIFT` |
| `/customers/{…}/{store}/…` | `/customers/{…}/{customer_store}/…` | `DOC_DRIFT` |
| `/tasks/{id}` | `/tasks/{task_id}` (e sem `GET` unitário no código) | `DOC_DRIFT` / `DOC_ONLY` |
| `/me/seller-portfolio` | alias real `/seller-portfolios/me` | `DOC_DRIFT` (alias documentado) |
| Transfer `…/{seller_id}/customers/transfer` | `POST /seller-portfolios/transfer` (+ bulk) | `DOC_ONLY` + `CODE_ONLY` |

**CODE_ONLY — categorias (código sem entrada §3 casada):**

| Categoria | Exemplos | Evidência |
|-----------|----------|-----------|
| Analytics BFF | `/analytics/rol/summary`, `department-idd`, OTD panel/series/lines, proposals OV… | `analytics_routes.py` + `main.include_router` |
| Proposal documents ADY | `/proposal-documents*` | `proposal_documents_routes.py` |
| Production BFF | `/production/*`, `/products/*/factory-status\|structure` | `production_bff_routes.py` |
| Jobs | `/integrations/jobs/ready-to-invoice-scan`, `task-due-scan` | `integration_jobs_routes.py` |
| Home favorites | `/me/home-favorites` | `home_favorites_routes.py` |
| Portfolios extras | `…/permanent`, `…/members`, `…/owner`, `transfer-customers-bulk`, `…/audit` | `seller_portfolio_routes.py` |
| Customers extras | `in-scope`, `search`, `contacts*`, `open-orders` por conta, `audit` | `customer_routes.py` |
| Realtime | `WEBSOCKET /commercial/realtime/ws` | `realtime_routes.py` (doc §3.21 menciona WS, sem linha de método dedicada no parse) |

**DOC_ONLY planejado (amostra — não implementar aqui):** `/opportunities*`, `/forecast*`, `/prospects*`, `/samples*`, `/visits*`, `/settings/pipelines|stages|reasons|segments…`, `/profitability*`, `/sequences*`, `/accounts` (lista F5), `/audit` global, `/data-quality*`.

**Arquivos analisados R1:**

- `docs/12-roadmap-e-evolucao/commercial/API-ROUTES.md`
- `commercial-api/commercial_app/main.py`
- `commercial-api/commercial_app/interface/http/routes/*.py` (18 módulos; todos os routers incluídos)
- `commercial-api/commercial_app/application/security/commercial_permissions.py`

### 19.2 R2 — dashboard-commercial

| Campo | Valor factual |
|-------|----------------|
| Classificação | **`LEGACY_BUT_REGISTERED`** |
| Pacote | `plugins/dashboard-commercial/` |
| Manifest | `id=dashboard-commercial`, `basePath=/apps/dashboard-commercial`, permission `dashboard-commercial.view`, **`showInMenu: true`** |
| Compose | `infra/docker-compose.yml` / `.dev.yml` service `dashboard-commercial` → `delpi-dashboard-commercial` |
| Gateway | sem location nominal; coberto por padrão `/apps/([^/]+)/assets/` → `delpi-$1` |
| Destino API | **api-delpi direto** (`/apps/api-delpi/commercial`, `/dashboard`, `/products`) — **não** chama `commercial-api` |
| Telas | Home KPIs; `/otd`; `/otd/pedido/{b}/{o}/{l}`; `/ov/{proposalNumber}` |
| Permissão MFE | só manifest; sem gate RBAC React adicional |
| Relação com `plugins/commercial` | irmão legado coexistente; **sem** redirect F2c; overlap funcional de KPIs/OTD/OV; Portal reutiliza **classe CSS** `dashboard-commercial` como scope (não o MFE) |
| Stubs client sem UI | `getNewClientsAverage`, `getNewClientsRolPct` definidos no client, sem hook/página |
| Runtime ainda necessário | uso real, quem tem `dashboard-commercial.view`, se menu é visto em prod |

### 19.3 R3 — api-delpi / PVA

**Consumido por commercial-api** (`DelpiCommercialGateway` — `CONSUMED_COMMERCIAL_API`):

| Contrato (path api-delpi) | Finalidade |
|---------------------------|------------|
| `GET …/totvs-open-orders` (+ por cliente) | Pedidos BFF |
| `GET …/totvs-recently-closed-orders` | Recently closed |
| `GET …/ops-abertas` | OPs |
| `GET …/customers/search` | Busca clientes |
| `POST …/customers/enrichment` | Enrichment |
| `POST …/customers/open-order-metrics` | Load-summary / in-scope metrics |
| `POST …/customers/billing-series` | Séries faturamento |
| `GET …/totvs-outbound-invoices/…` | NF Conta |
| `GET /commercial/*` (via `get_commercial_analytics`) | KPIs/OTD/OV BFF |
| `GET /dashboard/department-idd` / `department-indicators` | SI/IDD |
| `GET/POST /commercial-proposals*` | ADY |
| `GET /production*` / `/products*` | Production BFF |

**Consumido por dashboard-commercial** (`CONSUMED_DASHBOARD`): `/apps/api-delpi/commercial/*` (ROL, closing, OTD, proposals…), `/dashboard/department-*`, `/products/{code}/structure`.

**Consumido por outros no repo** (`CONSUMED_OTHER`):

| Consumidor | Path | Evidência |
|------------|------|-----------|
| `production-control-api` | `totvs-open-orders`, `ops-abertas` | docs/README production-control |
| `financial-api` | `/commercial/rol/by-branch` | `delpi_financial_gateway.py` |
| `shared/delpi_api_client` | `/commercial/new-clients-average` | client library |
| `minha-delpi-ai-api` | referências path em smoke/intent | testes/scripts |

**Legado documentado ainda no código api-delpi** (`LEGACY_DOCUMENTED` + handlers ainda presentes):

| Path | Status no repo |
|------|----------------|
| `/pedidos-venda-abertos/sellers*` (CRUD carteira) | Router ativo em `pedidos_venda_abertos_router.py`; **nenhum** consumidor em `commercial-api` / `plugins/commercial` / `dashboard-commercial` → também `NO_REPO_CONSUMER_FOUND` (MFE/BFF) |
| `/pedidos-venda-abertos/customers/{c}/{l}/avatar` | Idem — canônico em commercial-api |
| `GET …/clientes/{c}/{l}/notas-fiscais` | Doc `API-ROUTES` §4.1 diz “commercial-api BFF”; **gateway commercial usa `totvs-outbound-invoices`**, não este path → `NO_REPO_CONSUMER_FOUND` + drift documental |

**Prefixo propostas:** commercial-api consome `/commercial-proposals` (EN). Paths `/propostas-comerciais` permanecem no controller api-delpi (`LEGACY_DOCUMENTED` / possível alias — não rastreado como consumer do Portal).

**Não prova:** ausência de consumer no monorepo ≠ ausência de uso em produção.

### 19.4 R4 — Help coverage real

**Distinção:** `HELP-COVERAGE.md` mede gaps de **campo/coluna** (`hint`/`headerHint`) via auditor estrutural (snapshot: 0 gaps). Esta matriz mede **help por tela/área**.

| Cobertura | Telas/áreas (resumo) |
|-----------|----------------------|
| **COVERED** | Overview; Minhas tarefas; Meus pedidos (+ detalhe linha/OP); Conta 360; Propostas (+ detalhe); OTD lista; Oportunidades (+ detalhe); Carteiras admin (+ detalhe); Equipe admin; SLAs; Perfil; Manual `/help`; Shell nav |
| **PARTIAL** | Início (várias keys `CM_HELP.home.*` sem uso em `features/home`); Minha Carteira (literal `hint=` pontual); Pedido na Conta; Admin hub; Grupos; Sala (só panel, inbox/canvas sem `CM_HELP`) |
| **STALE** | — nenhum classificado com evidência forte de texto obsoleto nesta passagem |
| **NO_HELP_FOUND** | Detalhe linha OTD (`AnalyticsOtdLineDetailPage`); 404; redirect `analytics/team` (não é tela) |
| **UNCERTAIN** | NF na Conta (página sem `CM_HELP` direto; pode herdar billing) |

**Fontes:** `helpTooltips.ts` (`CM_HELP`), `userManualContent.ts`, `userManualTermCatalog.ts`, column helps, `HELP-COVERAGE.md`.  
**Não** foi escrito help novo.

### 19.5 R5 — SI / IDD

**Cadeia comprovada (Overview):**

```text
OverviewPage (DepartmentIddBadge + useDepartmentIndicatorScores)
  → GET /apps/commercial-api/analytics/department-idd
  → GET /apps/commercial-api/analytics/department-indicators
      → analytics_routes.bff_department_idd / bff_department_indicators
      → DelpiCommercialGateway.get_dashboard_department_*
      → api-delpi GET /dashboard/department-idd | /department-indicators
      → DashboardDepartment*Service
      → shared StrategicIndicatorsApiClient
      → strategic-indicators-api
           /strategic-indicators/integrations/dashboard-department-score
           /strategic-indicators/integrations/dashboard-department-indicators
      → GetDashboardDepartment*UseCase → StrategicIndicatorsSnapshotService
```

**Indicadores SI na Overview (scores por `indicator_id`):**  
IDs em `plugins/commercial/src/features/overview/siIndicatorIds.ts` — `commercial-rol`, `commercial-rol-weg`, `commercial-rol-new-business`, `commercial-sales-order-otd`, `commercial-closing-rate`, `commercial-new-business-rol-pct` + badge IDD (`department.score`).  
**Owner aparente do score:** `strategic-indicators-api`.  
**Valores dos KPIs numéricos da Overview** (R$, %, etc.) vêm de **outras** rotas `/analytics/*` (api-delpi `/commercial/*`), não do endpoint `department-indicators`.

**TO_INVENTORY_EXTERNAL:** detalhe SQL/TOTVS dentro de cada medição do snapshot SI além do hop `CommercialMetricsSnapshotService` / gateways SI→api-delpi (fora do escopo delimitado).

### 19.6 Evidências externas (permanecem abertas)

Inalteradas vs § 15: SHA implantado, migrations aplicadas, env prod, Permissive ativo?, users/roles reais, telemetria, processo humano, uso por filial, uso real do dashboard-commercial e das rotas PVA sellers.
