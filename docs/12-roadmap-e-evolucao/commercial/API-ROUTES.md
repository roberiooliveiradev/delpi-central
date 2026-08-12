# Portal Comercial — mapeamento de rotas de API

> **Status:** catálogo de contratos (ago/2026) — especificação; implementação por fase  
> **Gateway HTTP sugerido:** `/apps/commercial-api` → serviço `commercial-api`  
> **TOTVS:** somente via **api-delpi** (SQL Protheus)  
> **Naming:** paths e `operationId` em **English**; mensagens ao usuário em **pt-BR**  
> **Relacionados:** [DATA-MODEL.md](./DATA-MODEL.md) · [WIREFRAMES.md](./WIREFRAMES.md) · [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md) · [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md)

---

## 1. Princípios de contrato

| Item | Padrão |
|------|--------|
| Envelope | `{ success, message, data, meta }` |
| `operationId` | snake_case EN; igual OpenAPI e `meta.operationId` |
| `meta` | `entity`, `shape`, paginação, `freshness` quando couber |
| Auth | Bearer JWT (Keycloak); RBAC na API |
| Escopo de dados | `own` \| `team` \| `branch` \| `all` — parâmetros do client **não** ampliam acesso |
| Escrita sensível | `Idempotency-Key`; updates com `version` / `If-Match` |
| Datas | ISO 8601 |
| Paginação | `page`, `page_size` (ou cursor documentado) · **obrigatório** em listagens (escala) |
| Erros | `error.code` de domínio + `recoverable` |
| Smoke | Nível A por rota nova |
| Escala | Sem “list all”; timeouts no gateway TOTVS; routers por domínio — playbook § 14 |

**Quem chama o quê:**

```text
Portal Comercial (MFE)
  ├─ commercial-api     → Postgres Delpi + escopo/membership + BFF TOTVS
  └─ api-delpi          → KPIs /commercial/*, propostas (sem membership de carteira)

commercial-api
  └─ gateway HTTP       → api-delpi (open-orders, enrichment, billing, NF, metrics)
```

**Escopo de clientes:** ver [SCOPE-OWNERSHIP.md](./SCOPE-OWNERSHIP.md) — `manage` \| `team.view` = irrestrito; demais = union das carteiras do membership.

Dashboard Comercial e Propostas Comerciais continuam falando **direto** com api-delpi.

---

## 2. Índice por fase

| Fase | Serviço | Escopo |
|------|---------|--------|
| **F1** | commercial-api | `GET /health`, OpenAPI, auth smoke |
| **F2** | commercial-api | Seller portfolios + customer avatars (estado Delpi migrado) |
| **F2b** | api-delpi (existente) + commercial-api | Paridade UX: MFE consome open-orders TOTVS + portfolios Delpi |
| **F5** | commercial-api | Me, tasks, activities, prospects, visits, accounts 360, audit, outbox ops |
| **F6** | commercial-api | Opportunities, pipeline, forecast |
| **F7** | commercial-api | Samples, order-confirmations, delivery-exceptions, approvals |
| **Admin** | commercial-api | Settings (pipelines, stages, reasons, SLAs, segments, families) |
| **—** | api-delpi | KPIs `/commercial/*`, propostas, pedidos TOTVS — **já existem** (manter) |

---

## 3. commercial-api — catálogo completo

Prefixo interno da API: `/` (exposto como `/apps/commercial-api/...`).  
Colunas: **Method · Path · operationId · Fase · Permissão (proposta) · Entidade · Shape · WF**.

### 3.1 Platform / health (F1)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/health` | `get_commercial_health` | F1 | público/interno | `health` | `scalar` | — |
| GET | `/ready` | `get_commercial_ready` | F1 | interno | `health` | `scalar` | — |

### 3.2 Me / home (F2b parcial + F5)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/me/summary` | `get_my_commercial_summary` | F2b/F5 | `commercial.home.view` | `commercial_summary` | `composite_analysis` | WF-01 |
| GET | `/me/worklist` | `get_my_worklist` | F5 | `commercial.worklist.view` | `worklist` | `paged_list` | WF-06 · query `scope=mine\|team`, `assignee_user_id` (team) |
| GET | `/me/worklist/done` | `get_my_completed_worklist` | F5 | `commercial.worklist.view` | `worklist` | `paged_list` | Concluídas · `scope`, `assignee_user_id`, `limit` (1–100) |
| DELETE | `/tasks/{id}` | `delete_task` | F5 | `commercial.followups.manage` | `task` | `scalar` | Soft delete · criador \| responsável \| gestor |
| GET | `/me/seller-portfolio` | `get_my_seller_portfolio` | F2 | `commercial.accounts.view` | `seller_portfolio` | `scalar` | WF-03 |

