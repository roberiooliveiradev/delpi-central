# Roadmap — desacoplamento de JSONs e generalização LLM/OpenAPI

**Status:** **REABERTO — Onda J P0**  
**Plano ativo:** [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)  
**Owner arquitetural:** Minha DELPI AI / OpenAPI-first tool routing  
**Dependência:** `../openapi-first-universal-tool-routing.md`

## 1. Resultado esperado

Evoluir o chat para um motor realmente generalizável, sem catálogo técnico paralelo nem NLU endpoint-specific escondida em outra representação:

```text
TARGET
mensagem + contexto estruturado
→ semantic understanding
→ goals/subtasks/entities/references
→ allowed Action Catalog
→ semantic retrieval
→ structured planner restricted to candidates
→ OpenAPI schema binder + validator
→ RBAC/policy/confirmation
→ generic execution
→ responseSchema + semantic metadata
→ schema-driven presentation
→ grounded synthesis + contextual recommendations
```

## 2. Estado histórico × estado vigente

As Ondas A–I foram executadas e produziram evidências úteis. Uma auditoria posterior encontrou drifts materiais no estado final, portanto:

```text
PASS histórico ≠ PASS do candidate atual
```

Os principais drifts são:

- path→domain map movido para Python;
- parameter strategy recriada por path/operationId;
- multi-turn continuity recriada por path-tail/operationId inventory;
- registry `operationIds` residual como catálogo técnico;
- semantic authority duplicada;
- recommendations ainda com fallback/oracle estático;
- capability metadata de efeito/risco incorreta;
- Clean Architecture/DI residual;
- credential defaults em smoke;
- unknown-provider anterior ao último diff material.

A Onda J existe para corrigir esses pontos e produzir **novo candidate final**.

## 3. Ledger macro vigente

| ID | Requisito | Owner na Onda J |
|---|---|---|
| RQ-01 | Remover autoridade técnica duplicada de path/method/operationId/schema/strategy | E11.S2–S5 |
| RQ-02 | Remover NLU endpoint/domain-specific desnecessária | E11.S6 |
| RQ-03 | Pedidos longos → goals/subtasks completos | E11.S6/S9 |
| RQ-04 | Follow-up por estado estruturado, sem URL substring/tail | E11.S4 |
| RQ-05 | Argumentos semanticamente extraídos e validados pelo OpenAPI | E11.S3 |
| RQ-06 | Action/capability sem mini-catálogo técnico paralelo | E11.S5/S7 |
| RQ-07 | Composition/enrichment dependentes de goals/actions permitidas | revalidar S9 |
| RQ-08 | Recommendations realmente contextuais e validadas | E11.S7 |
| RQ-09 | Preservar policy/business/safety determinísticos | transversal/S9 |
| RQ-10 | Presentation universal schema-first | revalidar S9 |
| RQ-11 | Preservar send/stream/simulate/persist/F5/UI | E11.S9 |
| RQ-12 | Provar unknown external API + metamorphic rename no candidate final | E11.S9 |
| RQ-13 | Controlar latency/tokens/model calls/tool count | E11.S9 |
| RQ-14 | Cleanup só após generalização; nenhum substituto semântico | E11.S1–S10 |

O detalhamento atômico está no ledger RQ11-* do Plano 11.

## 4. Decisões travadas

### D-01 — não existe migração cega JSON → LLM

| Conteúdo | Destino |
|---|---|
| path/method/operationId/params/schema | OpenAPI + Action Catalog |
| compreensão de pedido/contexto | semantic understanding estruturado |
| argument delta | planner/TU + binder schema-driven |
| required/type/enum/format | validator determinístico |
| RBAC/sensitivity/confirmation | policy determinística |
| business rule/factual verdict | domínio determinístico |
| UX/copy/prompt | conteúdo configurável |
| apresentação genérica | responseSchema + payload + metadata |
| framing/recommendação contextual | síntese grounded existente quando possível |

### D-02 — também não existe migração JSON → hardcode Python/TS

Eliminar um catálogo significa eliminar a **authority conceitual**.

```text
pathMarkers JSON → _DOMAIN_RULES Python = FAIL
parameterStrategy JSON → if path → strategy = FAIL
routeSegment JSON → path-tail = FAIL
path markers → route.operationIds manual = residual técnico
```

### D-03 — OpenAPI standard é suficiente para plugabilidade

`x-delpi.*` é enrichment opcional. Uma API OpenAPI externa padrão deve conseguir entrar por import/index/binding/policy sem core edit por endpoint.

### D-04 — planner não autoriza execução

Retrieval/planner escolhe entre candidates permitidas; validator e RBAC/sensitivity/confirmation continuam soberanos.

### D-05 — evidence freshness

Candidate evidence pertence ao `gitSha/config/model/catalog/dataset` avaliado. Mudança posterior que afeta a dimensão invalida aquele PASS até rerun.

### D-06 — complete means complete

`PARTIAL`, `LEGACY_FALLBACK`, `INCONCLUSIVE`, TODO/FIXME/HACK ou flag sem exit criteria não podem coexistir com `FINAL_RESULT=PASS` quando pertencem ao objetivo material.

## 5. Sequência de execução atual

### Ondas A–I — histórico

| Onda | Tema | Estado atual |
|---|---|---|
| A | baseline/contratos | histórico válido como baseline |
| B | routing universal | implementação existente, revalidada na Onda J |
| C | understanding | implementação existente, cleanup reaberto |
| D | multi-turn/args | implementação existente, path coupling reaberto |
| E | capabilities/composition | implementação existente, metadata reaberta |
| F | recommendations | implementação existente, cutover contextual reaberto |
| G | presentation/skills | implementação existente, revalidar no candidate final |
| H | eval/cutover | PASS histórico, não release vigente |
| I | zero mapa lateral | **PASS invalidado por substitutos semânticos encontrados** |

