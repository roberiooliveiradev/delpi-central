# Factory Supply — Technical Contracts (Documentation 4/5)

> **Status:** contratos técnicos planejados — Documentation 4/5.
> **Escopo:** APIs, rotas, RBAC, persistência PostgreSQL, integrações, idempotência, concorrência, auditoria, observabilidade.
> **Limite:** DOCUMENTATION-ONLY. Nenhum código, rota, migration, tabela, permissão ou pacote foi criado por este documento.
> **Depende de:** `README.md` (Doc 1/5 — produto/arquitetura), `DOMAIN-MODEL.md` (Doc 2/5 — agregado + estados + idempotência), `UX-SPEC.md` (Doc 3/5 — superfícies + Kanban).

**Terminologia:** `PROVEN` = evidência real no working tree (arquivo:linha auditável). `TARGET` = decisão de contrato congelada nesta fase, ainda não implementada. `PLANNED` = plano consistente com convenção, pendente de confirmação. `TO_INVENTORY` = lacuna de evidência que bloqueia congelamento. `FUTURE` = fora do escopo atual, apenas fronteira documentada.

---

## 1. Purpose and status

Este documento traduz o produto (Doc 1/5), o domínio (Doc 2/5) e a UX (Doc 3/5) em **contratos técnicos explícitos**: ownership de backend, superfície HTTP, envelope/erros, idempotência, concorrência, RBAC, persistência PostgreSQL, correlação ERP, auditoria, observabilidade, compatibilidade e rollout.

Nada aqui autoriza implementação. Campos marcados `TO_INVENTORY`/`TO_DESIGN` **não** estão prontos para código.

Invariantes preservados:

```text
BACKEND_REQUIRED = YES
DIRECT_MFE_TO_API_DELPI = NO
LINE_FEEDER_RUNTIME_DEPENDENCY = NO
TOTVS_WRITE_SUPPORT = NO
```

## 2. Accepted architecture

```text
Portal / Minha DELPI
        ↓  JWT (Keycloak, usuário real)
Factory Supply MFE  (plugin factory-supply)
        ↓  HTTPS /apps/factory-supply-api — JWT propagado
Factory Supply Backend/BFF  (factory-supply-api — TARGET)
        ├── Factory Supply PostgreSQL (schema factory_supply — TARGET)
        └── API DELPI  (bearer propagado do usuário — PROVEN pattern)
                ↓
              TOTVS
            READ ONLY
```

- `production-control-api` **não** é dependência. Line Feeder é `PROVEN_REFERENCE_IMPLEMENTATION`.
- O MFE nunca chama `api-delpi` — regra `mfe-own-api-no-direct-api-delpi.mdc`.
- API DELPI é a única fronteira de leitura TOTVS; não escreve nada em nome do Factory Supply.
- Estado operacional (missões, itens, sinais, handoffs, evidências, auditoria, idempotência) é persistido pelo próprio backend no schema dedicado.

## 3. Contract design principles

1. **Domain-owned routes, not UI-shaped routes.** Rotas derivam de invariantes do agregado (Doc 2/5) e das projeções aceitas (Doc 3/5), não de widgets.
2. **Queries coesas por superfície**, não um endpoint por card/kpi.
3. **Comandos semânticos por transição**, nunca `PATCH /mission` genérico com campos mutáveis arbitrários.
4. **Toda escrita material** carrega: AuthZ backend + validação de invariante + ator autenticado + `Idempotency-Key` + `expected_version` + registro de auditoria — na mesma transação do agregado.
5. **HTTP success ≠ business outcome.** Resposta de comando expõe estado resultante, versão resultante e `overall_stage` derivado.
6. **Campos técnicos em inglês** (`english-code-identifiers.mdc`); PT-BR apenas em `message`/locale/UI.
7. **Aditivo por padrão** (`contract-evolution-backward-compatibility.mdc`): breaking change exige bump/explicit flag, nunca silencioso.

## 4. Backend ownership decision

**DECISÃO (TARGET):** Factory Supply possui backend próprio — `factory-supply-api` — um bounded-context API no mesmo padrão de `production-control-api` / `requests-api` / `helpdesk-api`.

**O backend possui:** orquestração de domínio/aplicação do Factory Supply, escritas operacionais, persistência PostgreSQL própria, mediação de AuthZ e filial, idempotência, concorrência otimista, auditoria de domínio, composição de leituras ERP via API DELPI e projeções derivadas para UI (Kanban `overall_stage`, `available_actions`).

**O backend NÃO possui:** verdade de estoque TOTVS, SQL genérico, sequenciamento de PCP, WMS genérico, credenciais ERP no browser, qualquer escrita TOTVS.

**Evidência de convenção:** 19 diretórios `*-api` no monorepo (`production-control-api`, `requests-api`, `supplies-api`, `helpdesk-api`, …), cada um com pacote `{domínio}_app` (domain/application/infrastructure/interface/composition), `migrations/V00N__*.sql` próprias e schema PostgreSQL dedicado.

## 5. Naming decision

| Identificador | Valor congelado | Evidência |
|---|---|---|
| Diretório do backend | `factory-supply-api/` | `PROVEN` — padrão `{domínio}-api` (19 siblings) |
| Pacote Python | `factory_supply_app/` | `PROVEN` — `production_control_app`, `requests_app` |
| Mount HTTP externo | `/apps/factory-supply-api` | `PROVEN` — `PPC_API_BASE = "/apps/production-control-api"` em `plugins/production-control/src/api/httpClient.ts` |
| Prefixo interno de rotas | `/v1` | `TARGET` — precedente `requests-api` (`APIRouter(prefix="/v1")`); production-control usa paths planos; adotamos `/v1` por headroom de evolução |
| Schema PostgreSQL | `factory_supply` | `PROVEN` — `production_control`, `my_requests`, `supplies`, `core_domain` |
| Plugin MFE | `factory-supply` (Doc 1/5) | `TARGET` — manifesto na Doc 5/5/implementação |

Alternativa avaliada e rejeitada: estender `production-control-api`. Motivo: ownership de domínio distinto (Doc 1/5 §correção), Line Feeder segue operacional sem acoplamento, e Factory Supply tem ciclo de vida/consumidores próprios (MFE dedicado + futuro Operator Cockpit).

## 6. Topology

```text
Browser (portal.delpi) — JWT usuário
  └─ plugin factory-supply (MFE)
        fetch /apps/factory-supply-api/v1/**
        ├─ GET  queries  (idempotência N/A)
        └─ POST commands (Idempotency-Key + expected_version)

factory-supply-api (FastAPI — TARGET)
  ├─ PostgreSQL (schema factory_supply, transações de agregado)
  └─ api-delpi (GET somente, Authorization: Bearer <jwt do usuário> — padrão
     PROVEN em DelpiProductionGateway.bearer_authorization_from_context)
        └─ TOTVS (READ ONLY)
```

## 7. MFE/BFF boundary

- MFE consome **somente** `/apps/factory-supply-api/v1/**`.
- O backend emite projeções completas (`overall_stage`, `available_actions`, contagens) — o MFE nunca recombina dimensões de item para derivar estado de missão (correção §5.2 da tarefa, Doc 3/5 §Kanban).
- O MFE traduz erros por `data.code` (estável, inglês) — nunca faz parse de `message` PT.
- O MFE envia `Idempotency-Key` (UUID gerado por intenção de comando, reutilizado em retry) e `expected_version` (da última leitura da missão).

## 8. Response envelope

**DECISÃO (TARGET, convenção PROVEN):** envelope canônico de bounded-context API:

```json
// sucesso — ok(data, message)
{ "success": true,  "message": "…", "data": { … } }

// erro — fail(message, status, data) com code estável em data
{ "success": false, "message": "…", "data": { "code": "version_conflict", "field": "expected_version", "current_version": 7 } }
```

