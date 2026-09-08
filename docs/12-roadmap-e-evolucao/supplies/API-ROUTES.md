# API-ROUTES — supplies-api e reuso api-delpi

Arquitetura: `MFE → supplies-api → api-delpi | purchase-requests-api | SI | Core`.

Envelope alvo: `{ success, message, data, meta }`.  
AuthN: JWT Keycloak.  
AuthZ: **permissions efetivas resolvidas pelo Core API**, nunca lista de permissions dos claims JWT.

Status: `EXISTENTE` · `COMPOSICAO_BFF` · `NOVO_PROPOSTO` · `BLOQUEADO` · `LEGADO`.

---

## 1. Política de autorização

O BFF resolve authorization em quatro camadas:

```text
capability
  AND unit scope quando houver dado TOTVS
  AND resource scope / ownership
  AND business rule
```

Não espelhar CRUD em permission codes. Ver [ADR-007](./adr/ADR-007-permission-minimization.md).

Capabilities canônicas P0/P1:

- `supplies.portal.access`
- `supplies.purchase-requests.access`
- `supplies.operations.access`
- `supplies.analytics.access`
- `supplies.administration.manage`
- `supplies.purchase-requests.view-all`
- `supplies.purchase-requests.export`
- `supplies.unit.filial-{TOTVS}`

Qualquer regra `ANY_OF`/`ALL_OF` deve ser explícita no contrato; não usar “ou” informal.

---

## 2. Rotas da supplies-api

