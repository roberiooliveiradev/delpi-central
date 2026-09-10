# E3.S1 — Grafo de estado multi-turn (inventário)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** D (plano 03)  
**Fontes:** `onda-a-inventory.md` §1–3 + greps HEAD (sem migração de runtime)

## Veredito

```text
MULTI_TURN_STATE_GRAPH = PASS
OWNER_PER_CONCEPT = PASS
AUTHORITY_VS_STRUCTURED_FLAGGED = PASS
NO_RUNTIME_MIGRATION = PASS
SELECTED_ACTION_KEY_CLARIFIED = PASS
```

## Nota estrutural

Não existe chave `selectedAction`. Continuidade operacional = **`selectedExternalAction`** (metadata do turno) + **`lastAction`** (working memory reconstruída do histórico / `toolCalls`).

## Onda A — âncoras (plano 03)

| Achado | Onde |
|--------|------|
| Follow-up / refinement path markers = **Authority residual** → plano 03 | `onda-a-inventory.md` §1 |
| `routeSegment` consumers (refinement select + pagination) → plano 03 | §2 |
| Classify follow-up path via action (não path) já parcialmente presente | §3 |

## Matriz concept → owner → persist → authority → class

| concept | owner (file:symbol) | persist? | authority signal | class |
|---------|---------------------|----------|------------------|-------|
| **selectedExternalAction** | Producer: `chat_tool_context_result_assembly_service` ← selection pipeline. Consumers: intelligence metadata, soft-handoff, multi-intent, admin debug. | Turn metadata only (não DB). Replay via `toolCalls` no histórico. | Action/catalog id no turno; payload ainda pode anexar `routeSegment` | STRUCTURED_STATE (+ PATH_COUPLING residual) |
| **lastAction** | `chat_conversation_memory_extractor._extract_last_action`. Consumers: grounded planning, reference resolution, param inherit (`operational_api_parameter_builder_service`). | Rebuild de `toolCalls` (path, params, operationId, actionId). Postgres overlay **não** guarda lastAction. | Prefer `actionId`/`operationId`; name ainda via path substring residual | STRUCTURED_STATE (+ PATH_COUPLING em name-from-path) |
| **resultSets** | Content: `result_set_references.json`. Build: `chat_result_set_reference_service.build_result_sets`. Resolve: `chat_reference_resolution_service` | Snapshot WM / prior-turn packing; **não** Postgres session memory | Field maps + ordinals (sem path) | STRUCTURED_STATE + SCHEMA_BINDING (aliases) |
| **arguments / entity refs** | Focus: `chat_working_memory_service` + `operationalFocus`. Resolve: `chat_reference_resolution_service`. Topic ledger: `chat_conversation_state_service.ensure_topic_ledger` | Focus (`productCode`,`branch`,`warehouse`,`period`) → Postgres. Args full → lastAction/history. Topic `resolvedArguments` → snapshot | Explicit turn > focus > lastAction.params | STRUCTURED_STATE |
| **pagination** | Vocab: `operational_refinement.json`. Plan: `chat_operational_refinement_pagination_service.plan_pagination_follow_ups`. Select: `external_action_refinement_route_selection_service.select_pagination` | Recent params via toolCalls; delta não persistido separado | Phrases = VOCAB; re-select fallback ainda exige `route_segment` / path fragments | VOCABULARY + PATH_COUPLING (rebind) + SCHEMA_BINDING parcial |
| **time range / period** | `chat_date_range_intent_service` + extractor; copy: `operational_parameters.json`; inherit: `ChatOperationalFollowUpRoutingService` + `playbookPathMarkers` | `operationalFocus.period` → Postgres; topic `timeRange` no ledger | UX copy = JSON; **date follow-up gate** ainda path/segment | UX + VOCABULARY + PATH_COUPLING |
| **selection_pending** | `chat_catalog_selection_pending_service` + `selection_pending.json` | Metadata `selectionPending` no histórico | Candidates estruturados; copy UX do bundle | STRUCTURED_STATE + UX |
| **activeQuery** | `chat_active_query_session_service` | Metadata `activeQuery` (+ `routeSegment` opcional) | Continuidade por subIntent/expectedParam; topic-change + `segment_from_message` | STRUCTURED_STATE + PATH_COUPLING |
| **conversation_state / topic ledger** | `chat_conversation_state_service` + `conversation_state.json` | Snapshot / previous messages; **não** Postgres overlay de entidades | Patterns = VOCAB; topics/`resolvedArguments`/`timeRange` = structured | STRUCTURED_STATE + VOCABULARY |
| **working memory** | `chat_working_memory_service` + memory service + Postgres overlay | Hybrid: rebuild history + Postgres entities | Structured focus/refs; followUpType ainda intent-vocab | STRUCTURED_STATE |
| **operational_follow_up_routing.json** | `ChatOperationalFollowUpRoutingService` (+ route context, matcher, dates, capabilities) | N/A (content) | **`messageSegmentTerms` → `routeSegment`**, `preferredRouteId`, `playbookPathMarkers` = **AUTHORITY** | PATH_COUPLING + VOCABULARY |
| **operational_group_by_refinement.json** | `ChatOperationalGroupByRefinementService.match_route_for_path` (`pathContains`) | Dimension/params via last path+params | **`pathContains` AUTHORITY** | PATH_COUPLING + VOCABULARY |
| **operational_refinement.json** | `ChatOperationalRefinementContentService` → vocabulary | N/A | Detection phrases; binding downstream path/segment-aware | VOCABULARY (fast path OK p/ E3.S6) |
| **operational_parameters.json** | `ChatOperationalParameterService` (+ delegates) | Pending via metadata | UX clarify; **`implicitReferenceDateTodayPathMarkers`** residual | UX + PATH_COUPLING |

## Authority vs structured (routing/args)

| Sinal | Uso atual | Status E3 |
|-------|-----------|-----------|
| `messageSegmentTerms` → `routeSegment` | Follow-up route pick | **AUTHORITY** residual |
| `preferredRouteId` / registry `routeSegment` | Refinement + domain select | **AUTHORITY** residual |
| `pathContains` (group_by) | Match rota/dimensão/refetch | **AUTHORITY** residual |
| Path fragments in pagination infer | Rebind sem action_id | **AUTHORITY** fallback |
| `playbookPathMarkers` / date `routeSegments` | Date inherit | **AUTHORITY** residual |
| `lastAction.actionId` + params | Continuity / inherit | **STRUCTURED** (alvo) |
| `resultSets` + ordinals | Entity refs multi-turn | **STRUCTURED** |
| Topic `resolvedArguments` / `timeRange` | Ledger | **STRUCTURED** (pouco usado no routing) |
| `selectionPending` | Clarify/select | **STRUCTURED** |
| Pagination/filter phrases | Detect only | **VOCABULARY** (manter sob schema bind) |

## Lacunas (não bloqueiam inventário)

1. Serialização canônica multi-turn: `actionId` estável em `lastAction` (pré-condição Onda B já entregue no cutover); path ainda identity de fato em vários consumidores.
2. Postgres não persiste lastAction/resultSets/selectedExternalAction — F5 depende do histórico de mensagens.
3. Topic ledger (`resolvedArguments`) existe mas routing/refinement ainda não o tratam como fonte primária.
4. Cutover natural: E3.S7 (follow-up → shadow) e E3.S5 (group_by sem `pathContains`).

## Próximo

**E3.S2** — baseline harness das famílias de follow-up do plano 03 (sem cutover).
