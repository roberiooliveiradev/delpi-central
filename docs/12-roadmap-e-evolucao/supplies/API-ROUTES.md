# API-ROUTES — supplies-api e reuso api-delpi

> **Revisado em 2026-09-16 contra o código atual.**
> Arquitetura: `MFE → supplies-api → api-delpi | purchase-requests-api | strategic-indicators-api | Core`.
>
> O MFE **não** chama `api-delpi` nem `purchase-requests-api`. Downstreams:
> `supplies-api → api-delpi` (pedidos) e `supplies-api → purchase-requests-api` (solicitações).

Envelope alvo: `{ success, message, data, meta }`.
AuthN: JWT Keycloak.
AuthZ: permissions efetivas resolvidas pelo Core API; não usar lista de permissions dos claims JWT como fonte final.
Target RBAC ([ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md)): rotas normais exigem `supplies.access`; administração exige `supplies.manage`. Unidade é filtro de dados `01`/`02`, não permission. SC do Portal é acompanhamento global via S2S confiável para `purchase-requests-api`. O standalone mantém o RBAC próprio.

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

Capabilities canônicas do Portal:

- `supplies.access`
- `supplies.manage`

Escopo de dados operacional: `01` e `02`. Não há `supplies.unit.*` nem `supplies.purchase-requests.view-all`.

Não espelhar CRUD em permission codes. Qualquer `ANY_OF`/`ALL_OF` precisa ser decisão formal do contrato antes da implementação.

---

## 2. Rotas confirmadas no código atual da supplies-api

