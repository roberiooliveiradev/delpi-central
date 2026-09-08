# API-ROUTES — supplies-api e reuso api-delpi

Arquitetura: `MFE → supplies-api → api-delpi | purchase-requests-api | SI | Core`.

Envelope: `{ success, message, data, meta }` alinhado ao Playbook 10.  
Auth: JWT Keycloak. Permission checada no BFF.

Status: `EXISTENTE` (hoje noutro backend) · `COMPOSICAO_BFF` · `NOVO_PROPOSTO` · `BLOQUEADO` · `LEGADO`

---

## A. Rotas novas da supplies-api (produto)

| Method | Path | operationId | Owner | Auth | Permission | Request | Response | Fonte | Cache | Paginação | Filtros | Erros | Consumidor | Status |
|--------|------|-------------|-------|------|------------|---------|----------|-------|-------|-----------|---------|-------|------------|--------|
| GET | `/health` | `get_supplies_api_health` | supplies-api | público | — | — | `{status}` | local | no | no | — | 5xx | k8s/compose | NOVO_PROPOSTO |
| GET | `/ready` | `get_supplies_api_ready` | supplies-api | público | — | — | deps | PG+http | no | no | — | 503 | compose | NOVO_PROPOSTO |
| GET | `/me/capabilities` | `get_supplies_capabilities` | supplies-api | JWT | `supplies.access` (ou alias) | — | `{ capabilities, allowedUnits }` | Core perms + catálogo unidades | no | no | — | 401 | MFE shell | NOVO_PROPOSTO |
| GET | `/home/attention` | `get_supplies_home_attention` | supplies-api | JWT | access | branch? | cards alerta | composição | curto | no | branch | 403 filial | WF-01 | COMPOSICAO_BFF |
| GET | `/analytics/overview` | `get_supplies_overview` | supplies-api | JWT | analytics.view | período, branch | 6–8 KPIs + meta SI | api-delpi + SI | curto | no | branch dates | 403 | WF-02 | COMPOSICAO_BFF |
| GET | `/purchase-requests` | `list_portal_purchase_requests` | supplies-api | JWT | purchase-requests.view | query contrato SC | lista | **PR-api C1** / PG C2 | no | sim | contrato 0.2 | 403 fail-closed | WF-04 | COMPOSICAO_BFF |
| GET | `/purchase-requests/{branch}/{number}` | `get_portal_purchase_request` | idem | JWT | view | — | detalhe | PR-api | no | — | — | 404 | WF-04 | COMPOSICAO_BFF |
| GET | `/inventory/stock-value` | `get_portal_stock_value` | supplies-api | JWT | inventory **ou** analytics | query | data | `get_supplies_stock_value` | conforme api-delpi | — | branch location | 403 | WF-15 | COMPOSICAO_BFF |
| GET | `/safety-stock/summary` | `get_portal_safety_stock_summary` | supplies-api | JWT | inventory.view | query ESTSEG | data | `get_supplies_safety_stock_summary` | — | — | filial | 403 | WF-16 | COMPOSICAO_BFF |
| GET | `/safety-stock/items` | `list_portal_safety_stock_items` | idem | JWT | inventory.view | query | paged | api-delpi | — | sim | — | 403 | WF-16 | COMPOSICAO_BFF |
| GET | `/suppliers/{code}/{store}` | `get_portal_supplier_360` | supplies-api | JWT | suppliers.view | branch? | composição | SA2 + OTD + PCs + qualidade HTTP | curto | — | — | 404 | WF-10 | COMPOSICAO_BFF |
| GET | `/products/{code}` | `get_portal_product_360` | supplies-api | JWT | products.view | branch | composição | products\* + safety-stock | curto | — | — | 404 | WF-13 | COMPOSICAO_BFF |
| GET | `/products/{code}/where-used` | `get_portal_product_where_used` | supplies-api | JWT | products.view | — | parents | `get_product_parents` | — | — | — | 404 | WF-14 | COMPOSICAO_BFF |
| GET/PATCH | `/me/preferences` | `get/patch_supplies_preferences` | supplies-api | JWT | access | body | prefs | PG | no | — | — | 422 | WF-01 | NOVO_PROPOSTO |
| POST | `/tasks` | `create_supply_task` | supplies-api | JWT | access | body | task | PG | no | — | — | 422 | WF-03 | NOVO_PROPOSTO |
| GET | `/tasks` | `list_supply_tasks` | supplies-api | JWT | access | — | paged | PG | no | sim | status | — | WF-03 | NOVO_PROPOSTO |

Demais BFF 1:1 (CPV, OTD, giro, savings, PO-OTD, consumption-analysis, stock-balances, price-history, product purchases): mesmo padrão — **COMPOSICAO_BFF**, operationId `get_portal_*` espelhando o TOTVS, permission da cap, filtros iguais aos atuais.