- `PROVEN`: `ok()/fail()` em `production-control-api/production_control_app/core/responses.py` e `requests-api/requests_app/core/responses.py`.
- `PROVEN`: código de erro estável em `data.code` via `ApplicationError(code, status_code, field)` + `_handle()` em `requests-api/requests_app/interface/http/routes/requests_routes.py`.
- **Não** copiar o envelope api-delpi `{success,message,data,meta}`: `meta` existe para chat/tools da api-delpi; bounded APIs usam o envelope simples — manter o padrão do próprio contexto.
- Listas paginadas: `data.items[]` + `data.pagination{page,page_size,total}` (offset) ou `data.next_cursor` (history) — ver §16.

## 9. Error model

Taxonomia estável (`data.code`, inglês, machine-readable). `message` PT-BR para UX; cliente decide por `code`.

| HTTP | `code` | Significado | Retry pelo cliente |
|---|---|---|---|
| 400 | `validation_error` | payload malformado | não (corrigir) |
| 401 | (corpo Keycloak/gateway) | não autenticado | re-login |
| 403 | `branch_access_denied` / `permission_denied` | sem permissão ou filial | não |
| 404 | `mission_not_found` / `item_not_found` | entidade inexistente | não |
| 409 | `state_conflict` | transição inválida no estado atual | não (relê estado) |
| 409 | `version_conflict` | `expected_version` stale | relê e reenvia |
| 409 | `idempotency_conflict` | mesma key, payload diferente | não (nova key = nova intenção) |
| 422 | `idempotency_required` | header ausente em comando | reenviar com key |
| 422 | `domain_rule_violation` | invariante de domínio (ex.: qty<0, unidade divergente) | não |
| 502/503 | `downstream_unavailable` | api-delpi/TOTVS tecnicamente indisponível (timeout/5xx/conexão) | GET: retry limitado; comando: usuário decide |
| 403 | `downstream_access_denied` | dependência autoritativa negou a leitura (401/403 downstream) — falha de integração/AuthZ, **não** evidência ERP | não — investigar permissão |
| 500 | `internal_error` | inesperado | não |

Evidência: códigos `idempotency_required`, `branch_access_denied` (via `BranchAccessDenied`/`branch_access_error`), `DelpiGatewayError` com `status_code` propagado — todos `PROVEN` em requests-api/production-control-api.

## 10. Idempotency transport

**DECISÃO (TARGET, convenção PROVEN):**

- **Transporte:** header HTTP `Idempotency-Key` — `PROVEN` em `requests-api/requests_app/interface/http/routes/requests_routes.py` (`Header(alias="Idempotency-Key")`, obrigatório em writes → `422 idempotency_required`).
- **Escopo:** `(key, route, actor_user_id)` — mesma key em rota/ator distinto não colide.
- **Storage:** tabela `{schema}.idempotency_keys(key, route, actor_user_id, response_snapshot JSONB, created_at)` — DDL `PROVEN` em `requests-api/migrations/V003__idempotency_keys.sql` e `helpdesk-api/migrations/V003__idempotency_keys.sql`.
- **Request fingerprint (TARGET — congelado como semântica, algoritmo `TO_INVENTORY`):** toda key persistida grava `request_fingerprint` — hash determinístico da **requisição de comando semântica** (campos de domínio do body: comando, parâmetros, quantidades, motivo, `expected_version`), serializada canonicamente. **Exclui** metadados voláteis de transporte (Authorization, request-id, trace). Algoritmo exato (ex.: canonical-JSON + SHA-256) não é congelado — sem precedente PROVEN no repo.
- **Replay:** mesma key + mesma rota + mesmo ator + **mesmo fingerprint** → resposta gravada retornada, **sem** reexecutar transição; resposta marca `data.idempotent_replay: true` (TARGET — marcador aditivo observável sobre o padrão atual).
- **Conflito:** mesma key + mesma rota + mesmo ator + **fingerprint diferente** → `409 idempotency_conflict` — key nova = intenção nova.
- requests-api atual não persiste fingerprint (`PROVEN` — tabela tem só key/route/actor/snapshot) → `TO_INVENTORY`: evoluir a convenção compartilhada `idempotency_keys` vs coluna extra local; schema planejado já reserva a coluna (§39).
- **Retenção:** chaves são registros de deduplicação, não auditoria — retenção à definir (`TO_INVENTORY`, sugestão ≥ 90 dias; auditoria vive em `supply_events`, §31).
- **Semântica pós-timeout:** se o comando comitou e a resposta se perdeu, o retry com a mesma key devolve a resposta gravada → cliente converge para o estado real sem duplicar efeito.
- **GETs puros:** `NOT_APPLICABLE` (Doc 2/5).
- **Observação ERP persistida + sync de sinais:** replay-safe **sem exigir key do cliente** — deduplicação por chave natural (ver §25, §19): mesma evidência ERP observada duas vezes não duplica correlação; mesma necessidade planejada ressincronizada não duplica `demand_signal` ativo.

## 11. Concurrency transport

**DECISÃO (TARGET):** concorrência otimista por versão de agregado.

- `supply_missions.version` (inteiro, monotônico, incrementa em cada transição comitada).
- Todo comando de transição exige `expected_version` no corpo (`{command}` body field — inglês).
- Respostas de leitura (`missions`, `mission detail`, projeções) sempre expõem `version`.
- Stale → `409` + `data:{code:"version_conflict", current_version}`. Cliente relê e decide — **nunca** last-write-wins (gap do Line Feeder explicitamente não copiado).
- `If-Match`/ETag avaliado e rejeitado: **sem precedente no repositório** (nenhum uso em `*-api`), e `expected_version` no corpo é mais ergonômico para clientes JSON de comando. Alinhado a `platform-data-persistence.mdc` §Concorrência (`optimistic lock/version` é a estratégia listada).
- Itens não versionam separadamente: a versão do **agregado** protege missão+itens (mesma fronteira de consistência do Doc 2/5).

## 12. Time and branch semantics

- **Storage:** `TIMESTAMPTZ` (`PROVEN` convenção — todas as migrations inspectadas usam `TIMESTAMPTZ`).
- **API:** ISO 8601 com offset (`2026-09-30T14:30:00-03:00`); `need_window` como par `{need_window_start, need_window_end}` de instants. `date-only` apenas onde semântica for "dia civil" (ex.: `next periods` por dia) — documentado por campo.
- **Filial:** campo `branch` (2 chars, `"01"|"02"`) transportado em **query param** (GET) e **body field** (comando) — convenção `PROVEN` (`line_feeder_routes.py` usa `branch: Query`/`body.branch`). Nunca `X-Branch` header implícito.
- Browser informa `branch`; backend **valida** contra permissão `.view.filial-*`/escopo do ator — branch fornecido **nunca** é autoridade (§20).
- Comparações de urgência/janela usam instant; fuso de exibição é responsabilidade da UI, nunca da regra.

## 13. Route taxonomy

Categorias (não 1:1 com widgets):

| Categoria | Rotas | Natureza |
|---|---|---|
| Visão geral | 1 | query agregada (KPIs/contagens) |
| Missões | 2 | lista paginada + detalhe de agregado |
| Projeção Kanban | via `GET /missions?projection=kanban` | query derivada |
| Necessidades | 2 | signals ativas + próximos períodos |
| Almoxarifado | 1 | work queue item-grão (`group_by` opcional) |
| Minha coleta | 1 | missões do ator em fase de coleta |
| Devoluções | 1 | worklist de itens com dimensão return |
| Histórico | 2 | histórico operacional (cursor) + trilha da missão |
| Catálogos de filtro | 1 | metadados de filtro coesos |
| Comandos de missão/item | 12 | writes semânticos |
| Sincronização de sinais | 1 | replay-safe |
| Evidência ERP | 1 | refresh de correlação |

## 14. Command model

Somente comandos justificados por Doc 2/5 (transições das dimensões) + Doc 3/5 (ações das superfícies). Cada comando: `POST` semântico, `Idempotency-Key`, `expected_version`, `branch` no body, permissão dedicada, auditoria obrigatória. Resposta: `{mission, items, overall_stage, version, available_actions}` resultante.