| Method | Path | Capability | Fonte | Status |
|---|---|---|---|---|
| GET | `/health` | público | local | **IMPLEMENTADO** |
| GET | `/ready` | público | local + dependências | **IMPLEMENTADO** |
| GET | `/me/capabilities` | `supplies.access` | Core + catálogo de units | **IMPLEMENTADO** |
| GET | `/me/preferences` | `supplies.access` | PG supplies | **IMPLEMENTADO** |
| PATCH | `/me/preferences` | `supplies.access`; `default_branch ∈ allowedUnits` | PG supplies | **IMPLEMENTADO** |
| ~~GET~~ | ~~`/home/attention`~~ | — | removido no HOME-ATTENTION.P3 — não existe fonte canônica de tarefas do usuário e a Home não deve compor pendências operacionais (custo/latência); páginas de destino mantêm seus próprios resumos | **REMOVIDO** |
| GET | `/analytics/overview` | `supplies.access` | `branch` repetido (0, 1 ou N). 0 ou 01+02 = consolidado; uma filial = escopo único. SI: uma chamada `department-indicators`. Série OTD usa a mesma regra (uma filial ou consolidado 01+02). Filial inválida = 422. | **IMPLEMENTADO** |
| GET | `/analytics/otd/series` | `supplies.access` + unit | api-delpi | **IMPLEMENTADO** |
| GET | `/analytics/otd` | `supplies.access` + unit | api-delpi + SI | **IMPLEMENTADO** |
| GET | `/purchase-requests` | `supplies.access` + units + CC | PR-api (`?branch=` repetido, `sort_by`/`sort_dir` allow-list + `overall_stage` owner-local, antes da página). `requester.display_name` = nome oficial Minha DELPI via vínculo `mapped` Core `user_protheus_identities` (S2S batch + directory lookup, ≤2 chamadas/página, soft-fail) | **IMPLEMENTADO_C1** |
| GET | `/purchase-requests/summary` | `supplies.access`; downstream S2S | PR-api `/summary`. `total_requests` = SCs distintas; `total_items` = linhas; `stage_counts`/`buckets` = cabeçalho pelo estágio conservador. Ignora `overall_stage` para manter os demais atalhos. Cap do recorte derivado; acima disso 422 e a lista segue. | **IMPLEMENTADO** |
| GET | `/purchase-requests/{branch}/{number}` | `supplies.access` + unit + resource scope | PR-api | **IMPLEMENTADO_C1** |
| GET | `/purchase-requests/export` | `supplies.access`; downstream S2S; acompanhamento global | PR-api `/export` → CSV default ou `format=xlsx` | **IMPLEMENTADO_C1** |
| GET | `/purchase-requests/cost-centers` | `supplies.access` + units | PR-api facet — `C1_CC`+`CTT_DESC01` no universo autorizado; o filtro explícito não estreita a própria facet | **IMPLEMENTADO** |
| GET | `/purchase-requests/requesters/{pid}/photo?branch=..&date_from=..&date_to=..` | `supplies.access` + units | proxy BFF scope-guarded: pid deve pertencer ao facet `/requesters` da mesma query (escopo CC do caller) → identidade `mapped` → foto S2S Core; UUID/token nunca saem do server; 403 sem unidade; 404 fora do universo/sem vínculo/foto | **IMPLEMENTADO** |
| GET | `/purchase-orders` | `supplies.access` + units | api-delpi `GET /supplies/purchase-orders` | **IMPLEMENTADO** |
| GET | `/purchase-orders/{branch}/{number}` | `supplies.access` + filtro de dados `01`/`02` | api-delpi `GET /supplies/purchase-orders/{branch}/{order_number}` | **IMPLEMENTADO** |
| GET | `/purchase-orders/export` | `supplies.access` + units | api-delpi `GET /supplies/purchase-orders/export` → XLSX no BFF | **IMPLEMENTADO** |
| GET | `/users/{id}/profile` | self portal; terceiro admin | Core + prefs | **IMPLEMENTADO** |
| PATCH | `/users/{id}/profile` | self only + portal | PG prefs | **IMPLEMENTADO** |
| GET | `/users/{id}/related-requests` | `supplies.access` + self\|admin (`_assert_can_view`) + units | SCs do vínculo target: Core `user_ids` lookup → `protheus_user_id` mapped → PR-api `requester_user_id`; `branch` opcional fail-closed; `date_from` explícito; paginação máx 100; `sort_by`/`sort_dir` passthrough; degrade `{error}`/`requester_unmapped`/`identity_lookup_unavailable` | **IMPLEMENTADO** (USERS.PROFILE.S1–S3) |
| GET | `/users/{id}/photo` | `supplies.access` + self\|admin | proxy BFF → Core `person-profiles/{id}/photo` S2S; 404 fail-closed; `Cache-Control: private` | **IMPLEMENTADO** (USERS.PROFILE.S1) |
| GET | `/market-intelligence/filters` | `supplies.access` (sem filtro de unidade — dado de mercado global) | external-data-api `/v1/market-data/catalog` via S2S | **IMPLEMENTADO** (PROC-0076) |
| GET | `/market-intelligence/summary` | `supplies.access` | external-data-api via S2S; média/variação/cobertura/frescor calculados no BFF com `Decimal`; unidade corrigida (`BRL/metric ton` quando convertido, com `native`/`conversion` auditáveis); `freshness` por cadência de publicação do provedor — consulta histórica não vira `stale` | **IMPLEMENTADO** (PROC-0076.R1) |
| GET | `/market-intelligence/series` | `supplies.access` | external-data-api via S2S (janela ≤366 dias chunked); granularidade day/month/year; ponto BRL = observação convertida (nunca taxa sintética); `unit`/`native_unit`/`freshness` no envelope | **IMPLEMENTADO** (PROC-0076.R1) |
| GET | `/market-intelligence/monthly-averages` | `supplies.access` | médias mensais paginadas; `fx_rate` = média PTAX do mês, `null` sem câmbio válido (nunca zero); `partial_reason` distingue `fx_missing` | **IMPLEMENTADO** (PROC-0076.R1) |

A lista acima deve ser atualizada sempre que uma rota for realmente adicionada/removida do runtime. Não promover status por intenção de roadmap.

---

## 3. Contratos futuros por página — ainda não implementados na supplies-api

As rotas abaixo são **alvos de composição** e só entram em implementação quando a página correspondente for promovida segundo o roadmap page-by-page.