> `get_my_seller_portfolio` também em `/seller-portfolios/me` (alias canônico § 3.3).

### 3.3 Seller portfolios (F2) — migração Delpi

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/seller-portfolios/me` | `get_my_seller_portfolio` | F2 | `commercial.accounts.view` | `seller_portfolio` | `scalar` | WF-03 |
| GET | `/seller-portfolios` | `list_seller_portfolios` | F2 | `commercial.seller-portfolios.manage` | `seller_portfolio` | `paged_list` | WF-05 |
| GET | `/seller-portfolios/coverage-audit` | `get_seller_portfolios_coverage_audit` | E6.1 | manage | `portfolio_coverage` | `scalar` | WF-05R |
| POST | `/seller-portfolios/customer-coverage` | `lookup_seller_portfolios_customer_coverage` | E6.4 | accounts.view | `portfolio_coverage` | `list` | WF-03 / Conta |
| GET | `/seller-portfolios/load-summary` | `get_seller_portfolios_load_summary` | E6.2 | manage | `portfolio_load` | `scalar` | WF-05R / ORG |

**Dependência TOTVS (api-delpi):** `POST /pedidos-venda-abertos/customers/open-order-metrics` (`list_customer_open_order_metrics`) — agrega `open_value` + `has_overdue` por cliente; alimenta load-summary e gap «sem cobertura» (universo = clientes com pedido aberto).

| GET | `/seller-portfolios/{seller_id}` | `get_seller_portfolio` | F2 | manage ou own | `seller_portfolio` | `scalar` | WF-05 |
| POST | `/seller-portfolios` | `create_seller_portfolio` | F2 | manage | `seller_portfolio` | `scalar` | WF-05 |
| PATCH | `/seller-portfolios/{seller_id}` | `update_seller_portfolio` | F2 | manage | `seller_portfolio` | `scalar` | WF-05 |
| DELETE | `/seller-portfolios/{seller_id}` | `deactivate_seller_portfolio` | F2 | manage | `seller_portfolio` | `scalar` | WF-05 |
| PUT | `/seller-portfolios/{seller_id}/customers` | `replace_seller_customers` | F2 | manage | `seller_customer` | `list` | WF-05 |
| POST | `/seller-portfolios/{seller_id}/customers` | `add_seller_customer` | F2 | manage | `seller_customer` | `scalar` | WF-05 |
| DELETE | `/seller-portfolios/{seller_id}/customers` | `remove_seller_customer` | F2 | manage | `seller_customer` | `scalar` | WF-05 |
| POST | `/seller-portfolios/{seller_id}/customers/transfer` | `transfer_seller_customers` | F2 | manage | `seller_customer` | `scalar` | WF-05 |

**Body delete/remove:** query ou body com `customer_code` + `customer_store`.  
**Transfer:** `to_seller_id`, lista de clientes, `reason_note` obrigatório → grava `audit_log`.

### 3.4 Customer avatars (F2)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/customers/{customer_code}/{store}/avatar` | `get_customer_avatar` | F2 | `commercial.accounts.view` | `customer_avatar` | file/scalar | WF-04 |
| PUT | `/customers/{customer_code}/{store}/avatar` | `upsert_customer_avatar` | F2 | manage ou accounts.manage | `customer_avatar` | `scalar` | WF-04 |
| DELETE | `/customers/{customer_code}/{store}/avatar` | `delete_customer_avatar` | F2 | manage | `customer_avatar` | `scalar` | WF-04 |

`GET` pode retornar `FileResponse` (binário) ou URL assinada — documentar no OpenAPI.

### 3.4b Open orders / billing / NF (BFF TOTVS + escopo commercial)

