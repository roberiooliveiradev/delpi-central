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
- **Retenção:** `24_HOURS` replay window — CONGELADO FS-C0.T12 (§52; precedente requests-api `max_age_hours=24`); após a janela a key expira e retry exige nova intenção; claim in-flight nunca deletado; auditoria vive em `supply_events` (§31, §52).
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

Notas: `record-collection` cobre "iniciar coleta" — a primeira coleta registrada marca a dimensão em progresso (não inventar comando separado sem justificativa). Quantidade de retorno pode ser `null` quando não estabelecida (Doc 3/5 — sugestão híbrida `PARTIAL` até P2-B, §53).

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

## 28. Operator Cockpit future integration (CONGELADO FS-C0.P1)

**Inventário do estado atual do Cockpit (PROVEN):** Operator Cockpit = superfície **pública** do bounded context `production-control` — `public-hub` `/p/production-control/cockpit/{token}` → rotas `/public/machine-load/{token}/*` em `production-control-api` (somente leitura + `POST /{token}/bench-sessions` com `operator_code`/`operator_name` **auto-declarados** via `X-Delpi-Bench-Session`). **Não há JWT Keycloak no surface** — operadores de chão de fábrica não são usuários Portal. `plugins/production-control/.../operatorCockpitLink.ts` gera os links. Nenhuma rota "request material" existe hoje → tudo `TARGET`.

**Consequência de AuthZ (modelo fechado):** o pedido do operador **não é comando com RBAC de usuário** — não existe usuário Keycloak para propagar. A fronteira é **service-to-service**: `production-control-api` (BFF do cockpit) → `factory-supply-api` com **identidade de serviço confiável** (padrão `PROVEN`: `X-Delpi-Service-Token` + `X-Delpi-Caller-App`; precedente de trusted-caller por rota `PROVEN` em `api-delpi/.../supplies_bff_service_access.py`). O FS expõe a rota para o caller `production-control-api` **sem** `factory-supply.access` de usuário (que exigiria usuário); valida: caller trusted + payload de domínio (filial válida, material existe, unidade = `B1_UM`, qty Decimal>0, intent ∈ {anticipate,additional}). `operator_ref` = `operator_code`/`operator_name` declarados — **dado de negócio auditável, nunca autoridade de acesso**. Usuários FS (almoxarife/feeder) seguem RBAC normal nas ações operacionais subsequentes.

**Contrato semântico futuro (FUTURE, não implementar):** `POST /v1/operator-requests` — serviço `production-control-api` → FS. Payload: `{branch, work_center, op_order?, operation_seq?, product_code, requested_qty, unit, intent, candidate_signal_id?, operator_ref, reason?, requested_at, correlation_ref?}` + headers `Idempotency-Key` (Cockpit gera por intenção — FS-C0.T6), `X-Request-ID` (T11), `X-Delpi-Service-Token`+`X-Delpi-Caller-App: production-control-api`.

- FS valida tudo no estado **corrente** — `candidate_signal_id` e quantidades exibidas ao operador são hints, nunca autoridade; estado stale → reavaliação server-side (concorrência §10/§11: match+reconcile dentro da tx, `expected_version`/lock de sinal quando aplicável).
- Resposta: `{request_id, status(received|reconciled|conflict), reconciled_signal_id?, current_state}` — `conflict` determinístico (sem saldo elegível / sem sinal compatível / unidade divergente) devolve contexto p/ o Cockpit decidir UX; **nunca** split automático.
- Reconciliação: `ANTICIPATE` → link `operator_request.reconciled_signal_id` + semântica de urgência no sinal (qty planejado inalterado); `ADDITIONAL` → `demand_signal` `source=operator_request` próprio vinculado ao request (planejado intacto).
- Workflow resultante entra nos mecanismos aceitos (outbox §33 → realtime/notificação para usuários FS autorizados); **sem** canal realtime dedicado ao Cockpit até requisito provado.
- Sem TOTVS write (`FACTORY_SUPPLY_TOTVS_WRITE = NO`); sem acesso Cockpit ao DB FS; sem imports cross-context.

## 29. Duplicate-request reconciliation (RESOLVIDO FS-C0.P1)

Propriedade da reconciliação: **aplicação/domínio do Factory Supply**, não do Cockpit nem do MFE.

- Pedido chega com `intent` explícita → FS avalia `demand_signals`/`mission_items` ativos na mesma `(branch, work_center, material, unit)` + contexto de produção (`op_order`/`operation_seq` quando presente) + janela compatível (`need_at` — algoritmo de janela `TO_DESIGN`).
- `ANTICIPATE` → **vínculo** ao sinal compatível (`reconciled_signal_id` + marcação `operator_requested`/urgência); quantidade planejada inalterada; `requested_qty` > saldo elegível → `conflict` (nunca auto-split para ADDITIONAL).
- `ADDITIONAL` → **novo fato** (`demand_signal` `source=operator_request` vinculado ao `operator_request`); planejado inalterado.
- Sem `intent` compatível → `409 conflict`/`422` determinístico; sem sinal compatível para `ANTICIPATE` → `conflict` com contexto.
- Congelado: **nunca** dobrar quantidade silenciosamente; todo pedido gera `operator_requests` auditável próprio (§39) — evidência durável mesmo sem missão imediata.

## 30. Line Feeder coexistence/cutover