| Command | Path | Permissão | Pós-condição |
|---|---|---|---|
| `request_supply_material` | POST `/v1/missions/request-material` | `factory-supply.missions.request` | missão criada (ou vinculada — §29) com itens requisitados; auditoria `request` |
| `plan_supply_mission` | POST `/v1/missions/{id}/plan` | `factory-supply.missions.manage` | destino/janela/atribuição confirmados; missão entra no funil |
| `replan_supply_mission` | POST `/v1/missions/{id}/replan` | `factory-supply.missions.manage` | campos alterados + rastro de replanejamento |
| `cancel_supply_mission` | POST `/v1/missions/{id}/cancel` | `factory-supply.missions.manage` | `lifecycle=cancelled` + motivo; itens travam |
| `close_supply_mission` | POST `/v1/missions/{id}/close` | `factory-supply.missions.manage` | `lifecycle=closed` se invariantes de fechamento ok |
| `start_item_preparation` | POST `/v1/missions/{id}/items/{item_id}/start-preparation` | `factory-supply.preparation.manage` | item dimensão prep → in_progress |
| `record_item_preparation` | POST `/v1/missions/{id}/items/{item_id}/record-preparation` | `factory-supply.preparation.manage` | `prepared_qty` registrada (parcial permitida) |
| `record_item_collection` | POST `/v1/missions/{id}/items/{item_id}/record-collection` | `factory-supply.collection.manage` | `collected_qty` + handoff implícito armazém→alimentador |
| `record_item_handoff` | POST `/v1/missions/{id}/items/{item_id}/record-handoff` | `factory-supply.collection.manage` | handoff alimentador→CT aceito/pendente |
| `record_item_delivery` | POST `/v1/missions/{id}/items/{item_id}/record-delivery` | `factory-supply.delivery.confirm` | `delivered_qty` + recebido_por CT |
| `record_item_return` | POST `/v1/missions/{id}/items/{item_id}/record-return` | `factory-supply.returns.manage` | `returned_qty` + motivo + handoff→armazém |
| `sync_supply_demand_signals` | POST `/v1/demand-signals/sync` | **SERVICE** `factory-supply.service.demand-sync` (§40-B — não é permissão de usuário) | signals ativas atualizadas de forma replay-safe |
| `refresh_item_erp_evidence` | POST `/v1/missions/{id}/items/{item_id}/erp-evidence/refresh` | **SERVICE** `factory-supply.service.erp-evidence-reconcile` (§40-B; gatilho interativo opcional `TO_INVENTORY`) | observação ERP deduplicada persistida |

Notas: `record-collection` cobre "iniciar coleta" — a primeira coleta registrada marca a dimensão em progresso (não inventar comando separado sem justificativa). Quantidade de retorno pode ser `null` quando não estabelecida (Doc 3/5 — `RETURN_QUANTITY_RULE = TO_INVENTORY`).

## 15. Query model

| Query | Path | Conteúdo | Paginação |
|---|---|---|---|
| `get_factory_supply_overview` | GET `/v1/overview` | contagens por estágio/dimensão, KPIs operacionais | — |
| `list_supply_missions` | GET `/v1/missions` | missões + resumo de itens; `projection=kanban` adiciona `overall_stage`+contagens | page/page_size |
| `get_supply_mission` | GET `/v1/missions/{id}` | agregado completo: missão, itens, handoffs, evidências, `version`, `available_actions`, `overall_stage` | — |
| `list_supply_needs` | GET `/v1/needs` | `demand_signals` ativas + vínculo a missão | page/page_size |
| `list_upcoming_supply_needs` | GET `/v1/needs/upcoming` | necessidades agrupadas por período futuro | page/page_size |
| `list_warehouse_work_queue` | GET `/v1/warehouse/work-queue` | itens com trabalho pendente, grão item, `group_by=stage` para board | page/page_size |
| `list_my_collection` | GET `/v1/my-collection` | missões atribuídas ao ator em coleta (modo execução) | page/page_size |
| `list_supply_returns` | GET `/v1/returns` | itens com dimensão return ativa/fechada | page/page_size |
| `list_supply_history` | GET `/v1/history` | eventos operacionais fechados + auditoria | cursor |
| `get_supply_mission_history` | GET `/v1/missions/{id}/history` | trilha da missão (timeline do drawer) | cursor |
| `get_supply_lookup_metadata` | GET `/v1/lookup-metadata` | catálogos de filtro: filiais autorizadas, CTs de destino, estágios, motivos | — |

Todos os GETs aceitam `branch` (obrigatório onde semântica for single-branch) + filtros documentados por rota. Nenhuma rota retorna histórico ilimitado.

## 16. Kanban projection contract

`GET /v1/missions?projection=kanban&branch=01` retorna itens de missão projetados:

```json
{
  "mission_id": "…", "destination": {"work_center": "…", "label": "…"},
  "need_window": {"start": "…", "end": "…"},
  "overall_stage": "ready_for_pickup",
  "item_count": 3, "ready_items": 2, "pending_items": 1, "exception_items": 0,
  "assignment": {"feeder_user_id": "…", "display_name": "…"},
  "partial": true, "has_return": false,
  "urgency": {"due_at": "…", "overdue": false},
  "available_actions": ["record_item_collection", "replan_supply_mission"],
  "version": 7
}
```

- **`overall_stage` é derivado pelo backend** — enum fechado `a_preparar|em_preparo|pronto_para_retirada|em_coleta|entregue` (labels PT na UI; valores técnicos EN: `to_prepare|preparing|ready_for_pickup|collecting|delivered`). Owner da derivação: serviço de aplicação/domínio do Factory Supply — algoritmo determinístico sobre dimensões de item, especificado na implementação; o frontend nunca reimplementa (correção §5.2).
- `closed`/`cancelled` não aparecem no board. `has_return` é badge, não coluna.
- **Sem soma de quantidades de unidades incompatíveis** — contagens são de **itens** (inteiros), nunca de quantidade.

## 17. Mission contract

Campos do agregado expostos (detalhe e listas):

`mission_id`, `branch`, `destination{work_center, label}`, `need_window{start,end}`, `production_context{op_order, operation_seq, product}`, `assignment{feeder_user_id, display_name}`, `collection_round_ref?`, `lifecycle_status(draft|planned|in_progress|completed|closed|cancelled)`, `overall_stage`, `available_actions[]`, `version`, `created_at/by`, `closed_at?`, `cancel_reason?`.

## 18. Item contract

`item_id`, `product_code`, `product_description_snapshot`, `unit`, quantidades por dimensão `{required, requested, prepared, collected, delivered, returned}` (decimal + unit, `null` onde não estabelecida), status por dimensão (`pending|in_progress|done|partial|blocked`), `erp_evidence{status, matched_ref?, observed_at}` (§26), `pickup_location_snapshot?`, `exception?`, `version` herda da missão.

## 19. Demand signal contract

`signal_id`, `signal_key` (chave natural de dedup: branch×op×operação×material×janela×fonte), `source (scheduled_operation|operator_request)`, `branch`, `work_center`, `op_order`, `operation_seq`, `material`, `unit`, `qty_needed`, `need_at`, `status(active|superseded|linked)`, `synced_at`, `mission_link{mission_id,item_id}?`.

Sync (§14) regrava estado por `signal_key`: ativo existente com mesmo fingerprint → update; inexistente na fonte nova → `superseded`; nunca duplica ativo (Doc 2/5 idempotência).

## 20. Handoff/collection/delivery contract

`handoff` é fato separado do agregado (Doc 2/5): `{handoff_id, mission_item_id, direction(collection|delivery|return), from_actor_user_id, to_actor_user_id?, to_context(warehouse|work_center), qty, unit, at, note?}`. Comandos `record-collection`/`record-delivery`/`record-return` criam handoffs na mesma transação do agregado — **não** expor `POST /handoffs` genérico.

## 21. Actor identity

- Persistido: `actor_user_id` = `user.id ?? user.sub` (estável) — `PROVEN` (`requests_permissions.py`: `id or sub`; `idempotency_keys.actor_user_id`).
- Snapshot de exibição: `actor_display_name` = `user.name ?? user.email` — `PROVEN` mesma fonte.
- **Nunca** persistir JWT, token, claims completas ou email como identidade primária.

## 22. PostgreSQL ownership

