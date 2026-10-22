# DÉLIA — Conversation Queue Runtime Inventory & Contract v1

**Status:** INVENTORY + CONTRACT_PROPOSAL (não implementado)  
**TASK_ID:** DELIA-C3-CONVERSATION-QUEUE-RUNTIME-INVENTORY-AND-CONTRACT-01  
**HEAD auditado:** `151b7f5e32dcb45d4311cdad37c84be97006987c` (main, 2026-10-22)  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Spec de produto:** [`71-conversation-queue-and-my-work-ux-specification.md`](./71-conversation-queue-and-my-work-ux-specification.md) §§3–6, 13  
**Componente já implementado:** `ConversationQueue` (plugin-ui, F03-A, ledger §6.368)

> Escopo desta task: `DOCUMENTATION_FIRST / CONTRACT_FIRST`. **Zero** alteração de runtime, zero endpoints, zero workers, zero tabelas. Toda afirmação abaixo tem arquivo/símbolo como evidência.

---

## 1. Fluxo real de turno (auditado no HEAD)

```text
USER INTENT (texto livre ou decisão tipada)
→ DeliaComposer / App.tsx            plugins/delia/src/ui/DeliaComposer.tsx · src/App.tsx
→ submitInteractionTurn()            plugins/delia/src/api/interactionClient.ts:298
→ POST /apps/delia-api/interaction/turns  (fetch; Accept: ndjson+json; Bearer; AbortSignal)
→ ROUTE  register_interaction_routes → submit_delia_interaction_turn()
                                   delia-api/app/interfaces/http/interaction_routes.py:120
→ AUTHENTICATION  auth middleware + subject_bearer ContextVar
                                   app/infrastructure/auth/subject_bearer.py; bind no worker (interaction_routes.py:269)
→ SYNTACTIC VALIDATION  ALLOWED_BODY_KEYS={input,context,confirmation,workspace,max_execution_stage,command}
                                   interaction_routes.py:69–98 (chaves extras → 400)
→ LIVE AUTHORIZATION  has_delia_access → CORE_PERMISSION "delia.access" ou superadmin
                                   handle_interactive_turn.py:112,186 (_require_access, fail-closed)
→ APPLICATION USE CASE  HandleInteractiveConversationTurn.execute()
                                   app/application/interaction/handle_interactive_turn.py:255
→ DOMAIN  InteractionSession(uuid4) + InteractionTurn(uuid4) + record_interaction_turn()
                                   app/domain/interaction/model.py:83,128 · rules.py:74
→ OBSERVATION  ActivityEventSink (ActivityPhase.*) — somente no modo NDJSON
                                   app/application/interaction/activity.py:335
→ ORCHESTRATION  capability orchestration opcional (governed attempt; PREPARE/ACT owners)
                                   capability_attempt.py; deadline TurnDeadline.start(turn_budget)
→ MODEL PORT  InvokeModel (existing port)
                                   app/application/model_invocation/invoke_model.py
→ PRESENTATION  compose_presentation (message_kind canonico)
                                   app/application/interaction/presentation.py
→ RESPONSE  InteractiveTurnResult (JSON) ou ActivityEvent.v1 NDJSON + turn_result/turn_error
                                   contracts.py:159 (InteractiveTurnResult); interaction_routes.py:230+
→ POSTCONDITION  result turn gravado na session EFÊMERA; UI aplica resultado localmente
→ UI STATE  App.tsx: turns[], loading, requestMode, requestEpochRef (guarda de late completion)
```

**Evidência de statelessness:** `execute()` cria `InteractionSession(session_id=str(uuid.uuid4()))` **a cada POST** (`handle_interactive_turn.py:278`). Não existe `conversation_id` em `delia-api/app/` (grep 0 hits). Continuidade é client-carried: `context[]` é **dado transiente não confiável**, validado e repassado ao port de modelo — “never authority, memory, or evidence” (docstring, linhas 7–13).

## 2. Inventário de mecanismos existentes

