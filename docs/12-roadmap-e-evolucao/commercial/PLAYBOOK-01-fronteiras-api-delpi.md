# Playbook 01 — Fronteiras api-delpi × commercial-api

**Contrato vivo** — define o que fica em cada serviço e como evitar duplicação de SQL TOTVS / CRM Delpi.

**Status:** ago/2026 — baseline documental; implementação nas fases F1–F2b do [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) (produto ao usuário: **Portal Comercial**).  
**Referência de padrão:** [maintenance/PLAYBOOK-01-fronteiras-api-delpi.md](../maintenance/PLAYBOOK-01-fronteiras-api-delpi.md).

O MFE legado `pedidos-venda-abertos` permanece até a fase **F2c** (depreciação pós-paridade). A UI canônica-alvo das jornadas de carteira/pedidos é o **Portal Comercial** (`plugins/commercial`).

---

## 1. Princípio

| Camada | Responsabilidade |
|--------|------------------|
| **api-delpi** | Única implementação de SQL Protheus; KPIs e listagens TOTVS; contrato `{ success, message, data, meta }`; OpenAPI + `route_contract_registry` |
| **commercial-api** | CRUD operacional Postgres; workflows CRM; orquestração; **gateways HTTP** para TOTVS via api-delpi |
| **MFE existentes** | Podem chamar api-delpi **direto** para reads TOTVS já estabilizados (`dashboard-commercial`, `propostas-comerciais`, listagens de pedidos) |
| **commercial-workspace / Portal Comercial / CRUD migrado** | Chama **somente** `commercial-api` para estado Delpi (JWT); reads TOTVS via api-delpi ou via gateway da commercial-api; nunca SQL Server |

```text
Browser (dashboard / propostas / pedidos read)
  → api-delpi → SQL Server (TOTVS)

Browser (workspace / carteira CRUD / CRM)
  → commercial-api → Postgres
  → commercial-api → DelpiApiClient → api-delpi → TOTVS
```

**Proibido:**

- Copiar queries TOTVS de `api-delpi/.../totvs/**` para `commercial-api`.
- Segundo client SQL Server no plugin ou na commercial-api.
- Expandir CRUD de carteira/oportunidade/forecast **dentro** da api-delpi após ADR-001.
- MFE de workspace chamar api-delpi bypassando commercial-api para dados que a API dedicada já agrega.

---

## 2. Mapa de dados

| Conceito | Persistência canônica | Leitura TOTVS |
|----------|----------------------|---------------|
| ROL, conversão, OTD, novos negócios | — (calculado) | api-delpi `/commercial/*` |
| Proposta OV (dashboard) | — | api-delpi `/commercial/proposals` |
| Proposta ativa + PDF | — | api-delpi `/propostas-comerciais` |
| Pedido em aberto / NF saída | — | api-delpi `/pedidos-venda-abertos` (GETs) |
| Cliente cadastro (`codigo`+`loja`) | TOTVS SA1 | api-delpi |
| **Seller portfolio / customers** | **Postgres `commercial-api`** (após F2) | Enriquecimento via api-delpi |
| **Customer avatar** | **Postgres + volume `commercial-api`** | — |
| Opportunity / stage history | Postgres commercial-api | Refs externas (proposta/pedido) |
| Activity / task / worklist | Postgres commercial-api | — |
| Forecast declarado | Postgres commercial-api | Meta via SI / api-delpi |
| Sample / order confirmation case | Postgres commercial-api | Pedido via api-delpi |
| Metas / IDD | strategic-indicators-api | Fontes via api-delpi |

### Identificadores canônicos

```text
customer_key  = customer_code + "|" + store
order_key     = branch + "|" + order_number + "|" + line_item
proposal_key  = branch + "|" + proposal_number + "|" + revision
product_key   = normalized product_code
user_key      = Keycloak sub
```

Nomes técnicos (paths, tables, `operationId`, permissions): **English**.  
Mensagens e rótulos ao usuário: **pt-BR**.

---

## 3. O que permanece na api-delpi

### 3.1 Prefixos estáveis

| Prefixo | Uso |
|---------|-----|
| `/commercial/*` | KPIs e propostas OV (todos GET) |
| `/pedidos-venda-abertos/` (**somente** listagens TOTVS) | Pedidos, ops abertas, search, enrichment, billing-series, NF |
| `/propostas-comerciais/*` | Propostas ativas + PDF |
| `/sales/`, `/products/.../sales*` | Satélites de vendas |
| `/financial/rol` | Base financeira quando aplicável |

