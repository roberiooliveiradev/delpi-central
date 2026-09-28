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
- **Request fingerprint (TARGET — congelado FS-C0.T6):** `request_fingerprint = SHA-256(bytes UTF-8 de canonical_json(comando_semântico))`. **Canonicalização:** modelo tipado validado → dict JSON-compatível → chaves de objeto ordenadas recursivamente → arrays preservam ordem de negócio → `Decimal`→string canônica (`normalize()`, `1`/`1.0`/`1.000` → `"1"`) → nulos/omissos resolvidos pela semântica do comando tipado (default ≠ ausente só se o schema os distinguir) → `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)` → UTF-8. **Nunca** hash do body bruto (ordem de propriedade não é semântica). SHA-256 = digest determinístico de identidade, não autenticação — sem HMAC/secret (sem requisito de segurança provado no repo; nenhum helper canônico existe → implementação **local** em factory-supply-api).
- **Input do fingerprint:** `operation_id` (ou identidade de rota) + identificadores de path (`mission_id`, `item_id`) + `branch` + todos os campos de domínio do body tipado (quantidade, unidade, motivo, `expected_version`, etc.). **Excluídos:** ator (já no escopo UNIQUE), Authorization/JWT, timestamp, User-Agent, request/trace-id, metadados de rede, ordem de headers/propriedades. `expected_version` participa: retry pós-`version_conflict` com versão corrigida = **nova intenção → nova key** (mantém §4 do produto: mesmo key+comando diferente → 409).
- **Replay:** mesma key + mesma rota + mesmo ator + **mesmo fingerprint** → resposta gravada retornada (mesmo status), **sem** reexecutar transição; resposta marca `data.idempotent_replay: true` (TARGET — marcador aditivo observável). **AuthN/AuthZ reavaliados em todo request antes do replay** — snapshot nunca vaza para ator desautorizado.
- **Conflito:** mesma key + mesma rota + mesmo ator + **fingerprint diferente** → `409 idempotency_conflict` — key nova = intenção nova; nada é mutado nem sobrescrito.
- **Fluxo (primeira requisição):** AuthN/AuthZ → validação tipada → fingerprint → claim `INSERT` na `idempotency_keys` → comando de domínio → mutation + `supply_events` + outbox + `response_snapshot` → **um único commit** → resposta. `response_snapshot` gravado na mesma tx da mutação (elimina a janela requests-api, que comita em conexão separada — desvio TARGET justificado).
- **Falhas não consomem key:** validação/AuthZ/precondição/`version_conflict`/downstream falham **antes ou com** rollback — a tx não comita, logo **nenhum registro de key permanece**; falha transitória nunca envenena a key. Apenas respostas de sucesso (2xx) são persistidas.
- **Concorrência mesma key:** a constraint UNIQUE faz o segundo `INSERT` esperar o commit/rollback do primeiro; ao resolver: rollback → contender tenta de novo como claim novo; commit+mesmo fingerprint → replay; commit+fingerprint divergente → `409`. Nunca mutação dupla.
- **Mesma key / outro ator ou outra rota:** escopo independente — UNIQUE é por `(key, route, actor_user_id)`; key de um usuário nunca devolve snapshot de outro.
- requests-api atual não persiste fingerprint (`PROVEN` — tabela tem só key/route/actor/snapshot) → convenção compartilhada evolui para `(key, route, actor_user_id, request_fingerprint)`; coluna reservada no schema planejado (§39). Adicionar `response_status INT` (precedente helpdesk `response_status`+`response_body`) para replay fiel do status.
- **Retenção:** chaves são registros de deduplicação, não auditoria — política final `TO_FS_C0_T12` (deve cobrir retries realistas; precedente requests-api usa janela `max_age_hours=24` no read; auditoria vive em `supply_events`, §31).
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

Somente comandos justificados por Doc 2/5 (transições das dimensões) + Doc 3/5 (ações das superfícies). Cada comando: `POST` semântico, `Idempotency-Key`, `expected_version`, `branch` no body, auditoria obrigatória. Resposta: `{mission, items, overall_stage, version, available_actions}` resultante.

AuthZ de usuário para **todos** os comandos interativos: `factory-supply.access` + `factory-supply.view.filial-{branch}` — modelo congelado §40-A (Product Master, FS-C0.T3). **Não existe permissão por comando**: a coluna AuthZ abaixo expressa sempre a mesma composição; proteção adicional = validação de filial do agregado + invariantes de domínio + versão + idempotência, não catálogo RBAC granular.

| Command | Path | AuthZ user | Pós-condição |
|---|---|---|---|
| `request_supply_material` | POST `/v1/missions/request-material` | `access`+`filial` (§40-A) | missão criada (ou vinculada — §29) com itens requisitados; auditoria `request` |
| `plan_supply_mission` | POST `/v1/missions/{id}/plan` | `access`+`filial` | destino/janela/atribuição confirmados; missão entra no funil |
| `replan_supply_mission` | POST `/v1/missions/{id}/replan` | `access`+`filial` | campos alterados + rastro de replanejamento |
| `cancel_supply_mission` | POST `/v1/missions/{id}/cancel` | `access`+`filial` | `lifecycle=cancelled` + motivo; itens travam |
| `close_supply_mission` | POST `/v1/missions/{id}/close` | `access`+`filial` | `lifecycle=closed` se invariantes de fechamento ok |
| `start_item_preparation` | POST `/v1/missions/{id}/items/{item_id}/start-preparation` | `access`+`filial` | item dimensão prep → in_progress |
| `record_item_preparation` | POST `/v1/missions/{id}/items/{item_id}/record-preparation` | `access`+`filial` | `prepared_qty` registrada (parcial permitida) |
| `record_item_collection` | POST `/v1/missions/{id}/items/{item_id}/record-collection` | `access`+`filial` | `collected_qty` + handoff implícito armazém→alimentador |
| `record_item_handoff` | POST `/v1/missions/{id}/items/{item_id}/record-handoff` | `access`+`filial` | handoff alimentador→CT aceito/pendente |
| `record_item_delivery` | POST `/v1/missions/{id}/items/{item_id}/record-delivery` | `access`+`filial` | `delivered_qty` + recebido_por CT |
| `record_item_return` | POST `/v1/missions/{id}/items/{item_id}/record-return` | `access`+`filial` | `returned_qty` + motivo + handoff→armazém |
| `sync_supply_demand_signals` | job interno `demand_signal_sync` (§40-B — sem rota pública; execução in-process) | system actor | signals ativas atualizadas de forma replay-safe |
| `refresh_item_erp_evidence` | POST `/v1/missions/{id}/items/{item_id}/erp-evidence/refresh` — opcional `TO_INVENTORY` | job `erp_evidence_reconcile` (§40-B); se interativo: `access`+`filial` | observação ERP deduplicada persistida |

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