| Mecanismo | Local | Status | Reutilizável p/ fila? |
|---|---|---|---|
| `POST /interaction/turns` + validação + erro tipado | `app/interfaces/http/interaction_routes.py` | PROVEN | Sim — superfície de admissão/execução |
| `HandleInteractiveConversationTurn` | `app/application/interaction/` | PROVEN | Sim — executor de turno |
| `InteractionSession/Turn` + `record_interaction_turn` | `app/domain/interaction/` | PROVEN (efêmero) | Sim — modelo de turno |
| `ActivityEvent.v1` NDJSON stream | `interaction_routes.py:230+`, `activity.py` | PROVEN | Sim — canal de status (per-request; ver §6.3) |
| `PendingWriteStore` | `app/application/interaction/pending_proposals.py` | PROVEN | **Parcial** — padrão (bounded, RLock, TTL, digest, single-use); escopo = writes governados, não fila de turnos |
| `TurnDeadline`/budget | `interaction/turn_budget.py` | PROVEN | Sim — timeout por turno |
| `AbortController` + `requestEpochRef` | `plugins/delia/src/App.tsx:183-185` | PROVEN | Sim — cancelamento de transporte local + serialização client |
| Core schedulers (`notification_dispatch`, `usage_session_flush`, `data_retention`) | `core-api/app/infrastructure/schedulers/` | PROVEN (outro domínio) | **Não** — housekeeping Core, ownership errado |
| `queue.Queue` no stream | `interaction_routes.py:266` | PROVEN | **Não** — buffer de transporte por request; comentário explícito: “NOT an execution queue” |
| Durable Workflow Runtime | doc 43 | **TARGET/C5 — não existe** | Bloqueado por gate de fase |
| Task/Case/Room/Inbox | doc 36 | **TARGET/C6 — não existe** | Bloqueado por gate de fase |
| Automation Hub execution contract | doc 43 §2 (referência) | TARGET — sem runtime aqui | Delegação futura, não owner desta fila |
| Persistência (SQL/repository) | delia-api | **AUSENTE** — service stateless (`app/infrastructure/` = auth/http/interop/logging/model_invocation/openapi) | Não existe |
| Idempotência HTTP | — | **AUSENTE** (sem key em `/interaction/turns`) | Padrão digest de `PendingWriteStore` é o precedente |
| Identidade de conversa persistente | — | **AUSENTE** | Gap real (§4) |

## 3. Reuse Gate

| Responsabilidade | Equivalente | Owner | Decisão |
|---|---|---|---|
| Identidade da conversa | **NO** — session é por request | — | NEW (ADR: ver §7.1) |
| Estado do turno | YES (efêmero) `InteractionTurn`/`SessionStatus`/`ActivityPhase` | `delia-api` domain/application interaction | EXTEND |
| Admissão de solicitações | YES `POST /interaction/turns` | `delia-api` interfaces/http | EXTEND |
| Pendências e ordenação | TO_INVENTORY — `PendingWriteStore` é o precedente process-local, mas cobre **writes**, não fila | `application/interaction/pending_proposals.py` | EXTEND-PATTERN (novo store coeso, mesmo padrão) |
| Idempotência | YES (padrão) digest single-use `take_if_current` | `pending_proposals.py` | EXTEND (mesma disciplina) |
| Persistência | NO | — | BLOCKED_BY_GATE (dados/persistência = decisão arquitetural, C5+) |
| Processamento sequencial | NO — hoje o cliente serializa (1 em voo) | — | EXTEND client-driven (§7.6) |
| Concorrência | YES limitado — `RLock` em `PendingWriteStore`; epoch/abort no MFE | `pending_proposals.py` + `plugins/delia` | EXTEND |
| Cancelamento | YES parcial — `AbortController` (transporte), `TurnDeadline`, `ActivityPhase.CANCELLED` | frontend + interaction | EXTEND (item ≠ turno: ver §7.5) |
| Eventos/status | YES `ActivityEvent.v1` NDJSON | `interaction/activity.py` + route | REUSE (consulta/eventos) |

## 4. Gaps reais

1. **Identidade de conversa** — não existe autoridade server-side; cada POST cria session nova. Sem ela, "fila por conversa" não tem âncora autoritativa.
2. **Admissão de pendências** — `/interaction/turns` executa imediatamente; não há "admitir sem executar".
3. **Estado durável de pendências** — nenhuma persistência; `PendingWriteStore` é process-local E por-worker (multi-worker = misses já conhecidos do mecanismo de pending writes).
4. **Sequenciamento autoritativo** — hoje garantido só pelo cliente; duas abas/submissões concorrentes não são ordenadas pelo backend.
5. **Idempotência de turno/enqueue** — nenhuma chave de idempotência no contrato de turnos.
6. **Ownership da label/título** — `ConversationQueueItem.label` é consumer-owned; nenhum campo de título existe no contrato de turnos.

## 5. Fronteiras preservadas