**Não** permanecem em `/pedidos-venda-abertos`: `sellers/*` (GET/POST/PATCH/DELETE) nem `customers/.../avatar` — são estado Delpi.

Nova rota TOTVS → checklist `.cursor/rules/new-api-route-checklist.mdc` + `api-delpi-openapi-route-standards.mdc`.

---

## 4. O que sai da api-delpi (migração F2) — obrigatório

**Regra:** toda rota de `pedidos-venda-abertos` cujo dado canônico **não** é TOTVS (Postgres plugins / arquivo de avatar) **migra** para `commercial-api` — leitura e escrita. Lista canônica: [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md) § 3.2.

| operationId atual (api-delpi) | operationId alvo (commercial-api, EN) | Path alvo sugerido |
|---|---|---|
| `get_my_seller_portfolio` | `get_my_seller_portfolio` | `GET /seller-portfolios/me` |
| `list_seller_portfolios` | `list_seller_portfolios` | `GET /seller-portfolios` |
| `get_seller_portfolio` | `get_seller_portfolio` | `GET /seller-portfolios/{seller_id}` |
| `create_seller_portfolio` | `create_seller_portfolio` | `POST /seller-portfolios` |
| `update_seller_portfolio` | `update_seller_portfolio` | `PATCH /seller-portfolios/{seller_id}` |
| `deactivate_seller_portfolio` | `deactivate_seller_portfolio` | `DELETE /seller-portfolios/{seller_id}` |
| `replace_seller_customers` | `replace_seller_customers` | `PUT /seller-portfolios/{seller_id}/customers` |
| `add_seller_customer` | `add_seller_customer` | `POST /seller-portfolios/{seller_id}/customers` |
| `remove_seller_customer` | `remove_seller_customer` | `DELETE /seller-portfolios/{seller_id}/customers` |
| `transfer_seller_customers` | `transfer_seller_customers` | `POST /seller-portfolios/{seller_id}/customers/transfer` |
| `get_customer_avatar` | `get_customer_avatar` | `GET /customers/{customer_code}/{store}/avatar` |
| `upsert_customer_avatar` | `upsert_customer_avatar` | `PUT /customers/{customer_code}/{store}/avatar` |
| `delete_customer_avatar` | `delete_customer_avatar` | `DELETE /customers/{customer_code}/{store}/avatar` |

Transição F2: dual-read/dual-write permitido **só** até cutover. Após cutover, api-delpi **não** permanece dona canônica dessas rotas (deprecar com 410 ou proxy temporário documentado). Enrichment TOTVS (`search`, `enrichment`, `billing-series`) continua na api-delpi.

### Plano de migração

```text
1. Scaffold commercial-api + schema Postgres + volume avatars
2. Dual-read/dual-write (feature flag) — comparar contagens de portfolios/customers
3. MFE pedidos-venda-abertos aponta TODAS as rotas Delpi (GET sellers + writes + avatars) para commercial-api
4. Deprecar na api-delpi o conjunto completo § 3.2 (não só POST/PATCH/DELETE)
5. Não apagar migrations antigas aplicadas; schema antigo read-only até limpeza aprovada
6. Nunca `reset` de schema em produção (plugins-migrations-no-reset-prod)
```

Anexos/avatars: volume `${DELPI_DATA_HOST_DIR}/commercial-avatars` (ou equivalente) nos **dois** composes — regra `persistent-upload-storage.mdc`.

---

## 5. Gateway na commercial-api

**Port alvo (exemplo):** `commercial_app/domain/ports/delpi_commercial_read_port.py`  
**Gateway alvo:** `commercial_app/infrastructure/gateways/delpi_commercial_gateway.py`

| Método port (EN) | Chama api-delpi |
|---|---|
| `search_active_customers(...)` | `GET /pedidos-venda-abertos/customers/search` |
| `enrich_customers(...)` | `POST /pedidos-venda-abertos/customers/enrichment` |
| `list_billing_series(...)` | `POST /pedidos-venda-abertos/customers/billing-series` |
| `list_open_orders(...)` | `GET /pedidos-venda-abertos/` |
| `list_customer_invoices(...)` | `GET /pedidos-venda-abertos/clientes/{codigo}/{loja}/notas-fiscais` |
| `get_rol_by_customer(...)` | `GET /commercial/rol/by-customer` |
| `get_otd_panel(...)` | `GET /commercial/sales-order-otd/panel` |
| `get_proposal(...)` / `list_proposals(...)` | `/commercial/proposals` ou `/propostas-comerciais` conforme caso |