- Rota de leitura autoritativa: `get_product_internal_movements` (`GET /products/{code}/internal-movements`) — `PROVEN` (FS-C0.T1 executado): fonte `SD3010` (SD3) + `SB1010`, filtros `D_E_L_E_T_=''` e `D3_ESTORNO<>'S'`; campos `branch, location, document, issue_date, product_code, product_description, unit, movement_type(TM), cf, quantity, production_order(OP), user_name`; filtros `branch/location/tm/op/kind=warehouse_transfer(DE0|RE0)`; paginação `page/page_size` (máx 500).
- **Identidade estável de movimento: `NO_STABLE_MOVEMENT_ID_EXPOSED`** — `R_E_C_N_O_` existe na fonte e ordena a resposta mas **não é exposto**. Não inventar ID.
- **Fingerprint composto (TARGET — baseline de correlação):** `(branch, product_code, document, issue_date, cf, movement_type, location, quantity, production_order?)` — determinístico sobre campos autoritativos retornados; unicidade **não provada** para ocorrências idênticas (mesmo doc/produto/cf/local/qtd) — dedup aceita esse colapso documentado (`confidence` `high` quando tuple única na página avaliada, `medium` caso contrário).
- Pairing de transferência DE0(sai)/RE0(entra): `DETERMINISTIC_DERIVATION` consumer-side por `(document, issue_date, product_code)` com tolerância a órfãos — referência `PROVEN` em `line_feeder_warehouse_transfers.py`; sem chave de par autoritativa em SD3.
- Evolução opcional (`EVOLVE_EXISTING`, não bloqueante): expor `R_E_C_N_O_` como `movement_recno` — campo já presente na mesma query autoritativa (gate A); estabilidade condicional (RECNO reciclável em pack/reorg Protheus) — `TO_INVENTORY` se decisão for assumi-lo como identidade persistente; fingerprint composto permanece o baseline seguro.
- Deduplicação: UNIQUE `(mission_item_id, evidence_fingerprint)` — reobservação do mesmo fato não duplica correlação nem efeito operacional.
- Erros downstream: falha genérica na rota retorna `error_response` status 400 — gateway FS trata todo não-2xx como falha técnica (`unavailable`/`downstream_*`), nunca como `not_found`.

## 26. ERP evidence states

**CONGELADO (corrigido — AuthZ não é evidência):**