- `LINE_FEEDER_RUNTIME_DEPENDENCY = NO`. Zero chamadas/importações de `production-control-api`.
- Line Feeder permanece operacional e intacto; suas tabelas `production_control.*` **não** são fonte do Factory Supply nem recebem escrita cruzada.
- Sem dual-write, sem migração silenciosa. Cutover só após paridade funcional + aceite de produto + migração explícita aprovada (Doc 5/5 sequencia).
- Grão per-product do V007 **não** reutilizado — Factory Supply preserva mission+item com rastreabilidade por destino/CT.
- Última-milha: permissões distintas (`factory-supply.*` vs `production-control.*`) impedem confusão de ownership.

## 31. Audit

Auditoria de domínio ≠ log técnico. `supply_events` append-only:

`{event_id, mission_id, item_id?, event_type(command|transition|erp_observation|signal_sync), action, actor_user_id, actor_display_name, prev_state?, new_state?, qty_delta?, reason?, idempotency_key?, correlation_id?, created_at}` — `correlation_id` = identificador `X-Request-ID` da requisição/execução de job (§32); `request_id` separado **removido** no modelo SINGLE_ID (redundante — o request id **é** o correlation id).

- Gravado na **mesma transação** do agregado — transição sem evento não existe.
- Append-only lógico; nunca update/delete (retenção: **5 anos** — CONGELADO FS-C0.T12 §52; `actor_display_name` elegível a anonimização após 2 anos conforme padrão canônico ROPA audit_logs 730d; rastreabilidade é o produto).
- Logs de aplicação não são auditoria.

## 32. Observability

Conforme `platform-reliability-observability.mdc`/`observability-standards.mdc`:

- Logs estruturados: `correlation_id`, `operation_id`, `route`, `actor_user_id` (ou `job_name`+`run_id` em jobs), `branch`, `duration_ms`, outcome; sem tokens/segredos/payloads ERP sensíveis.

**Correlation contract (CONGELADO FS-C0.T11 — modelo `SINGLE_ID`):**

