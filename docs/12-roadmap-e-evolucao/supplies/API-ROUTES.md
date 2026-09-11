# API-ROUTES — supplies-api e reuso api-delpi

> **Revisado em 2026-09-10 contra o código atual.**  
> Arquitetura: `MFE → supplies-api → api-delpi | purchase-requests-api | strategic-indicators-api | Core`.

Envelope alvo: `{ success, message, data, meta }`.  
AuthN: JWT Keycloak.  
AuthZ: permissions efetivas resolvidas pelo Core API; não usar lista de permissions dos claims JWT como fonte final.

Status documental:

- `IMPLEMENTADO`: rota confirmada no código atual da `supplies-api`;
- `IMPLEMENTADO_C1`: composição atual via `purchase-requests-api`, antes de C2;
- `PLANEJADO`: contrato alvo documentado, ainda sem rota na `supplies-api`;
- `BLOQUEADO`: falta contrato/evidência material para executar.

A existência de uma rota equivalente na `api-delpi` **não** torna automaticamente a rota BFF `IMPLEMENTADO`.

---

## 1. Política de autorização

```text
capability
AND unit scope quando houver dado TOTVS
AND resource scope / ownership quando aplicável
AND business rule
```

Capabilities canônicas:

- `supplies.portal.access`
- `supplies.purchase-requests.access`
- `supplies.operations.access`
- `supplies.analytics.access`
- `supplies.administration.manage`
- `supplies.purchase-requests.view-all`
- `supplies.purchase-requests.export`
- `supplies.unit.filial-{TOTVS}`

Não espelhar CRUD em permission codes. Qualquer `ANY_OF`/`ALL_OF` precisa ser decisão formal do contrato antes da implementação.

---

## 2. Rotas confirmadas no código atual da supplies-api

| Method | Path | Capability | Fonte | Status |
|---|---|---|---|---|
| GET | `/health` | público | local | **IMPLEMENTADO** |
| GET | `/ready` | público | local + dependências | **IMPLEMENTADO** |
| GET | `/me/capabilities` | `supplies.portal.access` | Core + catálogo de units | **IMPLEMENTADO** |
| GET | `/me/preferences` | `supplies.portal.access` | PG supplies | **IMPLEMENTADO** |
| PATCH | `/me/preferences` | `supplies.portal.access`; `default_branch ∈ allowedUnits` | PG supplies | **IMPLEMENTADO** |
| GET | `/home/attention` | `supplies.portal.access` | composição autorizada | **IMPLEMENTADO** |
| GET | `/analytics/overview` | `supplies.analytics.access` + unit | api-delpi + SI | **IMPLEMENTADO** |
| GET | `/analytics/otd/series` | `supplies.analytics.access` + unit | api-delpi | **IMPLEMENTADO** |
| GET | `/analytics/otd` | `supplies.analytics.access` + unit | api-delpi + SI | **IMPLEMENTADO** |
| GET | `/purchase-requests` | `supplies.purchase-requests.access` + unit + CC | PR-api | **IMPLEMENTADO_C1** |
| GET | `/purchase-requests/{branch}/{number}` | `supplies.purchase-requests.access` + unit + resource scope | PR-api | **IMPLEMENTADO_C1** |
| GET | `/purchase-requests/export` | access + export + unit + CC/view-all | PR-api list hop | **IMPLEMENTADO_C1** |
| GET | `/users/{id}/profile` | self portal; terceiro admin | Core + prefs | **IMPLEMENTADO** |
| PATCH | `/users/{id}/profile` | self only + portal | PG prefs | **IMPLEMENTADO** |

A lista acima deve ser atualizada sempre que uma rota for realmente adicionada/removida do runtime. Não promover status por intenção de roadmap.

---

## 3. Contratos futuros por página — ainda não implementados na supplies-api

As rotas abaixo são **alvos de composição** e só entram em implementação quando a página correspondente for promovida segundo o roadmap page-by-page.

