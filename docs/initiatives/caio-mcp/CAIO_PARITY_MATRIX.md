# CAIO 2.0 — Matriz de paridade Portal Comercial ↔ CAIO MCP

**Base:** `main = 361d09da96` · inventário de 133 operações HTTP da
`commercial-api` (16 famílias de rotas) + surface do Portal em
`plugins/commercial`. Deploy em produção verificado em
`delpi-commercial-api` (`361d09da9`).

**Regra de paridade:** paridade = operação de negócio elegível
acessível via uma das seis tools semânticas com o mesmo usuário,
escopo, dados e autorização. Tela, arquivo binário e canal de tempo
real não são operações elegíveis — classificação
`NOT_SEMANTICALLY_ELIGIBLE` (NSE) com justificativa.

## Resumo quantitativo

| Classe | N | Detalhe |
|---|---|---|
| Operações HTTP inventariadas | 133 | 16 route files + websocket |
| `NOT_SEMANTICALLY_ELIGIBLE` | 7 | binário/multipart/push/jobs |
| Elegíveis (denominador) | 126 | — |
| Implementadas via 6 tools (`PROVEN_CURRENT`) | 126 | 123 capabilities + knowledge topics + get_context |
| `BLOCKED_EXTERNAL` / `TO_IMPLEMENT` | 0 | — |

**PARITY_PERCENT = 126/126 = 100%** das operações elegíveis mapeadas
para a superfície semântica — com a ressalva honesta de que a prova é
por dispatch+contrato (use cases/gateways oficiais) e smoke de
produção; `tools/call` autenticada fim-a-fim aguarda registro do
client `mcp-commercial` no Keycloak (`TEST_NOT_RUN`).

## Operações implementadas por família (PROVEN_CURRENT)

### Carteiras — `seller_portfolio_routes` (19 ops)

| Route | CAIO |
|---|---|
| GET /seller-portfolios/me | `read portfolio.me` |
| GET /seller-portfolios/{id} | `read portfolio.get` |
| GET /seller-portfolios | `read portfolio.list` (manage/team) |
| GET .../{id}/audit | `read portfolio.audit` |
| GET /seller-portfolios/audit/coverage | `read portfolio.coverage_audit` |
| GET /seller-portfolios/load-summary | `read portfolio.load_summary` |
| POST /seller-portfolios/customer-coverage | `read portfolio.customer_coverage` |
| POST /seller-portfolios | `execute portfolio.create` |
| PATCH .../{id} | `execute portfolio.update` |
| PUT .../{id}/customers | `execute portfolio.customers_replace` |
| POST .../{id}/customers | `execute portfolio.customer_add` |
| DELETE .../{id}/customers/... | `execute portfolio.customer_remove` |
| PUT .../{id}/members | `execute portfolio.members_replace` |
| POST .../{id}/members | `execute portfolio.member_add` |
| DELETE .../{id}/members/... | `execute portfolio.member_remove` |
| PUT .../{id}/owner | `execute portfolio.owner_set` |
| POST .../transfer-customers | `execute portfolio.transfer` |
| POST .../transfer-customers-bulk | `execute portfolio.transfer_bulk` |
| DELETE .../{id} (deactivate) / purge | `delete portfolio.deactivate` / `portfolio.purge` |

### Clientes — `customer_routes` (10 ops)

| Route | CAIO |
|---|---|
| GET /customers/search | `read customer.search` |
| GET /customers/in-scope | `read customer.list` |
| POST /customers/enrichment | `read customer.enrichment` |
| POST /customers/billing-series | `read customer.billing_series` |
| GET /customers/center-assignments | `read customer.center_assignments` |
| GET .../outbound-invoices | `read customer.outbound_invoices` |
| GET .../outbound-invoices/{...} | `read customer.outbound_invoice` |
| GET .../open-orders | `read customer.open_orders` |
| GET .../contacts | `read customer.contacts` |
| GET .../account-audit | `read customer.account_audit` |
| POST/PATCH/DELETE .../contacts | `execute contact.create/update` + `delete contact.delete` |

### Pedidos — `open_orders_routes` (3 ops)

| Route | CAIO |
|---|---|
| GET /open-orders | `read open_order.list` |
| GET /open-orders/recently-closed | `read open_order.recently_closed` |
| GET /ops-abertas | `read open_order.open_ops` |

### Propostas — `proposal_documents_routes` + analytics (6 ops)

| Route | CAIO |
|---|---|
| GET /proposals (portal search) | `read proposal.list` |
| GET /proposals/{interna} | `read proposal.get` |
| GET /analytics/proposals | `read proposal.analytics_list` |
| GET /analytics/proposals/{num} | `read proposal.analytics_get` |
| GET /analytics/proposals/{num}/history/events | `read proposal.history_events` |
| GET proposal document/PDF (binário) | `NSE` — fluxo binário |

