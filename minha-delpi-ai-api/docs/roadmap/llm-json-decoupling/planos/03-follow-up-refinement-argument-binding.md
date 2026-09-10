# Plano 03 — Follow-up, refinement e argument binding generalizados

**Prioridade:** P0  
**Status execução:** Onda D · **ATENDIDO_PARCIAL** · E3.S1–S7 OK · E3.S8 parcial · E9.S12.A DELETE `messageSegmentTerms` OK · `playbookPathMarkers` residual  
**Evidência:** [`../evidence/e3-s1-multi-turn-state-inventory.md`](../evidence/e3-s1-multi-turn-state-inventory.md) · [`../evidence/e3-s2-follow-up-baseline.md`](../evidence/e3-s2-follow-up-baseline.md) · [`../evidence/e3-s3-turn-refinement-contract.md`](../evidence/e3-s3-turn-refinement-contract.md) · [`../evidence/e3-s4-schema-driven-argument-binder.md`](../evidence/e3-s4-schema-driven-argument-binder.md) · [`../evidence/e3-s5-schema-driven-group-by.md`](../evidence/e3-s5-schema-driven-group-by.md) · [`../evidence/e3-s6-pagination-filter-fast-path.md`](../evidence/e3-s6-pagination-filter-fast-path.md) · [`../evidence/e3-s7-follow-up-routing-cutover.md`](../evidence/e3-s7-follow-up-routing-cutover.md) · [`../evidence/e3-s8-persist-reload-cleanup.md`](../evidence/e3-s8-persist-reload-cleanup.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
**Objetivo perceptível:** continuidade conversacional, paginação, filtros, group-by e complementação de argumentos devem funcionar a partir do estado estruturado da conversa e do schema da action, não de substrings de rota ou frases cadastradas.

## CURRENT

Fontes prioritárias:

- `operational_follow_up_routing.json`;
- `operational_group_by_refinement.json`;
- `operational_refinement.json`;
- `operational_parameters.json`;
- `conversation_state.json`, `result_set_references.json`, `selection_pending.json` e services relacionados.

Padrões residuais:

```text
follow-up text
-> messageSegmentTerms / routeSegment / preferredRouteId
-> previous path match
-> inherited parameter strategy
```

ou:

```text
"agrupe por filial"
-> pathContains conhecido
-> group_by conhecido
-> refetch rule conhecida
```

## TARGET

```text
message
+ selectedAction/result reference anterior
+ resolvedEntities/resolvedArguments/timeRange/pagination
+ candidate action schema
-> semantic refinement
-> proposed argument delta
-> deterministic schema validation
-> policy
-> execute/re-render
```

## Requisitos

| ID | Requisito |
|---|---|
| R03-01 | Persistir/reutilizar action/context/result reference estruturados. |
| R03-02 | Remover continuidade baseada em path substring. |
| R03-03 | Resolver refinements por schema: page, page_size, branch, warehouse, dates, group_by etc. |
| R03-04 | Missing required gera clarify específico e grounded. |
| R03-05 | Valores herdados só são reutilizados quando semanticamente compatíveis. |
| R03-06 | F5/replay preserva comportamento sem nova inferência desnecessária. |

## Etapas

### E3.S1 — Grafo de estado multi-turn — **ATENDIDO**

**Fazer:** mapear producer/consumer/persistence de `selectedAction`, action metadata, result references, arguments, entity refs, pagination, time range e pending requirements.

**Feito:** inventário em [`../evidence/e3-s1-multi-turn-state-inventory.md`](../evidence/e3-s1-multi-turn-state-inventory.md). Nota: chave real = `selectedExternalAction` + `lastAction` (não existe `selectedAction`).

**Pronto quando:** cada dado necessário possui owner e estratégia de serialização/replay. ✅

### E3.S2 — Baseline de follow-up — **ATENDIDO**

Cobrir:

- “e a expedição?”;
- “agora só filial 02”;
- “próxima página”;
- “traga 100 linhas”;
- “agrupe por filial”;
- “compare com o mês anterior”;
- “use o mesmo produto”;
- troca explícita de assunto;
- referência ambígua a dois resultados anteriores.

Medir R3/R6/R7/R8/R9/R11.

**Feito:** harness `tests/unit/domain/services/test_e3_s2_follow_up_baseline.py` + [`../evidence/e3-s2-follow-up-baseline.md`](../evidence/e3-s2-follow-up-baseline.md). Sem cutover.

### E3.S3 — Canonical refinement contract — **ATENDIDO**

**Fazer:** definir output estruturado de refinement, contendo referência alvo, argument delta, presentation delta e confidence/clarification quando aplicável.

**Não fazer:** incluir path/operationId como chave de decisão semântica.

**Feito:** `TurnRefinement` + `TurnRefinementValidatorService` + adapter legado; evidência [`../evidence/e3-s3-turn-refinement-contract.md`](../evidence/e3-s3-turn-refinement-contract.md). Planners `OperationalRefinement` permanecem authority (sem cutover).

**Teste:** malformed output, unknown field, invalid enum, conflicting inherited arg. ✅

### E3.S4 — Schema-driven argument binder — **ATENDIDO**

**Fazer:** usar OpenAPI parameters/requestBody como autoridade; combinar valores explícitos, contexto e inferência; validar/coagir deterministicamente.

**Não fazer:** LLM decidir required/type/enum ou inventar valor ausente.

**Feito:** `SchemaDrivenArgumentBinderService` orquestra retain/coerce/`ValidateActionArgumentsService` sobre `TurnRefinement`; evidência [`../evidence/e3-s4-schema-driven-argument-binder.md`](../evidence/e3-s4-schema-driven-argument-binder.md). Sem cutover dos planners.

**Teste:** required present/missing, path/query/body, enum/type/format, additionalProperties e conflicting values. ✅

### E3.S5 — Group-by/refetch generalization — **ATENDIDO**

**Fazer:** derivar parâmetros e enums do schema; decidir local transform vs refetch por capability real do resultado/action, não por path fixo.

**Feito:** `SchemaDrivenGroupByRefinementService` + `match_route_for_action_id` no collector legado; evidência [`../evidence/e3-s5-schema-driven-group-by.md`](../evidence/e3-s5-schema-driven-group-by.md).

**Teste:** mesma semântica com provider/path/operationId renomeados; group_by diferente; action sem group_by deve rejeitar/clarificar. ✅

### E3.S6 — Pagination/filter fast paths — **ATENDIDO**

**Fazer:** manter parsers determinísticos para valores explícitos quando vantajoso (`página 3`, `50 linhas`, `filial 01`), mas aplicar delta apenas sobre parâmetros aceitos pelo schema.

**Feito:** `SchemaDrivenPaginationFilterService` + evidência [`../evidence/e3-s6-pagination-filter-fast-path.md`](../evidence/e3-s6-pagination-filter-fast-path.md).

**Teste:** phrases exatas + frases livres + field inexistente. ✅

### E3.S7 — Follow-up cutover — **ATENDIDO**

**Fazer:** trocar `operational_follow_up_routing` por resolução via contexto estruturado + candidates; usar legacy apenas como shadow temporário.

**Feito:** authority = `follow_up_type → routeSegment`; `messageSegmentTerms` observer; shadow log; evidência [`../evidence/e3-s7-follow-up-routing-cutover.md`](../evidence/e3-s7-follow-up-routing-cutover.md).

**Teste:** follow-up entre actions irmãs (`preferredRouteId`), troca de domínio e referência a resultado não imediatamente anterior (topic switch sem segment). ✅

### E3.S8 — Persist/reload e cleanup — **ATENDIDO_PARCIAL**

**Fazer:** materializar metadados necessários para não reconsultar LLM só para reconstruir títulos/action refs; remover routeSegments/message terms mortos.

**Feito:** harness de continuidade F5 via histórico; `deleteDeferredToWaveH` nos terms observer. Evidência [`../evidence/e3-s8-persist-reload-cleanup.md`](../evidence/e3-s8-persist-reload-cleanup.md).

**Feito (E9.S12.A):** DELETE de `messageSegmentTerms`.

**Não feito:** DELETE de `playbookPathMarkers` (E9.S12.B); Postgres lastAction.

**Teste:** F5/replay via previous_messages; historical turn. ✅ parcial

## Invariantes

- Explicit current-turn value vence contexto anterior.
- Required ausente permanece ausente até usuário/contexto grounded fornecer valor.
- Refino não altera action autorizada para uma não permitida.
- Alteração de formato de apresentação não dispara tool call desnecessária quando os dados existentes bastam.

## Aceite

```text
MULTI_TURN_REFERENCE = PASS
ARGUMENT_SCHEMA_BINDING = PASS
MISSING_REQUIRED_CLARIFY = PASS
GROUP_BY_WITHOUT_PATH_COUPLING = PASS
PAGINATION_FILTER = PASS
PERSIST_RELOAD = PASS
SEND_STREAM_SIMULATE = PASS
```