| Página / fluxo | Method | Path alvo | Capability | Fonte provável/canônica | Estado |
|---|---|---|---|---|---|
| Pedidos | GET | `/purchase-orders` | `supplies.operations.access` + unit | api-delpi PO/OTD | PLANEJADO |
| Detalhe pedido | GET | `/purchase-orders/{branch}/{number}` | operations + unit + resource | api-delpi PO/receipts | PLANEJADO |
| Entregas | GET | `/deliveries/late` | operations + unit | api-delpi PO-OTD panel | PLANEJADO |
| Estoque | GET | `/inventory/stock-value` | política a fechar na página | api-delpi stock-value | PLANEJADO |
| Estoque | GET | `/inventory/stock-balances` | operations + unit | api-delpi stock-balances | PLANEJADO |
| Giro | GET | `/inventory/turnover` | analytics + unit | api-delpi inventory-turnover | PLANEJADO |
| ESTSEG | GET | `/safety-stock/summary` | operations + unit | api-delpi safety-stock | PLANEJADO |
| ESTSEG | GET | `/safety-stock/items` | operations + unit | api-delpi safety-stock | PLANEJADO |
| ESTSEG detalhe | GET | `/safety-stock/items/{code}` | operations + unit + item | api-delpi | PLANEJADO |
| Consumo | GET | `/safety-stock/consumption-analysis/summary` | operations + unit | api-delpi | PLANEJADO |
| Consumo | GET | `/safety-stock/consumption-analysis/items` | operations + unit | api-delpi | PLANEJADO |
| Savings | GET | `/analytics/savings` | analytics + unit | api-delpi + SI | PLANEJADO |
| CPV dedicado | GET | `/analytics/cpv` | analytics + unit | api-delpi | PLANEJADO |
| Fornecedores | GET | `/suppliers` | operations; unit conforme fonte | api-delpi / busca fornecedor | **BLOQUEADO** se contrato de busca não estiver comprovado |
| Fornecedor 360 | GET | `/suppliers/{code}/{store}` | operations + unit/resource | api-delpi + PG; Qualidade somente após P-11 | PLANEJADO |
| Nota fornecedor | POST | `/suppliers/{code}/{store}/notes` | operations + unit/resource/ownership | PG | PLANEJADO |
| Nota fornecedor | PATCH | `/suppliers/{code}/{store}/notes/{note_id}` | operations + unit/resource/ownership | PG | PLANEJADO |
| Produtos | GET | `/products` | operations | api-delpi products | PLANEJADO |
| Produto 360 | GET | `/products/{code}` | operations + unit quando bloco exigir | api-delpi | PLANEJADO |
| Onde usado | GET | `/products/{code}/where-used` | operations | `get_product_parents` | PLANEJADO |
| Histórico preço | GET | `/products/{code}/price-history` | operations + unit quando aplicável | api-delpi | PLANEJADO |
| Tasks | GET | `/tasks` | portal + resource scope | PG | PLANEJADO |
| Tasks | POST | `/tasks` | portal + capability do recurso + scope | PG | PLANEJADO |
| Tasks | PATCH | `/tasks/{task_id}` | portal + capability do recurso + ownership | PG | PLANEJADO |
| Administração SC | GET | `/administration/purchase-request-scopes` | administration + unit aplicável | PR-api C1 / PG C2 | PLANEJADO |
| Administração SC | PATCH | `/administration/purchase-request-scopes/{id}` | administration + unit + audit | PR-api C1 / PG C2 | PLANEJADO |

**Regra:** quando uma página for promovida, reler produtores/consumidores e transformar apenas os contratos READY_CONFIRMED/READY_BOUNDED em receita executável. Não implementar em lote esta tabela.

---

## 4. AuthZ e contrato Core

Fonte:

```text
JWT válido
→ Core /me
→ effective permissions
→ capabilities + allowedUnits
→ resource/business scope
```

Para visibilidade de apps/rotas do Portal, o contrato vigente é:

```text
GET /core-api/me
GET /core-api/me/apps  # apps[].routes
```

**Não existe dependência canônica em `/me/routes`.** Documentação/testes futuros devem validar `apps[].routes` em `/me/apps`.

---

## 5. Reuso api-delpi — não criar SQL gêmeo

Antes de criar qualquer rota TOTVS nova, provar gap nas famílias existentes: CPV, OTD, stock value, inventory turnover, savings, PO OTD/panel/series, SC/linked orders/receipts, safety stock, consumption analysis, stock balances, product last purchase/purchases/price history/suppliers/stock/parents/search.

MFE `plugins/supplies` nunca consome `api-delpi` diretamente; a `supplies-api` compõe/adapta o contrato do produto.

---

## 6. Composição resiliente

Rotas compostas devem definir timeout por dependência, budget global, fan-out seguro, política de cache/stale quando aplicável, correlation id e falha parcial explícita.

Falha de AuthZ nunca vira partial success. Recurso principal inexistente continua 404. Falha do Core que impede comprovar autorização deve ser fail-closed.

---

## 7. Erros padrão BFF

| HTTP | Uso |
|---|---|
| 401 | identidade/token inválido |
| 403 | capability, unidade ou recurso negado |
| 404 | recurso inexistente |
| 409 | conflito/idempotência |
| 422 | query/body inválido |
| 502/504 | downstream/timeout quando a operação não puder ser parcial |
| 503 | autorização/dependência crítica indisponível |
| 429 | rate limit existente |

Mudança de contrato deve seguir a regra canônica de compatibilidade e atualizar producer + consumer + testes + Help/docs quando user-facing.