- `plugin-ui`: somente apresentação (`ConversationQueue` já entregue).
- `plugins/delia`: composição, adapter tipado, fixture QA (já gated).
- `delia-api` Application `interaction/`: **owner legítimo** do lifecycle de interação — a fila é lifecycle de solicitações de interação, portanto candidata correta a extensão **dentro** deste bounded context.
- Core: RBAC/`delia.access` — inalterado.
- Domain APIs/owners MCP: execução material — inalterado.
- Automation Hub: execução técnica delegada futura — não owner desta fila.

## 6. Proposta `conversation.queue.v1`

### 6.1 Modelo de execução — duas alternativas avaliadas

| | A. Backend-driven drain | B. Admission-authority + client-driven (**recomendada v1**) |
|---|---|---|
| Quem dispara o próximo item | worker/loop/scheduler no backend | o MFE submete o item HEAD via o POST /interaction/turns existente |
| Novo scheduler/engine | Exigiria — BLOCKED_BY_GATE (proibido nesta fase e sem owner) | **Não** — preserva o modelo request-driven comprovado |
| Persistência | Forte pressão | mesma limitação do `PendingWriteStore` (process-local v1) |
| Semântica falha/retry | runtime próprio | item FAILED/EXPIRED; retry = nova admissão explícita |
| Risco | transformar delia-api em scheduler | mínimo; cada POST permanece independente |

**Decisão proposta:** alternativa B. A fila é **autoridade de admissão e ordenação**; a execução continua sendo o fluxo de turno existente. O backend rejeita a execução de qualquer item que não seja o HEAD elegível → serialização garantida server-side mesmo com N abas.

### 6.2 Identidade e isolamento

- `conversation_id`: **server-issued** (uuid4), criado na primeira admissão ou por `POST /conversations` (ver ADR §7.1). Nunca derivado de id do frontend; o cliente pode enviar `client_correlation_id` como hint não-autoritativo.
- `queue_item_id`: server-issued por admissão.
- Vinculação: `subject` (bearer) + `actor_user_id` (PlatformAccessContext) + tenant via contexto de acesso — mesma disciplina de `PendingWrite.actor_user_id`.
- Conversa encerrada/troca de contexto/revogação: itens ficam `EXPIRED`/`CANCELLED`; leitura e mutação exigem a mesma live AuthZ (`delia.access`) + posse do `actor_user_id` — fail closed.

### 6.3 Admissão

`POST /conversations/{conversation_id}/queue/items` (owner: delia-api)

```json
{
  "input": "texto da solicitação",
  "title": "rótulo curto opcional (<=120 chars, consumer-owned)",
  "idempotency_key": "client-generated-uuid",
  "depends_on_item_id": null,
  "context_echo": { }
}
```

- Resposta `201`: `{conversation_id, queue_item_id, position, revision}` — `ADMISSION_ACCEPTED`, **não** `QUEUED`-confirmado até leitura/estado retornar (HTTP 200/201 ≠ outcome).
- Erros: `unauthenticated 401`, `forbidden 403`, `invalid_request 400` (campos extras, limites), `conversation_not_found 404`, `capacity_exceeded 429`, `duplicate_idempotency_key 200-idempotent` (retorna o item existente).
- Limites: `MAX_PENDING_ITEMS` por conversa (sugestão 32), `INPUT` ≤ 16_384 (alinhado a `INTERACTION_INPUT_CHAR_LIMIT`), TTL por item (sugestão 300s — espelha `DEFAULT_PENDING_TTL_SECONDS`).

Estados do item:

```text
SUBMISSION_REQUESTED → ADMISSION_ACCEPTED → QUEUED ⇄ BLOCKED(depends_on)
QUEUED → HEAD_ELIGIBLE → RUNNING → COMPLETED | FAILED | CANCELLED | EXPIRED
QUEUED → REMOVED
```

### 6.4 Consulta

`GET /conversations/{conversation_id}/queue` → `{items[], revision, next_item_id}`

- `items[]`: `{queue_item_id, position, status, title, reason?, eligibility:{move_up,move_down,remove}, created_at}`.
- `revision` incrementa a cada mutação — base do controle de concorrência otimista.
- Atualização de status: **reuso do canal ActivityEvent.v1** durante o turno RUNNING (já chega ao MFE); para mudanças de fila fora de turno, v1 usa **consulta explícita pós-ação** (cada resposta de mutação retorna o estado reconciliado). Polling/WebSocket novo: **não proposto** — sem necessidade comprovada.

### 6.5 Reordenação

`POST /conversations/{id}/queue/items/{item_id}/move`