| Method | Path | operationId | Capability | Unit? | Resource rule | Fonte | Status |
|---|---|---|---|---|---|---|---|
| GET | `/health` | `get_supplies_api_health` | público | não | — | local | NOVO_PROPOSTO |
| GET | `/ready` | `get_supplies_api_ready` | público | não | — | PG + deps HTTP | NOVO_PROPOSTO |
| GET | `/me/capabilities` | `get_supplies_capabilities` | `supplies.portal.access` | não | effective permissions do Core | Core + catálogo units | NOVO_PROPOSTO |
| GET | `/home/attention` | `get_supplies_home_attention` | `supplies.portal.access` | quando card usa TOTVS | omitir cards sem capability/recurso | composição | COMPOSICAO_BFF |
| GET | `/analytics/overview` | `get_supplies_overview` | `supplies.analytics.access` | sim | branch ∈ allowedUnits | api-delpi + SI | COMPOSICAO_BFF |
| GET | `/purchase-requests` | `list_portal_purchase_requests` | `supplies.purchase-requests.access` | sim | escopo CC fail-closed; view-all só amplia CC | PR-api C1 / PG C2 | **IMPLEMENTADO_C1** |
| GET | `/purchase-requests/{branch}/{number}` | `get_portal_purchase_request` | `supplies.purchase-requests.access` | sim | SC deve pertencer ao escopo efetivo | PR-api C1 / PG C2 | **IMPLEMENTADO_C1** |
| GET | `/purchase-requests/export` | `export_portal_purchase_requests` | `access` + `export` + unit | sim | CC via PR-api | PR-api list hop | **IMPLEMENTADO_C1** |
| GET | `/inventory/stock-value` | `get_portal_stock_value` | `supplies.operations.access` **ou política formal `ANY_OF(operations,analytics)`** | sim | branch permitida | api-delpi `get_supplies_stock_value` | COMPOSICAO_BFF |
| GET | `/inventory/stock-balances` | `list_portal_stock_balances` | `supplies.operations.access` | sim | branch permitida | api-delpi stock-balances | COMPOSICAO_BFF |
| GET | `/inventory/turnover` | `get_portal_inventory_turnover` | `supplies.analytics.access` | sim | branch permitida | api-delpi inventory-turnover | COMPOSICAO_BFF |
| GET | `/safety-stock/summary` | `get_portal_safety_stock_summary` | `supplies.operations.access` | sim | branch permitida | api-delpi safety-stock | COMPOSICAO_BFF |
| GET | `/safety-stock/items` | `list_portal_safety_stock_items` | `supplies.operations.access` | sim | branch permitida | api-delpi safety-stock | COMPOSICAO_BFF |
| GET | `/safety-stock/items/{code}` | `get_portal_safety_stock_item` | `supplies.operations.access` | sim | item no recorte | api-delpi safety-stock detail | COMPOSICAO_BFF |
| GET | `/safety-stock/consumption-analysis/summary` | `get_portal_consumption_analysis_summary` | `supplies.operations.access` | sim | branch permitida | api-delpi | COMPOSICAO_BFF |
| GET | `/safety-stock/consumption-analysis/items` | `list_portal_consumption_analysis_items` | `supplies.operations.access` | sim | branch permitida | api-delpi | COMPOSICAO_BFF |
| GET | `/purchase-orders` | `list_portal_purchase_orders` | `supplies.operations.access` | sim | branch permitida | api-delpi PO-OTD/panel | COMPOSICAO_BFF |
| GET | `/purchase-orders/{branch}/{number}` | `get_portal_purchase_order` | `supplies.operations.access` | sim | PC no recorte | api-delpi PO/receipts | COMPOSICAO_BFF |
| GET | `/deliveries/late` | `list_portal_late_deliveries` | `supplies.operations.access` | sim | branch permitida | api-delpi PO-OTD panel | COMPOSICAO_BFF |
| GET | `/analytics/otd` | `get_portal_otd` | `supplies.analytics.access` | sim | branch permitida | api-delpi `get_supplies_otd` | COMPOSICAO_BFF |
| GET | `/analytics/cpv` | `get_portal_cpv` | `supplies.analytics.access` | sim | branch permitida | api-delpi `get_supplies_cpv` | COMPOSICAO_BFF |
| GET | `/analytics/savings` | `get_portal_savings` | `supplies.analytics.access` | sim | branch permitida | api-delpi + SI | COMPOSICAO_BFF |
| GET | `/suppliers` | `search_portal_suppliers` | `supplies.operations.access` | conforme fonte | restringir ao recorte possível | api-delpi / gap SA2 search | BLOQUEADO se busca SA2 faltar |
| GET | `/suppliers/{code}/{store}` | `get_portal_supplier_360` | `supplies.operations.access` | sim para blocos TOTVS | fornecedor/branch no escopo | api-delpi + Qualidade + PG | COMPOSICAO_BFF |
| POST | `/suppliers/{code}/{store}/notes` | `create_supplier_note` | `supplies.operations.access` | sim | fornecedor no escopo; auditoria | PG | NOVO_PROPOSTO |
| PATCH | `/suppliers/{code}/{store}/notes/{note_id}` | `update_supplier_note` | `supplies.operations.access` | sim | ownership/política de equipe + escopo fornecedor | PG | NOVO_PROPOSTO |
| GET | `/products` | `search_portal_products` | `supplies.operations.access` | conforme recorte | — | api-delpi products | COMPOSICAO_BFF |
| GET | `/products/{code}` | `get_portal_product_360` | `supplies.operations.access` | sim para estoque/ESTSEG | branch/item no escopo | api-delpi | COMPOSICAO_BFF |
| GET | `/products/{code}/where-used` | `get_portal_product_where_used` | `supplies.operations.access` | não/derivado da fonte | — | `get_product_parents` | COMPOSICAO_BFF |
| GET | `/products/{code}/price-history` | `get_portal_product_price_history` | `supplies.operations.access` | sim quando aplicável | item no escopo | api-delpi | COMPOSICAO_BFF |
| GET | `/me/preferences` | `get_supplies_preferences` | `supplies.portal.access` | não | próprio usuário | PG | NOVO_PROPOSTO |
| PATCH | `/me/preferences` | `patch_supplies_preferences` | `supplies.portal.access` | default_branch deve estar em allowedUnits | próprio usuário | PG | NOVO_PROPOSTO |
| GET | `/users/{id}/profile` | `get_supplies_user_profile` | self: `supplies.portal.access` · outro: `supplies.administration.manage` | não | self ou admin | Core + PG prefs | NOVO_PROPOSTO |
| PATCH | `/users/{id}/profile` | `patch_supplies_user_profile` | self only + `supplies.portal.access` | default_branch ∈ allowedUnits | só próprio usuário na P0 | PG prefs | NOVO_PROPOSTO |
| GET | `/tasks` | `list_supply_tasks` | `supplies.portal.access` | conforme refs | próprio usuário/equipe permitida | PG | NOVO_PROPOSTO |
| POST | `/tasks` | `create_supply_task` | `supplies.portal.access` + capability do recurso referenciado | sim se ref TOTVS | validar ref + ownership | PG | NOVO_PROPOSTO |
| PATCH | `/tasks/{task_id}` | `update_supply_task` | `supplies.portal.access` + capability do recurso referenciado | sim se ref TOTVS | ownership/equipe + ref autorizada | PG | NOVO_PROPOSTO |
| GET | `/administration/purchase-request-scopes` | `list_purchase_request_scopes` | `supplies.administration.manage` | sim | unidades administradas | PR-api C1 / PG C2 | COMPOSICAO_BFF |
| PATCH | `/administration/purchase-request-scopes/{id}` | `update_purchase_request_scope` | `supplies.administration.manage` | sim | unidade administrada + auditoria | PR-api C1 / PG C2 | COMPOSICAO_BFF |

