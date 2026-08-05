# Inventário de ativos — domínio Comercial

> **Status:** baseline factual (ago/2026)  
> **Produto ao usuário:** **Portal Comercial** (`id` técnico `commercial`)  
> **Playbook mestre:** [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)  
> **Fronteiras:** [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)

Este documento lista o que **já existe** no monorepo para o domínio Comercial e o que ainda é lacuna. Serve para evitar reimplementação, orientar a migração do estado Delpi para `commercial-api` e a **paridade** que libera a depreciação de `pedidos-venda-abertos`.

**Destino de produto:** as funcionalidades do Portal do Vendedor (`pedidos-venda-abertos`) serão reimplementadas no **Portal Comercial**; o plugin antigo só é depreciado após o gate § 2.1.1 do playbook.

---

## 1. Plugins MFE

| Plugin `id` | Nome ao usuário | `basePath` | Papel | Consome |
|---|---|---|---|---|
| `dashboard-commercial` | Dashboard Comercial | `/apps/dashboard-commercial` | Cockpit KPIs (ROL, conversão, OTD, novos negócios, propostas OV) | api-delpi `/commercial/*` |
| `pedidos-venda-abertos` | Portal do Vendedor | `/apps/pedidos-venda-abertos` | Legado até paridade; depois **depreciado** | api-delpi + (F2) commercial-api |
| `propostas-comerciais` | Propostas Comerciais | `/apps/propostas-comerciais` | Listagem, detalhe e PDF de propostas ativas | api-delpi `/propostas-comerciais/*` |

**Não existem ainda:** `commercial` (**Portal Comercial**), `commercial-api`.

**Depreciação planejada (após paridade):** `pedidos-venda-abertos` — ver playbook § 2.1.1 / fases F2b–F2c.

### Telas observadas

| Plugin | Páginas / rotas principais |
|---|---|
| `dashboard-commercial` | Dashboard, detalhe proposta OV, OTD painel, OTD linha |
| `pedidos-venda-abertos` | Pedidos, clientes (carteira), detalhe cliente, config vendedores |
| `propostas-comerciais` | Lista, detalhe, export PDF |

Docs locais:

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
| Lê ou escreve estado **Delpi** (Postgres plugins / arquivo de avatar) | **migra** para `commercial-api` (F2) — leitura **e** escrita |

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

### 3.2 Estado Delpi (Postgres / avatar) — **migrar inteiro → commercial-api**

Inclui **CRUD e leituras** cujo dado canônico é Delpi (não TOTVS):

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

Após F2 cutover: MFE chama commercial-api para **todas** as rotas da tabela acima; enriquecimento de cliente (search/enrichment/billing) continua na api-delpi via gateway quando a commercial-api precisar compor resposta.

Permissões atuais: `pedidos-venda-abertos.access`, `pedidos-venda-abertos.admin` (mapear/espelhar na commercial-api na migração).

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

## 6. Persistência Delpi hoje

| Dado | Onde | Migração alvo |
|---|---|---|
| Seller portfolio + customers | Postgres plugins schema via api-delpi | `commercial-api` (F2) |
| Customer avatars (binário + meta) | Disco + Postgres (api-delpi) | `commercial-api` + volume Compose (`persistent-upload-storage`) |
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
| Conta 360 | **parcial** | Check-up no Portal do Vendedor; sem timeline unificada |
| Oportunidades / pipeline | **novo** | — |
| Ofertas / propostas | **parcial** | Dois conceitos OV × proposta ativa; sem SLA de etapas |
| Forecast | **novo** | Metas via SI; forecast declarado ausente |
| Pedidos e entregas | **parcial** | Lista aberta + OTD; sem confirmação/workflow |
| Amostras | **novo** | — |
| Visitas | **parcial** | `customer-experience` existe; integração Comercial indefinida |
| Análises / cockpit | **existente** | `dashboard-commercial` + `/commercial` |
| Gestão à Vista | **parcial** | `tv-dashboard` disponível; painéis Comercial a definir |
| Administração (carteiras) | **parcial** | CRUD na api-delpi → migrar |

---

## 9. Riscos de sobreposição

1. **Duas “propostas”:** `/commercial/proposals` (OV dashboard) vs `/propostas-comerciais` (documento ativo). Documentar no UX e no dicionário.
2. **Carteira hoje na api-delpi:** migrar estado Delpi para commercial-api (F2) e UI para Portal Comercial (F2b) antes de depreciar o plugin legado.
3. **Shell sem runtime de módulo:** não inventar `RouteDelegate` local; plugins continuam independentes até F3–F4.
4. **Docs desalinhadas:** referência rápida api-delpi pode omitir rotas (ex.: `get_commercial_rol_by_customer`) — inventário deste arquivo prevalece até sync.

---

## 10. Referências de código

| Área | Path |
|---|---|
| Commercial router | `api-delpi/app/interface/http/routes/commercial/` |
| Pedidos router | `api-delpi/app/interface/http/routes/pedidos_venda_abertos/` |
| Propostas controller | `api-delpi/app/interface/http/propostas_comerciais_controller.py` |
| Use cases commercial | `api-delpi/app/application/use_cases/commercial/` |
| TOTVS commercial repos | `api-delpi/app/infrastructure/persistence/totvs/commercial_repositories/` |
| Postgres carteira | `api-delpi/app/infrastructure/persistence/plugins/repositories/pedidos_venda_abertos/` |
| Compose / volumes | `infra/docker-compose*.yml`, `infra/README-ambiente.md` |
