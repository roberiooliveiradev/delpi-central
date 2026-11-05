# 237 — DÉLIA · Pydantic AI Native-First — Real Owner Tool Loop / Binding / Evidence Rework

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-REAL-OWNER-TOOL-LOOP-AND-EVIDENCE-REWORK-01`  
**DATE:** 2026-11-04  
**STATUS:** PLANNED — NÃO IMPLEMENTADO; base factual: execução doc 236  
**PREDECESSORS:** docs 231–236, principalmente plano 235, relatório 236 e ledger  
**IMPLEMENTATION_BASELINE:** `57ca0e26842aeb0d55ce5da21d93e42afe887cd3`  
**EXECUTION_REPORT_HEAD:** `3830bd5b94d3002b4277b41103508f6729941264`  
**BRANCH:** `main`, reancorar no HEAD vivo  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**LOCAL ISOLATED REBUILD/E2E:** AUTHORIZED if demonstrably isolated from production  
**EXECUTOR:** Cursor — uma única iteração, diagnóstico→correção mínima→validação real→ledger/push.

## 0. Decisão / gatilho factual

O Documento 236 comprova o avanço estrutural Pydantic AI Native-First no código e o matching entre `EVALUATED_SHA` e `LOCAL_RUNTIME_SHA` em `docker-compose.dev`. **Não comprova inteligência operacional funcional**: E02_POST fez `tool_calls=1` (list), `collected=0`, `OWNER_READS=0`, `NON_GROUNDED`, `owner_path_unbound`, ~8977 ms, 1422 input/29 output tokens reportados; E03 intermitentemente `investigation_agent_error`; RC-B/RC-C/REF05 live continuam pendentes. API health online não implica binding de owner, nem `HTTP 200` equivale a business outcome.

**Verdict independent coordination:** `REWORK` para aceite funcional; as mudanças estruturais 235/236 podem permanecer com aceitação parcial. Corrigir **o caminho genérico** Catálogo→Agent tool choice→Invoke→owner authorized READ→observe→next tool→Outcome; jamais fazer hardcode de produto, especialista ou comparação, nem criar fallback que invoque primeiro tool da lista.

## 1. Reancoragem / autoridades

Antes de código: HEAD + origin/main + git status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → arquitetura técnica → product spec → thematic docs 220,226,228–237 → ledger; fase/CP/RQ/contratos. Preservar WIP alheio. Não presumir status do runtime ou provider. Para cada componente: `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`, owner, consumers, contrato, tests. Conflito canônico: `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED` explícito, não reinterpretar.

## 2. Diagnóstico causal obrigatório e limitado (mesma iteração; sem inventário infinito)

Capturar traces **de uma pergunta E02 real** com correlation_id, sem expor secrets, respostas brutas sensíveis ou prompts privados. **Separar três elos**:
1. `_project_semantic_tool_catalog`: quantos grupos/capabilities cada owner autorizado realmente publica? operação READ/DISCOVERY/ANALYSIS? quais nomes/descriptions/input schemas e limites são projetados? catalog emptiness/truncation/omissão de DAVI? `_groups` live AuthZ? efeitos do `MAX_SURFACE_ENTRIES`/budget/serialização?
2. `Agent.run_sync`: após `list_read_capabilities`, a resposta voltou ao modelo? qual chamada/retorno o modelo produziu? final text, erro do provider, request/tool usage, tool stop/retry, budget, structured-schema format? Alguma incompatibilidade `pydantic-ai==2.50.0` com o modelo OpenAI-compatible/Ollama `delia-qwen3`? A resposta curta (29 output tokens) não prova isoladamente falha de framework.
3. `invoke_read_capability` / `_governed_semantic_tool_invoke` / `_invoke_selected`: foi chamada? Se não, não atribuir defeito à Domain API. Se sim, qual `capability_id` real, schema validation, candidate binding, owner dispatch, auth denial ou error? Trace `discovery→candidate_token→READ` sem forjar token.

Preparar matriz A/B no runtime real isolado: E02 com catálogo e modelo real; tool forced em `FunctionModel` apenas para distinguir wiring de agent choice (testes de integração, sem forçar production calls); comparar variações de projeção de catálogo e native tool registrations, com métricas. Não adicionar lógica oculta de heurística de seleção ao produto. Diagnosticar E03 `investigation_agent_error` por tipo/cadeia causa e capacidade de recuperação nativa segura, sem engolir erro numa resposta normal.

## 3. Corrigir o uso nativo do Pydantic AI, não criar outro fluxo

- **Preferir primeiro** `Agent`, `FunctionToolset`, prepared/dynamic toolset, typed tool metadata/schema, `RunContext`, validators, `UsageLimits`, usage/observability native version 2.50.0. Confirmar assinatura real no SDK instalado; se necessary upgrade, lock/test e documentação, não segundo framework.
- Se catalog listado como JSON volumoso estiver impedindo decisão, tornar capabilities elegíveis encontráveis em superfície de tools nativa (dynamic registration, native tool search/deferred loading se disponível), com schema real e descrições limitadas, preservando owner-neutral IDs e RBAC; não confiar na metadata para autorização. Tool schema `arguments: dict` é tipagem superficial: validar real owner schema em Application, e considerar esquema específico nativo por capability **somente com contrato confiável e sem gerar código/provider branch por capability**.
- Não cadastrar no Agent ferramentas autorizadas fora da live surface; revalidar permissões e candidate binding no instante de cada execução, mesmo que a ferramenta tenha sido apresentada antes.
- Se toolset e modelo forem incompatíveis, corrigir configuração/adapters/binding e provar `list→invoke` no mesmo turno; não implementar `if user asks 'estrutura' then call DAVI`, fallback determinístico `pick first`, regex query router ou `_governed_owner_path` para produzir sucesso artificial.
- LLM decide ações sucessivas depois de evidências, incluindo cross-owner; tools não decidem semântica do objetivo. Reduzir chamadas redundantes, sem remover safeguards. Output context precisa incluir results/evidence handles úteis e validados; testar truncation e limites.
- `request_user_clarification` registra apenas solicitação; provar lifecycle de resposta e continuação do mesmo objetivo no turno seguinte através do contexto existente, sem assumir que concatenação das últimas quatro mensagens equivale a recuperação de evidência persistida.

## 4. Corrigir dois riscos de Evidence, sem comparador especializado

**R-E1 — Composição antecipada**: `_finalize_agent_collected_attempts` retorna `composed_attempt` com SUCCESS antes de verificar plano/obrigações pendentes. RED: usuário pede estruturas A+B **e especificação C**; agente compõe A+B mas C não foi lida. Provar que retorno final NÃO é `GROUNDED` / sucesso completo. Composição de duas fontes é observação parcial; nunca proof da conclusão de todo objetivo. No fix, compor como recurso opcional, mas passar por Outcome/Evidence normal com cobertura de obrigações existentes. Não criar gerenciador de objetivos paralelo.

**R-E2 — Capability identity ≠ evidence satisfaction**: `_attempt_satisfies_obligation` atualmente iguala obligation à `remote_capability`, `action_id` ou `specialist_id`; isso só prova qual tool executou, não qual dado/fato foi obtido. RED: pergunta pede especificação aprovada de A; READ genérica `search_items` com provenance metadata mas payload irrelevante → obrigação não satisfeita. Equivalência somente via owner-authoritative identity/outcome/typed contract e referência real. `source_id` é proveniência, não semantic relevance por si só. Reutilizar contratos `SourceRef`, `SpecialistOutcome`, goal evidence relevance, Claim/evidence validators existentes; nada de nova Evidence Engine, regex ou domínio hardcoded.

**R-E3 — Plan omission**: optional `declare_investigation_goal` não deve permitir ao LLM omitir requisição material explicitamente presente e ainda retornar FACT completo. Reusar a obrigação original de contrato e validação; teste adversarial de omissão. `no plan` é válido para READ simples, não prova suficiência para pedido composto. Se não há evidência verificável para todo pedido, retornar parcial/inconclusivo.

**R-E4 — Multiple owner observations**: `business>1` e no compose pode cair em `last` e perder resultados. RED: consulta exige dois fatos heterogêneos, ambos verificados, modelo sintetiza resposta citando ambos; terminal deve preservar ambos, sem inventar `VerifiedCompositeEvidence` de estrutura para qualquer dado. Reusar contrato adequado de projeção/agregação; não forçar comparação de produtos.

## 5. Testes de comportamento e generalização

### Minimum RED/GREEN deterministic
- Catalog vazio vs populado; entries visíveis ao LLM e schema válido.
- `FunctionModel` chama list depois invoke e uma segunda invoke conforme resultado A.
- `list` isolado não gera falso FACT, logs indicam precisamente `NO_OWNER_READ`, não mascarar causa.
- Unknown ID, stale catalog, schema invalid, revoked AuthZ, write by READ surface, unsafe MCP metadata, candidate forged, prompt injection, excessive output, timeout and cancel; nenhum owner READ indevido.
- E03 agent_error com provider rejection/retry budget teste; uma falha não dispara legado.
- R-E1/2/3/4 negativos, SRC/REF05 root correto, source lineage.
- Clarification+resume, prior context and evidence handles correctness.
- NDJSON & JSON terminal exactly once; error codes and status honest.

### Real local isolated owner matrix (SHA matched)
1. E01 SIPOC conceptual: responde adequadamente, não exige READ nem business FACT.
2. E02 estrutura `90260147`: **OWNER_READS>=1**, identity correspondendo ao objeto, business evidence validada, user outcome relevante.
3. E03 compare `90260147 × 90260148`: **>=2 READs autorizadas**, raízes corretas; agente (não roteiro programado) decide próximas ações e apresenta diferenças fundamentadas.
4. E04 consulta A+B com obrigação C heterogênea, confirma pendência se C faltante.
5. E05 discovery-first real `candidate_token` e READ correspondente.
6. E06 cross-owner multi-step: retorno A altera a tool selecionada B, sem provider branch.
7. E07 ambígua: esclarece e recupera continuidade em novo turno; evidence reutilizada somente válida/fresh.
8. E08 owner unavailable / forbidden / revoked: fail closed, 0 false grounded.
9. E09 JSON/NDJSON activity + deadline/cancel.
10. E10 3+ tools em domínios novos sem hardcode e medidas de latência/token.

**If an owner cannot supply the target** after correct routing: classify availability/access/contract issue, not engineer a fake grounded response. `RC-B, RC-C, REF05` PASS only on real corresponding outcomes.

### Required instrumentation
`BASE_HEAD, EVALUATED_SHA, LOCAL_RUNTIME_SHA, MODEL_ID/CONFIG_HASH, correlation_id, catalog_counts_by_owner, tool_calls_by_name, LLM_requests/input/output_tokens, model_finish_reason/error_type (when available), invoke attempts/results, owner READs, first-read ms, latency, source identities, outcome, grounding, limits/retries, auth decisions`. No tokens/secrets/PII in logs. Status `NOT_MEASURED` where provider omits.

## 6. Execution boundary and anti-regression

Use real dev `docker-compose.dev` isolated workspace with code mounted/recreate and prove no shared prod services/volumes before starting. The prior report did so. **Local rebuild permitted, production forbidden**. `up-prod-sequential.sh` prohibited. Reanchor HEAD before tests and before push, preserve concurrent WIP, stage task paths. Run full delia-api pytest, focused tests, static boundaries, JSON/NDJSON consumers if changed; residual search. Do not claim full implementation complete with owner READs=0; cannot call `ACCEPT`.

**Business correctness/safety gates are nonnegotiable:** Core live RBAC, Domain authority, Policy/Decision, PREPARE≠ACT, no autonomous real writes, no OT direct LLM commands. MCP content/schema untrusted. Model may propose goals/claims; actual facts come from owner outcome. No persistence of chain-of-thought.

## 7. Acceptance gates

AC01 genuine catalog→native Agent selection→invoke tool→authorized owner READ on E02 with exact identity, no hardcode.  
AC02 E03 real 2+ READs & verified task outcome; not just tool count.  
AC03 dependent multi-action across owners/discovery-first demonstrated live.  
AC04 no silent legacy orchestration/alternative framework.  
AC05 composed A+B does not hide C omission; heterogeneous evidence binds real facts, not metadata.  
AC06 non-compare multi-source answer preserves relevant source evidence.  
AC07 revoke/write/injection/candidate/limits negative tests pass; no false `GROUNDED`.  
AC08 clarification is usable across turns with relevant previously-verified context.  
AC09 native Pydantic AI handling used and no second own planner/selector.  
AC10 clean full suite, JSON/NDJSON, runtime_sha == evaluated_sha.  
AC11 real tokens/latency/owner reads/per-task status captured, no fabricated metrics.  
AC12 doc 238 execution report + ledger, residuals and commits verified on `main` (subject to current document numbering and concurrent commits).

Classification: `ACCEPT` only if all functional/security gates proved; `ACCEPT_WITH_RESIDUAL` only for contained external blocks, not masked core E02 no-owner; `REWORK` for a working catalog with no owner READ caused by new runtime; `INCONCLUSIVE` for missing evidence. Document absence of environment as `TEST_NOT_RUN`, not PASS.

## 8. Required execution report

```text
DÉLIA EXECUTION REPORT — REAL OWNER TOOL LOOP / EVIDENCE REWORK
TASK_ID:
BASE_HEAD:
IMPLEMENTATION_SHA:
FINAL_HEAD:
ORIGIN_MAIN:
PUSH_VERIFIED:
AUTHORITY_REANCHOR:
CP_RQ_PHASE:
EXISTING_EQUIVALENT:
REUSE_DECISION:
CAUSAL_DIAGNOSIS_E02:
CATALOG_COUNTS_BY_OWNER:
MODEL_TOOL_CHOICES_AND_FINISH_REASONS:
INVOKE_REACHED:
OWNER_AUTHZ_AND_DISPATCH:
Pydantic_AI_NATIVE_FIX:
CODE_REMOVED_RETAINED:
EVIDENCE_E1_E2_E3_E4:
RC_B:
RC_C:
REF05:
E01_E10_LIVE_MATRIX:
LIVE_OWNER_READS:
EVALUATED_SHA:
LOCAL_RUNTIME_SHA:
MODEL_CONFIG_HASH:
INPUT_TOKENS:
OUTPUT_TOKENS:
LLM_REQUESTS:
TOOL_CALLS:
TIME_TO_FIRST_OWNER_READ:
TOTAL_LATENCY:
BUSINESS_TASK_OUTCOME:
FALSE_GROUNDED_COUNT:
RED_GREEN:
BACKEND_REGRESSION:
JSON_NDJSON:
SECURITY_NEGATIVES:
GENERALIZATION:
RESIDUAL_SEARCH:
DOCS_LEDGER:
UNRESOLVED:
VERDICT:
PRODUCTION_DEPLOY: NOT_AUTHORIZED
```

## 9. Execution order

**No additional plan-only iteration.** Reanchor; capture actual trace for E02; write REDs; fix root cause in native agent/toolset or catalog/invoke boundary; get E02 real owner READ; run E03/multi-step; fix evidence E1–E4; run security/generalization/NDJSON/full regression; local SHA-matched E2E; update execution doc/ledger; commit/push; report. If a genuine external blocker prevents parts, provide exact proof and execute all remaining independent steps; never mark blocked scenarios PASS.


---

## Update after execution (2026-11-04) — doc 238 + native capability reference 239

This task was executed and reported in [doc 238](238-native-first-real-owner-tool-loop-binding-and-evidence-hardening-execution-report.md), implementation SHA `0b40e42af6d3bb6b6f7d2e185fe92db92e70b46d`. **E02 real owner READ now GROUNDED/OBSERVATION**, discover→execute→get_product_structure, approximately 41s; backend pytest GREEN and 11-line NDJSON verified by executor. **E03/E04/E05/E10 multi-step remain residual**; the complete generalist-agent functional acceptance is **not proven**. Production deploy remains NOT_AUTHORIZED.

A permanent feature/API inventory, examples, native-first adoption gates, historical prompt outcomes and next experiments are recorded in **[doc 239 — Pydantic AI native capabilities & execution evidence register](239-pydantic-ai-native-capabilities-reference-and-execution-evidence-register.md)**. Before any new agent capability, consult doc 239 **and independently verify installed SDK signatures and owner contracts**; do not create another bespoke planner or provider-specific flow. Doc 239 is a technical reference, not evidence of tests or phase advancement.