### Onda J — correção arquitetural — **ABERTA**

Executar sem saltos:

```text
E11.S0  rebaseline + inventário + freeze
E11.S1  enforcement que detecta equivalência semântica
E11.S2  domain classification sem path authority
E11.S3  argument binder schema-driven; remove endpoint strategy
E11.S4  multi-turn por structured state; remove path/operation continuity
E11.S5  remove registry/operationIds como routing authority
E11.S6  semantic authority única; cleanup de NLU endpoint-specific
E11.S7  contextual recommendations + capability effect metadata
E11.S8  Clean Architecture/DI + security hygiene
E11.S9  final candidate R1–R11 + unknown + metamorphic + live parity
E11.S10 final residual scan + docs + verify-final
```

Para cada workstream:

```text
CUTOVER
→ GENERALIZATION
→ CLEANUP
→ VERIFY
→ COMPLETE_GATE
```

Não desbloquear etapa dependente sem pós-condição comprovada.

## 6. Unknown external API — critério real

Unknown significa provider/action/paths/operationIds não conhecidos pelo runtime e não adicionados a selector/vocabulary/path map para o teste.

Fluxo obrigatório:

```text
OpenAPI fictício
→ import/index
→ agent binding
→ allowed actions
→ retrieval
→ planner
→ validator
→ policy
→ executor
→ presentation
```

Depois executar variante metamórfica renomeando:

```text
provider
path
operationId
```

preservando semântica/schema.

Mensagem aleatória sem sentido é negative/no-tool; não é unknown-provider.

## 7. Métricas obrigatórias

Medir baseline e candidate final:

```text
task_decomposition_recall
action_top_k_recall
action_selection_accuracy
argument_extraction_accuracy
missing_required_argument_accuracy
false_tool_call_rate
unnecessary_follow_up_rate
multi_request_completion_rate
multi_turn_reference_accuracy
unknown_api_task_success_rate
metamorphic_rename_pass_rate
task_success_rate
safety_violation_rate
p50/p95_latency
llm_calls_per_turn
tokens_per_turn
tool_calls_per_turn
PATH_COUPLED_RUNTIME_RULES
OPERATION_ID_COUPLED_RUNTIME_RULES
ENDPOINT_STRATEGY_RULES
MANUAL_INTENT_RULES
LEGACY_FALLBACKS
SHADOWS_WITHOUT_EXIT
TECHNICAL_CATALOG_ENTRIES
HARDCODED_SMOKE_CREDENTIAL_DEFAULTS
TODO_FIXME_HACK_MATERIAL_COUNT
```

## 8. Invariantes de segurança e negócio

Não migrar para decisão livre do LLM:

- RBAC/permissions;
- sensitivity/write/admin/destructive enforcement;
- confirmation policy;
- URL/host executável;
- required/type/enum/format;
- factual verdicts/regras de domínio;
- limites operacionais, payload caps, timeout/retry;
- secrets/config de provider.

Capability metadata descritiva deve ser coerente com method/sensitivity/policy, mas não substitui enforcement.

## 9. Paridade transversal obrigatória

Candidate final deve avaliar conforme applicability:

- send;
- stream;
- simulate;
- UI;
- compound;
- multi-turn;
- partial failure;
- persist/reload/F5;
- history/replay;
- admin/debug/telemetry;
- schema-driven presentation;
- Ajuda se user-facing;
- LLM-off/fallback seguro quando aplicável.

## 10. Definition of Done global

Somente fechar/arquivar quando no mesmo candidate final:

```text
CUTOVER_RESULT = PASS
GENERALIZATION_RESULT = PASS
CLEANUP_RESULT = PASS
UNKNOWN_EXTERNAL_API = PASS
METAMORPHIC_PROVIDER_PATH_OPERATION_RENAME = PASS
COMPOUND_LONG_REQUEST = PASS
MULTI_TURN_FOLLOW_UP = PASS
REQUIRED_ARGUMENT_CLARIFY = PASS
UNAUTHORIZED_WRITE_SAFETY = PASS
SEMANTIC_AUTHORITY_SINGLE_OWNER = PASS
CONTEXTUAL_RECOMMENDATIONS = PASS
CAPABILITY_SECURITY_METADATA = PASS
CLEAN_ARCHITECTURE = PASS
SECURITY_HYGIENE = PASS
SEND_STREAM_SIMULATE_UI = PASS
PERSIST_RELOAD_F5 = PASS
R1_R11_REQUIRED_DIMENSIONS = PASS
NO_ENDPOINT_CATALOG_AUTHORITY = PASS
RESIDUAL_SCAN = PASS
DOCS_MATCH_FINAL_HEAD = PASS
COMPLETE_GATE = PASS
VERIFY_FINAL = PASS
```

Qualquer `PARTIAL`, required `WARN`, `INCONCLUSIVE`, `LEGACY_FALLBACK` incompatível com o objetivo ou prova de SHA anterior ao último diff material mantém:

```text
FINAL_RESULT = VERIFY_FINAL_FAILED
```

## 11. Fontes de execução

- planejamento/rebaseline: [`prompt-cursor-plano-mestre.md`](./prompt-cursor-plano-mestre.md);
- execução: [`prompt-cursor-execucao-corretiva.md`](./prompt-cursor-execucao-corretiva.md);
- plano ativo: [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md);
- histórico: [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) e [`ARCHIVED.md`](./ARCHIVED.md).