| Method | Path | operationId | Fase | Permissão | entity | shape | Notas |
|--------|------|-------------|------|-----------|--------|-------|-------|
| GET | `/open-orders/` | `list_commercial_open_orders` | F2b | `commercial.accounts.view` | `open_orders` | `list` | Escopo commercial; proxy → `GET …/totvs-open-orders` |
| GET | `/open-orders/ops-abertas` | `list_commercial_open_ops` | F2b | `commercial.accounts.view` | `open_ops` | `list` | Proxy TOTVS sem membership |
| POST | `/customers/billing-series` | `list_commercial_customer_billing_series` | F2b | accounts.view | `billing_series` | `scalar` | `filter_pairs` antes do gateway |
| GET | `/customers/{customer_code}/{store}/outbound-invoices` | `list_commercial_customer_outbound_invoices` | F2b | accounts.view | `outbound_invoice` | `paged_list` | `ensure_allows` → `GET …/totvs-outbound-invoices/{c}/{s}` |

MFE Portal **não** chama `GET /pedidos-venda-abertos/` (PVA) / billing-series / NF legada na api-delpi — só paths TOTVS via commercial-api.

### 3.5 Accounts / Conta 360 (F5; leitura TOTVS via gateway)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/accounts` | `list_commercial_accounts` | F5 | `commercial.accounts.view` | `account` | `paged_list` | WF-03 |
| GET | `/accounts/{customer_code}/{store}/360` | `get_account_360` | F5 | view | `account_360` | `composite_analysis` | WF-04 |
| GET | `/accounts/{customer_code}/{store}/timeline` | `get_account_timeline` | F5 | view | `activity` | `paged_list` | WF-04 |
| GET | `/accounts/{customer_code}/{store}/activities` | `list_account_activities` | F5 | view | `activity` | `paged_list` | WF-04 |
| GET | `/accounts/{customer_code}/{store}/visits` | `list_account_visits` | F5 | view | `visit` | `paged_list` | — |
| GET | `/accounts/{customer_code}/{store}/plan` | `get_account_plan` | M5/F5+ | view | `account_plan` | `scalar` | — |
| PUT | `/accounts/{customer_code}/{store}/plan` | `upsert_account_plan` | M5 | `commercial.accounts.manage` | `account_plan` | `scalar` | — |
| GET | `/accounts/{customer_code}/{store}/health` | `get_account_health` | P2 | view | `account_health` | `scalar` | — |

`get_account_360` **compõe**: portfolio Delpi + open orders + billing (gateway api-delpi) + tasks/activities locais.

### 3.6 Tasks / worklist (F5)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/tasks` | `list_tasks` | F5 | `commercial.followups.manage` ou worklist.view | `task` | `paged_list` | WF-06 |
| POST | `/tasks` | `create_task` | F5 | followups.manage | `task` | `scalar` | WF-06 |
| GET | `/tasks/{id}` | `get_task` | F5 | view/manage | `task` | `scalar` | WF-06 |
| PATCH | `/tasks/{id}` | `update_task` | F5 | manage | `task` | `scalar` | WF-06 · **entregue** |
| POST | `/tasks/{id}/complete` | `complete_task` | F5 | manage | `task` | `scalar` | WF-06 |
| POST | `/tasks/{id}/reassign` | `reassign_task` | F5 | `seller-portfolios.manage` + carteira ativa destino | `task` | `scalar` | WF-06 · **P1 entregue** [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) |
| POST | `/tasks/{id}/defer` | `defer_task` | F5 | manage | `task` | `scalar` | WF-06 |

`create_task` aceita `description` (Observação) e `assignee_user_id` (P1 — gestão). Worklist: `scope=team` + `assignee_user_id` opcional + `attachment_count`. Anexos P2: § 3.18 (`/attachments`, volume `commercial-attachments`).

### 3.7 Activities (F5)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/activities` | `list_activities` | F5 | accounts.view | `activity` | `paged_list` | — |
| POST | `/activities` | `create_activity` | F5 | followups.manage | `activity` | `scalar` | — |
| GET | `/opportunities/{id}/activities` | `list_opportunity_activities` | F6 | pipeline.view | `activity` | `paged_list` | WF-08 |