- **Header canônico:** `X-Request-ID` — inventário prova que **nenhum** header de correlação existe hoje (gateway sem injeção, `shared/delpi_auth` sem request-id, api-delpi `request_observability_middleware` só propaga `X-Operation-Id`/`X-Response-Time-Ms`, bounded APIs e portal client sem correlação). Convenção de headers custom é `X-*`/adapter-propagated (`X-Delpi-Caller-App` PROVEN). FS adota `X-Request-ID` como candidata a convenção de plataforma — sem `traceparent`/W3C (não PROVEN) e sem segundo ID: o request id **é** o correlation id propagado entre hops (`SINGLE_ID`, menor modelo compatível com `observability-standards` "reutilizar header canônico existente").
- **Formato:** UUID4 (`gen_random_uuid`/uuid4 — convenção PROVEN do repo para identificadores).
- **Inbound:** aceita `X-Request-ID` válido (string não-vazia, ≤120 chars, charset seguro); ausente/malformado → **gera servidor-side** (nunca rejeita por metadado de observabilidade); valor do cliente nunca é autoridade (só rastreio). Bind em contextvar (padrão `request_context.py` api-delpi). **Response:** ecoa `X-Request-ID` no header da resposta (precedente `X-Operation-Id` echo); envelope `fail` inclui `error.correlation_id` p/ suporte (mensagem amigável + referência técnica; sem stack).
- **Downstream api-delpi:** gateway FS propaga `X-Request-ID` junto a `X-Delpi-Caller-App` nos adapters (mesmo padrão `headers={...}` PROVEN). api-delpi hoje ignora header desconhecido — propagação é aditiva e segura; quando api-delpi adotar o padrão, o FS já está correto.
- **Idempotência × correlação:** `Idempotency-Key` = identidade semântica de retry; `correlation_id` = identidade de rastreio — conceitos distintos. Replay idempotente: o evento de negócio original preserva seu `correlation_id`; o retry carrega **novo** `correlation_id` apenas em logs/telemetria (sem segundo `supply_events`, sem novo outbox).
- **Audit:** `supply_events.correlation_id` persiste o ID da requisição/job que causou o evento (liga ação→comando→auditoria→outbox→notificação); não substitui `event_id`/`aggregate_id`/`actor`/`idempotency_key`.
- **Outbox:** `integration_outbox.correlation_id` copiado da transação de origem — entrega WS/notificação rastreável até o comando/run que a gerou.
- **Jobs (`demand_signal_sync`, `erp_evidence_reconcile`):** cada run gera `correlation_id` UUID4 próprio + `job_name`/`run_id` nos logs — propagado para leituras api-delpi, mutações, audit (`actor_type=system`), outbox e telemetria. Não se personifica request de usuário.
- **Async multi-etapa:** reconciliação posterior **nova** correlation por execução + link via `aggregate_id`/`mission_item_id` + referência ao evento originador (`handoff`/`delivery` id no payload) — sem `causation_id` (não PROVEN) e sem correlação eterna entre jobs.
- **WebSocket payload:** `{event_id, event_type, aggregate_id, occurred_at, dedupe_key?, correlation_id?}` — correlation só como metadado de diagnóstico; frontend nunca o usa para lógica de negócio.
- **Notificação portal:** `dedupeKey`+`actionTarget` (§33) permanecem os campos canônicos; `correlation_id` pode ir em `payload.metadata` se o catálogo suportar — nunca como dedupe key nem visível ao usuário final.
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
| 12b | FS | POST | `/v1/operator-requests` | create_operator_request | W | **trusted service caller** (`X-Delpi-Service-Token`+`X-Delpi-Caller-App: production-control-api` — cockpit é superfície pública sem JWT usuário; `operator_ref` = dado de negócio) | KEY | — | — | valida filial/produto/unidade/sinal corrente (§28) | PLANNED_NEW (FS-C0.P1) |
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
| api-delpi | get_production_losses_records | /production/losses/records | evidência perda MP (`R`/`S`) → sugestão retorno (§53) | REUSE_AS_IS — somente se P2-B decidir usar |
| api-delpi | get_production_losses_top_materials | /production/losses/top-materials | idem agregado | REUSE_AS_IS — idem |
| api-delpi | list_production_appointments* | /production/appointments/* | contexto produzido/perdido PA (§53.1) | REUSE_AS_IS — contexto, não fórmula |
| api-delpi | — | movimentos `TM 999` / devolução tipada / saldo-99-por-OP | confirmação de retorno | **GAP §53.4** — avaliar `EVOLVE_EXISTING`/nova rota no P2-B |
| api-delpi | get_product_detail / get_product_summary | /products/{code}/… | master data | REUSE_AS_IS |
| api-delpi | ~~list_warehouses~~ | — | fatos de armazém cobertos por composição (§27) | NOT_NEEDED |

Contagem: FS 26 superfícies planejadas (11 query/meta + 13 comandos + 1 WS + 1 job). api-delpi: 13 reuse + 1 evolve + 0 new.

## 39. Complete data model matrix

Schema `factory_supply` — todas `PLANNED` (DDL na implementação; sem SQL aqui).

| Tabela | Propósito | PK | Campos-chave | UNIQUE/FK | Branch | Version | Índices | Status |
|---|---|---|---|---|---|---|---|---|
| supply_missions | raiz do agregado | id UUID | branch, destination_work_center, need_window_start/end, op_order, operation_seq, product_context, feeder_user_id, collection_round_ref, lifecycle_status, overall_stage cache?, version, created_by/at, closed_at, cancel_reason | — | sim | version INT | (branch, lifecycle_status), (branch, destination, need_window_start), (feeder_user_id) | PLANNED |
| supply_mission_items | itens do agregado | id UUID | mission_id FK, seq, product_code, unit, qty_required/requested/prepared/collected/delivered/returned NUMERIC, dim status, snapshots (desc, location, stock_at_decision, committed_at_decision), exception | UNIQUE(mission_id,seq) FK→missions | via mission | herdada | (mission_id), (branch implícito via join) | PLANNED |
| demand_signals | necessidades planejadas/operacionais | id UUID | signal_key, source, branch, work_center, op_order, operation_seq, product_code, unit, qty_needed, need_at, status, fingerprint, synced_at | UNIQUE(branch,signal_key) WHERE status='active' | sim | — | (branch,work_center,need_at) | PLANNED |
| mission_demand_links | reconciliação signal↔missão/item | id UUID | signal_id FK, mission_id FK, mission_item_id FK?, link_type(planned|operator_requested), created_at | UNIQUE(signal_id,mission_item_id) | via mission | — | (mission_id) | PLANNED |
| operator_requests | evidência durável de pedido de operador (FS-C0.P1 §28) | id UUID | branch, work_center, op_order?, operation_seq?, product_code, unit, requested_qty NUMERIC, intent(anticipate|additional), candidate_signal_id?, reconciled_signal_id FK?, operator_ref JSONB{code,name}, reason?, status(received|reconciled|conflict|rejected|fulfilled), outcome_ref JSONB?, idempotency_key, correlation_id, requested_at, decided_at, created_at | dedupe por `idempotency_keys` (mesma convenção §10 — sem UNIQUE extra); FK→demand_signals | sim | — | (branch,work_center,product_code), (reconciled_signal_id), (requested_at) | PLANNED |
| handoffs | custódia por item | id UUID | mission_item_id FK, direction(collection|delivery|return), from_actor_user_id, to_actor_user_id?, to_context, qty NUMERIC, unit, at, note | FK→items | via item→mission | — | (mission_item_id), (to_actor_user_id,at) | PLANNED |
| erp_observations | evidência ERP por item | id UUID | mission_item_id FK, status enum, evidence_fingerprint, matched_ref JSONB?, confidence?, observed_at, source, payload_snapshot JSONB bounded | UNIQUE(mission_item_id, evidence_fingerprint) | via item | — | (mission_item_id,status) | PLANNED |
| supply_events | auditoria append-only | id UUID | mission_id, item_id?, event_type, action, actor_user_id, actor_display_name, prev_state, new_state, qty_delta, reason, idempotency_key, request_id, correlation_id, created_at | — | via mission (denorm branch col para filtro) | — | (branch,created_at) cursor, (mission_id,created_at) | PLANNED |
| idempotency_keys | dedup de comandos | id UUID | key, route, actor_user_id, **request_fingerprint** (SHA-256 canonical-JSON — §10 congelado T6), response_status INT, response_snapshot JSONB, created_at | UNIQUE(key,route,actor_user_id); fingerprint compara dentro do escopo | — | — | (created_at) retenção 24h — §52 | PLANNED (convenção PROVEN + extensão TARGET) |
| integration_outbox | entrega pós-commit (portal notif + realtime routing, §33) | id UUID | event_type, aggregate_type, aggregate_id, **correlation_id** (do comando/run originador — §32), payload JSONB (userIds, permissionCodes, dedupeKey, actionTarget), attempts, next_attempt_at, published_at, created_at | UNIQUE(event_type,aggregate_id,dedupe_key?) — dedupe semântico §33 | branch no payload | — | (published_at NULL, next_attempt_at) | PLANNED (precedente `PROVEN` requests-api V005 + commercial) |
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
| production-control-api (BFF do Cockpit — superfície pública sem JWT usuário) | factory-supply-api | `POST /v1/operator-requests` | → (futuro) | **service identity**: `X-Delpi-Service-Token` + `X-Delpi-Caller-App` (sem `access`/`.view.filial-*` de usuário — não há usuário Keycloak; `operator_ref` declarado = dado de negócio) | validação de domínio FS (§28) | KEY cockpit | BFF | mesmo envelope | FUTURE |
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
2. ~~Semântica de reconciliação pedido↔sinal existente (§29)~~ — RESOLVIDO FS-C0.P1: `intent` explícita `anticipate|additional`, `operator_requests` + boundary service-caller (§28).
3. ~~Regra de quantidade de retorno~~ — RESOLVIDO FS-C0.P2-B: `RETURN_FORMULA_STATUS=READY`, modelo 3-camadas §53.7; evolução `internal-movements` (`D3_NUMSEQ`) aditiva na implementação.
4. ~~Prioridade/score~~ — RESOLVIDO FS-C0.P3: `TIME_TO_NEED_FIRST` (§49); `priority_score = NOT_SUPPORTED` permanece; limiares de banda `TO_DESIGN/TO_BENCHMARK` (não bloqueia).
5. ~~Escopo de escrita por filial~~ — RESOLVIDO FS-C0.T3: `.view.filial-*` é escopo de filial e gateia writes (precedente `PROVEN`: `assert_can_view_branch` em mutações do Line Feeder); composição congelada `access` + `view.filial-{branch}` (§40-A).
6. Cache operacional (TTL/fail-open) — `TO_DESIGN`; v1 sem cache semântico.
7. ~~Header exato de correlação propagado ao api-delpi~~ — RESOLVIDO FS-C0.T11: `X-Request-ID` propagado pelos adapters (padrão `X-Delpi-*` headers); api-delpi ignora hoje, propagação aditiva (§32).
8. Forma interna de `matched_ref`/fingerprint de movimento — pendente da confirmação de ID estável (§25).
9. ~~Algoritmo de `request_fingerprint`~~ — RESOLVIDO FS-C0.T6 (§10). ~~Retenção~~ — RESOLVIDO FS-C0.T12: matriz completa §52 (audit/histórico 5y, idempotency 24h, outbox pub 30d/falho sem TTL, checkpoint corrente, ROPA-compliant).
10. ~~Identidade das capacidades de serviço~~ — RESOLVIDO FS-C0.T5: in-process + shared service token (§40-B); sem service account, sem permissões Core.
11. Gatilho interativo opcional para refresh manual de evidência ERP — se existir, coberto por `access`+`filial` (§40-B; decisão UX).

## 44. TO_INVENTORY

| Item | Bloqueia |
|---|---|
| ~~Campos de `get_product_internal_movements`~~ — RESOLVIDO FS-C0.T1: sem ID estável; fingerprint composto §25 é o baseline | — |
| ~~Campos de `list_production_order_operation_materials(_batch)`~~ — RESOLVIDO FS-C0.T1: SD4 `original_qty/open_qty/consumed_qty/commitment_count`; batch sem cap server-side → FS auto-chunk obrigatório | — |
| Estabilidade de `R_E_C_N_O_` como identidade persistente (pack/reorg Protheus) — decide se EVOLVE_EXISTING `movement_recno` vale a pena sobre o fingerprint | §25, C8 |
| ~~Catálogo de armazéns~~ — RESOLVIDO §27: REUSE_AS_IS + composição BFF (sem nova rota) | — |
| ~~Convenção de header de correlação~~ — RESOLVIDO FS-C0.T11: `X-Request-ID` `SINGLE_ID` (nenhum header canônico existia — gateway/shared/api-delpi/bounded APIs limpos); formato UUID4; propagação adapter-side (§32) | — |
| ~~Política de escopo de escrita por filial~~ — RESOLVIDO FS-C0.T3: `.view.filial-*` = escopo de filial (leitura+escrita), precedente `PROVEN`; composição `access`+`filial` congelada §40-A | — |
| ~~Registro das 3 permissões~~ — RESOLVIDO FS-C0.T4: contrato de manifesto, sync declarativo (`sync_module`), atribuição via `rbac.manage`+`roles.manage`, resolver `/me`, default DENY, fail-closed documentados em §40-A — apenas execução pendente | — |
| ~~Tabela/serviço de conversão de unidades~~ — RESOLVIDO FS-C0.T7: `NOT_REQUIRED`; unidade autoritativa `B1_UM` provada em todos os contratos (§51) | — |
| ~~Identidade de serviço~~ — RESOLVIDO FS-C0.T5: in-process jobs + `API_DELPI_INTERNAL_SERVICE_TOKEN` (§40-B); sem service account/permissões Core | — |
| ~~Algoritmo de `request_fingerprint`~~ — RESOLVIDO FS-C0.T6: canonical-JSON+SHA-256, convenção `(key,route,actor_user_id)` + coluna `request_fingerprint`+`response_status` (§10, §39); helper local (sem consumidor cruzado provado) | — |
| ~~Retenção~~ — RESOLVIDO FS-C0.T12: matriz §52; resta apenas registrar categoria FS na ROPA na implementação (ação docs) e estimar volume `supply_events` em homologação | §52 |
| Empenho como campo vs rota dedicada (hoje via operation materials — confirmar) | §41 |
| ~~Decisão de produto: reconciliação pedido×sinal (§29)~~ — RESOLVIDO FS-C0.P1 | — |
| ~~Decisão de produto: fórmula de retorno~~ — RESOLVIDO FS-C0.P2-B (§53.7); resta evolução aditiva `internal-movements` (`D3_NUMSEQ`/direção tipada) na implementação | — |

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

**DECISÃO `FROZEN` (FS-C0.P3):** `PRIORITY_POLICY = TIME_TO_NEED_FIRST`; `priority_score = NOT_SUPPORTED` permanece — sem score opaco, sem AI/ML.

Backend computa por fila (worklist): `ELIGIBILITY(stage-aware) → OVERDUE(need_at<now ∧ ação pendente, derivado — nunca flag) → need_at ASC → tie-breakers` (creation seq → stable item id; sem significado de negócio).

- Filas por estágio: **warehouse** (preparável) × **feeder** (coletável) — não-acionável aparece como `waiting`/`blocked`, nunca como próxima ação executável;
- campos do DTO de worklist/Kanban: `need_at`, `stage`, `eligibility` (`actionable|waiting|blocked`), `overdue`, `priority_reason` (explicável, string de domínio), `blocked_reason?`, `urgency_band?` (`ATRASADO|URGENTE|ALTA|NORMAL|FUTURA` — limiares `TO_DESIGN/TO_BENCHMARK`, backend-owned; ausentes até definidos);
- operator request: sem boost — ANTICIPATE reconciliado reordena pelo `need_at` resultante; ADDITIONAL compete pela mesma política;
- shortage/exceção ERP: `blocked`/warning, não prioridade — `ACTIONABILITY != IMPORTANCE`;
- urgência nunca altera `stage`/lifecycle; reordenação por realtime via outbox aceito.

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

## 52. Retention + cleanup contract (CONGELADO FS-C0.T12)

**Governança encontrada (PROVEN):** ROPA `docs/13-auditoria-lgpd/ropa-registro-tratamento.md` + constantes canônicas `core-api/app/domain/lgpd/privacy_constants.py::DATA_RETENTION_DAYS` (`audit_logs=730` com **anonimização** de IP/payload — não delete; `notifications=180`, `deleted_notifications=30`, `usage_*=365`, `consent_records=1825`) + job canônico `core-api/app/infrastructure/jobs/data_retention_job.py` (CLI `flask data-retention run`, agendado ~24h, UPDATE de anonimização + DELETE por cutoff, `logger.info` com contagens). **Sem política que exceda/conflite com os targets do Product Master** — regra superior não existe; precedente de 5 anos existe (`consent_records=1825` — evidência legal). **Sem conflito de governança** — mas com obrigação de minimização PII (ver abaixo).

| Classe | Tabela(s) | Retenção-alvo | Início do relógio | Exceção ativo/não-resolvido | Evidência/base |
|---|---|---|---|---|---|
| A. Auditoria de domínio | `supply_events` | **5 anos** (Product Master; precedente legal 1825d) | `created_at` | append-only; nunca purge rotineiro antes do prazo | legítimo interesse/rastreabilidade (ROPA §2) |
| B. Histórico operacional | `supply_missions`, `supply_mission_items`, `handoffs`, exceções resolvidas | **5 anos** | `completed_at`/`cancelled_at` (estado terminal) | ativo/aberto **nunca** purgado por idade | Product Master |
| B2. Divergências resolvidas | exceptions/`UNIT_DIVERGENCE`/`divergent` resolvidos | **5 anos** com o histórico | `resolved_at` | não-resolvido nunca purgado | Product Master |
| C. Idempotência técnica | `idempotency_keys` | **24 h replay window** | `created_at` | claim in-flight nunca deletado (UNIQUE-wait §10) | PM + precedente requests-api `max_age_hours=24` |
| D. Outbox publicado | `integration_outbox` (`published_at NOT NULL`) | **30 dias** | `published_at` | — | PM (transporte técnico; evento de negócio vive em A) |
| D2. Outbox pendente/falho | `integration_outbox` (`published_at NULL`) | **sem TTL por idade** — retry→published→30d; dead-letter = `TO_IMPLEMENTATION_DESIGN`, preservado até resolução explícita | — | nunca purge por idade | PM |
| E. Checkpoints de sync | `integration_checkpoints` | **estado corrente + histórico técnico mínimo** (geração anterior só até substituição confirmada) | `updated_at` | checkpoint corrente **nunca** removido (anti cold-start §33) | PM |
| F. Observações ERP | `erp_observations` | com o histórico operacional que referenciam (**5 anos** quando ligadas a item/missão retida); snapshots ERP contínuos não retidos só por existir | `observed_at` | evidência referenciada por histórico retido nunca órfã | PM + §19 |
| G. Logs/métricas técnicas | fora do schema | `PLATFORM_OWNED / OUT_OF_SCOPE` — FS emite telemetria, não cria política própria | — | — | plataforma |

**PII/minimização (ROPA-compliant):** `supply_events` guarda `actor_user_id` + `actor_display_name` (snapshot). Alinhado ao padrão canônico de anonimização (audit_logs 730d → campos pessoais nulados, linha preservada): `actor_display_name` elegível a anonimização após **2 anos**; `actor_user_id`+fatos de negócio persistem os 5 anos (rastreabilidade legítima — mesma lógica de `consent_records=1825`). **Obrigação de documentação:** registrar categoria Factory Supply na ROPA na implementação (ação docs, não runtime). Nunca persistir JWT/service token/email/claims — retenção não autoriza coletar mais.

**Direitos do titular/legal hold:** mecanismo canônico = anonimização (UPDATE nulando campos pessoais — `data_retention_job`), não delete de auditoria; exclusão de titular segue fluxo Core ("anonimizado após solicitação" — ROPA §1). **LEGAL_HOLD_SUPPORT = NOT_PROVEN** — nenhum mecanismo de legal hold existe; FS não inventa.

**Cleanup ownership/execution:** `factory_supply_retention_cleanup` — job **in-process** em factory-supply-api (modelo T5: env-flag `FACTORY_SUPPLY_JOBS_ENABLED`, single-run; sem service identity — trabalho local no próprio schema). Sem Core/api-delpi/pc-api tocando tabelas FS. Lotes limitados, predicados indexados (`created_at`/`published_at`/`status`), sem table lock, retry-safe, `correlation_id`+`job_name`/`run_id` por execução, métricas de contagens (padrão `logger.info(results=...)` do job canônico). **CLEANUP_CADENCE = TO_BENCHMARK** (precedente diário ~24h do core retention job é candidato default, não congelado).

**Ordem segura (conceitual):** (1) `idempotency_keys` >24h não-in-flight → (2) `integration_outbox` publicado >30d → (3) gerações obsoletas de `integration_checkpoints` (nunca o corrente) → (4) histórico operacional >5y em estado terminal (quando elegível, com dependents preservados: não deletar pai enquanto auditoria/evidência retida depender). Purge técnica ≠ purge de auditoria — classes distintas, nunca o mesmo predicado.

**Pós-condições de purge:** sucesso só se o DB provar: elegíveis removidos + inelegíveis retidos + ativos intactos + integridade referencial preservada. "DELETE executou" não é evidência.

**Anti-recursão de auditoria:** cleanup técnico emite telemetria de execução (contagens), **não** `supply_events` por linha deletada; purge de histórico de negócio (se um dia aplicável) gera no máximo um registro governamental sumarizado — nunca evento por linha.

**Backup ≠ retenção:** remoção do banco ativo não implica remoção imediata de mídia de backup — lifecycle de backup é infra/plataforma; sem promessas de eliminação LGPD além do provado.

**Índices candidatos (defer físico p/ migration design):** `idempotency_keys(created_at)`, `integration_outbox(published_at NULL, next_attempt_at)` já planejado + `(published_at)`, `supply_events(created_at)`, `missions(status, completed_at)` se coluna existir — colunas novas só se o lifecycle não expuser equivalente (`completed_at`/`resolved_at` avaliados no DDL V001).

---

## 53. Return evidence inventory (CONGELADO FS-C0.P2-A — inventário, não fórmula)

**Decisão PM:** `RETURN_POLICY = HYBRID` — FS **pode** sugerir quantidade de devolução a partir de fatos autoritativos; sugestão é explicável e **nunca** verdade de estoque; confirmação reconcilia contra evidência ERP de saldo/movimento. Apontamentos TOTVS (produção/refugo/setup/perda) jamais são escritos pelo FS (`FACTORY_SUPPLY_TOTVS_WRITE = NO`). `SUGGESTED_RETURN_QTY ≠ CONFIRMED_RETURN_QTY`.

### 53.1 Inventário de fatos autoritativos (PROVEN — fonte: api-delpi working tree)

| Fonte | Tabela(s) | Campos/semântica | Rotas/contratos PROVEN | Impacto em quantidade |
|---|---|---|---|---|
| Apontamento de produção | `SH6010` (`H6_TIPO=P`) + `SH1010`→`SHB010` (CT) + `SYS_USR` | OP, produto PA, operação, recurso→CT, operador, ini/fim, `H6_QTDPROD`, `H6_QTDPERD` (perda do **PA apontado**, unidade `B1_UM` do PA, conversão MI), `R_E_C_N_O_` | `list_production_appointments*`, `get_production_appointments_*` | `QTDPROD` última operação do PA = origem do `SD3 PR0` (entrada estoque — mesmo fato, doc `producao-entrada-estoque.md`). `QTDPERD` = PA perdido na operação — **não** é perda de MP |
| Apontamento de operação | `HZA010` | `HZA_STATUS` 1=rodando·2=encerrado c/ apontamento·3=descartado, `HZA_TPTRNS` 1=m.o.·2=máquina, `HZA_IDAPON`→SH6 | machine-load (agregado interno) | **STATUS/TIME_ONLY** — zero campos de quantidade; dedup SH6 via `IDAPON` |
| Perdas de material | `SBC010` + `SB1` + `SC2` + `CYO` + `SYS_USR` | `BC_TIPO` `R`=refugo/`S`=scrap (mutuamente exclusivos por linha), `BC_PRODUTO`=MP (`B1_TIPO=MP` no repo losses), `BC_QUANT`, unit=`B1_UM` do MP, OP, operação, recurso, motivo, operador, data; **`BC_SEQSD3`→SD3**, **`BC_IDENSH6`→SH6** | `get_production_losses_records`, `get_production_losses_top_materials`, rotas `refugos/*` (`R` apenas, exclui MP de terceiro) | **QUANTITY_AFFECTING** — perda de MP por OP/material |
| Empenho/consumo | `SD4010` + `SB1` (+`SH8` p/ CT) | `D4_COD`=componente, `D4_PRODUTO`=PA pai, `D4_QTDEORI`=empenho original, `D4_QUANT`=saldo empenhado, `D4_QTNECES`=requerido; **`consumed = QTDEORI−QUANT` derivado** | `list_production_order_operation_materials(_batch)`, `get_production_consumption_*` | **QUANTITY_AFFECTING** — "consumo derivado" ≠ consumo físico garantido |
| Movimentações | `SD3010` + `SB1` | `D3_COD`, `D3_LOCAL`, `D3_DOC`, `D3_EMISSAO`, `D3_TM`, `D3_CF`, `D3_QUANT`, `D3_OP`, `D3_USUARIO`, `D3_ESTORNO`, `D3_NUMSEQ`. **Padrões provados (P2-A.1)**: entrada produção=`010/PR0`@01+OP · consumo/perda=saída `TM999`+OP (CF `RE0/RE1/RE2/RE9`, local 99 ou 01) · **transferência=par 2 linhas** mesmo `D3_DOC`: saída `999/RE4`@origem + entrada `499/DE*`@destino, `D3_OP` vazio · perda SBC=saída `999/RE0`@99 linkada por `BC_SEQSD3=D3_NUMSEQ` | `get_product_internal_movements` (`/{code}/internal-movements`) | **QUANTITY_AFFECTING** — direção = TM(`<500` entrada/`≥500` saída)+LOCAL; `D3_NUMSEQ` = identidade de movimento linkável |
| Saldos | `SB2010` | `B2_LOCAL` 01=almox·99=fábrica·50=WIP·98=aux; saldo por item+armazém | `get_product_stock`, `get_supplies_stock_balances_*` | `factory_stock` corrente — sem grão OP/missão |
| OPs | `SC2010` / `VW_PCP_ORDENS_PRODUCAO` | `C2_QUANT` planejada, `C2_QUJE` produzida, `C2_DATRF` encerramento, `C2_PRODUTO` | `get_production_pcp_orders_*`, `get_production_order_by_op` | contexto de ordem |
| BOM/roteiro | `SG1010` (`G1_COMP`), `SG2010` (`G2_OPERAC`/`G2_SETUP`) | estrutura componente↔PA, última operação, setup horas | `get_production_shared_structure_intermediates` | conversão PA→MP **não** congelada — preferir evidência real |
| Setup/paradas | `SHY.HY_SETUP`, `SG2.G2_SETUP`, view horas improdutivas | horas de preparo/parada + custo R$ | `get_production_unproductive_hours_*`, OEE | **TIME_ONLY** — nunca subtrair de material |

### 53.2 Matriz de sobreposição (double-counting) — **RESOLVIDA por dados TOTVS** (FS-C0.P2-A.1, probes read-only `scripts/sql/fs_return_overlap_probe*.py`, set/2026)

| Par | Classificação | Base probada |
|---|---|---|
| SH6 `QTDPROD` ↔ SD3 `PR0` | **SAME_FACT** | doc canônica + dados: `010/PR0`@01 sempre com OP — nunca somar ambos |
| SH6 `QTDPERD` ↔ SBC `BC_QUANT` | **DISTINCT_FACT** | QTDPERD = PA perdido na operação; SBC = MP perdido (produto/unidade diferentes); `BC_IDENSH6` existe mas está **sempre vazio** (50153 linhas `R` → `idh6_null`=50153) |
| SBC `'R'` ↔ SBC `'S'` | **DISTINCT** por linha; `'S'` **sem ocorrências** desde 2025 | census por `BC_TIPO`: só `R` populado; somar R+S é seguro, manter filtro `both` |
| SBC ↔ SD3 saída@99 | **SAME_PHYSICAL_FACT** | `BC_SEQSD3` (varchar, ex. `UDALFY`) = `SD3.D3_NUMSEQ`; join linha-a-linha: qtd e OP idênticos, movimento = **`LOCAL=99, TM=999, CF=RE0`** — SBC é o registro descritivo/motivo da baixa SD3; nunca somar os dois |
| SD4 consumido (`QTDEORI−QUANT`) ↔ SD3 saída@99 com OP | **PARTIAL_OVERLAP — mesma família física** | probe por OP+material: `Σ saída@99 (TM≥500, OP)` ≈ `Σ(QTDEORI−QUANT) + Σ SBC` — exato em ~80% das OPs; exceções existem (consumo em outro armazém) |
| SD4 consumido ↔ SBC perda | **DISTINCT_FACT** | a identidade acima prova que a perda **não** baixa `D4_QUANT` → `SBC_DOES_NOT_REDUCE_SD4`; subtrair SD4-consumido **e** SBC é seguro |
| SD3 `TM999`@99 com OP ↔ consumo **mais** perda | **PARTIAL_OVERLAP (agrega ambos)** | `TM999`@99 com `D3_OP` inclui baixas de consumo (CF `RE0/RE1/RE2/RE9`) **e** perdas (CF `RE0` via SBC); para isolar consumo físico: `D3_NUMSEQ ∉ SBC.BC_SEQSD3` |
| Transferência 01↔99 ↔ consumo/perda | **DISTINCT_FACT** | pares de transferência têm `D3_OP` **vazio**; consumo/perda têm OP |
| Entrada@99 `499/DE*` ↔ saída@01 `999/RE4` | **SAME_FACT — par de abastecimento 01→99** | mesmo `D3_DOC`+`D3_COD`+`qtd`; `D3_OP` vazio |
| Entrada@01 `499/DE*` ↔ saída@99 `999/RE4` | **SAME_FACT — par de devolução 99→01** | mesmo `D3_DOC`+`D3_COD`+`qtd`; `D3_OP` vazio |

> **Regra pós-prova:** uma fonte por fato físico — `delivered` (par 01→99), `consumed` (SD4-derivado **ou** `TM999@99+OP` menos SBC — nunca ambos), `loss` (SBC **ou** seu SD3 linkado — mesmo fato), `returned` (par 99→01).

### 53.3 Fatos de retorno candidatos (A–F)

| # | Fato | Fonte+contrato | Grão | Confiança | Lacuna |
|---|---|---|---|---|---|
| A | `delivered_to_factory_qty` | **par SD3**: saída `TM999/CF RE4`@01 + entrada `TM499/CF DE*`@99, mesmo `D3_DOC` (PROVEN) | filial+material+data | **alta** | `D3_OP` **vazio** em transferências — correlação a OP/missão só por FS-trace+atributos |
| B | `actual_consumed_qty` | SD4 derivado `QTDEORI−QUANT` (PROVEN) **ou** `Σ SD3 TM999@99 + OP` **excluindo** `NUMSEQ ∈ SBC` (PROVEN ≈ equivalente) | filial+OP+operação+material | alta | SD4=ledger derivado; SD3=físico — escolher um (P2-B) |
| C | `authoritative_loss_qty` | SBC `BC_TIPO='R'` (único tipo populado) = saída `999/RE0`@99 linkada (`BC_SEQSD3=D3_NUMSEQ`) | filial+OP+operação+material | **alta** (físico) | `production_losses_records` não expõe `loss_qty` por unit tipada? — expõe; `motivo`/CYO ok |
| D | `authoritative_scrap_qty` | SBC `BC_TIPO='S'` | idem | n/a | **0 ocorrências desde 2025** — tipo existe no contrato mas sem dados; manter `both` |
| E | `authoritative_returned_qty` | **par SD3**: saída `999/RE4`@99 + entrada `499/DE4`@01 (PROVEN) | filial+material+data | alta | sem `D3_OP` — correlação por atributos/FS-trace |
| F | `current_factory_stock_qty` | SB2 `B2_LOCAL='99'` | filial+material | alta | saldo corrente global, sem grão OP |

### 53.4 Gaps de contrato api-delpi (P2-B follow-up) — revisado pós-P2-A.1

1. Sem rota dedicada de **movimentos de consumo/requisição** (`TM 999`+OP) — hoje só legível via `internal-movements` sem `kind`, por produto.
2. Sem contrato expondo **sentido tipado** da transferência — semântica provada (TM+LOCAL+CF, par `RE4`/`DE*`), mas hoje é convenção de código/documento, não campo tipado no DTO.
3. Sem contrato de **saldo 99 por OP** — SB2 é por produto+armazém; `D3_OP` ausente nas transferências impede correlação ERP de saldo por OP — o grão por missão/CT é responsabilidade do **trace operacional FS** (§13, Doc 1/5).
4. ~~Perda↔empenho~~ **RESOLVIDO**: SBC não baixa `D4_QUANT`; perda está dentro de `TM999`@99 mas **fora** de `QTDEORI−QUANT`.
5. `internal-movements` é `GET /products/{code}/…` — fan-out por material da missão (padrão batch já usado em operation-materials pode ser precedente); expõe `D3_NUMSEQ`? — **verificar exposição do NUMSEQ** (hoje `R_E_C_N_O_` ordena internamente; NUMSEQ é o link SBC↔SD3 probado).
6. BOM/estrutura→consumo teórico: não necessário — evidência real suficiente (§53.3-B/C/D).

### 53.5 Estados de sugestão e confirmação

- Sugestão omite componente ausente como `*_UNKNOWN` (Doc 2/5 §15-A) — nunca zero silencioso.
- `CONFIRMED_RETURN_QTY` = handoffs `direction=return` factuais + evidência SD3 99→01 correlacionada (`erp_observations` §26); divergência abre exceção `divergent`.
- **`RETURN_FORMULA_STATUS = READY` — congelado FS-C0.P2-B** (modelo §53.7): consumo preferido = **SD3 físico** `TM999`+OP menos `NUMSEQ ∈ SBC`; SD4 = contexto de empenho; `already_returned` reduz a sugestão; capacidade global BI reconcilia. `record_item_return` segue manual/`null` até implementação.

### 53.6 Testes futuros obrigatórios (spec-only)

perda `R` e `S` não somadas duas vezes no mesmo material/OP · consumo SD4-derivado nunca somado a `TM 999` da mesma OP · `PR0` nunca subtraído de material · sugestão com `LOSS_UNKNOWN` não vira zero · divergência sugestão×saldo-99 observado abre exceção · `correlation_basis` registrada em toda sugestão · unit mismatch MP×PA → `UNIT_DIVERGENCE`, nunca conversão.

### 53.7 Return policy freeze (FS-C0.P2-B — `ACCEPTED`)

**Power BI baseline (`PROVEN_REFERENCE_IMPLEMENTATION`):** `Qtd devolver total = Saldo fábrica(Σ SB2 99) − Saldo Empenho(Σ SD4.D4_QUANT)`, filtro `> 0` → `ERP_GLOBAL_RETURN_CAPACITY = MAX(0, warehouse_99_stock − open_commitment)`. FS preserva o conceito global e adiciona trace por missão/CT, evidência física, histórico de retorno, divergência e auditoria — não copia o BI cegamente.

**Modelo congelado:**

```text
OPERATIONAL_RETURN_SUGGESTION(item/CT)
  = FS delivered_qty − consumido reconhecido (SD3 físico 99 excl. SBC)
    − perda SBC (uma vez) − already_returned_qty
   por material+filial, alocado a CT somente via trace FS

erp_global_return_capacity(material) = MAX(0, stock_99 − open_commitment)

reconciliation = Σ suggested vs capacity
  → matched | divergent | incomplete_evidence | unavailable
```

- `AUTOMATIC_RETURN_SUGGESTION = YES` — calculada e exibida quando evidência suficiente; label user-facing **"Sugestão de devolução"** (nunca "saldo oficial"/"quantidade garantida");
- divergente: expõe sugestão operacional **e** capacidade ERP — nenhum lado alterado silenciosamente;
- `suggested < capacity` é alocação válida — não auto-expande;
- UI item: entregue / consumido reconhecido / perdas / já devolvido / sugestão restante / ERP global / status;
- contract fitness final: `internal-movements` **EVOLVE_EXISTING** (expor `D3_NUMSEQ` p/ dedup SBC↔SD3 + direção tipada TM+LOCAL); `production_losses_records`, operation-materials/consumption, `get_product_stock` = REUSE_AS_IS; sem SQL genérico em runtime FS.