### Analytics — `analytics_routes` (21 ops)

| Route | CAIO |
|---|---|
| GET /analytics/customer-centers | `read customer_center.list` |
| GET /portfolio-billing-share | `analyze portfolio.billing_share` |
| GET /portfolio-billing-ranking | `analyze portfolio.billing_ranking` |
| GET /open-portfolio/summary | `analyze portfolio.open_summary` |
| GET /open-portfolio/horizon | `analyze portfolio.open_horizon` |
| GET /rol/summary | `analyze rol.summary` |
| GET /rol/series | `analyze rol.series` |
| GET /rol/by-product | `analyze rol.by_product` |
| GET /rol/by-customer | `analyze rol.by_customer` |
| GET /billing/by-customer-month | `analyze billing.by_customer_month` |
| GET /closing-rate | `analyze closing_rate.summary` |
| GET /closing-rate/series | `analyze closing_rate.series` |
| GET /sales-order-otd | `analyze sales_order_otd.summary` |
| GET /sales-order-otd/panel | `analyze sales_order_otd.panel` |
| GET /sales-order-otd/series | `analyze sales_order_otd.series` |
| GET /sales-order-otd/lines/{b}/{o}/{l} | `analyze sales_order_otd.line_detail` |
| GET /new-business-rol-pct | `analyze new_business.rol_pct` |
| GET /new-business-rol-target-pct | `analyze new_business.rol_target_pct` |
| GET /weg-rol-target-pct | `analyze weg.rol_target_pct` |
| GET /dashboard/department/{idd,indicators} | `analyze dashboard.department_idd` / `department_indicators` |
| GET /proposals/collaborator-summary | `analyze opportunity.collaborator_summary` |

### Worklist — `worklist_routes` (10 ops)

| Route | CAIO |
|---|---|
| GET /worklist | `read worklist.mine` |
| GET /worklist/completed | `read worklist.done` |
| GET /tasks | `read task.list` |
| POST /tasks | `execute task.create` |
| PATCH /tasks/{id} | `execute task.update` |
| POST /tasks/{id}/complete | `execute task.complete` |
| POST /tasks/{id}/defer | `execute task.defer` |
| POST /tasks/{id}/reassign | `execute task.reassign` |
| DELETE /tasks/{id} | `delete task.delete` |
| POST/GET activities | `execute activity.create` + `read activity.list` |

### Grupos — `group_routes` (7 ops)

`read group.list/get` · `execute group.create/rename/members_replace/
member_add/member_remove` · `delete group.delete` — manage-only.

### SLA — `settings_routes` (4 ops)

`read sla_policy.list` · `execute sla_policy.create/update` ·
`delete sla_policy.deactivate`.

### Home favorites — `home_favorites_routes` (2 ops)

`read home_favorite.list` · `execute home_favorite.put`.

### Administração — `administration_routes` (1 op)

`read team.roster` (manage).

### Anexos — `attachment_routes` (4 ops)

`read attachment.list` · `delete attachment.delete` · upload
(multipart) `NSE` · download (binário) `NSE`.

### Salas e mensagens — `interaction_room_routes` (18 ops)

`read interaction_room.list/get/members/messages/shared_items/pins/
mention_suggest/entity_preview` · `execute interaction_room.resolve/
rename/member_add/member_remove/mark_read` ·
`execute interaction_message.post/update/reaction_set/
reaction_clear/pin/unpin` · `execute task.from_message` ·
`delete interaction_room.delete` · `delete interaction_message.delete`.

### Produção BFF — `production_bff_routes` (4 ops)

`read production.order/appointments/product_status/product_structure`.

### Perfil de usuário — `user_profile_routes` (6 ops)

`read user_profile.get` · `execute user_profile.update` ·
`delete user_profile.photo_delete` · photo get/upload (binário/
multipart) `NSE`.

### NSE consolidadas (7)

| Operação | Motivo |
|---|---|
| GET /realtime/ws | canal push persistente — não é operação request/response |
| POST attachments upload | multipart binário |
| GET attachments download | stream binário |
| GET user photo | binário |
| POST user photo | multipart binário |
| GET proposal document (pdf) | binário |
| POST integration-jobs/scan (2) | jobs internos de sistema, não operações de usuário |

## Cobertura de conhecimento (E5)

`caio_commercial_knowledge.json` v2.0 — 16 tópicos ativos + 1 planned:
`caio.usage`, `caio.tool_map`, `commercial.glossary`,
`commercial.portfolio_governance`, `commercial.worklist_process`,
`commercial.interaction_rooms`, `commercial.indicators`,
`commercial.scope_semantics`, `commercial.permissions`,
`commercial.integrations`, `commercial.delete_governance`,
`commercial.honest_states`, `commercial.processes`,
`commercial.proposals`, `commercial.otd`, `commercial.production`.
Fonte canônica citada por tópico (rotas, use cases, helpers, docs).
`products.guide` permanece `planned` honesto.