| Estado | Definição |
|---|---|
| `matched` | avaliação autoritativa **autorizada** completou e encontrou evidência compatível |
| `not_found` | avaliação autoritativa **autorizada** completou com sucesso e **zero** evidência compatível — factual, nunca erro |
| `unknown` | evidência ainda não avaliada ou informação de correlação insuficiente |
| `unavailable` | fonte autoritativa **não pôde ser avaliada tecnicamente**: timeout, falha de conexão, downstream 5xx, resposta parcial inutilizável — carrega `retryable` + `observed_at` |
| `divergent` | evidência autoritativa existe mas conflita materialmente com o rastro operacional (ex.: qty/direção/tipo/**unidade** — igualdade numérica com `unit` diferente é `divergent`, nunca `matched`; unit do movimento ausente → `unknown`, §51) |

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
OUTBOX_REQUIRED_NOW   = YES   ← corrigido FS-C0.T5-realtime (antes: NO)
```

Gate reavaliado após decisão de produto (sync automático + push realtime + fallback de notificação): entrega de notificação portal deve sobreviver falha/rate-limit do provedor, routing online×offline acontece **após** o commit de domínio, e WS é efêmero — portanto outbox PostgreSQL transacional **é** necessária (precedente `PROVEN`: `requests-api/migrations/V005__integration_outbox.sql`, `commercial_app/.../integration_outbox_repository_port.py`). Event bus/broker externo segue `NO` — não há consumidor assíncrono externo; nenhum Kafka/RabbitMQ/Redis.

**Cadeia congelada (padrão Commercial `PROVEN`, adaptado ao bounded context FS — padrão reutilizado, código nunca importado):**

```text
job de sync/reconcile (§40-B)
→ leitura autoritativa api-delpi
→ snapshot/checkpoint persistido + diff determinístico (keys naturais)
→ mutação de domínio + auditoria na mesma transação
→ enqueue integration_outbox (mesma tx)
→ worker flush pós-commit:
    online  → realtime hub → WebSocket → MFE (toast + estado)
    offline → portal notification (dedupeKey + deep link)
```

- **Diff:** checkpoint por `source_key` com keys estáveis (`IntegrationCheckpoint.metadata["keys"]` — precedente `ReadyToInvoiceSnapshotDeltaService.compute_delta`: `entered = current − previous`, serviço puro). FS: diff de `demand_signals` por `need_key`+fingerprint; evidência por movement fingerprint. Nenhum evento por alteração de campo — só transições de estado significativas.
- **Cold start:** primeiro scan persiste baseline e **enfileira zero** (`previous_key_count == 0` → `enqueued=0`, `PROVEN` — anti-flood); exceção crítica preexistente vai só à área de exceções persistente, não à notificação.
- **WS é canal de entrega, nunca fonte de verdade** — mutação de domínio nunca depende de socket conectado; 1 leitura ERP por ciclo, nunca 1 por cliente WS.
- **Hub realtime (owner = factory-supply-api):** implementação local seguindo o padrão `CommercialRealtimeHub` (`PROVEN` — rooms, presence por user com multi-aba=1 online, ping/pong ~25s, idle-close ~75s, `schedule_broadcast` thread-safe→queue→broadcast, dead-socket cleanup, worker em lifespan). Rooms FS: `user:{id}` + `filial:{01|02}` (atribuídas server-side por permissão resolvida — cliente nunca escolhe sala).
- **WS authZ (precedente `resolve_websocket_user`, `PROVEN`):** `validate_token(JWT)` → `load_user_rbac` (`/me` Core) → exige `factory-supply.access` + resolve filiais por `BRANCH_PERMISSIONS` → `WS_1008_POLICY_VIOLATION` em falha; claims fallback = `permissions[]` (fail-closed).
- **Presence scope = `FACTORY_SUPPLY_APP`:** `is_user_online` conta sockets **do WS do Factory Supply** (precedente `TaskPortalNotificationDeliveryPolicy.split_online_offline` usa o hub do próprio app, não "online no Portal").
- **Delivery policy:** usuário ativo no FS → realtime + toast + atualização de estado/área de exceções, **sem** notificação portal duplicada; usuário fora do FS → Minha DELPI notification com deep link ao contexto FS; retry (`attempts>0`) **não** re-broadcast WS (evita toast duplicado — precedente `PublishIntegrationOutboxUseCase`); rate-limit → `defer`+backoff por linha.
- **Dedupe:** identidade semântica por `event_type × aggregate_id × recipient` (`dedupeKey` em payload — precedente); uma ocorrência de negócio nunca vira toast+notificação+retry para o mesmo usuário.
- **Destinatários:** resolvidos por `factory-supply.access` + `view.filial-{branch}` (+ ator atribuído quando a semântica exigir — ex.: feeder designado); entrega pode usar `permissionCodes` (precedente portal). **Nenhuma permissão `notifications.*` extra.**
- **Audiência filial:** evento de filial 01 nunca chega a socket/notificação de usuário sem `view.filial-01` — filtro server-side por sala/recipient.
- **Notificações portal:** categorias declaradas no catálogo canônico `core-api/app/content/notification_catalog.json` (regra `notification-catalog-preferences` — mute/estrela/e-mail vêm de graça); categorias mínimas por outcome/exceção, nunca por tick.
- **Mensagem de sucesso:** "Transferência confirmada" — material, quantidade, destino/contexto, timestamp; ator somente se autoritativo (`user_name` SD3 exposto em internal-movements — §25); nunca inferir identidade.
- **Exceções persistentes:** divergência/erro não é toast-only — área persistente de exceções no produto (quantidade divergente, movimento divergente, evidência não localizada após política, fonte indisponível, falha de sync acionável, correlação não resolvida). Falha transitória (timeout/retry) = telemetria, não exceção de negócio.
- **Multi-instância (restrição MVP explícita):** hub in-memory é por-réplica; jobs + WS no MVP vivem na mesma réplica designada (`FACTORY_SUPPLY_JOBS_ENABLED` + deploy de 1 réplica para o slice realtime). Réplicas múltiplas servindo WS exigiriam fan-out entre réplicas — `TO_INVENTORY` futuro, sem Redis/pubsub sem necessidade provada.
- **Cadência:** `TO_BENCHMARK` — `SYNC_CADENCE` não é congelada; roadmap exige validação de carga/fan-out api-delpi antes de fixar (precedente existente: ~60s no Commercial — apenas referência, não alvo). "Realtime" UX = poll autoritativo + push WS imediato pós-diff.
- **Manual trigger ops:** precedente Commercial expõe `POST /integrations/jobs/*-scan` com permissão `manage` — FS não tem `manage`; gatilho manual permanece `TO_INVENTORY` (sem endpoint enquanto não houver justificativa+permissão explícita).

### Taxonomia de eventos FS (TARGET — nomes canônicos `domain.verb` conforme precedente `presence.updated`/`worklist.*`)

| Evento | Classe | Destino |
|---|---|---|
| `supply_need.changed` | REALTIME_ONLY | sala `filial:{b}` — refresh Necessidades/Kanban; sem spam portal |
| `supply_mission.changed` | REALTIME_ONLY | sala `filial:{b}` — invalida listas/drawer |
| `supply_transfer.matched` | REALTIME_AND_PORTAL_NOTIFICATION | toast sucesso + notificação offline; actor se autoritativo |
| `supply_transfer.divergent` | REALTIME_AND_PORTAL_NOTIFICATION + PERSISTENT_EXCEPTION | toast warning + notificação + área de exceções |
| `supply_transfer.not_found` | REALTIME_AND_PORTAL_NOTIFICATION + PERSISTENT_EXCEPTION | toast error + notificação + área de exceções |
| `supply_sync.error` | PERSISTENT_EXCEPTION (ação) / TECHNICAL_TELEMETRY (transitório) | área de exceções quando acionável; métrica/log sempre |
| `presence.updated` | REALTIME_ONLY (interno hub) | sala `team`/gestor — opcional FS |

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

- Credenciais só no backend; JWT do usuário propagado à api-delpi em contexto interativo (`bearer_authorization_from_context` `PROVEN`); jobs internos usam `API_DELPI_INTERNAL_SERVICE_TOKEN` + `X-Delpi-Caller-App` (§40-B, `PROVEN`) — sem service-account nova, sem JWT fabricado.
- Sem segredo ERP no MFE; sem JWT/claims como autoridade final — permissões avaliadas server-side a cada request.
- Modelo de usuário FROZEN §40-A: `factory-supply.access` + `.view.filial-{branch}`; enforcement por request: AuthN → `access` → `assert_valid_branch` → `.view.filial-*` → `aggregate.branch` confere → invariantes → mutação+auditoria (padrão `PROVEN` `BranchAccessService`/`can`/`has_permission` do delpi_auth+Core).
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

| # | Owner | Método | Path | operationId | R/W | AuthZ user | Idemp. | Conc. | Paginação | Deps ERP | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FS | GET | `/v1/overview` | get_factory_supply_overview | R | `access`+`filial` | N/A | — | — | nenhum (projeção local) | PLANNED_NEW |
| 2 | FS | GET | `/v1/missions` | list_supply_missions | R | `access`+`filial` | N/A | — | page | nenhum | PLANNED_NEW |
| 3 | FS | GET | `/v1/missions/{id}` | get_supply_mission | R | `access`+`filial` | N/A | — | — | opcional (evidence) | PLANNED_NEW |
| 4 | FS | GET | `/v1/needs` | list_supply_needs | R | `access`+`filial` | N/A | — | page | sinais já sincronizados | PLANNED_NEW |
| 5 | FS | GET | `/v1/needs/upcoming` | list_upcoming_supply_needs | R | `access`+`filial` | N/A | — | page | sinais | PLANNED_NEW |
| 6 | FS | GET | `/v1/warehouse/work-queue` | list_warehouse_work_queue | R | `access`+`filial` | N/A | — | page | nenhum | PLANNED_NEW |
| 7 | FS | GET | `/v1/my-collection` | list_my_collection | R | `access`+`filial` | N/A | — | page | nenhum | PLANNED_NEW |
| 8 | FS | GET | `/v1/returns` | list_supply_returns | R | `access`+`filial` | N/A | — | page | nenhum | PLANNED_NEW |
| 9 | FS | GET | `/v1/history` | list_supply_history | R | `access`+`filial` | N/A | — | cursor | nenhum | PLANNED_NEW |
| 10 | FS | GET | `/v1/missions/{id}/history` | get_supply_mission_history | R | `access`+`filial` | N/A | — | cursor | nenhum | PLANNED_NEW |
| 11 | FS | GET | `/v1/lookup-metadata` | get_supply_lookup_metadata | R | `access`+`filial` | N/A | — | — | CTs/warehouses via api-delpi | PLANNED_NEW |
| 12 | FS | POST | `/v1/missions/request-material` | request_supply_material | W | `access`+`filial` | KEY | — | — | valida produto/CT | PLANNED_NEW |
| 13 | FS | POST | `/v1/missions/{id}/plan` | plan_supply_mission | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 14 | FS | POST | `/v1/missions/{id}/replan` | replan_supply_mission | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 15 | FS | POST | `/v1/missions/{id}/cancel` | cancel_supply_mission | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 16 | FS | POST | `/v1/missions/{id}/close` | close_supply_mission | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 17 | FS | POST | `/v1/missions/{id}/items/{iid}/start-preparation` | start_item_preparation | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 18 | FS | POST | `/v1/missions/{id}/items/{iid}/record-preparation` | record_item_preparation | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 19 | FS | POST | `/v1/missions/{id}/items/{iid}/record-collection` | record_item_collection | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 20 | FS | POST | `/v1/missions/{id}/items/{iid}/record-handoff` | record_item_handoff | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 21 | FS | POST | `/v1/missions/{id}/items/{iid}/record-delivery` | record_item_delivery | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 22 | FS | POST | `/v1/missions/{id}/items/{iid}/record-return` | record_item_return | W | `access`+`filial` | KEY | EV | — | — | PLANNED_NEW |
| 23 | FS | — | job interno `demand_signal_sync` (sem rota pública) | sync_supply_demand_signals | W | system actor | NATURAL | — | — | machine-load + materials batch | PLANNED_JOB |
| 24 | FS | POST | `/v1/missions/{id}/items/{iid}/erp-evidence/refresh` — opcional | refresh_item_erp_evidence | W | job `erp_evidence_reconcile` (+`access`+`filial` se interativo) | NATURAL | — | — | internal-movements | PLANNED_JOB + TO_INVENTORY |
| 25 | FS | WS | `/v1/realtime` (upgrade) | factory_supply_realtime_connect | R | `access`+`filial` (resolve_websocket_user §33) | N/A | — | — | nenhum | PLANNED_NEW |

(`access`+`filial` = `factory-supply.access` + `factory-supply.view.filial-{branch}` — modelo FROZEN §40-A, sem permissão por rota; KEY = `Idempotency-Key` obrigatório + `request_fingerprint` persistido; NATURAL = dedup por chave natural; EV = `expected_version`; SERVICE = capacidade interna/serviço §40-B — não exposta como permissão de usuário no manifesto.)

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
| api-delpi | get_product_internal_movements | /products/{code}/internal-movements | evidência de movimento → correlação | REUSE_AS_IS (fingerprint composto §25 — FS-C0.T1; evolve opcional `movement_recno`) |
| api-delpi | get_production_consumption_by_item | /production/consumption/by-item | contexto de consumo | REUSE_AS_IS |
| api-delpi | get_product_detail / get_product_summary | /products/{code}/… | master data | REUSE_AS_IS |
| api-delpi | ~~list_warehouses~~ | — | fatos de armazém cobertos por composição (§27) | NOT_NEEDED |

Contagem: FS 25 superfícies planejadas (11 query/meta + 12 comandos + 1 WS + 1 job). api-delpi: 13 reuse + 1 evolve + 0 new.

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
| idempotency_keys | dedup de comandos | id UUID | key, route, actor_user_id, **request_fingerprint** (SHA-256 canonical-JSON — §10 congelado T6), response_status INT, response_snapshot JSONB, created_at | UNIQUE(key,route,actor_user_id); fingerprint compara dentro do escopo | — | — | (created_at) retenção TO_FS_C0_T12 | PLANNED (convenção PROVEN + extensão TARGET) |
| integration_outbox | entrega pós-commit (portal notif + realtime routing, §33) | id UUID | event_type, aggregate_type, aggregate_id, payload JSONB (userIds, permissionCodes, dedupeKey, actionTarget), attempts, next_attempt_at, published_at, created_at | UNIQUE(event_type,aggregate_id,dedupe_key?) — dedupe semântico §33 | branch no payload | — | (published_at NULL, next_attempt_at) | PLANNED (precedente `PROVEN` requests-api V005 + commercial) |
| integration_checkpoints | snapshot/diff de syncs (§33) | id UUID | source_key, cursor_value, metadata JSONB `{keys,keyCount}`, updated_at | UNIQUE(source_key) | por source_key (ex.: `demand_sync:01`) | — | (source_key) | PLANNED (precedente `PROVEN` `IntegrationCheckpointRepositoryPort`) |

Notas: `qty` NUMERIC(18,6) (nunca float — precisão de quantidade); `unit` NOT NULL = `B1_UM` autoritativa do material (FS-C0.T7 — **sem** tabela/engine de conversão; igualdade exata com `accepted_unit` do item); nenhuma FK cruzando contexto (API DELPI = identificadores + snapshots); branch denormalizado em `supply_events` para filtro eficiente; `integration_outbox` enfileirado na **mesma transação** da mutação de domínio e publicado pós-commit pelo worker (§33).

## 40. Complete RBAC matrix

**Modelo de usuário — FROZEN pelo Product Master (FS-C0.T3).** Factory Supply é deliberadamente um app operacional simples: **exatamente 3 permissões de usuário**, duas dimensões (acesso à aplicação + escopo de filial). Não existem permissões por comando, por superfície, por CRUD, por histórico ou por configuração — e nenhuma pode ser adicionada sem nova decisão explícita de produto.

```text
PRODUCT_RBAC_MODEL:        FROZEN
USER_PERMISSION_COUNT:     3
USER_PERMISSION_CATALOG:   factory-supply.access
                           factory-supply.view.filial-01
                           factory-supply.view.filial-02
PER_COMMAND_USER_PERMISSIONS: NO
CONFIGURATION_UI_REQUIRED: NO
```

### A. USER / INTERACTIVE capabilities (manifesto/Core/Keycloak)

| Permissão | Semântica | Cobertura backend | Escopo | Status |
|---|---|---|---|---|
| `factory-supply.access` | gate de aplicação | entrada no app + pré-condição de toda rota | — | TARGET |
| `factory-supply.view.filial-01` | **escopo de filial** — autoriza leitura **e** mutações operacionais na filial 01 | todas queries + todos comandos §14/§15 restritos à filial | filial 01 | TARGET (convenção PROVEN) |
| `factory-supply.view.filial-02` | idem, filial 02 | idem | filial 02 | TARGET (convenção PROVEN) |

Semântica congelada:

```text
factory-supply.access + factory-supply.view.filial-{branch}
= ler e executar todos os comandos operacionais da filial autorizada
```

- **`.view.filial-*` não é read-only** — é escopo de filial. Convenção `PROVEN` no repo: `production-control.view.filial-{01|02}` gateia escritas (`BranchAccessService.assert_can_view_branch` invocado em mutações como `close_pick_plan`/picked/delivered, `production_control_app/domain/services/branch_access_service.py` + `line_feeder_service.py`), não apenas leituras; a mesma permissão governa ver a necessidade e alterar a lista de coleta (Doc 1/5 §18). Manifest declara `production-control.view.filial-01|02` (linhas 68–79 do manifest).
- **Ambas as filiais** = usuário opera 01 e 02; front oferece seletor. Sem `factory-supply.access` → 403 mesmo com `.view.filial-*` presente. Sem `.view.filial-{b}` → 403 `branch_access_denied` na filial b. Superadmin: bypass via `is_superadmin` (`PROVEN`: `authz_core.has_permission` + `security.can`) — sem reimplementação local.
- **Resolução de autoridade (`PROVEN`):** manifesto `permissions[]` declara códigos → Core registra no catálogo na ativação do plugin (`register_plugin_use_case` → `PluginPermissionSyncService`/`plugin_permissions.sync_module`; mudança de permissões exige nova versão do plugin, `plugin.permission_change_not_allowed`) → admin RBAC atribui a roles (`rbac.manage`) → `delpi_auth` middleware valida JWT Keycloak e resolve `user.permissions` via Core API (`load_user_rbac`, `DELPI_AUTH_CORE_API_URL`) → backend checa `has_permission`/`can` por request.
- **Enforcement backend por request:** AuthN → `can(user, "factory-supply.access")` → `assert_valid_branch` → `can(user, BRANCH_PERMISSIONS[branch])` → carregar agregado → `aggregate.branch == branch autorizada` → invariantes → mutação + auditoria na mesma transação. `branch` do cliente **nunca** é autoridade (§20); missão de outra filial falha fechada mesmo com `branch` forjado. Frontend esconde ações por UX apenas.

**Declaração de manifesto (TARGET — contrato `PROVEN` em `plugins/production-control/production-control.manifest.json`):** cada permissão é `{code, name, description, module}` — `module` normalizado para o plugin id pelo `PluginPermissionSyncService.normalize_desired`; `code` obrigatório e único por módulo; `name`/`description` PT-BR user-facing. Declarações alvo:

```json
{ "code": "factory-supply.access",             "name": "Abastecimento Fabril",                 "description": "Acessar e operar o Abastecimento Fabril." },
{ "code": "factory-supply.view.filial-01",     "name": "Abastecimento Fabril — filial 01 (SC)", "description": "Acessar dados e operações da filial 01 (SC)." },
{ "code": "factory-supply.view.filial-02",     "name": "Abastecimento Fabril — filial 02 (ES)", "description": "Acessar dados e operações da filial 02 (ES)." }
```

**Versionamento de permissões (`PROVEN`):** `sync_module` é **declarativo por módulo** — código mantido preserva o UUID (e portanto `role_permissions`/overrides de usuário); código novo é inserido; código removido do manifesto é **deletado** do catálogo. Mudança no conjunto exige **nova versão do plugin** (`register_plugin_use_case` na branch de versão nova); `update_plugin_manifest` rejeita diff de permissões (`plugin.permission_change_not_allowed`). Nenhuma remoção prevista para as 3 permissões — o conjunto nasce completo na primeira versão.

**Atribuição e resolução (`PROVEN`):** admin atribui via `POST/PUT /admin/rbac/roles/{id}/permissions` (`AddPermissionToRoleUseCase`/`ReplaceRolePermissionsUseCase`, guard `rbac.manage`+`roles.manage`); efetivo por usuário = roles diretas ∪ roles via grupos ± overrides de usuário (`PermissionResolver.resolve`, com cache). Registro de plugin **não** auto-atribui a role alguma → `DEFAULT_ACCESS = DENY` até mapeamento administrativo (fail-closed). Semântica de papel (`almoxarife`, `alimentador`, `operador`) **não** é identidade RBAC — são personas operacionais sobre os mesmos 3 códigos.

**Consumo backend (contrato — precedente `PROVEN` `production_control_app/core/security.py`):**

```python
FS_ACCESS = "factory-supply.access"
BRANCH_PERMISSIONS = {"01": "factory-supply.view.filial-01",
                      "02": "factory-supply.view.filial-02"}
```

Mapa branch→permission é do backend FS; Core conhece apenas códigos (rótulos SC/ES são nome/descritivo user-facing do manifesto, não mapeamento técnico). Superadmin: bypass automático — `is_superadmin` resolve **todos** os códigos no Core (`PermissionResolver`) e `has_permission`/`can` retornam `True`; FS não implementa nada customizado e não cria outro modelo admin.

**Falhas (fail-closed, `PROVEN`):** permissão não registrada ou não atribuída → `has_permission` falso → 403; Core indisponível → cache stale dentro do `RBAC_STALE_TTL`, senão `_rbac_from_claims` com `permissions=[]`, `is_superadmin=False` → 403 (claims **nunca** concedem permissão; sem flag de confiança em claims); sem `access` → 403 `PermissionError`; filial não autorizada → 403 `branch_access_denied`; filial inválida → 422 `InvalidBranch`; sem JWT válido → 401.

**Ordem de implementação:** (1) manifesto `factory-supply` com as 3 permissões na versão inicial → (2) registro do plugin no Core (`register` → `sync_module` insere catálogo) → (3) admin mapeia permissões→roles → (4) usuários efetivos recebem escopo → (5) backend enforce (constantes já especificadas acima). Nenhuma rota FS pode existir em produção antes de (2); testes de §15 do roadmap validam (3)–(5).

### B. SYSTEM / SERVICE capabilities — execution model FROZEN (FS-C0.T5)

Capacidades internas são **jobs in-process** de `factory-supply-api`, não identidades RBAC. `SERVICE_PERMISSION_CODES_REQUIRED = NO` — os placeholders `factory-supply.service.*` abaixo são **nomes de job/contrato interno**, nunca códigos de permissão a registrar no Core.

| Job interno | Owner | Gatilho | Autoridade | Status |
|---|---|---|---|---|
| `demand_signal_sync` | factory-supply-api — task asyncio no lifespan (precedente `PROVEN`: `ProductionRunPollerService`, `run_outbox_worker_loop`, purchase-requests notification jobs, `integration_jobs_scheduler`) | loop periódico interno; **cadência `TO_BENCHMARK`** (§33 — validar carga antes de fixar) | leituras api-delpi §38 + checkpoint/diff §33 + escrita `demand_signals`+outbox; nunca TOTVS write | TARGET |
| `erp_evidence_reconcile` | idem | pós-`record_item_delivery` (hook interno) + passo periódico replay-safe; cadência `TO_BENCHMARK` | leitura internal-movements + upsert `erp_observations` + eventos de divergência §33; nunca escreve ERP | TARGET |
| `manual evidence refresh` (opcional) | idem — rota §38 #24 coberta por `access`+`filial` se interativa | request de usuário | idem | TO_INVENTORY (só se UX pedir gatilho manual) |

**Modelo de execução (`PROVEN`):**
- **Runtime:** `asyncio.create_task` com loop `while not stopped`, start/stop no lifespan do FastAPI, intervalo via settings, erro por tick isolado (try/except + log + continua), shutdown limpo via `asyncio.Event` — padrão exato de `production_run_poller_service.py` / `outbox_worker.py` / purchase-requests `startup/*_job.py`. Sem OS cron/K8s cron/automação externa.
- **Multi-instância:** env-flag `FACTORY_SUPPLY_JOBS_ENABLED` habilita workers apenas na réplica designada (precedente `PROVEN`: `REQUESTS_OUTBOX_WORKER_ENABLED`); dedup por chave natural (signal fingerprint / movement fingerprint) torna execução dupla replay-safe mesmo em corrida.
- **Identidade técnica:** sem usuário sintético, sem JWT fabricado, sem token de usuário persistido. Actor em `supply_events` de origem job: `actor_type="system"`, `actor_user_id="factory-supply-api"`; ação humana que dispara follow-up preserva ator humano separado do ator técnico.
- **Auth api-delpi (`PROVEN`, nenhum evolve necessário):** gateway FS emite `X-Delpi-Caller-App: factory-supply-api` + `API_DELPI_INTERNAL_SERVICE_TOKEN` via `apply_internal_service_headers`/`bearer_authorization_from_context` — com usuário no contexto propaga JWT; em background usa o token interno. O middleware `delpi_auth` resolve token de serviço válido como identidade interna (`id="internal-service"`, `is_superadmin=True`) → lê qualquer rota api-delpi (superfície já read-only; MCP exclui identidade de serviço explicitamente). Credencial existente, guarded por `credential_guard` (sem Keycloak client, sem service account nova, sem escopo extra: FS só consome os GETs documentados §38 — least-privilege é contratual, não mecânico).
- **Escopo de filial:** jobs iteram filiais do catálogo autoritativo/config (`ALLOWED_BRANCHES` — precedente `production_control_app/core/security.py`); execução técnica **não** usa `.view.filial-*` (isso é escopo de usuário, não de job).
- **Retry/replay:** leituras autoritativas retriáveis; passos locais idempotentes por upsert/natural-key dedup — reconheciliação repetida do mesmo movimento não duplica evidência; nenhum retry cego em mutação local não-idempotente; contagens de retry fixos não congeladas (política `http-integration-resilience`).
- **Falhas:** downstream 5xx/timeout → retry próximo tick + observabilidade; 401/403 downstream → falha técnica AuthZ/integração (`downstream_access_denied` path, §9/§26), **nunca** evidência persistida; resposta inválida → falha técnica; DB local → transação atômica, sem sinal parcial; correlação ambígua → `unknown`, nunca match fabricado; nenhuma falha vira `NOT_FOUND` ou sucesso.
- **Observabilidade:** log estruturado por tick — job, run_id, started/finished, branch, records observed/created/superseded/correlated, erros, latência downstream, retry/replay — sem payloads sensíveis/tokens; métricas de saúde do sistema, nunca performance de pessoas.
- **Auditoria:** mudança de domínio (signal criado/superado, evidência correlacionada) → `supply_events` `actor_type=system` na mesma transação; poll sem alteração → telemetria técnica apenas, sem inundação de auditoria.
- **Endpoints internos:** `NO` — sem `POST /internal/*` enquanto execução for in-process; gatilho manual operacional exige contrato+segurança explícitos futuros.

Capacidades de serviço **nunca** expandem autoridade além do read-only ERP: não leem o que o canal api-delpi não expõe e nunca implicam escrita TOTVS.

**Pendências restantes:** (a) execução do registro — manifesto declarado na versão inicial do plugin + `register` no Core + mapeamento admin a roles (mecanismo 100% `PROVEN` — FS-C0.T4; resta apenas execução em fase de implementação, sem gap arquitetural); (b) identidade das capacidades §40-B (FS-C0.T5); (c) definição operacional de quais roles recebem os 3 códigos (decisão administrativa na implantação, fora do escopo técnico). Enforcement: sempre backend; visibilidade no MFE é apenas UX.

## 41. Complete integration matrix

| Produtor | Consumidor | Contrato | Direção | AuthN | AuthZ | Idempotência | Autoridade | Falha | Status |
|---|---|---|---|---|---|---|---|---|---|
| MFE factory-supply | factory-supply-api | HTTP/JSON `/apps/factory-supply-api/v1` | → | JWT usuário (Keycloak) | permissões factory-supply.* + filial server-side | KEY em comandos | BFF | envelope erro + codes | TARGET |
| factory-supply-api | api-delpi | HTTP GET rotas §38 | → | Bearer propagado do usuário (PROVEN) | permissões api-delpi do usuário | GET retry limitado | api-delpi | 503→downstream_unavailable | TARGET |
| factory-supply-api | PostgreSQL | driver/SQL schema factory_supply | → | credencial serviço (backend-only) | — | transação agregado | FS | transacional | TARGET |
| Operator Cockpit | factory-supply-api | `request-material` source=cockpit | → (futuro) | JWT usuário operador | `access` + `.view.filial-*` | KEY cockpit | BFF | mesmo envelope | FUTURE |
| factory-supply-api (jobs §40-B) | api-delpi | GETs §38 (`X-Delpi-Caller-App: factory-supply-api`) | → | `API_DELPI_INTERNAL_SERVICE_TOKEN` (identity `internal-service`, read-only surface) | proven shared-token S2S; sem permissões Core | GET retry limitado | api-delpi | 5xx→retry próximo tick; 401/403→falha técnica | PROVEN |
| api-delpi | factory-supply-api (erros) | 401/403 downstream | ← | — | — | — | api-delpi | `downstream_access_denied` — nunca persiste evidência ERP | TARGET |
| factory-supply | consumidor de notificações | evento derivado de supply_events | → (futuro) | plataforma | — | dedup natural | FS | fora do caminho síncrono | FUTURE_CONSUMER_EVENT |
| api-delpi | TOTVS | read-only existente | → | existente | existente | — | TOTVS | propagada | PROVEN |

## 42. Decisions frozen

1. `factory-supply-api` — backend dedicado (dir/pacote/mount/schema).
2. Envelope bounded `{success,message,data}` + `data.code` de erro estável.
3. `Idempotency-Key` header + tabela `idempotency_keys` (key,route,actor,request_fingerprint) + replay de snapshot; mesmo escopo+fingerprint → replay; fingerprint divergente → `idempotency_conflict` (algoritmo congelado FS-C0.T6: canonical-JSON tipado + SHA-256, §10).
4. `expected_version` + `version` — conflito 409 `version_conflict`; sem last-write-wins.
5. `overall_stage` derivado no backend; `available_actions` semânticas; frontend nunca rederiva.
6. ERP evidence: `matched|not_found|unknown|unavailable|divergent` com semântica fechada (§26); 401/403 downstream são falha de integração/AuthZ (`downstream_access_denied`), nunca evidência persistida.
7. `branch` em query/body, validado server-side; dados persistidos branch-scoped.
8. TIMESTAMPTZ + ISO 8601 instants; unidade+NUMERIC em toda quantidade; sem soma entre unidades incompatíveis.
9. Auditoria append-only `supply_events` na mesma transação; ator = `id/sub` + display snapshot; sem tokens persistidos.
10. `EVENT_BUS_REQUIRED_NOW=NO`; `OUTBOX_REQUIRED_NOW=YES` (corrigido FS-C0.T5-realtime: delivery portal retryable/dedup/pós-commit — §33); realtime hub local + presence `FACTORY_SUPPLY_APP` + diff/checkpoint + cold-start anti-flood; `SYNC_CADENCE=TO_BENCHMARK`.
11. `TOTVS_WRITE_SUPPORT=NO`, `DIRECT_MFE_TO_API_DELPI=NO`, `LINE_FEEDER_RUNTIME_DEPENDENCY=NO`.
12. Catálogo de comandos §14 e queries §15 (contratos conceituais congelados; nomes de operationId `TARGET`).
13. Batch api-delpi obrigatório para fan-out; nenhuma rota ilimitada; cursor para histórico.
14. api-delpi: 13 reuse + 0 evolve obrigatório + 0 new — `NEW_API_DELPI_ROUTES_REQUIRED = NO` (§27 inspeção bounded; FS-C0.T1 confirmou campos; `movement_recno` é evolução opcional não-bloqueante §25).
15. RBAC de usuário **FROZEN** (Product Master, FS-C0.T3): exatamente 3 permissões — `factory-supply.access` + `factory-supply.view.filial-01` + `factory-supply.view.filial-02`; sem permissão por comando/superfície; `.view.filial-*` = escopo de filial (leitura+escrita), convenção `PROVEN` em production-control.
16. Service identity **FROZEN** (FS-C0.T5): jobs in-process `demand_signal_sync`/`erp_evidence_reconcile` em `factory-supply-api`; auth api-delpi via `API_DELPI_INTERNAL_SERVICE_TOKEN` + `X-Delpi-Caller-App` (`PROVEN`); `SERVICE_PERMISSION_CODES_REQUIRED=NO`, `SERVICE_ACCOUNT_REQUIRED=NO`, `INTERNAL_ENDPOINTS_REQUIRED=NO`; multi-instância por env-flag single-replica; nunca excedem read-only ERP.

## 43. Decisions not frozen

1. Algoritmo exato de derivação de `overall_stage` (owner=backend congelado; regra detalhada na implementação a partir das dimensões Doc 2/5).
2. Semântica de reconciliação pedido↔sinal existente (§29) — decisão de produto pendente.
3. Regra de quantidade de retorno (`RETURN_QUANTITY_RULE = TO_INVENTORY` herdado).
4. Prioridade/score (`priority_score = NOT_SUPPORTED` até política existir — expostos `due_at|overdue|time_to_need` factuais).
5. ~~Escopo de escrita por filial~~ — RESOLVIDO FS-C0.T3: `.view.filial-*` é escopo de filial e gateia writes (precedente `PROVEN`: `assert_can_view_branch` em mutações do Line Feeder); composição congelada `access` + `view.filial-{branch}` (§40-A).
6. Cache operacional (TTL/fail-open) — `TO_DESIGN`; v1 sem cache semântico.
7. Header exato de correlação propagado ao api-delpi — `TO_INVENTORY` convenção do gateway.
8. Forma interna de `matched_ref`/fingerprint de movimento — pendente da confirmação de ID estável (§25).
9. ~~Algoritmo de `request_fingerprint`~~ — RESOLVIDO FS-C0.T6: canonical-JSON tipado + SHA-256, escopo `(key,route,actor_user_id)`, single-tx claim+mutation+snapshot, replay `idempotent_replay:true`, falha não consome key (§10). Retenção de `idempotency_keys` permanece `TO_FS_C0_T12`.
10. ~~Identidade das capacidades de serviço~~ — RESOLVIDO FS-C0.T5: in-process + shared service token (§40-B); sem service account, sem permissões Core.
11. Gatilho interativo opcional para refresh manual de evidência ERP — se existir, coberto por `access`+`filial` (§40-B; decisão UX).

## 44. TO_INVENTORY

| Item | Bloqueia |
|---|---|
| ~~Campos de `get_product_internal_movements`~~ — RESOLVIDO FS-C0.T1: sem ID estável; fingerprint composto §25 é o baseline | — |
| ~~Campos de `list_production_order_operation_materials(_batch)`~~ — RESOLVIDO FS-C0.T1: SD4 `original_qty/open_qty/consumed_qty/commitment_count`; batch sem cap server-side → FS auto-chunk obrigatório | — |
| Estabilidade de `R_E_C_N_O_` como identidade persistente (pack/reorg Protheus) — decide se EVOLVE_EXISTING `movement_recno` vale a pena sobre o fingerprint | §25, C8 |
| ~~Catálogo de armazéns~~ — RESOLVIDO §27: REUSE_AS_IS + composição BFF (sem nova rota) | — |
| Convenção de header de correlação no gateway portal→api-delpi | §32 |
| ~~Política de escopo de escrita por filial~~ — RESOLVIDO FS-C0.T3: `.view.filial-*` = escopo de filial (leitura+escrita), precedente `PROVEN`; composição `access`+`filial` congelada §40-A | — |
| ~~Registro das 3 permissões~~ — RESOLVIDO FS-C0.T4: contrato de manifesto, sync declarativo (`sync_module`), atribuição via `rbac.manage`+`roles.manage`, resolver `/me`, default DENY, fail-closed documentados em §40-A — apenas execução pendente | — |
| ~~Tabela/serviço de conversão de unidades~~ — RESOLVIDO FS-C0.T7: `NOT_REQUIRED`; unidade autoritativa `B1_UM` provada em todos os contratos (§51) | — |
| ~~Identidade de serviço~~ — RESOLVIDO FS-C0.T5: in-process jobs + `API_DELPI_INTERNAL_SERVICE_TOKEN` (§40-B); sem service account/permissões Core | — |
| ~~Algoritmo de `request_fingerprint`~~ — RESOLVIDO FS-C0.T6: canonical-JSON+SHA-256, convenção `(key,route,actor_user_id)` + coluna `request_fingerprint`+`response_status` (§10, §39); helper local (sem consumidor cruzado provado) | — |
| Retenção de idempotency_keys e volume estimado de supply_events | §23 |
| Empenho como campo vs rota dedicada (hoje via operation materials — confirmar) | §41 |
| Decisão de produto: reconciliação pedido×sinal (§29) e regra de retorno | comandos |

## 45. Inputs for Documentation 5/5

1. Sequência de implementação: migrations → backend scaffold → rotas query → comandos → sync → MFE wiring → cockpit boundary.
2. Requisitos testáveis por contrato: por comando (authz, EV, key, pós-condição), por query (paginação, filial), por estado ERP (§26), por reconciliação (§29).
3. Itens TO_INVENTORY desta doc viram tarefas de inventário/decisão do roadmap.
4. Critérios de aceite do gate de qualidade (§58 da tarefa) mapeados para testes de contrato.
5. Cutover Line Feeder: checklist de paridade + depreciação governada.
6. Manifesto do plugin `factory-supply` + registro das 3 permissões Core (§40-A; implementation phase).

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
- Ports exigidos pelo domínio/aplicação: `SupplyMissionRepositoryPort`, `DemandSignalRepositoryPort`, `HandoffRepositoryPort`, `ErpObservationRepositoryPort`, `SupplyEventRepositoryPort`, `IdempotencyRepositoryPort`, `IntegrationOutboxRepositoryPort`, `IntegrationCheckpointRepositoryPort` (precedentes `PROVEN` requests-api/commercial-api), `RealtimeHubPort` (entrega WS — §33), `PortalNotificationPort` (fallback offline — precedente `CoreNotificationAdapter`), `ProductionReadGateway` (OPs/operações/materiais/CTs), `StockReadGateway` (saldos/locations/blocks), `MovementReadGateway` (movimentos internos), `MasterDataGateway` (produtos/warehouses), `ClockPort`/`UnitOfWorkPort`.
- Chamada HTTP externa **fora** da transação DB do agregado (platform-data-persistence §Transações): leituras ERP acontecem antes do commit; observações persistidas guardam só resultado.

## 47. Contract ownership (API surface)

| Superfície | Owner | Contém | Não contém |
|---|---|---|---|
| `/apps/factory-supply-api/v1/*` | factory-supply-api | semântica de produto: missões, sinais, preparo, coleta, handoff, entrega, devoluções, histórico, projeções | fatos ERP, SQL genérico, cache de verdade TOTVS |
| `/apps/api-delpi/*` (ou mount atual) | api-delpi | fatos autoritativos ERP/TOTVS (OPs, materiais, saldos, movimentos, CTs, master data) | workflow/policy do Factory Supply, rotas nomeadas para o produto |

Rotas novas na api-delpi só quando o fato ERP não tem contrato tipado (§27). Nunca usar rota de SQL genérico como bypass (§30 da tarefa — não existe tal rota canônica para consumo direto; toda falta vira contrato tipado novo).

## 48. Available-action projection

`available_actions: string[]` em respostas de missão — códigos técnicos dos comandos §14 atualmente permitidos **pelo estado do agregado** (não por papel do usuário). Owner: serviço de aplicação/domínio. Caráter: **metadado consultivo de UX** — não é autorização: toda rota de escrita revalida permissão + invariante + versão. **`available_actions` ≠ catálogo de permissões** — a disponibilidade da ação deriva de filial autorizada + estado de domínio + invariantes (§40-A); RBAC de usuário é só `access`+`filial`. Semântico (verbos de domínio), não nomes de botão. Convenção repo compatível: payloads já carregam flags derivadas (`PROVEN` — LineFeederRequirementCard consome `can_*`-style derivados do backend em production-control).

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

- **Tipo:** `NUMERIC` no banco (alvo `NUMERIC(18,6)` — precedente `PROVEN` `DECIMAL(18,6)` em `stock_balances_sql.py`); JSON number com precisão decimal — **nunca** float binário para quantidade (`platform-data-persistence`). **Caveat de fronteira:** api-delpi serializa quantidades SD4 como float (`CAST AS FLOAT` + `float()` — PROVEN em `operation_materials_item.py`); o gateway FS converte na entrada `Decimal(str(value))` — nunca opera/persiste o float bruto. Comparação: **Decimal exato** — `QUANTITY_TOLERANCE = EXACT_DECIMAL_COMPARISON` (sem tolerância inventada).
- **Unidade — política congelada FS-C0.T7 (`AUTHORITATIVE_TOTVS_UNIT`):** `unit` = código `SB1.B1_UM` autoritativo — **mesma fonte em todos os contratos consumidos**: operation-materials (`unit`, PROVEN join `P.B1_UM`), internal-movements (`unit` ← `SB1.B1_UM`), stock-balances items (`unit_of_measure` ← `MAX(NULLIF(TRIM(B1_UM),''))`), demand_signals (`unit` do sinal). `get_product_stock` **omite** unit → compor via `B1_UM` do master data/produto no mesmo `product_code` (nunca inferir).
- **Sem conversão:** `UNIT_CONVERSION_ENGINE=NOT_REQUIRED`, `UNIT_CONVERSION_TABLE=NOT_REQUIRED`, `UNIT_CONVERSION_CONFIGURATION=NOT_REQUIRED`, sem UI de configuração. SD4 soma `original_qty/open_qty/consumed_qty` já agrupadas por `(product_code, B1_UM)` — interpretadas na unidade retornada, sem relabel.
- **Sem agregação entre unidades incompatíveis:** contagens agregadas são de itens/missões (inteiros); somas de quantidade só dentro de `product_code × unit` idênticos — card de missão nunca soma `100 KG + 50 MT`.
- **Validação de escrita:** quantidade = `Decimal` válido, não-negativo onde aplicável; `unit` do comando **idêntica** à `accepted_unit` do item (não "conversível" — igualdade exata); divergente → `422 domain_rule_violation`; caller não submete unidade alternativa; MFE nunca é validador final.
- **Unidade ausente/desconhecida:** estado explícito `unit_unknown` de qualidade de dado — nunca default silencioso; **writes que mudam quantidade falham fechado** quando a unidade autoritativa está indisponível; leitura/exibição mostra "unidade indisponível".
- **Divergência de unidade (`UNIT_DIVERGENCE`):** se sync autoritativo retornar unidade diferente para o mesmo material/contexto de um item já operado → classificar como divergência de unidade (exceção persistente §33), **não** delta numérico; quantidades históricas preservam a unidade registrada; nunca subtrair entre unidades distintas.
- **Correlação ERP:** compara `material × branch × quantity × unit` (+ fingerprint §25); igualdade numérica com unidade diferente → `DIVERGENT` (não `MATCHED`); unidade do movimento ausente → `unknown` (não MATCHED).
- **Arredondamento/exibição:** backend persiste e compara `NUMERIC(18,6)` exato; UI formata PT-BR (`126,895 MT`) só na exibição — formatação nunca muta o valor persistido; sem precisão máxima por unidade além da escala 6 (não inventar arredondamento de negócio).
- **`null` semântico:** `returned_qty`/`prepared_qty` etc. `null` = não estabelecido — distinto de `0` (Doc 3/5 — "quantidade não estabelecida" é caso real de devolução); `null` nunca carrega unidade implícita.
