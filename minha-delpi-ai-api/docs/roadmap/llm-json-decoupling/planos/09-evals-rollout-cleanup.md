# Plano 09 — Evals, rollout, cutover e cleanup final

**Prioridade:** transversal  
**Status execução:** Onda H · E9.S1 **ATENDIDO** · E9.S2 **ATENDIDO_PARCIAL** · E9.S3 **ATENDIDO** (offline) · E9.S4 **ATENDIDO** · próxima E9.S5  
**Evidência:** [`../evidence/e9-s1-corpus-expanded.md`](../evidence/e9-s1-corpus-expanded.md) · [`../evidence/e9-s2-baseline-offline.md`](../evidence/e9-s2-baseline-offline.md) · [`../evidence/e9-s3-candidate-plans-offline.md`](../evidence/e9-s3-candidate-plans-offline.md) · [`../evidence/e9-s4-shadow-divergence.md`](../evidence/e9-s4-shadow-divergence.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
**Objetivo perceptível:** cada migração de catálogo/heurística para OpenAPI/LLM deve provar melhora generalizável, preservar segurança e só então remover legado.

## Fonte de verdade

Usar obrigatoriamente:

- `.cursor/rules/ai-intelligence-evaluation.mdc`;
- `minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md`;
- regras de plan execution/test-and-commit vigentes.

Não usar scripts isolados ou smokes históricos como critério final de release.

## Requisitos

| ID | Requisito |
|---|---|
| R09-01 | Congelar baseline antes de alterar comportamento. |
| R09-02 | Executar candidate no mesmo corpus/config. |
| R09-03 | Cobrir R1-R11 conforme applicability. |
| R09-04 | Provar unknown external API e metamorphic rename. |
| R09-05 | Medir compound, multi-turn, safety, latency e cost. |
| R09-06 | Fazer shadow/canary quando risco justificar. |
| R09-07 | Remover fallback/JSON morto somente após evidência. |
| R09-08 | Atualizar docs canônicas e limpar roadmap concluído conforme política documental. |

## Etapas

### E9.S1 — Dataset e manifesto imutável — **ATENDIDO** (2026-09-10)

**Feito (Onda A):** manifesto estreito `routing_cases@v1` (6 casos) — **imutável**.

**Feito (E9.S1):** corpus ampliado `r1_r11_corpus_v1` com **20/20** classes do §E9.S2 indexadas a harness existentes; freeze `datasetHash=371f0cfa…`; run em `docs/testing/evidence/runs/*_e9-s1-corpus-v1/`; Onda A intocada.

**Pendente para release R1–R11:** execução E9.S2; `openApiSchemaHash` / `actionCatalogHash` runtime.

### E9.S2 — Baseline R1-R11 — **ATENDIDO_PARCIAL** (2026-09-10)

**Feito:** baseline offline no corpus v1 — 16 módulos pytest / **99 passed**; mesmo `datasetHash` do E9.S1; evidência `e9-s2-baseline-offline-v1`.

**Pendente:** runners de fixtures JSON; dims live LLM; hashes de catálogo runtime.

Cobrir no mínimo (checklist do plano — harness indexado; execução plena progressiva):

1. action específica vs genérica;
2. semantic siblings;
3. multi-provider;
4. no-tool;
5. required present;
6. required missing -> clarify;
7. enum/type invalid;
8. pedido longo/compound;
9. multi-turn/follow-up;
10. typo/sinônimo/informal;
11. unknown external OpenAPI;
12. metamorphic provider/path/operationId rename;
13. unauthorized action;
14. write/destructive confirmation;
15. prompt/tool-output injection;
16. schema-driven presentation;
17. recommendations grounded;
18. send/stream/simulate;
19. persist/reload/F5;
20. partial failure.

### E9.S3 — Candidate evidence por plano — **ATENDIDO** (2026-09-10, offline)

**Feito:** mapa `e9_s3_plan_candidate_map.json` + runner offline; 8/8 planos `NO_REGRESSION_OFFLINE` no mesmo `datasetHash`; `globalPass=false` com dims deferred INCONCLUSIVE.

**Não fazer:** marcar PASS global com dimensão obrigatória FAIL/INCONCLUSIVE — **respeitado**.

### E9.S4 — Shadow divergence telemetry — **ATENDIDO** (2026-09-10)

**Feito:** inventário canônico `e9_s4_shadow_divergence_inventory.json` (6 shadows críticos) + gate pytest (owner, module em `app/domain/services/`, `sideEffects=false`, reasonFields, evidence). Sem novo sistema dual-run.

**Pronto quando:** divergências críticas possuem explicação e owner — **cumprido** via inventário + teste de explainability.

### E9.S5 — Canary/default cutover

**Fazer:** liberar candidate por cohort/agente/feature flag quando existir mecanismo canônico; definir rollback simples e observável.

**Teste:** live L1-L4 quando aplicável.

### E9.S6 — Cleanup gates

Antes de remover qualquer catálogo/heurística:

```text
candidate task success >= meta
unknown API = PASS
metamorphic = PASS
safety = PASS
required args = PASS
multi-turn = PASS
compound = PASS
latency/cost = aprovado
legacy fallback hit rate = residual e explicado
```

Depois remover código/conteúdo morto e atualizar audits.

### E9.S7 — Architecture audit

**Fazer:** procurar residuals no core genérico:

```text
pathMarkers
operationIdMarkers
parameterStrategy por endpoint
pathToken/pathContains para seleção
routeHints manuais
scopeToRouteId
preferredRouteId
manual endpoint priority
if path/provider/operationId
```

Cada residual deve ser removido ou explicitamente justificado como policy/compatibility/documentation fora do core genérico.

### E9.S8 — Verify-final

Executar matriz final:

| Objetivo | Prova | Resultado esperado |
|---|---|---|
| nova API sem código | unknown provider eval | PASS |
| rename técnico sem quebra | metamorphic eval | PASS |
| frases longas | compound corpus | PASS |
| follow-up | multi-turn corpus + F5 | PASS |
| argumentos | OpenAPI validator corpus | PASS |
| safety | unauthorized/write/injection | PASS |
| apresentação | unknown schema/provider | PASS |
| recomendações | grounded/allowlist | PASS |
| paridade | send/stream/simulate | PASS |
| eficiência | P50/P95/tokens/tool/LLM calls | aprovado |

### E9.S9 — Documentação e encerramento

**Fazer:** incorporar decisões finais em arquitetura/API/testing docs canônicos; atualizar changelog quando aplicável; remover roadmap concluído se deixar de ter valor futuro, seguindo política do diretório `roadmap`.

## Métricas mínimas

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
legacy_fallback_hit_rate
catalog_path_coupling_count
manual_intent_rule_count
```

## Release evidence obrigatória

Registrar:

```text
EVAL_SET_VERSION
BASELINE_RUN_ID
CANDIDATE_RUN_ID
R1_R11_SUMMARY
METRICS_BEFORE_AFTER
REGRESSIONS
P50_P95
COST_BUDGET
EXTERNAL_API_GENERALIZATION
COMPOUND_REQUESTS
MULTI_TURN
SAFETY_RESULT
LEGACY_FALLBACK_RATE
DECISION
```

## Aceite final da iniciativa

```text
GENERALIZATION = PASS
SAFETY = PASS
OUTCOME = PASS
EFFICIENCY = PASS/APPROVED
LEGACY_CATALOG_AUTHORITY = REMOVED
TECHNICAL_JSON_DUPLICATION = REMOVED_OR_JUSTIFIED
MANUAL_NLU_RULES = REDUCED_TO_JUSTIFIED_FAST_PATHS
DOCS_CANONICAL = UPDATED
```