| Decisão | Valor | Evidência |
|---|---|---|
| Schema | `factory_supply` | `TARGET` — convenção 1-schema-por-api `PROVEN` |
| PKs | `UUID DEFAULT gen_random_uuid()` | `PROVEN` (idempotency_keys, line_feeder) |
| Branch | coluna `branch VARCHAR(2) NOT NULL` em toda tabela de fatos | `TARGET` — convenção de filtro por filial `PROVEN` |
| Timestamps | `TIMESTAMPTZ DEFAULT NOW()` | `PROVEN` |
| Version | `INT NOT NULL DEFAULT 1` em `supply_missions` | `TARGET` — strategy `optimistic lock` em platform-data-persistence |
| Ator | `actor_user_id`/`created_by VARCHAR(100)` + display snapshot | `PROVEN` |
| FKs entre contextos | proibidas — API DELPI referenciada por identificadores/snapshots | `platform-data-persistence` |

## 23. Physical persistence model

Matriz completa em §39. Resumo do desenho (8 tabelas, sem tabela-por-classe mecânica — Abstraction Gate):

1. `supply_missions` — raiz do agregado (branch, destino, janela, contexto, atribuição, lifecycle, version, timestamps, atores).
2. `supply_mission_items` — itens (FK mission CASCADE lógico, material, unit, 6 quantidades, status por dimensão, snapshots de decisão, exceção).
3. `demand_signals` — necessidades (signal_key UNIQUE parcial ativo, fonte, dedup).
4. `mission_demand_links` — vínculo signal↔(mission,item) — justificado pela reconciliação §29.
5. `handoffs` — cadeia de custódia item-nível (direction enum, atores, qty, ts).
6. `erp_observations` — evidência ERP por item (status enum, matched ref, payload snapshot bounded, observed_at; UNIQUE (item_id, evidence_fingerprint) para dedup).
7. `supply_events` — auditoria append-only (ação, ator, prev→new, qty delta, motivo, idempotency_key, correlation_id).
8. `idempotency_keys` — convenção `PROVEN`.

Retorno: dimensão `returned` no item + handoffs `direction=return` + eventos — **sem** `return_records` separada (retorno não é fórmula; é quantidade + motivo + custódia).

## 24. Historical ERP snapshots

Snapshots permitidos como **evidência de decisão** (não verdade corrente): `product_description`, `unit`, `pickup_location`, `stock_at_decision`, `committed_at_decision`, `planned_ct`, `planned_need_at`. Prefixo `_snapshot`/`_at_decision` torna explícito. **Proibido** tratá-los como inventário atual — leituras correntes sempre via API DELPI (sem shadow inventory).

## 25. ERP correlation

- Rota de leitura autoritativa: `get_product_internal_movements` (`/products/{code}/internal-movements`) — `PROVEN`.
- Correlação determinística por composição: `branch × product × qty × janela ± tolerância × destino/origem × tipo de movimento`. **Sem inferência LLM.**
- Se a resposta de movimentos expuser ID estável de movimento → usar direto (`TO_INVENTORY` — campo a confirmar; se ausente, fingerprint composto persistido em `erp_observations.evidence_fingerprint` com `confidence` resultante `high|medium` documentado).
- Deduplicação: UNIQUE `(mission_item_id, evidence_fingerprint)` — reobservação do mesmo fato não duplica correlação nem efeito operacional.

## 26. ERP evidence states

**CONGELADO (corrigido — AuthZ não é evidência):**

| Estado | Definição |
|---|---|
| `matched` | avaliação autoritativa **autorizada** completou e encontrou evidência compatível |
| `not_found` | avaliação autoritativa **autorizada** completou com sucesso e **zero** evidência compatível — factual, nunca erro |
| `unknown` | evidência ainda não avaliada ou informação de correlação insuficiente |
| `unavailable` | fonte autoritativa **não pôde ser avaliada tecnicamente**: timeout, falha de conexão, downstream 5xx, resposta parcial inutilizável — carrega `retryable` + `observed_at` |
| `divergent` | evidência autoritativa existe mas conflita materialmente com o rastro operacional (ex.: qty/direção/tipo) |

**401/403 da api-delpi (ou de qualquer dependência autoritativa) NÃO são estados de evidência ERP.** São falhas de autenticação/autorização/integração: seguem o contrato de erro técnico (§9), fail-closed, observabilidade, e **jamais** persistem `erp_evidence`. Falta de permissão para perguntar ≠ incapacidade da fonte responder.

`timeout/conexão/5xx/parcial/ambíguo` jamais viram `not_found`.

## 27. New API DELPI read contracts

**Inspeção bounded executada (correção):** contratos atuais inspecionados contra cada fato de armazém que o Factory Supply precisa:

| Fato necessário | Contrato existente (PROVEN) | Cobertura |
|---|---|---|
| Armazém de origem por item (onde o saldo físico está) | `get_supplies_stock_balances_items` — campo `warehouse` (B2_LOCAL) + `branch` por linha de saldo | autoritativo |
| Armazém por produto em bloqueio | `list_product_inventory_blocks` — campo `warehouse` por produto (batch) | autoritativo |
| Local físico/bin de retirada | `list_product_physical_locations` — `physical_location` (BZ_MPLOCAL) | autoritativo |
| Contagem/filtro por armazém | `get_supplies_stock_balances_summary` — `warehouse_count` + filtro `warehouse` | autoritativo |
| Códigos de armazém válidos por filial (filtros/catálogo UX) | **composição em factory-supply-api**: distinct dos armazéns observados nos saldos relevantes + config por filial (padrão PROVEN do Line Feeder — `01`/`99` eram config, não catálogo) | server-side, sem nova rota |
| Descrição/nome de armazém | **não existe em nenhum contrato** — e **nenhuma necessidade aceita** (Docs 1–3) exige descrição; códigos TOTVS são exibidos como código | não necessário |

**DECISÃO: `REUSE_AS_IS` — `NEW_API_DELPI_ROUTES_REQUIRED = NO`.** O catálogo `list_warehouses` anteriormente proposto era conveniência de consumidor, não fato autoritativo faltante; composition no BFF + config por filial resolvem. Se uma necessidade futura provar lacuna autoritativa real (ex.: descrição de armazém exigida por regulamento), abre-se rota tipada — nunca SQL genérico.

Demais necessidades: `REUSE_AS_IS` ou `EVOLVE_EXISTING` (§41/§38). Nenhuma rota com nome/conceito Factory Supply na api-delpi.

## 28. Operator Cockpit future integration

**Contrato semântico futuro (FUTURE, não implementar):** Cockpit → `POST /v1/missions/request-material` (o mesmo comando, com `source=operator_cockpit` + `correlation_ref`). Payload: `{branch, op_order, operation_seq, work_center, items[{product_code, qty, unit}], requested_at, reason, source, correlation_ref}` + `Idempotency-Key` gerado pelo Cockpit por intenção.

- Factory Supply valida AuthZ/domínio — Cockpit nunca autoriza.
- Resposta: `request_accepted`, `correlated_mission_id?`, estado corrente.
- Contexto autoritativo prefilled pelo Cockpit; necessidade planejada vs pedido humano permanecem fatos distintos (Doc 1/5 invariante).

## 29. Duplicate-request reconciliation

Propriedade da reconciliação: **aplicação/domínio do Factory Supply**, não do Cockpit nem do MFE.

- Pedido humano chega → compara com `demand_signals`/`mission_items` ativos na mesma `(branch, work_center, material, unit, janela compatível)`.
- **TO_INVENTORY (decisão de negócio pendente):** vínculo ao item existente (`mission_demand_links` + marcação `operator_requested`) vs quantidade adicional. O schema suporta ambos — a escolha de semântica **não** foi inventada aqui; Doc 5/5 deve registrar a decisão de produto antes do código.
- O que está congelado: **nunca** dobrar quantidade silenciosamente; todo pedido gera fato auditável próprio.

## 30. Line Feeder coexistence/cutover

