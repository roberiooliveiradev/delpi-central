# Inventário de ativos — domínio Comercial

> **Status:** baseline factual + consolidação nativa em curso — [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md)  
> **Produto ao usuário:** **Portal Comercial** (`id` técnico `commercial`)  
> **Playbook mestre:** [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)  
> **Fronteiras:** [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)  
> **Ata × Portal + ecossistema MFEs:** [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) (§7)

Este documento lista o que **já existe** no monorepo para o domínio Comercial e o que ainda é lacuna. Serve para evitar reimplementação.

**Destino de produto:** o **Portal Comercial** é a UX canônica (páginas nativas). Plugins irmãos **coexistem** (decisão 5C); F2c só após Comercial ≥ PVA + pedido.

---

## 1. Plugins MFE

| Plugin `id` | Nome ao usuário | `basePath` | Papel | Consome |
|---|---|---|---|---|
| `commercial` | **Portal Comercial** | `/apps/commercial` | UX canônica (ops + Gestão + Propostas ADY) | commercial-api + api-delpi |
| `dashboard-commercial` | Dashboard Comercial | `/apps/dashboard-commercial` | Legado coexistente (referência até Gestão nativa) | api-delpi `/commercial/*` |
| `pedidos-venda-abertos` | Portal do Vendedor | `/apps/pedidos-venda-abertos` | Legado coexistente (F2c adiado) | api-delpi |
| `propostas-comerciais` | Propostas Comerciais | `/apps/propostas-comerciais` | Legado coexistente (referência até ADY nativo) | api-delpi `/propostas-comerciais/*` |

**Existem:** `plugins/commercial/`, `commercial-api/` (F0–F2b harden em `main`).

**Depreciação planejada (após homologação § 2.1.1):** `pedidos-venda-abertos` — [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md).

### Telas observadas