| Página / fluxo | Method | Path alvo | Capability | Fonte provável/canônica | Estado |
|---|---|---|---|---|---|
| Pedidos | GET | `/purchase-orders` | `supplies.access` + unit | api-delpi `GET /supplies/purchase-orders` (SC7 aberto + `summary`) | **IMPLEMENTADO** |
| Detalhe pedido | GET | `/purchase-orders/{branch}/{number}` | `supplies.access` + filtro de dados `01`/`02` + resource (universo aberto SC7) | api-delpi `GET /supplies/purchase-orders/{branch}/{order_number}` | **IMPLEMENTADO** |
| Entregas | GET | `/deliveries/late` | `supplies.access` + filtro de dados `01`/`02` | api-delpi `GET /supplies/purchase-order-otd/panel`; BFF+MFE em prod; [P0 freeze](./evidence/e9-wf07-p0-contract-freeze.md); [gate](./evidence/e9-wf07-federated-runtime-gate.md) | **GATE PASS** — recovery redeploy BFF 2026-09-21 |
| Estoque | GET | `/inventory/stock-value` | política a fechar na página | api-delpi stock-value | PLANEJADO |
| Estoque | GET | `/inventory/stock-balances/summary` | `supplies.access` + filtro de dados `01`/`02` | api-delpi `GET /supplies/stock-balances/summary` (`only_positive=false`; Todas=`branch=01&branch=02`) | **IMPLEMENTADO** — GATE E10 **PASS_DEPLOYED** — bundle federado verificado R1; residual `VISUAL=INCONCLUSIVE` ([S4](./evidence/e10-wf15-s4-final-acceptance.md), [R1](./ROADMAP-REBASELINE-R1-20261023.md)) |
| Estoque | GET | `/inventory/stock-balances/items` | `supplies.access` + filtro de dados `01`/`02` | api-delpi `GET /supplies/stock-balances/items` (`only_positive=false`; UM/`null`/`QATU` passthrough) | **IMPLEMENTADO** — GATE E10 **PASS_DEPLOYED** — bundle federado verificado R1; residual `VISUAL=INCONCLUSIVE` ([S4](./evidence/e10-wf15-s4-final-acceptance.md), [R1](./ROADMAP-REBASELINE-R1-20261023.md)) |
| Giro | GET | `/inventory/turnover` | analytics + unit | api-delpi inventory-turnover | PLANEJADO |
| ESTSEG | GET | `/safety-stock/filters` | `supplies.access` + filtro de dados `01`/`02`/`all` | api-delpi `GET /supplies/safety-stock/filters` | **IMPLEMENTADO** — [E11.S1](./E11-S1-SAFETY-STOCK-BFF-IMPLEMENTATION.md); BFF devolve `branch_catalog = OPERATIONAL_UNITS` (ignora `authorized_branches` upstream) |
| ESTSEG | GET | `/safety-stock/summary` | `supplies.access` + filtro de dados `01`/`02`/`all` | api-delpi `GET /supplies/safety-stock/summary` | **IMPLEMENTADO** — [E11.S1](./E11-S1-SAFETY-STOCK-BFF-IMPLEMENTATION.md); `all` repassado (produtor une 01+02) |
| ESTSEG | GET | `/safety-stock/items` | `supplies.access` + filtro de dados `01`/`02`/`all` | api-delpi `GET /supplies/safety-stock/items` (sort 9 campos, page_size ≤ 200) | **IMPLEMENTADO** — [E11.S1](./E11-S1-SAFETY-STOCK-BFF-IMPLEMENTATION.md) |
| ESTSEG detalhe | GET | `/safety-stock/items/{code}/details` | `supplies.access` + filial concreta `01`/`02` | api-delpi `GET /supplies/safety-stock/items/{code}/details` (seções compostas) | **IMPLEMENTADO** — [E11.S1](./E11-S1-SAFETY-STOCK-BFF-IMPLEMENTATION.md) |
| ESTSEG detalhe | GET | `/safety-stock/items/{code}/suppliers` | `supplies.access` + filial concreta `01`/`02` | api-delpi `GET /supplies/safety-stock/items/{code}/suppliers` | **IMPLEMENTADO** — [E11.S1](./E11-S1-SAFETY-STOCK-BFF-IMPLEMENTATION.md) |
| Consumo | GET | `/safety-stock/consumption-analysis/summary` | `supplies.access` + filtro de dados `01`/`02` | api-delpi | PLANEJADO (E12 — fora do escopo E11) |
| Consumo | GET | `/safety-stock/consumption-analysis/items` | `supplies.access` + filtro de dados `01`/`02` | api-delpi | PLANEJADO (E12 — fora do escopo E11) |
| Savings | GET | `/analytics/savings` | analytics + unit | api-delpi + SI | PLANEJADO |
| CPV dedicado | GET | `/analytics/cpv` | analytics + unit | api-delpi | PLANEJADO |
| Fornecedores | GET | `/suppliers` | `supplies.access` (sem filtro de unidade — SA2 compartilhada empresa 01; ver [P2 contract](./SUPPLIERS-P2-CONTRACT-READINESS.md) §3.1/§4) | api-delpi `GET /supplies/suppliers` via S2S individual | **BLOQUEADO** — contrato congelado P2; fila em E10 |
| Fornecedor 360 | GET | `/suppliers/{code}/{store}` | `supplies.access` + resource scoping | api-delpi `GET /integrations/protheus/suppliers/{id}` + PG; Qualidade somente após P-11 | PLANEJADO — fundação contratual em [P2 contract](./SUPPLIERS-P2-CONTRACT-READINESS.md) §6 |
| Nota fornecedor | POST | `/suppliers/{code}/{store}/notes` | `supplies.access` + filtro de dados `01`/`02`/resource/ownership | PG | PLANEJADO |
| Nota fornecedor | PATCH | `/suppliers/{code}/{store}/notes/{note_id}` | `supplies.access` + filtro de dados `01`/`02`/resource/ownership | PG | PLANEJADO |
| Produtos | GET | `/products` | `supplies.access` quando a página existir | api-delpi products | PLANEJADO |
| Produto 360 | GET | `/products/{code}` | `supplies.access` + filtro de dados `01`/`02` quando bloco exigir | api-delpi | PLANEJADO |
| Onde usado | GET | `/products/{code}/where-used` | `supplies.access` quando a página existir | `get_product_parents` | PLANEJADO |
| Histórico preço | GET | `/products/{code}/price-history` | `supplies.access` + filtro de dados `01`/`02` quando aplicável | api-delpi | PLANEJADO |
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