## Modelo de confirmação vigente

- `read`/`analyze`/`knowledge`: execução imediata após AuthZ.
- `execute`: criações/atualizações autorizadas executam direto —
  gates de permissão do backend soberanos.
- `delete`: sempre `phase=prepare` → proposta selada (actor +
  capability + alvo + fingerprint + TTL + uso único, HMAC) →
  `phase=commit` revalidando tudo; `confirmed=true` do cliente nunca
  é prova.

## Correções transversais — Issue #123

| Falha reportada | Causa raiz (compartilhada) | Correção |
|---|---|---|
| 8 reads → 502 com `pagination` | `_filters` injetava `page`/`page_size` em todo handler; `TypeError` era mascarado como `upstream_error` | paginação só flui para capabilities que a declaram em `fields`; caso contrário 400 tipado com os campos suportados |
| `*.series` → 502 | `granularity` exigida pelo owner (api-delpi) e ausente do allowed params de `sales_order_otd.series`; demais séries falhavam sem granularity | `ANALYZE_PROXY_MAP` agora declara `(path, allowed, required)` — `rol.series`/`closing_rate.series`/`sales_order_otd.series` exigem `granularity`; `rol.by_product`/`rol.by_customer` exigem `start_date`+`end_date` (DTO do owner); falta → 400 local |
| erros de validação upstream → 502 | gateway convertia todo `status >= 400` em `RuntimeError` | `DelpiUpstreamError` carrega o status upstream: 400/422 → 400 validation, 404 → 404, demais → 502 honesto |
| delete: executor antes de consume | commit executava e só depois consumia — janela de replay | `claim_valid_proposal`: validação + consumo na mesma seção crítica sob o lock; executor só roda após o claim; falha do executor deixa proposta consumida (replay impossível) + audit log `caio_delete_commit(ed)` |
| 403 intermitentes | classificados: `coverage_audit`/`portfolio.list`/`load_summary` são `commercial.manage`; demais exigem `commercial.access` — 403 = principal sem permissão naquela chamada (negação legítima, mesma regra das rotas REST) | sem mudança de comportamento |

**Capabilities com paginação `page`/`page_size`:** `proposal.list`,
`proposal.analytics_list`, `customer.search`, `customer.account_audit`,
`customer.outbound_invoices`, `portfolio.audit`,
`production.appointments`. **`interaction_room.list`** usa
`limit`/`cursor` (modelo cursor do owner) — `page` rejeitado com 400.

## Homologação — Issue #125

Matriz executável completa em  (123/123
operações com estado e nível de evidência por linha).

- Ambiente: PostgreSQL 15 isolado (schema , V001–V023);
  boundaries api-delpi/core-api substituídos por fakes somente no
  hop HTTP — use cases, repositórios e autorização reais.
- Suítes:  (537 pass),
   (34 pass E2 + boundary).
- Evidência real de integração: 55 operações E2 plugins-db; 23
  contrato+boundary completos; 22 contrato+auth; 20 boundary parcial;
  3 internas. Dados upstream api-delpi/TOTVS = BLOCKED_EXTERNAL
  (sem fixture live — documentado, não maquiado).
- Defeitos corrigidos:  (43 caps → 502 vira 400),
  ordem auth→validação no , coerção ISO→datetime em
  task/activity,  alinhado ao DTO+,
   default, catálogo  alinhado ao
  owner.
- Conhecimento: +3 tópicos dedicados (,
  , ) — 16 tópicos ativos.

## Homologação — Issue #125

Matriz executável completa em `CAIO_HOMOLOGATION_MATRIX.md` (123/123
operações com estado e nível de evidência por linha).

- Ambiente: PostgreSQL 15 isolado (schema `commercial`, V001–V023);
  boundaries api-delpi/core-api substituídos por fakes somente no
  hop HTTP — use cases, repositórios e autorização reais.
- Suítes: `tests/test_caio_homologation.py` (537 pass),
  `tests/test_caio_integration.py` (34 pass E2 + boundary).
- Evidência real de integração: 55 operações E2 plugins-db; 23
  contrato+boundary completos; 22 contrato+auth; 20 boundary parcial;
  3 internas. Dados upstream api-delpi/TOTVS = BLOCKED_EXTERNAL
  (sem fixture live — documentado, não maquiado).
- Defeitos corrigidos: `required_fields` (43 caps → 502 vira 400),
  ordem auth→validação no `tool_read`, coerção ISO→datetime em
  task/activity, `group.create` alinhado ao DTO+`replace_members`,
  `sort_order` default, catálogo `task.from_message` alinhado ao
  owner.
- Conhecimento: +3 tópicos dedicados (`commercial.proposals`,
  `commercial.otd`, `commercial.production`) — 16 tópicos ativos.