Admin mappings/scopes: proxy C1 para purchase-requests-api `/admin/*` com `supplies.manage`.

---

## B. Reuso api-delpi (não criar SQL gêmeo)

| Operação | operationId | Domínio | Fonte TOTVS | Uso Portal | Já suficiente? | Gap |
|----------|-------------|---------|-------------|------------|----------------|-----|
| CPV | `get_supplies_cpv` | analytics | SD3 | Overview, WF-20 | Sim | — |
| Giro | `get_supplies_inventory_turnover` | analytics | CPV×SB9 | Overview | Sim | — |
| Savings | `get_supplies_negotiation_savings_summary` | negotiations | Sheets | WF-18 | Sim p/ leitura | edição planilha externa |
| OTD | `get_supplies_otd` | deliveries | recebimentos | WF-02/11 | Sim gerencial | vs BI atraso |
| User email | `get_protheus_user_by_email_route` | mapping | SYS_USR | Admin SC | Sim | oid instável (inventory `stable: false`) |
| PO OTD | `get_supplies_purchase_order_otd` | PO | SC7/SD1 | WF-05/07 | Sim API | sem MFE |
| PO OTD panel | `get_supplies_purchase_order_otd_panel` | PO | | WF-07 | Sim API | UI |
| PO OTD series | `get_supplies_purchase_order_otd_series` | PO | | charts | Sim | UI |
| SC lines | `list_supplies_purchase_request_lines` | SC | SC1 | via PR-api | Sim | escopo CC no PR-api |
| SC by number | `get_supplies_purchase_request_lines` | SC | SC1 | detalhe | Sim | |
| Open coverage | `get_supplies_purchase_requests_open_coverage` | PCP/SC | SC1 ESTSEG | não tomar PCP | Sim p/ PCP | Portal não é dono |
| Linked orders | `list_supplies_purchase_request_recent_linked_orders` | SC | SC7 | detalhe SC | Sim | |
| Linked receipts | `list_supplies_purchase_request_recent_linked_receipts` | SC | SD1 | detalhe SC | Sim | |
| Requesters | `list_supplies_purchase_request_requesters_*` | SC | SYS_USR | filtros | Sim | oid instável |
| ESTSEG * | `get_supplies_safety_stock_*` (8 ops) | inventory | SB* SC* SD* | WF-16/17 | Sim | |
| Stock balances | `get_supplies_stock_balances_items/summary` | inventory | SB2 | WF-15 | Sim | vs BI estoque |
| Stock value | `get_supplies_stock_value` | analytics | SB9 | WF-15/02 | Sim | |
| Third party * | `get_supplies_third_party_materials_*` | beneficiamento | SB6 | **não** no Portal | Sim p/ outro app | FORA_DO_ESCOPO |
| Last purchase | `get_product_last_purchase` | product | SD1 | 360 | Sim | |
| Purchases | `get_product_purchases` | product | | 360 | Sim | |
| Price history | `get_product_purchase_price_history` | product | | WF-19 | Sim | |
| Budget history | `get_product_purchase_budget_history` | product | | P2 | Sim | |
| Suppliers of item | `get_product_suppliers` | product | SA5 | 360 | Sim | |
| Stock item | `get_product_stock` | product | SB2 | 360 | Sim | |
| Parents | `get_product_parents` | product | estrutura | WF-14 | Sim | vs BI |
| RM intelligence | `get_product_raw_material_*` | product | | 360 P1 | Sim | |
| Search part number | `search_products_by_supplier_part_number` | product | | busca Hub P1 | Sim | |
| Exclusive RM catalog | `list_exclusive_raw_materials_catalog` | product | | P2 | Sim | |
| Top products | `get_purchases_top_products` | purchases | | Overview P1 | Sim | |
| Product search | `search_products` | product | SB1 | WF-12 | Sim | |
| Freight links | `get_financial_purchase_freight_links` | financial | SF8 | DEEP_LINK não BFF próprio | Sim | não duplicar |
| SI supplies_* | get_si_indicator_supplies_* | SI via api-delpi/SI | snapshots | Overview | Sim | via SI-api preferencialmente |

**ENDPOINT_NOVO TOTVS:** somente se E1/E9/E8 provar gap (importações, alçadas UI, regra do BI). Checklist `new-api-route-checklist.mdc` + inglês.

---

## C. Erros padrão BFF

| HTTP | Uso |
|------|-----|
| 401 | JWT inválido |
| 403 | cap ou filial |
| 404 | fornecedor/item/SC |
| 409 | task idempotente / conflito |
| 422 | query/body |
| 502/504 | gateway TOTVS timeout |
| 429 | se gateway/rate-limit existir — respeitar |

Paginação: herdada das rotas TOTVS (`page`, `page_size` tiers).