### 3.8 Prospects (F5 / pós-paridade)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/prospects` | `list_prospects` | F5 | `commercial.accounts.view` | `prospect` | `paged_list` | WF-07 |
| POST | `/prospects` | `create_prospect` | F5 | `commercial.accounts.manage` | `prospect` | `scalar` | WF-07 |
| GET | `/prospects/{id}` | `get_prospect` | F5 | view | `prospect` | `scalar` | WF-07 |
| PATCH | `/prospects/{id}` | `update_prospect` | F5 | manage | `prospect` | `scalar` | WF-07 |
| POST | `/prospects/{id}/disqualify` | `disqualify_prospect` | F5 | manage | `prospect` | `scalar` | WF-07 |
| POST | `/prospects/{id}/convert` | `convert_prospect` | F5 | manage | `prospect` | `scalar` | WF-07 |
| GET | `/prospects/{id}/contacts` | `list_prospect_contacts` | F5 | view | `prospect_contact` | `list` | WF-07 |
| POST | `/prospects/{id}/contacts` | `create_prospect_contact` | F5 | manage | `prospect_contact` | `scalar` | WF-07 |
| PATCH | `/prospects/{id}/contacts/{contact_id}` | `update_prospect_contact` | F5 | manage | `prospect_contact` | `scalar` | WF-07 |
| DELETE | `/prospects/{id}/contacts/{contact_id}` | `delete_prospect_contact` | F5 | manage | `prospect_contact` | `scalar` | WF-07 |
| GET | `/prospects/funnel` | `get_prospects_funnel` | F5 | view | `prospect_funnel` | `playbook_report` | WF-07 |

### 3.9 Visits (F5+)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/visits` | `list_visits` | F5 | accounts.view | `visit` | `paged_list` | — |
| POST | `/visits` | `create_visit` | F5 | accounts.manage | `visit` | `scalar` | — |
| GET | `/visits/{id}` | `get_visit` | F5 | view | `visit` | `scalar` | — |
| PATCH | `/visits/{id}` | `update_visit` | F5 | manage | `visit` | `scalar` | — |
| POST | `/visits/{id}/complete` | `complete_visit` | F5 | manage | `visit` | `scalar` | — |

### 3.10 Opportunities & pipeline (F6)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/opportunities` | `list_opportunities` | F6 | `commercial.pipeline.view` | `opportunity` | `paged_list` | WF-08 |
| POST | `/opportunities` | `create_opportunity` | F6 | `commercial.opportunities.manage` | `opportunity` | `scalar` | WF-08 |
| GET | `/opportunities/{id}` | `get_opportunity` | F6 | view/manage | `opportunity` | `scalar` | WF-08 |
| PATCH | `/opportunities/{id}` | `update_opportunity` | F6 | manage | `opportunity` | `scalar` | WF-08 |
| POST | `/opportunities/{id}/stage-transitions` | `transition_opportunity_stage` | F6 | manage | `opportunity_stage_history` | `scalar` | WF-08 |
| POST | `/opportunities/{id}/close-won` | `close_opportunity_won` | F6 | manage | `opportunity` | `scalar` | WF-08 |
| POST | `/opportunities/{id}/close-lost` | `close_opportunity_lost` | F6 | manage | `opportunity` | `scalar` | WF-08 |
| GET | `/opportunities/{id}/history` | `get_opportunity_history` | F6 | view | `opportunity_stage_history` | `list` | WF-08 |
| GET | `/opportunities/{id}/products` | `list_opportunity_products` | F6 | view | `opportunity_product` | `list` | WF-08 |
| PUT | `/opportunities/{id}/products` | `replace_opportunity_products` | F6 | manage | `opportunity_product` | `list` | WF-08 |
| GET | `/pipeline/summary` | `get_pipeline_summary` | F6 | pipeline.view | `pipeline_summary` | `playbook_report` | WF-08 |
| GET | `/pipeline/changes` | `get_pipeline_changes` | F6 | pipeline.view | `pipeline_change` | `paged_list` | WF-08 |
| GET | `/pipeline/board` | `get_pipeline_board` | F6 | pipeline.view | `pipeline_board` | `composite_analysis` | WF-08 |