### Inteligência de mercado — códigos dedicados (R1.2)

`EXTERNAL_DATA_USE_NOT_APPROVED` do produtor é mapeado para **503 +
`error.code = "source_use_not_approved"`** — distinto de:

| Cenário | Contrato |
|---|---|
| usuário sem `supplies.access` no Core | 401/403 padrão (AuthN/AuthZ) |
| fonte existe mas uso `internal_display` pendente | 503 `source_use_not_approved` |
| contrato de direitos do produtor não comprovado (V004 pendente/divergente) | 503 `contract_not_ready` |
| fonte/ingestão/storage indisponível | 503 `external_data_unavailable` |
| instrumento desconhecido / sem observações | 404 / `data_status=no_data` |

O bloqueio de licença **nunca** vira 403 de autorização do usuário.
`/filters` expõe `selectable: false` em instrumentos/fontes sem
`internal_display` aprovado — o MFE esconde essas opções e nunca
consulta seus valores; `catalog.display_allowed` no produtor é a fonte
de verdade. Desbloqueio exige decisão institucional + migration aditiva.

**Default-deny (R1.3):** `selectable` só é `true` quando o produtor
envia `display_allowed: true` explícito — campo ausente, `null` ou
inválido em payload de versão anterior é tratado como não-selecionável
(o `default_instrument` nunca aponta para instrumento bloqueado). O MFE
aplica a mesma regra (`selectable === true` apenas).

Mudança de contrato deve seguir a regra canônica de compatibilidade e atualizar producer + consumer + testes + Help/docs quando user-facing.