```json
{ "direction": "up|down", "expected_revision": 7 }
```

- Somente itens `QUEUED` com `eligibility.move_*=true`; `BLOCKED` requer motivo de owner (`reason`).
- `expected_revision` divergente → `409 revision_conflict` com estado reconciliado.
- Resposta: estado autoritativo completo da fila (consumer nunca assume mutação local).

### 6.6 Remoção vs cancelamento

| Operação | Alvo | Contrato |
|---|---|---|
| `REMOVE_PENDING` | item QUEUED/BLOCKED | `DELETE /conversations/{id}/queue/items/{item_id}` → `204` + revision |
| `CANCEL_RUNNING` | turno em execução | **não implementado v1** — `STOP_RESPONSE` local (AbortController) permanece o mecanismo; backend `CANCELLED` é fase de atividade existente |
| `STOP_RESPONSE` | transporte cliente | existente — `abortRef.abort()` |

`AbortController` **não** cancela item admitido no backend — operações distintas por contrato.

### 6.7 Processamento (binding turno↔item)

Extensão **aditiva e opcional** do contrato existente `POST /interaction/turns`:

```json
{ "input": "...", "queue_item_ref": {"conversation_id": "...", "queue_item_id": "..."} }
```

- Backend: resolve item → exige `HEAD_ELIGIBLE` + mesma `conversation_id` + mesmo `actor_user_id` + não expirado → marca `RUNNING` → executa **exatamente o fluxo atual** (`HandleInteractiveConversationTurn`) → marca `COMPLETED`/`FAILED`.
- Item não-HEAD → `409 queue_item_not_eligible` (fail-closed; nunca enfileira sob demanda).
- Falha no turno → item `FAILED` com `reason` tipado; itens dependentes permanecem `BLOCKED`; itens independentes avançam.
- `depends_on_item_id` admite dependência — item vira elegível só após dependente terminal (`COMPLETED`); `FAILED`/`CANCELLED`/`EXPIRED` propaga `BLOCKED reason=dependency_failed` (não executa em cascata silenciosa).

### 6.8 Erros (catálogo fail-closed)

`unauthenticated`, `forbidden`, `invalid_request`, `conversation_not_found`, `queue_item_not_found`, `queue_item_not_eligible`, `queue_item_expired`, `revision_conflict`, `duplicate_idempotency_key` (idempotent-200), `capacity_exceeded`, `dependency_failed`, `model_unavailable`, `model_timeout`, `internal_error` — todos com `code` estável + `request_id`.

### 6.9 Observabilidade e outcome

Correlação: `conversation_id → queue_item_id → session_id/turn_id (ActivityEvent) → model_invocation_id → outcome`. Conclusão de turno ≠ sucesso material: outcome autoritativo permanece do owner (mesma disciplina de `grounding_status`/`provenance`). Logs: códigos + ids de correlação; **nunca** input completo, tokens, `proposal_ref` ou conteúdo sensível.

### 6.10 OpenAPI (proposta antes de implementação)

Owner: `delia-api`. Consumers: `plugins/delia` MFE. Padrão de rotas: existente (`/interaction/turns` → `/conversations/{id}/queue/items`). OperationIds sugeridos `enqueueConversationItem`, `getConversationQueue`, `moveConversationQueueItem`, `removeConversationQueueItem`. Versionamento: `conversation.queue.v1` no schema; campos aditivos-only; compatível por rejeição fail-closed de chaves desconhecidas (mesma política de `ALLOWED_BODY_KEYS`).

### 6.11 Mapeamento `ConversationQueue` (já implementado) ⇄ contrato

| Prop | Campo do contrato |
|---|---|
| `items[].id` | `queue_item_id` |
| `items[].label` | `title` (consumer-supplied) ou excerpt de `input` (≤120c) |
| `items[].ordinal` | `position` |
| `items[].status` | `QUEUED`→`queued`; `BLOCKED`→`blocked` |
| `items[].reason` | `reason` |
| `canMoveUp/Down/Remove` | `eligibility.*` |
| `loading/unavailable/error` | estados de leitura do GET |
| `onMoveUp/Down` | `POST .../move` |
| `onRemove` | `DELETE .../items/{id}` |
| `onExpandedChange` | local UI |

## 7. Decisões arquiteturais pendentes