| Plugin | Páginas / rotas principais |
|---|---|
| `commercial` | Home, open-orders, customers, seller-portfolios, **gestao/***, **propostas** (consolidação) |
| `dashboard-commercial` | Dashboard, detalhe proposta OV, OTD (legado) |
| `pedidos-venda-abertos` | Pedidos, clientes, detalhe, config (legado) |
| `propostas-comerciais` | Lista, detalhe, PDF (legado) |

Docs locais:

- `plugins/commercial/README.md`
- `plugins/dashboard-commercial/docs/`
- `docs/12-roadmap-e-evolucao/pedidos-venda-abertos/`
- `docs/12-roadmap-e-evolucao/propostas-comerciais/`

---

## 2. api-delpi — prefixo `/commercial` (TOTVS read)

Router: `api-delpi/app/interface/http/routes/commercial/commercial_router.py`  
Permissão típica: `api-delpi.access` **ou** `dashboard-commercial.view`.

| operationId | Method + path | Tipo |
|---|---|---|
| `get_head_office_rol_target_pct` | `GET /commercial/head_office_rol_target_pct` | KPI |
| `get_branch_rol_target_pct` | `GET /commercial/branch_rol_target_pct` | KPI |
| `get_head_office_weg_rol_target_pct` | `GET /commercial/head_office_weg_rol_target_pct` | KPI |
| `get_branch_weg_rol_target_pct` | `GET /commercial/branch_weg_rol_target_pct` | KPI |
| `get_head_office_new_business_rol_target_pct` | `GET /commercial/head_office_new_business_rol_target_pct` | KPI |
| `get_branch_new_business_rol_target_pct` | `GET /commercial/branch_new_business_rol_target_pct` | KPI |
| `get_commercial_rol_series` | `GET /commercial/rol/series` | Série |
| `get_commercial_rol_by_customer` | `GET /commercial/rol/by-customer` | Ranking |
| `list_commercial_proposals` | `GET /commercial/proposals` | Listagem OV |
| `get_commercial_proposal` | `GET /commercial/proposals/{proposal_number}` | Detalhe OV |
| `get_commercial_proposal_history_events` | `GET /commercial/proposals/{proposal_number}/history/events` | Histórico |
| `get_sales_conversion_rate` | `GET /commercial/closing-rate` | KPI |
| `get_new_clients_average` | `GET /commercial/new-clients-average` | KPI |
| `get_new_clients_rol_pct` | `GET /commercial/new-clients-rol-pct` | KPI |
| `get_new_business_rol_pct` | `GET /commercial/new-business-rol-pct` | KPI |
| `get_sales_order_otd` | `GET /commercial/sales-order-otd` | KPI |
| `get_sales_order_otd_panel` | `GET /commercial/sales-order-otd/panel` | Painel |
| `get_sales_order_otd_series` | `GET /commercial/sales-order-otd/series` | Série |
| `get_sales_order_otd_line_detail` | `GET /commercial/sales-order-otd/lines/{branch}/{order_number}/{line_item}` | Detalhe |

**Dono alvo:** permanece na api-delpi. Sem CRUD.

Docs: `api-delpi/docs/api/06-modulos-departamentais.md`, `comercial-sales-order-otd.md`, `comercial-taxa-conversao-estagios.md`.

---

## 3. api-delpi — prefixo `/pedidos-venda-abertos` (híbrido)

Router: `api-delpi/app/interface/http/routes/pedidos_venda_abertos/pedidos_venda_abertos_router.py`  
Migrations Postgres (hoje na api-delpi):  
`api-delpi/migrations/plugins/pedidos-venda-abertos/V001__create_seller_portfolio.sql`, `V002__customer_avatars.sql`.

**Regra de corte (obrigatória):**

| Critério | Destino |
|---|---|
| Lê view/SQL Protheus (pedido, NF, cliente TOTVS, enrichment) | **permanece** na api-delpi |
| Lê ou escreve estado **Delpi** (Postgres plugins / arquivo de avatar) | **já em** `commercial-api` (F2 cutover) — leitura **e** escrita; rotas api-delpi deprecated |

Não há exceção para “só GET”: se a fonte canônica não é TOTVS, a rota sai da api-delpi.

### 3.1 TOTVS / query — **permanecem** na api-delpi

| operationId | Method + path |
|---|---|
| `list_pedidos_venda_abertos` | `GET /pedidos-venda-abertos/` |
| `list_ops_abertas_pedidos_venda` | `GET /pedidos-venda-abertos/ops-abertas` |
| `search_active_customers_for_portfolio` | `GET /pedidos-venda-abertos/customers/search` |
| `enrich_portfolio_customers` | `POST /pedidos-venda-abertos/customers/enrichment` |
| `list_customer_billing_series` | `POST /pedidos-venda-abertos/customers/billing-series` |
| `list_cliente_notas_fiscais_saida` | `GET /pedidos-venda-abertos/clientes/{codigo}/{loja}/notas-fiscais` |

### 3.2 Estado Delpi (Postgres / avatar) — **canônico em commercial-api**

Inclui **CRUD e leituras** cujo dado canônico é Delpi (não TOTVS). Na api-delpi ficam **deprecated** até F2c:

| operationId | Method + path | Observação |
|---|---|---|
| `get_my_seller_portfolio` | `GET /pedidos-venda-abertos/sellers/me` | Read Postgres → migrar |
| `list_seller_portfolios` | `GET /pedidos-venda-abertos/sellers` | Read Postgres → migrar |
| `get_seller_portfolio` | `GET /pedidos-venda-abertos/sellers/{seller_id}` | Read Postgres → migrar |
| `create_seller_portfolio` | `POST /pedidos-venda-abertos/sellers` | Write Postgres |
| `update_seller_portfolio` | `PATCH /pedidos-venda-abertos/sellers/{seller_id}` | Write Postgres |
| `deactivate_seller_portfolio` | `DELETE /pedidos-venda-abertos/sellers/{seller_id}` | Soft deactivate |
| `replace_seller_customers` | `PUT /pedidos-venda-abertos/sellers/{seller_id}/customers` | Replace set |
| `add_seller_customer` | `POST /pedidos-venda-abertos/sellers/{seller_id}/customers` | |
| `remove_seller_customer` | `DELETE /pedidos-venda-abertos/sellers/{seller_id}/customers` | |
| `transfer_seller_customers` | `POST /pedidos-venda-abertos/sellers/{seller_id}/customers/transfer` | |
| `get_customer_avatar` | `GET .../customers/{codigo}/{loja}/avatar` | Arquivo + metadado Delpi |
| `upsert_customer_avatar` | `PUT .../customers/{codigo}/{loja}/avatar` | Volume persistente |
| `delete_customer_avatar` | `DELETE .../customers/{codigo}/{loja}/avatar` | |

Após F2 cutover: MFE **Portal Comercial** chama `commercial-api` (`/apps/commercial-api/seller-portfolios*`, avatars) para **todas** as rotas da tabela acima. Search/enrichment TOTVS: proxy na commercial-api → api-delpi; billing-series e NF: MFE chama api-delpi direto.

Permissões: `commercial.accounts.view` / `commercial.seller-portfolios.manage` (aliases: `pedidos-venda-abertos.access` / `.admin`). Rotas api-delpi `/sellers*` e avatars Delpi: **deprecated** (código pode permanecer até F2c).

---

## 4. api-delpi — prefixo `/propostas-comerciais`

Controller: `api-delpi/app/interface/http/propostas_comerciais_controller.py`

| operationId | Method + path | Tipo |
|---|---|---|
| `list_propostas_comerciais` | `GET /propostas-comerciais/` | TOTVS read |
| `get_proposta_comercial` | `GET /propostas-comerciais/{proposta_interna}` | TOTVS read |
| `export_proposta_comercial_pdf` | `GET .../pdf` | Export |
| `export_proposta_comercial_pdf_with_overrides` | `POST .../pdf` | Export com overrides locais (não grava Protheus) |

**Dono alvo:** permanece na api-delpi. Não confundir com `/commercial/proposals` (OV do dashboard).

---

## 5. Satélites relacionados

| operationId / superfície | Path | Relação |
|---|---|---|
| `list_sale_orders` | `GET /sales/` | Pedidos genéricos |
| `get_product_sales_open_orders` | `GET /products/{code}/sales/open-orders` | Pedidos por produto |
| `get_product_sales_summary` / `billing` | `GET /products/{code}/sales*` | Vendas produto |
| `get_financial_rol` | `GET /financial/rol` | Base financeira ROL |
| Indicadores SI comercial | `strategic-indicators-api` + gateways api-delpi | Metas / IDD |

Doc SI: `strategic-indicators-api/docs/COMMERCIAL_INDICATORS.md`.

---

## 6. Persistência Delpi

| Dado | Onde (atual) | Notas |
|---|---|---|
| Seller portfolio + customers | Schema Postgres `commercial` via **commercial-api** (default `COMMERCIAL_PORTFOLIO_SOURCE=commercial`) | Portal não compartilha runtime com PVA |
| Customer avatars | Volume `commercial-avatars` + `commercial.customer_avatars` | `redirect_slashes=False` na API; ver Mixed Content HTTPS |
| Schema legado `pedidos_venda_abertos` | Ainda no Postgres plugins — **só PVA** | Carteiras/avatars do plugin PVA; sem dual-read com `commercial.*` |
| Pedido / proposta / cliente cadastro | TOTVS via api-delpi | Permanecem |
| Oportunidade, tarefa, forecast, amostra | — | `commercial-api` (F5+) |

---

## 7. Plataforma — pré-requisitos de módulo

| Capacidade | Estado (ago/2026) |
|---|---|
| Spec plugin × módulo `schemaVersion 1.1.0` | Documentada em `docs/05-plugin-system/` |
| Runtime Core API + Portal `RouteDelegate` | **Pendente** ([roadmap](../../05-plugin-system/roadmap-implementacao-plugin-modulo.md)) |
| Pacote `@delpi/module-runtime` | **Pendente** |
| Manifest `type: module` em produção | **Não registrar** até F3–F4 |

---

## 8. Matriz gap × pilares do produto

| Pilar | Estado | Ativo atual / gap |
|---|---|---|
| Meu dia / worklist | **novo** | Sem fila central |
| Prospects | **novo** | Sem domínio próprio |
| Conta 360 | **parcial** | Check-up no Portal Comercial (+ PVA legado); sem timeline unificada |
| Administração (carteiras) | **parcial** | CRUD na **commercial-api**; PVA legado até F2c |
| Oportunidades / pipeline | **novo** | — |
| Ofertas / propostas | **parcial** | Dois conceitos OV × proposta ativa; sem SLA de etapas |
| Forecast | **novo** | Metas via SI; forecast declarado ausente |
| Pedidos e entregas | **parcial** | Lista aberta + OTD; sem confirmação/workflow |
| Amostras | **novo** | — |
| Visitas | **parcial** | `customer-experience` existe; integração Comercial indefinida |
| Análises / cockpit | **existente** | `dashboard-commercial` + `/commercial` |
| Gestão à Vista | **parcial** | GR no `tv-dashboard` (sem atalho no Comercial); painéis/conteúdo a definir |

---

## 9. Riscos de sobreposição

1. **Duas “propostas”:** `/commercial/proposals` (OV dashboard) vs `/propostas-comerciais` (documento ativo). Documentar no UX e no dicionário.
2. **Carteira:** canônica em commercial-api; não dual-write com schema legado após cutover.
3. **Shell sem runtime de módulo:** não inventar `RouteDelegate` local; plugins continuam independentes até F3–F4.
4. **HTTPS / Mixed Content:** nunca depender de redirect slash do FastAPI atrás de TLS — paths relativos + `redirect_slashes=False` na commercial-api.

---

## 10. Referências de código

| Área | Path |
|---|---|
| Portal Comercial MFE | `plugins/commercial/` |
| commercial-api | `commercial-api/commercial_app/` |
| Commercial router (KPIs) | `api-delpi/app/interface/http/routes/commercial/` |
| Pedidos router (TOTVS + legado) | `api-delpi/app/interface/http/routes/pedidos_venda_abertos/` |
| Propostas controller | `api-delpi/app/interface/http/propostas_comerciais_controller.py` |
| Use cases commercial | `api-delpi/app/application/use_cases/commercial/` |
| TOTVS commercial repos | `api-delpi/app/infrastructure/persistence/totvs/commercial_repositories/` |
| Postgres carteira (legado) | `api-delpi/.../pedidos_venda_abertos/` |
| Compose / volumes | `infra/docker-compose*.yml`, `infra/README-ambiente.md` |
| F2c redirects snippet | `gateway/snippets/commercial-f2c-redirects.conf` |