**Cliente:** `shared/delpi_api_client.DelpiApiClient` (mesmo padrão SI / Transformômetro).

**Headers:**

- `Authorization: Bearer` — JWT do usuário propagado.
- Fluxo S2S (`X-Delpi-Service-Token`) só se api-delpi ou chat precisarem de fachada futura — não na F1–F2 do MFE.

---

## 6. Rotas próprias da commercial-api

Catálogo completo (method, path, `operationId`, fase, permissão, shape, wireframe): **[API-ROUTES.md](./API-ROUTES.md)**.

Resumo por grupo:

| Grupo | Prefixo / exemplos | Fase |
|-------|---------------------|------|
| Health | `/health` | F1 |
| Seller portfolios | `/seller-portfolios` | F2 |
| Avatars | `/customers/{code}/{store}/avatar` | F2 |
| Worklist / tasks | `/me/worklist`, `/tasks` | F5 |
| Accounts 360 | `/accounts/...` | F5 |
| Prospects / visits | `/prospects`, `/visits` | F5 |
| Opportunities | `/opportunities`, `/pipeline/*` | F6 |
| Forecast | `/forecast/*` | F6 |
| Samples / confirmations / exceptions | `/samples`, `/order-confirmations`, `/delivery-exceptions` | F7 |
| Settings | `/settings/*` | F5+ |
| Audit | `/audit` | F2/F5 |

Contrato obrigatório:

- Envelope `{ success, message, data, meta }`
- `operationId` estável snake_case **English**, igual OpenAPI e `meta.operationId`
- `meta.entity`, `meta.shape`, paginação, freshness quando couber
- RBAC na API (filial, carteira `own|team|branch|all`) — nunca só no MFE
- Idempotency-Key em comandos sensíveis; version/If-Match em edits
- Smoke Nível A por rota

---

## 7. Checklist ao adicionar leitura TOTVS nova

1. [ ] Rota na api-delpi com `operation_id` registrado e envelope?
2. [ ] Doc em `api-delpi/docs/api/` + locale EN/pt-BR?
3. [ ] Teste smoke + `audit_route_test_coverage.py`?
4. [ ] Port + gateway na `commercial-api` (se o workspace precisar)?
5. [ ] Nenhum SQL Protheus fora da api-delpi?
6. [ ] MFE workspace não chama a rota TOTVS direto se a commercial-api já agrega?

---

## 8. Checklist ao adicionar CRUD Delpi novo

1. [ ] Entidade vive no Postgres da commercial-api?
2. [ ] Migration **nova** imutável (nunca editar V00N aplicada)?
3. [ ] Upload → volume Compose + `infra/README-ambiente.md`?
4. [ ] Permissão Keycloak + gate na API?
5. [ ] Texto PT-BR ao usuário fora de literais espalhados (content/i18n do pacote)?
6. [ ] **Não** adicionar o CRUD na api-delpi?

---

## 9. Evolução futura — fachada para chat / SI / TV

Se Minha DELPI Chat, SI ou TV precisarem de resumo CRM sem falar com a commercial-api:

- Preferir rotas api-delpi espelhadas (padrão Transforma+) com S2S → commercial-api.
- Ou import OpenAPI da commercial-api no chat (decisão por ADR).
- **Não** antecipar na F1–F2.

Apresentação chat: `schema-first-presentation-delivered.mdc` — sem presenter por rota.

---

## 10. Referências

- Inventário: [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md)
- Rotas: [API-ROUTES.md](./API-ROUTES.md)
- Modelo: [DATA-MODEL.md](./DATA-MODEL.md)
- ADR: [adr/ADR-001-commercial-api.md](./adr/ADR-001-commercial-api.md)
- Maintenance fronteiras: `docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md`
- Transformômetro: `docs/12-roadmap-e-evolucao/transformometro-app/README.md`
- Regras: `.cursor/rules/new-api-route-checklist.mdc`, `api-delpi-response-contract.mdc`, `persistent-upload-storage.mdc`, `plugins-migrations-no-reset-prod.mdc`