- `LINE_FEEDER_RUNTIME_DEPENDENCY = NO`. Zero chamadas/importações de `production-control-api`.
- Line Feeder permanece operacional e intacto; suas tabelas `production_control.*` **não** são fonte do Factory Supply nem recebem escrita cruzada.
- Sem dual-write, sem migração silenciosa. Cutover só após paridade funcional + aceite de produto + migração explícita aprovada (Doc 5/5 sequencia).
- Grão per-product do V007 **não** reutilizado — Factory Supply preserva mission+item com rastreabilidade por destino/CT.
- Última-milha: permissões distintas (`factory-supply.*` vs `production-control.*`) impedem confusão de ownership.

## 31. Audit

Auditoria de domínio ≠ log técnico. `supply_events` append-only:

`{event_id, mission_id, item_id?, event_type(command|transition|erp_observation|signal_sync), action, actor_user_id, actor_display_name, prev_state?, new_state?, qty_delta?, reason?, idempotency_key?, request_id?, correlation_id?, created_at}`.

- Gravado na **mesma transação** do agregado — transição sem evento não existe.
- Append-only lógico; nunca update/delete (retenção: integral — rastreabilidade é o produto).
- Logs de aplicação não são auditoria.

## 32. Observability

Conforme `platform-reliability-observability.mdc`/`observability-standards.mdc`:

- Logs estruturados: `request_id`, `operation_id`, `route`, `actor_user_id`, `branch`, `duration_ms`, outcome; sem tokens/segredos/payloads ERP sensíveis.
- Correlation ID propagado MFE→BFF→api-delpi (`X-Request-Id`/traceparent conforme gateway — `TO_INVENTORY` convenção exata de header no gateway atual).
- Métricas: latência/erro por rota; latência+taxa de erro da api-delpi por operationId; contagem por `erp_evidence.status`; `version_conflict` rate; `idempotent_replay` rate; `idempotency_conflict` count; signals sync result (created/updated/superseded).
- Métricas operacionais ≠ scoring de trabalhador (Doc 1/5).
- Tracing ponta a ponta desejável — `TARGET` alinhado ao que a plataforma já fizer (sem inventar stack nova).

## 33. Events/notifications gate

```text
EVENT_BUS_REQUIRED_NOW = NO
OUTBOX_REQUIRED_NOW   = NO
```

Comando síncrono + auditoria transacional cobrem os fluxos atuais; não existe consumidor assíncrono real hoje. Candidatos `FUTURE_CONSUMER_EVENT` (pronta→alimentador, pedido→almoxarifado, exceção, devolução requerida) ficam em `supply_events` — um consumidor futuro lê do audit ou de outbox se/adicionar broker real com owner+consumer+semântica de entrega justificados. Precedente existe quando necessário: `requests-api/migrations/V005__integration_outbox.sql` (`PROVEN`) — adotar **somente** quando um consumidor assíncrono real existir.

## 34. Migration strategy

- Diretório próprio `factory-supply-api/migrations/V00N__descricao.sql`, runner no startup do app (`PROVEN` — `run_migrations_on_startup()` em production-control-api lifespan).
- Append-only; arquivos aplicados imutáveis (`migrations-immutable-checksum.mdc`); produção sem reset (`plugins-migrations-no-reset-prod.mdc`).
- Expand-and-contract para breaking; backfill grande separado/observável.
- `V001__factory_supply_schema.sql` = criação do schema + tabelas §23 (conteúdo a detalhar na implementação — **não** criar nesta fase).
- Rollback = rollforward por nova migration quando já aplicada.

## 35. Multi-filial constraints

- `filial-01` (SC) e `filial-02` (ES) `PROVEN` no RBAC/manifesto (`production-control.view.filial-01|02`, `{BRANCH}_VIEW_PERMS`).
- Códigos de armazém (`01`,`99`) observados no Line Feeder são **config por filial**, não constantes globais — Factory Supply não hardcoda; resolve por contrato/config e catálogo (§27).
- Toda linha persistida é `branch`-scoped; queries sempre filtram filial autorizada no servidor.

## 36. Security

- Credenciais só no backend; JWT do usuário propagado à api-delpi (`bearer_authorization_from_context` `PROVEN`) — sem service-account nova nesta fase (`TO_INVENTORY` se syncs agendados exigirem S2S).
- Sem segredo ERP no MFE; sem JWT/claims como autoridade final — permissões avaliadas server-side a cada request.
- Writes fail-closed (sem permissão → 403; sem key → 422; sem versão → 422/400).
- Branch fail-closed (`branch_access_denied`).
- `TOTVS_WRITE_SUPPORT = NO` — não desenhar credencial de escrita TOTVS.

## 37. Fan-out/batching/cache

- Batch `PROVEN` contra N+1: `list_production_order_operation_materials_batch` (`/production/orders/operation-materials/batch`) — sync de sinais e projeções **obrigatório** usar batch, nunca 1 HTTP/card.
- `get_supplies_stock_balances_items` aceita filtros (product list, warehouse) — usar filtrado, não varredura.
- `list_product_physical_locations`/`inventory-blocks`: lookup por conjunto de produtos da página.
- Concorrência de fan-out limitada; timeout+retry limitado em GETs (`http-integration-resilience.mdc`).
- Cache: autoritativo corrente = sempre api-delpi (sem cache semântico v1). Se cache operacional curto for necessário: TTL curto + `stale:true`/`as_of` na resposta + fail-closed para decisões de saldo (Doc 2/5: criação fail-closed quando saldo indisponível). `TO_DESIGN` — não congelado.

## 38. Complete route catalog

Base FS: `/apps/factory-supply-api/v1` — todas `PLANNED_NEW`. api-delpi paths `PROVEN` via `delpi_production_gateway.py` + `route_contract_registry.py`.

| # | Owner | Método | Path | operationId | R/W | Permissão | Idemp. | Conc. | Paginação | Deps ERP | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FS | GET | `/v1/overview` | get_factory_supply_overview | R | .view | N/A | — | — | nenhum (projeção local) | PLANNED_NEW |
| 2 | FS | GET | `/v1/missions` | list_supply_missions | R | .view | N/A | — | page | nenhum | PLANNED_NEW |
| 3 | FS | GET | `/v1/missions/{id}` | get_supply_mission | R | .view | N/A | — | — | opcional (evidence) | PLANNED_NEW |
| 4 | FS | GET | `/v1/needs` | list_supply_needs | R | .view | N/A | — | page | sinais já sincronizados | PLANNED_NEW |
| 5 | FS | GET | `/v1/needs/upcoming` | list_upcoming_supply_needs | R | .view | N/A | — | page | sinais | PLANNED_NEW |
| 6 | FS | GET | `/v1/warehouse/work-queue` | list_warehouse_work_queue | R | .view | N/A | — | page | nenhum | PLANNED_NEW |
| 7 | FS | GET | `/v1/my-collection` | list_my_collection | R | .view | N/A | — | page | nenhum | PLANNED_NEW |
| 8 | FS | GET | `/v1/returns` | list_supply_returns | R | .view | N/A | — | page | nenhum | PLANNED_NEW |
| 9 | FS | GET | `/v1/history` | list_supply_history | R | .view | N/A | — | cursor | nenhum | PLANNED_NEW |
| 10 | FS | GET | `/v1/missions/{id}/history` | get_supply_mission_history | R | .view | N/A | — | cursor | nenhum | PLANNED_NEW |
| 11 | FS | GET | `/v1/lookup-metadata` | get_supply_lookup_metadata | R | .view | N/A | — | — | CTs/warehouses via api-delpi | PLANNED_NEW |
| 12 | FS | POST | `/v1/missions/request-material` | request_supply_material | W | .missions.request | KEY | — | — | valida produto/CT | PLANNED_NEW |
| 13 | FS | POST | `/v1/missions/{id}/plan` | plan_supply_mission | W | .missions.manage | KEY | EV | — | — | PLANNED_NEW |
| 14 | FS | POST | `/v1/missions/{id}/replan` | replan_supply_mission | W | .missions.manage | KEY | EV | — | — | PLANNED_NEW |
| 15 | FS | POST | `/v1/missions/{id}/cancel` | cancel_supply_mission | W | .missions.manage | KEY | EV | — | — | PLANNED_NEW |
| 16 | FS | POST | `/v1/missions/{id}/close` | close_supply_mission | W | .missions.manage | KEY | EV | — | — | PLANNED_NEW |
| 17 | FS | POST | `/v1/missions/{id}/items/{iid}/start-preparation` | start_item_preparation | W | .preparation.manage | KEY | EV | — | — | PLANNED_NEW |
| 18 | FS | POST | `/v1/missions/{id}/items/{iid}/record-preparation` | record_item_preparation | W | .preparation.manage | KEY | EV | — | — | PLANNED_NEW |
| 19 | FS | POST | `/v1/missions/{id}/items/{iid}/record-collection` | record_item_collection | W | .collection.manage | KEY | EV | — | — | PLANNED_NEW |
| 20 | FS | POST | `/v1/missions/{id}/items/{iid}/record-handoff` | record_item_handoff | W | .collection.manage | KEY | EV | — | — | PLANNED_NEW |
| 21 | FS | POST | `/v1/missions/{id}/items/{iid}/record-delivery` | record_item_delivery | W | .delivery.confirm | KEY | EV | — | — | PLANNED_NEW |
| 22 | FS | POST | `/v1/missions/{id}/items/{iid}/record-return` | record_item_return | W | .returns.manage | KEY | EV | — | — | PLANNED_NEW |
| 23 | FS | POST | `/v1/demand-signals/sync` | sync_supply_demand_signals | W | SERVICE .service.demand-sync | NATURAL | — | — | machine-load + materials batch | PLANNED_NEW |
| 24 | FS | POST | `/v1/missions/{id}/items/{iid}/erp-evidence/refresh` | refresh_item_erp_evidence | W | SERVICE .service.erp-evidence-reconcile | NATURAL | — | — | internal-movements | PLANNED_NEW |