### 3.11 Forecast (F6)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/forecast/cycles` | `list_forecast_cycles` | F6 | `commercial.forecast.view` | `forecast_cycle` | `paged_list` | WF-09 |
| POST | `/forecast/cycles` | `create_forecast_cycle` | F6 | `commercial.settings.manage` | `forecast_cycle` | `scalar` | WF-09 |
| GET | `/forecast/cycles/{id}` | `get_forecast_cycle` | F6 | view | `forecast_cycle` | `scalar` | WF-09 |
| GET | `/forecast/current` | `get_current_forecast` | F6 | view | `forecast_submission` | `composite_analysis` | WF-09 |
| GET | `/forecast/submissions` | `list_forecast_submissions` | F6 | view | `forecast_submission` | `paged_list` | WF-09 |
| POST | `/forecast/submissions` | `create_forecast_submission` | F6 | `commercial.forecast.submit` | `forecast_submission` | `scalar` | WF-09 |
| GET | `/forecast/submissions/{id}` | `get_forecast_submission` | F6 | view/submit | `forecast_submission` | `scalar` | WF-09 |
| PATCH | `/forecast/submissions/{id}` | `update_forecast_submission` | F6 | submit | `forecast_submission` | `scalar` | WF-09 |
| PUT | `/forecast/submissions/{id}/items` | `replace_forecast_items` | F6 | submit | `forecast_item` | `list` | WF-09 |
| POST | `/forecast/submissions/{id}/adjustments` | `create_forecast_adjustment` | F6 | submit/approve | `forecast_adjustment` | `scalar` | WF-09 |
| POST | `/forecast/submissions/{id}/submit` | `submit_forecast` | F6 | submit | `forecast_submission` | `scalar` | WF-09 |
| POST | `/forecast/submissions/{id}/approve` | `approve_forecast` | F6 | `commercial.forecast.approve` | `forecast_approval` | `scalar` | WF-09 |
| POST | `/forecast/submissions/{id}/reject` | `reject_forecast` | F6 | approve | `forecast_approval` | `scalar` | WF-09 |
| GET | `/forecast/history` | `get_forecast_history` | F6 | view | `forecast_snapshot` | `paged_list` | WF-09 |
| GET | `/forecast/accuracy` | `get_forecast_accuracy` | F6 | view | `forecast_accuracy` | `playbook_report` | WF-09 |
| GET | `/forecast/scenarios` | `get_forecast_scenarios` | F6 | view | `forecast_scenario` | `composite_analysis` | WF-09 |

### 3.12 Samples (F7)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/samples` | `list_samples` | F7 | `commercial.samples.view` | `sample` | `paged_list` | — |
| POST | `/samples` | `create_sample` | F7 | `commercial.samples.manage` | `sample` | `scalar` | — |
| GET | `/samples/{id}` | `get_sample` | F7 | view | `sample` | `scalar` | — |
| PATCH | `/samples/{id}` | `update_sample` | F7 | manage | `sample` | `scalar` | — |
| POST | `/samples/{id}/stage-transitions` | `transition_sample_stage` | F7 | manage | `sample_stage_history` | `scalar` | — |
| GET | `/samples/{id}/history` | `get_sample_history` | F7 | view | `sample_stage_history` | `list` | — |

### 3.13 Order confirmations (F7)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/order-confirmations` | `list_order_confirmations` | F7 | `commercial.order-confirmation.view` | `order_confirmation` | `paged_list` | — |
| POST | `/order-confirmations` | `create_order_confirmation` | F7 | manage | `order_confirmation` | `scalar` | — |
| GET | `/order-confirmations/{id}` | `get_order_confirmation` | F7 | view | `order_confirmation` | `scalar` | — |
| POST | `/order-confirmations/{id}/stage-transitions` | `transition_order_confirmation_stage` | F7 | manage | `order_confirmation_stage_history` | `scalar` | — |
| POST | `/order-confirmations/{id}/confirm` | `confirm_order_delivery_date` | F7 | manage | `order_confirmation` | `scalar` | — |

### 3.14 Delivery exceptions (F7)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/delivery-exceptions` | `list_delivery_exceptions` | F7 | `commercial.delivery-exceptions.view` | `delivery_exception` | `paged_list` | — |
| GET | `/delivery-exceptions/{id}` | `get_delivery_exception` | F7 | view | `delivery_exception` | `scalar` | — |
| POST | `/delivery-exceptions` | `create_delivery_exception` | F7 | view/manage | `delivery_exception` | `scalar` | — |
| POST | `/delivery-exceptions/{id}/actions` | `create_delivery_exception_action` | F7 | view | `delivery_exception_action` | `scalar` | — |
| POST | `/delivery-exceptions/{id}/resolve` | `resolve_delivery_exception` | F7 | manage | `delivery_exception` | `scalar` | — |

### 3.15 Approvals (F7+)

| Method | Path | operationId | Fase | Permissão | entity | shape | WF |
|--------|------|-------------|------|-----------|--------|-------|-----|
| GET | `/approvals` | `list_approvals` | F7 | conforme tipo | `approval` | `paged_list` | — |
| POST | `/approvals` | `create_approval` | F7 | requester | `approval` | `scalar` | — |
| POST | `/approvals/{id}/decide` | `decide_approval` | F7 | approver | `approval` | `scalar` | — |