### Export de SC

A exportação permanece permission separada enquanto houver necessidade de controlar saída de dados em massa:

```text
supplies.purchase-requests.access
AND supplies.purchase-requests.export
AND unit scope
AND CC scope/view-all
```

Se homologação provar que export não exige segregação distinta, ADR-007 permite condensar posteriormente.

---

## 3. Authz do `/me/capabilities`

Resposta conceitual:

```json
{
  "capabilities": {
    "portal": true,
    "purchaseRequests": true,
    "operations": true,
    "analytics": false,
    "administration": false,
    "purchaseRequestsViewAll": true,
    "purchaseRequestsExport": false
  },
  "allowedUnits": ["01"]
}
```

Fonte:

```text
JWT válido
→ Core /me
→ effective permissions
→ aliases temporários + permissions canônicas
→ capabilities + allowedUnits
```

Não derivar permissions finais de claims do JWT.

---

## 4. Reuso api-delpi — não criar SQL gêmeo

| Operação | operationId | Uso Portal | Gap |
|---|---|---|---|
| CPV | `get_supplies_cpv` | Overview/indicadores | — |
| Giro | `get_supplies_inventory_turnover` | Overview | — |
| Savings | `get_supplies_negotiation_savings_summary` | analytics/savings | edição continua externa |
| OTD | `get_supplies_otd` | analytics/OTD | comparar BI atraso |
| PO OTD | `get_supplies_purchase_order_otd` | pedidos/entregas | UI nova |
| PO OTD panel | `get_supplies_purchase_order_otd_panel` | atrasos | UI nova |
| PO OTD series | `get_supplies_purchase_order_otd_series` | charts | UI nova |
| SC lines | `list_supplies_purchase_request_lines` | via PR-api/C2 | escopo CC permanece fora da api-delpi |
| Linked orders/receipts | família purchase-request | detalhe SC | — |
| Safety stock | `get_supplies_safety_stock_*` | WF-16/17 | — |
| Stock balances | `get_supplies_stock_balances_items/summary` | inventory | comparar BI estoque |
| Stock value | `get_supplies_stock_value` | inventory/overview | — |
| Last purchase | `get_product_last_purchase` | produto 360 | — |
| Purchases | `get_product_purchases` | produto 360 | — |
| Price history | `get_product_purchase_price_history` | preço | — |
| Suppliers of item | `get_product_suppliers` | produto 360 | — |
| Stock item | `get_product_stock` | produto 360 | — |
| Parents | `get_product_parents` | onde usado | comparar BI |
| Product search | `search_products` | busca | — |
| Freight links | `get_financial_purchase_freight_links` | deep link | Financeiro continua owner |

Nova rota TOTVS somente após prova de gap e checklist canônico.

---

## 5. Composição resiliente

Rotas compostas como `/analytics/overview`, `/suppliers/{code}/{store}` e `/products/{code}` devem declarar:

- timeout por dependência;
- budget global;
- fan-out paralelo quando seguro;
- política de cache/stale;
- falha parcial explícita;
- correlation id;
- bloco/metadata `unavailable` quando dependência auxiliar falhar.

Exemplo permitido:

```text
CPV OK + OTD OK + stock timeout + SI OK
→ 200 parcial
→ stock indisponível sinalizado
→ restante da página utilizável
```

Exceções:

- falha de authz nunca vira partial success;
- recurso principal inexistente continua 404;
- falha do Core para comprovar autorização deve ser fail-closed.

---

## 6. Erros padrão BFF

| HTTP | Uso |
|---|---|
| 401 | identidade/token inválido |
| 403 | capability, unidade ou recurso negado |
| 404 | recurso inexistente |
| 409 | conflito/idempotência |
| 422 | query/body inválido |
| 502/504 | downstream indisponível/timeout quando a operação não puder ser parcial |
| 503 | serviço de autorização/dependência crítica indisponível |
| 429 | rate-limit existente |

Paginação mantém contrato do downstream quando compatível; qualquer mudança deve ser classificada conforme `contract-evolution-backward-compatibility.mdc`.