(KEY = `Idempotency-Key` obrigatório + `request_fingerprint` persistido; NATURAL = dedup por chave natural; EV = `expected_version`; SERVICE = capacidade interna/serviço §40-B — não exposta como permissão de usuário no manifesto.)

| Owner | operationId | Path (PROVEN) | Uso FS | Status |
|---|---|---|---|---|
| api-delpi | get_production_pcp_orders_items | /production/pcp-orders/items | catálogo OPs abertas → contexto produção | REUSE_AS_IS |
| api-delpi | get_production_order_by_op | /production/orders/{op} | detalhe OP | REUSE_AS_IS |
| api-delpi | get_production_machine_load_operations | /production/machine-load/operations | operações agendadas → sinais + janela | REUSE_AS_IS |
| api-delpi | get_production_machine_load_work_centers | /production/machine-load/work-centers | catálogo CTs destino | REUSE_AS_IS |
| api-delpi | list_production_order_operation_materials | /production/orders/{o}/operations/{s}/materials | materiais+empenho por operação | REUSE_AS_IS |
| api-delpi | list_production_order_operation_materials_batch | /production/orders/operation-materials/batch | fan-out controlado | REUSE_AS_IS |
| api-delpi | get_supplies_stock_balances_items | /supplies/stock-balances/items | saldo por item/armazém → cobertura | REUSE_AS_IS |
| api-delpi | get_product_stock | /products/{code}/stock | saldo pontual por produto | REUSE_AS_IS |
| api-delpi | list_product_physical_locations | /products/physical-locations | local físico de retirada | REUSE_AS_IS |
| api-delpi | list_product_inventory_blocks | /products/inventory-blocks | bloqueios de disponibilidade | REUSE_AS_IS |
| api-delpi | get_product_internal_movements | /products/{code}/internal-movements | evidência de movimento → correlação | EVOLVE_EXISTING (verificar ID estável/fingerprint — TO_INVENTORY) |
| api-delpi | get_production_consumption_by_item | /production/consumption/by-item | contexto de consumo | REUSE_AS_IS |
| api-delpi | get_product_detail / get_product_summary | /products/{code}/… | master data | REUSE_AS_IS |
| api-delpi | ~~list_warehouses~~ | — | fatos de armazém cobertos por composição (§27) | NOT_NEEDED |

Contagem: FS 24 rotas planejadas (11 query/meta + 13 comandos). api-delpi: 13 reuse + 1 evolve + 0 new.

## 39. Complete data model matrix

Schema `factory_supply` — todas `PLANNED` (DDL na implementação; sem SQL aqui).

| Tabela | Propósito | PK | Campos-chave | UNIQUE/FK | Branch | Version | Índices | Status |
|---|---|---|---|---|---|---|---|---|
| supply_missions | raiz do agregado | id UUID | branch, destination_work_center, need_window_start/end, op_order, operation_seq, product_context, feeder_user_id, collection_round_ref, lifecycle_status, overall_stage cache?, version, created_by/at, closed_at, cancel_reason | — | sim | version INT | (branch, lifecycle_status), (branch, destination, need_window_start), (feeder_user_id) | PLANNED |
| supply_mission_items | itens do agregado | id UUID | mission_id FK, seq, product_code, unit, qty_required/requested/prepared/collected/delivered/returned NUMERIC, dim status, snapshots (desc, location, stock_at_decision, committed_at_decision), exception | UNIQUE(mission_id,seq) FK→missions | via mission | herdada | (mission_id), (branch implícito via join) | PLANNED |
| demand_signals | necessidades planejadas/operacionais | id UUID | signal_key, source, branch, work_center, op_order, operation_seq, product_code, unit, qty_needed, need_at, status, fingerprint, synced_at | UNIQUE(branch,signal_key) WHERE status='active' | sim | — | (branch,work_center,need_at) | PLANNED |
| mission_demand_links | reconciliação signal↔missão/item | id UUID | signal_id FK, mission_id FK, mission_item_id FK?, link_type(planned|operator_requested), created_at | UNIQUE(signal_id,mission_item_id) | via mission | — | (mission_id) | PLANNED |
| handoffs | custódia por item | id UUID | mission_item_id FK, direction(collection|delivery|return), from_actor_user_id, to_actor_user_id?, to_context, qty NUMERIC, unit, at, note | FK→items | via item→mission | — | (mission_item_id), (to_actor_user_id,at) | PLANNED |
| erp_observations | evidência ERP por item | id UUID | mission_item_id FK, status enum, evidence_fingerprint, matched_ref JSONB?, confidence?, observed_at, source, payload_snapshot JSONB bounded | UNIQUE(mission_item_id, evidence_fingerprint) | via item | — | (mission_item_id,status) | PLANNED |
| supply_events | auditoria append-only | id UUID | mission_id, item_id?, event_type, action, actor_user_id, actor_display_name, prev_state, new_state, qty_delta, reason, idempotency_key, request_id, correlation_id, created_at | — | via mission (denorm branch col para filtro) | — | (branch,created_at) cursor, (mission_id,created_at) | PLANNED |
| idempotency_keys | dedup de comandos | id UUID | key, route, actor_user_id, **request_fingerprint** (hash canônico do comando semântico — §10), response_snapshot JSONB, created_at | UNIQUE(key,route,actor_user_id); fingerprint compara dentro do escopo | — | — | (created_at) retenção | PLANNED (convenção PROVEN + extensão TARGET) |

Notas: `qty` NUMERIC (nunca float — precisão de quantidade); `unit` NOT NULL com CHECK/validação de unidade compatível por material (TO_INVENTORY tabela de conversão TOTVS via api-delpi); nenhuma FK cruzando contexto (API DELPI = identificadores + snapshots); branch denormalizado em `supply_events` para filtro eficiente.

## 40. Complete RBAC matrix

Códigos `factory-supply.*` (convenção `PROVEN`: `production-control.{surface}.{view|manage}`, `.access`, `.view.filial-{code}`). Capacidades — rótulos de cargo **não** são autoridade. Duas classes distintas:

### A. USER / INTERACTIVE capabilities (manifesto/Core/Keycloak)