### 3.16 Settings / admin (F5+ / M5)

| Method | Path | operationId | Fase | Permissão | entity | shape |
|--------|------|-------------|------|-----------|--------|-------|
| GET/POST | `/settings/pipelines` | `list_pipelines` / `create_pipeline` | F6 | `commercial.settings.manage` | `pipeline` | list/scalar |
| PATCH | `/settings/pipelines/{id}` | `update_pipeline` | F6 | settings.manage | `pipeline` | scalar |
| GET/POST | `/settings/stages` | `list_pipeline_stages` / `create_pipeline_stage` | F6 | settings.manage | `pipeline_stage` | list/scalar |
| PATCH | `/settings/stages/{id}` | `update_pipeline_stage` | F6 | settings.manage | `pipeline_stage` | scalar |
| GET/POST/PATCH | `/settings/reasons` | `list_reasons` / `create_reason` / `update_reason` | F5 | settings.manage | `reference_reason` | … |
| GET/POST/PATCH | `/settings/slas` | `list_sla_policies` / `create_sla_policy` / `update_sla_policy` | F5 | settings.manage | `sla_policy` | … |
| GET/POST/PATCH | `/settings/segments` | `list_segments` / … | M5 | settings.manage | `reference_segment` | … |
| GET/POST/PATCH | `/settings/customer-groups` | `list_customer_groups` / … | M5 | settings.manage | `reference_customer_group` | … |
| GET/POST/PATCH | `/settings/product-families` | `list_product_families` / … | M5 | settings.manage | `reference_product_family` | … |

### 3.17 Audit & data quality

| Method | Path | operationId | Fase | Permissão | entity | shape |
|--------|------|-------------|------|-----------|--------|-------|
| GET | `/audit` | `list_commercial_audit` | F2/F5 | `commercial.audit.view` | `audit_log` | `paged_list` |
| GET | `/data-quality/issues` | `list_data_quality_issues` | M5 | `commercial.data-quality.manage` | `data_quality_issue` | `paged_list` |
| POST | `/data-quality/issues/{id}/resolve` | `resolve_data_quality_issue` | M5 | data-quality.manage | `data_quality_issue` | `scalar` |

### 3.18 Attachments (P2 — entregue)

| Method | Path | operationId | Fase | Permissão | entity | shape |
|--------|------|-------------|------|-----------|--------|-------|
| GET | `/attachments?owner_type=&owner_id=` | `list_attachments` | P2 | followups / accounts.view | `attachment` | `list` |
| POST | `/attachments` (multipart) | `upload_attachment` | P2 | followups.manage | `attachment` | `scalar` |
| GET | `/attachments/{id}/content` | `download_attachment` | P2 | followups / accounts.view | `attachment` | file |
| DELETE | `/attachments/{id}` | `delete_attachment` | P2 | followups.manage | `attachment` | `scalar` |

`owner_type` inicial: `task`. Volume: `COMMERCIAL_ATTACHMENT_UPLOAD_DIR` / `${DELPI_DATA_HOST_DIR}/commercial-attachments`.

### 3.19 Sequences (P2 — cadências)

| Method | Path | operationId | Fase | Permissão | entity |
|--------|------|-------------|------|-----------|--------|
| GET/POST | `/sequences` | `list_sequences` / `create_sequence` | P2 | settings / followups | `sequence` |
| PATCH | `/sequences/{id}` | `update_sequence` | P2 | settings | `sequence` |
| POST | `/sequences/{id}/activate` | `activate_sequence` | P2 | settings | `sequence` |
| POST | `/sequence-enrollments` | `create_sequence_enrollment` | P2 | followups.manage | `sequence_enrollment` |

> Tabelas de sequence ainda não estão no DATA-MODEL M1–M5 — criar migration dedicada antes de implementar (ADR curto).

### 3.20 Rentabilidade / boletos (P1–P2 — sensível)

| Method | Path | operationId | Fase | Permissão | Notas |
|--------|------|-------------|------|-----------|--------|
| GET | `/profitability` | `get_profitability` | P2 | `commercial.profitability.view` | Preferir read model; fonte TOTVS/financeira via api-delpi se existir |
| GET | `/profitability/export` | `export_profitability` | P2 | `commercial.profitability.export` | Audit obrigatório |
| GET | `/sales-issued-slips` | `list_sales_issued_slips` | P1 | permissão dedicada | Só se contrato TOTVS/api-delpi existir |