1. **ADR-1 — Identidade de conversa:** criar agregado `conversation_id` server-issued no delia-api (process-local v1) **ou** aguardar persistence/C5? Mínimo viável: emissor no mesmo bounded context, TTL-bound.
2. **ADR-2 — Estado da fila:** process-local bounded store (padrão `PendingWriteStore`, aceitando a mesma limitação multi-worker) **vs** store compartilhado (Redis/DB — exige decisão de dados). v1 proposto: process-local + flag honesta `durability=process_local`.
3. **ADR-3 — Backend-driven drain** fica explicitamente **fora** do escopo v1 (exige scheduler — C5/Automation Hub boundary).

## 8. Estratégia de testes de contrato

| Cenário | Classificação |
|---|---|
| Pergunta enviada idle | SUPPORTED_BY_EXISTING_CONTRACT |
| 2ª pergunta durante turno em andamento | REQUIRES_EXTENSION (admissão) |
| FIFO múltiplas pendências | REQUIRES_EXTENSION |
| Reordenação elegível | REQUIRES_EXTENSION |
| Mover item RUNNING | REQUIRES_EXTENSION (rejeição 409) |
| Remover pendente | REQUIRES_EXTENSION |
| Troca de conversa | REQUIRES_EXTENSION (conversation_id) |
| Reload/reconexão | BLOCKED_BY_GATE (sem persistência; itens expiram — comportamento honesto documentado) |
| Duas abas | REQUIRES_EXTENSION (server-side HEAD enforcement resolve) |
| Retry de enqueue / key duplicada | REQUIRES_EXTENSION (idempotency_key) |
| Falha de processamento | REQUIRES_EXTENSION (item FAILED + reason) |
| Revogação AuthZ | REQUIRES_EXTENSION (live check por operação) |
| Dependência entre itens | REQUIRES_EXTENSION (`depends_on`) |
| Turno com confirmação governada | SUPPORTED_BY_EXISTING_CONTRACT (comando tipado já existe) |
| Item com operação material | PLANNED (mesmo pipeline PREPARE/ACT) |
| Outcome não confirmado | SUPPORTED_BY_EXISTING_CONTRACT (grounding/limitations) |
| Backend indisponível | SUPPORTED_BY_EXISTING_CONTRACT (unavailable honesto no MFE) |

## 9. Respostas às perguntas de conclusão

- **Owner da interação hoje:** `delia-api` Application `interaction/` — `HandleInteractiveConversationTurn` (PROVEN).
- **Fluxo de turnos:** stateless request-scoped; contexto client-carried e validado (PROVEN).
- **Identidade persistente de conversa:** **não existe** (session por request) — gap PROVEN.
- **Fila/equivalente:** **não existe**; `PendingWriteStore` é o precedente de estado orquestral pendente (bounded/process-local/RLock/TTL/digest) para writes, não para fila de solicitações.
- **Estado autoritativo de pendências:** inexistente para turns; existe para pending writes.
- **Executor sequencial reutilizável:** **não existe**; serialização hoje é cliente (1 turno em voo) — contrato v1 formaliza enforcement server-side sem worker.
- **Concorrência backend:** nenhuma entre turnos (independentes); `RLock` interno no store de pending writes.
- **Consumo pelo frontend:** adapter tipado em `plugins/delia` mapeando contrato → props `ConversationQueue` (tabela §6.11); zero lógica de negócio no MFE.
- **O que estender:** `delia-api/application/interaction/` (novo store coeso + binding `queue_item_ref` no comando) e `interfaces/http` (4 operações); frontend: adapter + wiring no App.
- **O que não criar:** scheduler, worker, engine, segundo planner, novo notification system, controller genérico, persistência sem decisão de dados.
- **Menor próximo passo:** ADR-1+ADR-2 decididos → OpenAPI `conversation.queue.v1` → implementação bounded (store process-local + 4 rotas + binding) → adapter MFE → contract tests.

## 10. Decisões congeladas preservadas

- UI render-only; nenhum grant pelo clique (F03-A).
- `context[]` continua não-autoritativo.
- `PendingWrite`/PREPARE-ACT/confirmation tipada inalterados.
- HTTP 2xx nunca prova outcome; fase/CP-RQ inalterados.

```text
INVENTORY=EXECUTED
QUEUE_MECHANISM=NONE_PROVEN
CONVERSATION_IDENTITY=ABSENT_PROVEN
PRECEDENT=PendingWriteStore(process-local)
CONTRACT_V1=PROPOSED (admission-authority + client-driven drain)
ADR_REQUIRED=3
RUNTIME_CHANGED=NO
NEXT=ARCHITECTURE_DECISION(ADR-1,ADR-2)
```