| Permissão | Cobertura backend | Superfícies MFE | R/W | Escopo filial | Status |
|---|---|---|---|---|---|
| factory-supply.access | entrada no app (gate mínimo) | todas (visibilidade) | R | — | PLANNED |
| factory-supply.view | todas as queries §15 (todas filiais) | todas leitura | R | ambas | PLANNED |
| factory-supply.view.filial-01 / -02 | queries restritas à filial | todas leitura | R | única | PLANNED (convenção PROVEN) |
| factory-supply.missions.request | request-material | Necessidades/Cockpit path | W | valida filial do body | PLANNED |
| factory-supply.missions.manage | plan/replan/cancel/close | Kanban/detail | W | idem | PLANNED |
| factory-supply.preparation.manage | start/record preparation | Almoxarifado | W | idem | PLANNED |
| factory-supply.collection.manage | record collection/handoff | Minha coleta | W | idem | PLANNED |
| factory-supply.delivery.confirm | record delivery | Minha coleta/CT recebedor | W | idem | PLANNED |
| factory-supply.returns.manage | record return | Devoluções | W | idem | PLANNED |

### B. SYSTEM / SERVICE capabilities (não expostas como permissão de usuário)

| Capacidade (contrato interno) | Owner AuthN/AuthZ | Gatilho | Limite de autoridade | Status |
|---|---|---|---|---|
| `factory-supply.service.demand-sync` | **factory-supply-api** — invocação in-process (scheduler/runner próprio) ou S2S futura; **não** é permissão Core de usuário | agendamento interno / trigger de serviço | somente leitura ERP via api-delpi + escrita nos próprios `demand_signals`; nunca autoridade além da integração read-only | TARGET + `TO_INVENTORY` (identidade de serviço: in-process vs service-account) |
| `factory-supply.service.erp-evidence-reconcile` | idem | pós-entrega automático, reavaliação agendada; gatilho interativo opcional seria permissão separada (`TO_INVENTORY` se `.missions.manage` ou código novo o cobre) | idem — observa e persiste correlação, nunca escreve ERP | TARGET |

Capacidades de serviço **nunca** expandem autoridade além do read-only ERP: não leem o que o canal api-delpi não expõe e nunca implicam escrita TOTVS.

**Não pronto para implementação (NO):** (a) política de **escopo de escrita por filial** não tem precedente PROVEN — leitura usa sufixo `.view.filial-*`, mas nenhuma permissão de escrita sufixada foi observada (`TO_INVENTORY`: adotar `.{cap}.filial-*` ou validar filial no payload sem sufixo); (b) mapeamento capacidade→grupos Keycloak pendente; (c) modelo de identidade das capacidades de serviço (in-process vs S2S) pendente; (d) seeding no Core/manifesto é fase de implementação. Enforcement: sempre backend; visibilidade no MFE é apenas UX.

## 41. Complete integration matrix

| Produtor | Consumidor | Contrato | Direção | AuthN | AuthZ | Idempotência | Autoridade | Falha | Status |
|---|---|---|---|---|---|---|---|---|---|
| MFE factory-supply | factory-supply-api | HTTP/JSON `/apps/factory-supply-api/v1` | → | JWT usuário (Keycloak) | permissões factory-supply.* + filial server-side | KEY em comandos | BFF | envelope erro + codes | TARGET |
| factory-supply-api | api-delpi | HTTP GET rotas §38 | → | Bearer propagado do usuário (PROVEN) | permissões api-delpi do usuário | GET retry limitado | api-delpi | 503→downstream_unavailable | TARGET |
| factory-supply-api | PostgreSQL | driver/SQL schema factory_supply | → | credencial serviço (backend-only) | — | transação agregado | FS | transacional | TARGET |
| Operator Cockpit | factory-supply-api | `request-material` source=cockpit | → (futuro) | JWT usuário operador | .missions.request + filial | KEY cockpit | BFF | mesmo envelope | FUTURE |
| scheduler/internal (FS) | factory-supply-api | demand-signals/sync, erp-evidence reconcile | → (interno) | identidade de serviço (`TO_INVENTORY`: in-process vs S2S) | service capabilities §40-B | NATURAL dedup | FS domain | reagenda/observa | TARGET |
| api-delpi | factory-supply-api (erros) | 401/403 downstream | ← | — | — | — | api-delpi | `downstream_access_denied` — nunca persiste evidência ERP | TARGET |
| factory-supply | consumidor de notificações | evento derivado de supply_events | → (futuro) | plataforma | — | dedup natural | FS | fora do caminho síncrono | FUTURE_CONSUMER_EVENT |
| api-delpi | TOTVS | read-only existente | → | existente | existente | — | TOTVS | propagada | PROVEN |

## 42. Decisions frozen

1. `factory-supply-api` — backend dedicado (dir/pacote/mount/schema).
2. Envelope bounded `{success,message,data}` + `data.code` de erro estável.
3. `Idempotency-Key` header + tabela `idempotency_keys` (key,route,actor,request_fingerprint) + replay de snapshot; mesmo escopo+fingerprint → replay; fingerprint divergente → `idempotency_conflict` (algoritmo do fingerprint `TO_INVENTORY`).
4. `expected_version` + `version` — conflito 409 `version_conflict`; sem last-write-wins.
5. `overall_stage` derivado no backend; `available_actions` semânticas; frontend nunca rederiva.
6. ERP evidence: `matched|not_found|unknown|unavailable|divergent` com semântica fechada (§26); 401/403 downstream são falha de integração/AuthZ (`downstream_access_denied`), nunca evidência persistida.
7. `branch` em query/body, validado server-side; dados persistidos branch-scoped.
8. TIMESTAMPTZ + ISO 8601 instants; unidade+NUMERIC em toda quantidade; sem soma entre unidades incompatíveis.
9. Auditoria append-only `supply_events` na mesma transação; ator = `id/sub` + display snapshot; sem tokens persistidos.
10. `EVENT_BUS_REQUIRED_NOW=NO`, `OUTBOX_REQUIRED_NOW=NO` (triggers documentados §33).
11. `TOTVS_WRITE_SUPPORT=NO`, `DIRECT_MFE_TO_API_DELPI=NO`, `LINE_FEEDER_RUNTIME_DEPENDENCY=NO`.
12. Catálogo de comandos §14 e queries §15 (contratos conceituais congelados; nomes de operationId `TARGET`).
13. Batch api-delpi obrigatório para fan-out; nenhuma rota ilimitada; cursor para histórico.
14. api-delpi: 13 reuse + 1 evolve + 0 new — `NEW_API_DELPI_ROUTES_REQUIRED = NO` (§27 inspeção bounded).
15. RBAC dividido em capacidades USER (9, manifesto/Core) e SYSTEM/SERVICE (2 contratos internos — §40-B); capacidades de serviço nunca excedem read-only ERP.

## 43. Decisions not frozen

1. Algoritmo exato de derivação de `overall_stage` (owner=backend congelado; regra detalhada na implementação a partir das dimensões Doc 2/5).
2. Semântica de reconciliação pedido↔sinal existente (§29) — decisão de produto pendente.
3. Regra de quantidade de retorno (`RETURN_QUANTITY_RULE = TO_INVENTORY` herdado).
4. Prioridade/score (`priority_score = NOT_SUPPORTED` até política existir — expostos `due_at|overdue|time_to_need` factuais).
5. Escopo de escrita por filial (sufixo `.{cap}.filial-*` vs validação payload) — `TO_INVENTORY`.
6. Cache operacional (TTL/fail-open) — `TO_DESIGN`; v1 sem cache semântico.
7. Header exato de correlação propagado ao api-delpi — `TO_INVENTORY` convenção do gateway.
8. Forma interna de `matched_ref`/fingerprint de movimento — pendente da confirmação de ID estável (§25).
9. Algoritmo de `request_fingerprint` (semântica congelada; implementação `TO_INVENTORY`) + retenção de `idempotency_keys`.
10. Identidade das capacidades de serviço (in-process scheduler vs S2S/service-account) — §40-B.
11. Permissão interativa para refresh manual de evidência ERP, se desejada (§40-B).

## 44. TO_INVENTORY