**Não implementar** sem ficha de KPI + política de acesso (playbook FIN-004).

---

## 4. api-delpi — rotas TOTVS a **manter** (já existem)

Consumidas pelo Portal Comercial (F2b), dashboard e/ou gateway da commercial-api.

### 4.1 Pedidos / carteira enrichment (`/pedidos-venda-abertos`)

Leituras TOTVS **via gateway commercial-api** para o Portal (escopo na commercial). PVA legado pode chamar api-delpi direto até F2c.

| operationId | Method + path | Uso |
|-------------|----------------|------|
| `list_pedidos_venda_abertos` | `GET /pedidos-venda-abertos/` | Gateway commercial BFF + PVA legado (scope JWT só no PVA) |
| `list_ops_abertas_pedidos_venda` | `GET /pedidos-venda-abertos/ops-abertas` | Gateway commercial BFF |
| `search_active_customers_for_portfolio` | `GET .../customers/search` | commercial-api proxy (sem membership) |
| `enrich_portfolio_customers` | `POST .../customers/enrichment` | commercial-api (scope) → api-delpi |
| `list_customer_open_order_metrics` | `POST .../customers/open-order-metrics` | E6 load-summary (service) |
| `list_customer_billing_series` | `POST .../customers/billing-series` | commercial-api BFF (scope) |
| `list_cliente_notas_fiscais_saida` | `GET .../clientes/{codigo}/{loja}/notas-fiscais` | commercial-api BFF (scope); PVA legado |

### 4.2 KPIs / OTD / propostas OV (`/commercial`)

| operationId | Path | Uso |
|-------------|------|-----|
| `get_*_rol_target_pct` (6) | `/commercial/*_rol_target_pct` | Home gestão / dashboard |
| `get_commercial_rol_series` | `/commercial/rol/series` | Séries |
| `get_commercial_rol_by_customer` | `/commercial/rol/by-customer` | Conta / ranking |
| `list_commercial_proposals` / `get_commercial_proposal` / history | `/commercial/proposals*` | OV |
| `get_sales_conversion_rate` | `/commercial/closing-rate` | Hit rate |
| `get_new_clients_*` / `get_new_business_rol_pct` | `/commercial/new-*` | Novos negócios |
| `get_sales_order_otd*` | `/commercial/sales-order-otd*` | OTD |

### 4.3 Propostas ativas

| operationId | Path |
|-------------|------|
| `list_propostas_comerciais` | `GET /propostas-comerciais/` |
| `get_proposta_comercial` | `GET /propostas-comerciais/{proposta_interna}` |
| `export_proposta_comercial_pdf` | `GET .../pdf` |
| `export_proposta_comercial_pdf_with_overrides` | `POST .../pdf` |

### 4.4 Satélites (opcional)

| operationId | Path | Quando |
|-------------|------|--------|
| `list_sale_orders` | `GET /sales/` | Se open-orders view insuficiente |
| `get_product_sales_open_orders` | `GET /products/{code}/sales/open-orders` | Drill produto |
| `get_financial_rol` | `GET /financial/rol` | Base financeira |

---

## 5. api-delpi — rotas a **deprecar** (após F2 cutover)

Migradas para commercial-api § 3.3–3.4. Não criar features novas nelas.

| operationId legado | Destino commercial-api |
|--------------------|------------------------|
| `get_my_seller_portfolio` | idem |
| `list_seller_portfolios` | idem |
| `get_seller_portfolio` | idem |
| `create_seller_portfolio` | idem |
| `update_seller_portfolio` | idem |
| `deactivate_seller_portfolio` | idem |
| `replace_seller_customers` | idem |
| `add_seller_customer` | idem |
| `remove_seller_customer` | idem |
| `transfer_seller_customers` | idem |
| `get_customer_avatar` | idem |
| `upsert_customer_avatar` | idem |
| `delete_customer_avatar` | idem |

---

## 6. api-delpi — rotas **novas** (só se faltar contrato TOTVS)

Não inventar SQL na commercial-api. Se o Portal Comercial precisar e **não** houver operação:

| Necessidade | Ação | Fase |
|-------------|------|------|
| Carteira consolidada ROL+carteira (fórmula oficial) | Nova rota `/commercial/...` após ficha KPI F0 | Cockpit |
| Faturado não embarcado | Nova rota operacional + checklist OpenAPI | F7 |
| Boletos emitidos por Vendas | Nova rota + permissão sensível | P1 |
| Capacidade fábrica (read) | Avaliar domínio Produção; Comercial só consome | P2 |

Cada uma: `new-api-route-checklist.mdc` + registry + smoke.

---

## 7. Gateway commercial-api → api-delpi

Port sugerido: `DelpiCommercialReadPort` / `DelpiCommercialGateway`.

| Método port | Chama api-delpi | Usado por |
|-------------|----------------|-----------|
| `list_open_orders(filters)` | `list_pedidos_venda_abertos` | `get_account_360`, opcional BFF |
| `list_open_ops(filters)` | `list_ops_abertas_pedidos_venda` | summary |
| `search_customers(q)` | `search_active_customers_for_portfolio` | add customer |
| `enrich_customers(keys)` | `enrich_portfolio_customers` | list accounts |
| `billing_series(keys, period)` | `list_customer_billing_series` | account 360 |
| `list_invoices(code, store)` | `list_cliente_notas_fiscais_saida` | account 360 |
| `rol_by_customer(...)` | `get_commercial_rol_by_customer` | account / home |
| `otd_panel(...)` | `get_sales_order_otd_panel` | home gestão |

JWT do usuário propagado. Sem SQL Server no commercial-api.

---

## 8. Matriz tela → APIs

| Wireframe | commercial-api | api-delpi |
|-----------|----------------|----------|
| WF-01 Início | `get_my_commercial_summary`, worklist counts | ROL/OTD (gestão); opcional |
| WF-02 Open orders | — | `list_pedidos_venda_abertos`, ops |
| WF-03 Carteira | `get_my_seller_portfolio` / `list` + enrich via gateway | `enrich_portfolio_customers` |
| WF-04 Conta | `get_account_360` **ou** compose no MFE: portfolio + avatar + tasks | open-orders filter, billing, NF |
| WF-05 Carteiras admin | CRUD § 3.3 + search gateway | `search_active_customers_*` |
| WF-06 Meu dia | `get_my_worklist`, tasks | — |
| WF-07 Prospects | § 3.8 | — |
| WF-08 Oportunidades | § 3.10 | proposals (deep link) |
| WF-09 Forecast | § 3.11 | metas SI (indireto) |

**F2b mínimo (paridade):** § 3.3 + § 3.4 + § 4.1 (+ avatar). Conta 360 pode ser composição no MFE até F5.

---

## 9. Contagem resumida

| Bloco | Qtd aproximada de operationIds |
|-------|--------------------------------|
| commercial-api F1–F2 (health + portfolio + avatar) | ~16 |
| commercial-api F5 (me, tasks, activities, prospects, visits, accounts, audit, attachments) | ~45 |
| commercial-api F6 (opportunities + forecast + settings pipeline) | ~40 |
| commercial-api F7 (samples, confirmations, exceptions, approvals) | ~25 |
| commercial-api admin refs / DQ / sequences / profitability | ~25 |
| api-delpi já existentes (reuso) | ~30+ |
| api-delpi a deprecar | 13 |
| api-delpi novas (condicionais) | 0–N (F0 decide) |

---

## 10. Ordem de implementação sugerida

1. **F1** — health + skeleton OpenAPI + auth.  
2. **F2** — § 3.3 + § 3.4 + `audit_log` em transfer; deprecar espelho na api-delpi após cutover.  
3. **F2b** — MFE Portal Comercial chama § 4.1 + § 3.3/3.4.  
4. **F5** — § 3.2, 3.5–3.9, 3.17.  
5. **F6** — § 3.10–3.11 + settings pipelines.  
6. **F7** — § 3.12–3.15.  
7. **Admin/M5** — § 3.16 restante + DQ.  
8. **Condicionais** — § 3.19–3.20 e § 6 só com ADR/ficha.

---

## 11. Referências

- Envelope/meta: `.cursor/rules/api-delpi-response-contract.mdc` (espelhar na commercial-api)  
- Rota TOTVS nova: `.cursor/rules/new-api-route-checklist.mdc`  
- Modelo: [DATA-MODEL.md](./DATA-MODEL.md)  
- Inventário factual: [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md)  