| Item | Bloqueia |
|---|---|
| Campos exatos de `get_product_internal_movements` (ID estável de movimento? fingerprint composto necessário?) | §25, readiness de contratos |
| Campos de `list_production_order_operation_materials(_batch)` (empenho/open_qty/janela por material — confirmar contra resposta real) | sync de sinais |
| ~~Catálogo de armazéns~~ — RESOLVIDO §27: REUSE_AS_IS + composição BFF (sem nova rota) | — |
| Convenção de header de correlação no gateway portal→api-delpi | §32 |
| Política de escopo de escrita por filial (precedente `.filial-*` só em `.view`) | RBAC ready |
| Mapeamento capacidades→grupos Keycloak/Core manifesto | RBAC ready |
| Tabela/serviço de conversão de unidades TOTVS (validação de unidade compatível) | §39 |
| Identidade de serviço para capacidades §40-B (scheduler in-process vs S2S/service-account) — não criar service account sem decisão | §36, §40-B |
| Algoritmo de `request_fingerprint` + evolução da convenção `idempotency_keys` compartilhada vs campo local | §10, §39 |
| Retenção de idempotency_keys e volume estimado de supply_events | §23 |
| Empenho como campo vs rota dedicada (hoje via operation materials — confirmar) | §41 |
| Decisão de produto: reconciliação pedido×sinal (§29) e regra de retorno | comandos |

## 45. Inputs for Documentation 5/5

1. Sequência de implementação: migrations → backend scaffold → rotas query → comandos → sync → MFE wiring → cockpit boundary.
2. Requisitos testáveis por contrato: por comando (authz, EV, key, pós-condição), por query (paginação, filial), por estado ERP (§26), por reconciliação (§29).
3. Itens TO_INVENTORY desta doc viram tarefas de inventário/decisão do roadmap.
4. Critérios de aceite do gate de qualidade (§58 da tarefa) mapeados para testes de contrato.
5. Cutover Line Feeder: checklist de paridade + depreciação governada.
6. Manifesto do plugin `factory-supply` + permissões Core (implementation phase).

---

## 46. Clean architecture target

Layout do pacote `factory_supply_app/` conforme padrão `PROVEN` (`production_control_app`, `requests_app`):

```text
factory_supply_app/
├── domain/          # entidades, invariantes, derivação de overall_stage, erros de domínio
├── application/     # use cases por comando/query, ports (repositories, gateways, idempotency)
├── infrastructure/  # postgres_*_repository, api_delpi_*_gateway/client, persistence adapters
├── interface/http/  # routes, auth_http, request/response DTOs, error handlers
├── composition/     # wiring/factories (composer)
├── middleware/      # jwt_middleware
├── core/            # responses ok/fail, settings
└── migrations/      # V00N__*.sql
```

- `domain`/`application` **não** importam FastAPI, ORM, psycopg, httpx, SDK Keycloak, código de MFE ou provider externo (DIP — `clean-code-architecture-guardrails.mdc`).
- Ports exigidos pelo domínio/aplicação: `SupplyMissionRepositoryPort`, `DemandSignalRepositoryPort`, `HandoffRepositoryPort`, `ErpObservationRepositoryPort`, `SupplyEventRepositoryPort`, `IdempotencyRepositoryPort` (precedente `PROVEN` em requests-api), `ProductionReadGateway` (OPs/operações/materiais/CTs), `StockReadGateway` (saldos/locations/blocks), `MovementReadGateway` (movimentos internos), `MasterDataGateway` (produtos/warehouses), `ClockPort`/`UnitOfWorkPort`.
- Chamada HTTP externa **fora** da transação DB do agregado (platform-data-persistence §Transações): leituras ERP acontecem antes do commit; observações persistidas guardam só resultado.

## 47. Contract ownership (API surface)

| Superfície | Owner | Contém | Não contém |
|---|---|---|---|
| `/apps/factory-supply-api/v1/*` | factory-supply-api | semântica de produto: missões, sinais, preparo, coleta, handoff, entrega, devoluções, histórico, projeções | fatos ERP, SQL genérico, cache de verdade TOTVS |
| `/apps/api-delpi/*` (ou mount atual) | api-delpi | fatos autoritativos ERP/TOTVS (OPs, materiais, saldos, movimentos, CTs, master data) | workflow/policy do Factory Supply, rotas nomeadas para o produto |

Rotas novas na api-delpi só quando o fato ERP não tem contrato tipado (§27). Nunca usar rota de SQL genérico como bypass (§30 da tarefa — não existe tal rota canônica para consumo direto; toda falta vira contrato tipado novo).

## 48. Available-action projection

`available_actions: string[]` em respostas de missão — códigos técnicos dos comandos §14 atualmente permitidos **pelo estado do agregado** (não por papel do usuário). Owner: serviço de aplicação/domínio. Caráter: **metadado consultivo de UX** — não é autorização: toda rota de escrita revalida permissão + invariante + versão. Semântico (verbos de domínio), não nomes de botão. Convenção repo compatível: payloads já carregam flags derivadas (`PROVEN` — LineFeederRequirementCard consome `can_*`-style derivados do backend em production-control).

## 49. Priority contract

**DECISÃO:** `priority_score = NOT_SUPPORTED` — não existe política de negócio autorizada (`TO_DESIGN` desde Doc 2/5); nenhum score será inventado.

Até política existir, o backend expõe apenas fatos determinísticos:

- `due_at` (= `need_window.end`), `overdue: bool` (comparação server-side, instant), `time_to_need` (segundos — campo derivado opcional);
- ordenação default das listas de trabalho: `need_window.start` ASC (FIFO por início da necessidade — mesmo princípio `PROVEN` do Line Feeder: alocação FIFO por `scheduled start`), com `urgency.classification` apenas se classificação explícita vier do dado (ex.: OP marcada urgente — `TO_INVENTORY` se api-delpi expõe tal flag);
- frontend **não** inventa prioridade relativa nem cor de urgência fora desses fatos.

## 50. Pagination/filtering conventions

| Convenção | Valor | Evidência |
|---|---|---|
| Listas correntes (missions, needs, work-queue, returns, my-collection) | `page` + `page_size` (default 50, máx 200), resposta `data.pagination{page,page_size,total,items}` | `TARGET` — bounded-API usa `limit: Query(50, ge=1, le=200)` (`PROVEN` line_feeder_routes); api-delpi usa `page/page_size` tiers |
| Histórico (`/v1/history`, mission history) | **cursor** (`next_cursor` opaco; ordem `created_at` desc estável + tiebreaker por id) | `TARGET` — histórico operacional cresce ilimitadamente; offset profundo é caro e instável sob append |
| Sem endpoint ilimitado | obrigatório | platform-data-persistence |
| Filtros | query params nomeados: `branch`, `stage`, `destination`, `assignee`, `status`, `window_from`, `window_to`, `product`, `has_return`, `exception_only` | `TARGET` |
| Sort | `sort` fechado por rota (whitelist de campos; default documentado por rota) | `TARGET` |

## 51. Units/quantities contract

- **Tipo:** `NUMERIC` no banco; JSON number com precisão decimal — **nunca** float binário para quantidade (`platform-data-persistence` "tipos adequados a precisão").
- **Unidade:** `unit` (string, código TOTVS do produto — ex.: `PC`,`KG`,`CX`) obrigatória ao lado de **toda** quantidade em request/response.
- **Sem agregação entre unidades incompatíveis:** contagens agregadas são de itens/missões (inteiros); somas de quantidade só dentro de `product_code × unit` idênticos.
- **Validação:** unidade do comando deve ser igual ou conversível à unidade autoritativa do material (api-delpi master data); conversão exata exige tabela de unidades TOTVS — `TO_INVENTORY` qual contrato api-delpi a expõe; até lá, escrita de quantidade em unidade diferente da cadastrada **falha fechado** (`422 domain_rule_violation`).
- **Arredondamento/exibição:** UI formata; backend valida precisão máxima por unidade (placeholder `TO_INVENTORY` da precisão autoritativa).
- **`null` semântico:** `returned_qty`/`prepared_qty` etc. `null` = não estabelecido — distinto de `0` (Doc 3/5 — "quantidade não estabelecida" é caso real de devolução).
