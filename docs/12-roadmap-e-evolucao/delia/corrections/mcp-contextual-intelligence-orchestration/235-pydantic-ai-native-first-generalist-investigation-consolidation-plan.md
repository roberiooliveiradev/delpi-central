# 235 — DÉLIA · Pydantic AI Native-First — Consolidação do Agente Investigativo Generalista

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-NATIVE-FIRST-GENERALIST-INVESTIGATION-CONSOLIDATION-01`  
**DATE:** 2026-11-04  
**STATUS:** PLANNED — implementação e avaliação ainda NÃO executadas neste documento  
**EXECUTOR:** Devin (ou executor designado)  
**REPOSITORY:** `roberiooliveiradev/delpi-central`  
**PLANNING_HEAD_OBSERVED:** `df3dedadbf5707a431a1ff2ea363eca4cd2f1946` (reancorar antes de executar)  
**PREDECESSORS:** doc 231 (plano original), docs 232–234 (execuções e residuais), 230 (inventário), 226 (semantic-once), 229 (fragmentação), 228 (evidence obligations), ledger  
**DECISION:** Pydantic AI Native-First; UMA inteligência semântica investigativa, sem LangGraph nem infraestrutura agentiva paralela  
**EXECUTION:** uma tarefa integral, com fases internas, testes e relatório factual; nenhuma aprovação intermediária rotineira para remoção de código substituído  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**LOCAL ISOLATED BUILD + E2E:** AUTHORIZED, desde que não use comandos, credenciais, serviços ou volumes produtivos; acesso autorizado a owners é READ-only.

> **Decisão de produto:** o usuário fornece um objetivo, não um roteiro técnico. O agente Pydantic AI escolhe dinamicamente uma ou mais capabilities semânticas governadas, observa resultados, pode investigar outros owners/MCPs, sintetizar, esclarecer lacunas e continuar. **Nenhuma família de intenção (comparação de estruturas, atraso de pedido, indicador, fornecedor, engenharia) deve depender de um workflow hardcoded**. Adapters, AuthZ, Domain authority, Evidence, Policy, Decision, Outcome e proteção OT permanecem responsabilidades explícitas da DÉLIA/ecossistema.

## A. Estado real que esta continuação sucede

**PROVEN via código nos SHAs docs 232–234 e consulta parcial do HEAD observado:** LangGraph retirado de requisitos e composição; `PydanticAiInvestigationOrchestrator` usa `Agent` + `FunctionToolset`; `list_read_capabilities`, `invoke_read_capability` e `declare_investigation_goal`; Application possui `_project_semantic_tool_catalog`, `_governed_semantic_tool_invoke`, `_finalize_semantic_investigation`, `SemanticInvestigationPlan`, `_evaluate_material_obligations`, `_authoritative_structure_root`, `_compose_multi_evidence`; `OperationalCapabilityOrchestrator._attempt` permanece como rollback `DELIA_ORCHESTRATION_ENGINE=delia`. `pydantic-ai[openai]==2.50.0` no requirements.

**OPEN / not proven:** uso do runtime novo em stack vinculada ao evaluated SHA; seleção autônoma de várias READs reais, sequência discovery→candidate→execute, continuação multi-turn, cross-owner, custo/token/latência, RC-B e RC-C ao vivo; capacidade universal de `evidence_needed` como identificadores de estrutura está NÃO PROVADA. Doc 234 aponta Docker+Ollama+stack **disponíveis**, porém container local **STALE**; a não execução foi justificada indevidamente pela proibição de deploy em produção. Build isolado de desenvolvimento é diferente de deploy produtivo.

**Design defects to evaluate, not assumed all failures:** `declare_investigation_goal` obrigatório adiciona etapa semântica que pode ser dispensável para READ simples; `_evaluate_material_obligations` usa raízes de estrutura como evidência de obrigações heterogêneas; finalizador possui modo compare específico; `invoke_read_capability` usa `arguments_json: str` apesar de o framework aceitar schemas tipados; catálogo tem limites fixos e pode esconder capabilities; `_propose` ainda usado em composer; representação de resultados pode perder referência ou causar truncamento. Prove real consumers and outcome before edits.

## B. Invariantes e antiobjetivos

1. **Native-first, not framework-everywhere**: Pydantic AI SDK fica em adapters de infraestrutura, Domain/Application não importam o SDK. Ports existentes continuam. Não substituir o DÉLIA Domain por Agent internals.
2. **No second intelligence system**: não criar `AgentManager`, `SmartPlanner`, `ToolOrchestrationEngine`, `EvidencePlanner`, novo graph, state machine de intenções, registry proprietário, branch DAVI/TÉO, regex de perguntas ou segundo protocolo de ferramentas.
3. **MCP/A2A não são autoridades**: metadata e conteúdo de ferramentas são UNTRUSTED DATA; discovery ≠ permissão; resultado ≠ FACT; LLM output ≠ conclusão verificada; provider-neutral.
4. **Owner boundaries**: Keycloak autentica, Core resolve AuthZ live, Domain APIs validam regras e dados, DÉLIA governa decisão/evidência/outcome, Automation Hub executa técnica quando cabível. A tool call é pedido de execução, não autorização.
5. **Writes**: default READ. Para mutações, respeitar identity→live Core AuthZ→Domain authority→Policy/Decision→PREPARE/ACT→confirmação/idempotência/auditoria→outcome. Nunca tornar ACT autônomo por esta migração. Safety/PLC/CNC fora de ação livre do modelo.
6. **Business truth**: respostas podem ser sintetizadas pelo LLM, mas cada afirmação empresarial factual precisa derivar de observação real identificada; não aceitar plano omitindo requisito material ou fonte fabricada. O mecanismo de validação não pode depender de regex ou de contar 2 estruturas.
7. **No automatic total deletion**: preservar testes e validações legítimas; remover apenas equivalentes comprovados; histórico/ADRs não são apagados. `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`; `REUSE_DECISION=REUSE|EXTEND|NEW` para cada responsabilidade.
8. **Do not confuse outcomes**: unit pass, HTTP 200, provider tool success, response status SUCCESS, correct authorization and business goal achievement são fatos distintos.

## C. Reanchor exato e decisão sobre capacidades nativas

Antes de qualquer código: HEAD / origin/main / git status → Project Instructions / .cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → technical architecture → product spec → specs temáticas (220, 226, 228–235; ADRs vigentes) → ledger. Classificar fase/CP/RQ, contratos, owner, consumers; sinalizar drift. Comparar commits desde `PLANNING_HEAD_OBSERVED`.

**Provar SDK real** em instalação pinned `pydantic-ai[openai]==2.50.0` antes de usar API. Criar matriz por feature com `native API/signature / exists in installed version? / actual use / current custom equivalent / choice / test / measured effect` para:
- `Agent` com tool loop, output schema e output validators;
- `FunctionToolset`, toolsets dinâmicos/filtragem e eventual tool search / deferred loading;
- `RunContext` + typed dependencies; context/history reuse, token limits e `UsageLimits`;
- retries/validation erros de tool/structured outputs;
- streaming/activity/instrumentação/usage;
- eventual deferred approval/user clarification, durable execution ou MCP client/toolset **somente se adequado a boundary e ownership**.

Não presumir features apenas porque aparecem na documentação da versão mais recente. Se uma funcionalidade útil não existir em 2.50.0, avaliar atualização controlada do pacote com test matrix e migração de API, **não instalar outro framework nem criar uma implementação duplicada por conveniência**. Se não há necessidade provada, não adicionar subsistema de workflow durável.

## D. Contrato-alvo mínimo — ciclo dinâmico

```text
Authenticated User Turn / Event (context, request constraints)
  -> Application existing interaction boundary and truthful activity
  -> Pydantic AI Agent (infra port adapter): reason about objective
       -> inspect authorized semantic capabilities (native tools/toolset)
       -> request governed tool A -> real owner result + source refs
       -> decide B based on A; may ask clarification
       -> request B, then C... (possibly distinct owners/MCP)
       -> propose final structured answer: claims, cited evidence handles,
          uncertainty, gaps, task progression; no invented domain FACT
  -> DÉLIA deterministic Evidence/Policy/Outcome verification
  -> existing Interaction output (JSON/NDJSON/CRI), status and limitations
```

Agent may reason on its own; its proposals **never** grant capability permissions, make claims FACT, change industrial interlocks, or bypass live Domain validation.

**No mandatory `declare_investigation_goal` tool call on every turn.** Determine whether it is better replaced by typed run output/context or made optional. For simple asks, minimize pre-READ model calls; for complex asks, preserve durable *semantic goal and outstanding obligations* with no duplicative planner. Plan can change as new evidence appears, without rewriting original user intent or dropping explicit obligations.

**No mandatory `_compose_multi_evidence` for comparisons.** Agent can analyze evidence from 2+, or cross-type sources; typed deterministic comparison function remains optional capability when supported and useful, not a hardwired terminal branch. Specific identity/quantity verifiers run when relevant to the real domain payload, not as intent router.

## E. Execute in ONE iteration — bounded phases

### E0. Characterize baseline and freeze existing contracts
- Reanchor; read existing tests and docs 230–234. Build actual callgraph `POST /interaction/turns` and JSON/NDJSON paths, prior turns, Pydantic AI adapter, `_propose` callers, actual live surface/owner invoke, evidence, fallbacks and config. Record A/B existing and residual legacy consumers. No indefinite inventory; same task continues to implementation.
- Baseline local isolated scenario matrix using SHA-matched runtime if accessible. Record current failures honestly.
- Contract locks: `SupportsGovernedCapabilityAttempt`, `SupportsGovernedStageGates`, `ModelInvocationPort`, `InvokeModel`, `GovernedCapabilityAttempt`, `VerifiedCompositeEvidence`, `SourceRef`, Domain identity, AuthZ context, `TurnDeadline`, activity sink, NDJSON terminal, confirmation/write chain, discovery candidate binding.
- RED tests for target failures, including complex questions needing dependent 2–4 tools, differently-worded objectives, no predeclared compare path, and statements with missing evidence.

### E1. Native Agent / toolsets consolidation
- Reuse existing `PydanticAiInvestigationOrchestrator`, `PydanticAiModelInvocationAdapter`, approved application ports and provider-neutral adapters.
- Prefer native typed tool arguments and output types over `arguments_json` strings where real provider capability schemas permit. Maintain dynamic catalog/surface selection without leaking secrets. Use Pydantic AI dynamic/prepared toolsets only if supported by pinned version, with native schema validation; sanitize descriptions as UNTRUSTED.
- Replace extra model-driven admission/classification/decomposition/group selection/argument-generation only where Pydantic AI tool-driven reasoning demonstrably performs equivalent or better. Do not delete general conversational handling, Domain validation, SourceRef or user confirmation.
- Eliminate parallel selector/arggen/instruction purposes, duplicated retries and unnecessary `_propose` calls after proving no live consumers. Remove `DELIA_ORCHESTRATION_ENGINE=delia` rollback **only after** acceptance evidence or document bounded retention as a specific residual; goal is one permanent production semantic runtime, not 2 agent paths.
- Tool visibility ≠ permission; on each tool execution re-fetch live surface, check applicable Core/domain/policy gates, validate input, enforce read/write stage; no direct raw provider execution by agent.

### E2. True autonomous multi-action investigations
- Agent chooses sequence opportunistically: READ A, inspect result, then select READ B or DISCOVERY→candidate-bound READ C, optionally use a different MCP. No intent-specific scripts. Preserve relevant factual observations in bounded context.
- Preserve typed evidence handles/lineage outside token-only history; reuse verified evidence across turns only after checking freshness and scope; do not turn memory, cache, prior chat or tool metadata into authority.
- Let agent continue until justified completion, clarification, incomplete evidence or bounded limit. No model-driven assertion can force completion when required evidence absent.
- Add user clarification tool/output pattern with ability to resume investigation on next turn without losing previously verified sources; use existing interaction/session contracts, never invent new persistence without owner/consumers.
- For user-requested business actions: agent may propose eligible PREPARE through governed chain only if currently allowed; never make read-only tool implicitly ACT, never send/write without gates.
- No infinite loops: `UsageLimits`, per-turn deadlines, cancellation, bounded tool output, usage telemetry, idempotent owner reads/retries where required, exactly one terminal.

### E3. Generic evidence-backed synthesis / outcome without a custom planner
- Agent produces typed `answer/claims/evidence_refs/limitations/clarification_or_next_step` proposal or equivalent existing response contract; the exact schema comes from existing contracts, not a new competing evidence model.
- Evidence verifier resolves refs against actual tool outcomes/Domain provenance; checks correspondence, identity, domain-specific invariants and obligations explicit in original request. For structures, correct root is validated through authorized structured domain data. For specs/inventory/finance, use appropriate existing owner contract—not product root equalities.
- Replace terminal `comparison_requested` and count-of-two enforcement as generic routing. Existing deterministic comparison function may remain callable as an optional approved analysis capability, not hard-coded by the finalizer.
- If LLM invents/omits sources, unsupported figures, claimed action completion or material obligation, return honest limited/inconclusive response. Do not implement lexical keyword detector to check omitted obligations; use existing goal/evidence contract + typed claim references and test adversarial omissions.
- Do not persist chain-of-thought; retain only approved summaries, tool evidence and structured outcomes.

### E4. Cleanup without deleting domain authority
- Create deletion map: exact old function/file/config → consumers → native replacement → regression evidence → REMOVE/KEEP/EXTEND. Remove replaced semantic sequencers, selector functions, stage prompts, tool wrapper duplicates, unused flags, no-op adapters and obsolete test-only branches. Do not erase historically frozen evidence.
- Each delete requires caller/residual search and functional regression, but **not a new PO authorization**, as user authorized migration.
- Keep Clean Architecture; no SDK import in Domain/Application, no new runtime/provider branches, no duplicated authorization source.
- Avoid massive file splitting unless it concretely removes dependency/coupling with source evidence.

### E5. Functional evaluation: behavior, not architecture
**Run at least**:
1. Conceptual question (FAST / minimal unnecessary model calls).
2. Single authoritative owner READ with exact entity binding.
3. Multi-target comparison with real 2-source evidence but **no comparison-specific scripted workflow**.
4. Multi-step dependent investigation: result A determines B, B determines C.
5. Cross-owner investigation requiring different MCPs.
6. Discovery-first candidate-bound capability, no fake tokens.
7. Ambiguous objective: ask clarification; after user answers resume and preserve evidence.
8. Incomplete/missing third-party obligation, no false grounded.
9. Wrong-root, mixed-identity, wrong source, untrusted metadata, injected instructions.
10. Unknown capability, schema invalid, auth revoked, write/policy forbidden.
11. Long result + context limit; no evidence handles lost.
12. Follow-up using prior evidence without unauthorized memory reliance.
13. NDJSON activity, cancellation, deadline, exactly one terminal.
14. Several new paraphrases in unrelated domains; no DAVI/TÉO/product-code hardcode.
15. Real Domain/AuthZ/owner outcomes under local authenticated Keycloak context, when legitimately accessible.

Use real-model tests and mocks separately. Track test dataset, configuration, real task success, false grounding, model calls and tokens, tool calls, latency, first-owner READ, incomplete-answer honesty and activity sequence. Never count `HTTP 200` as outcome. Explicit `NOT_MEASURED` when provider omits usage.

### E6. Local runtime homologation without production deployment
- **Local isolated rebuild/test are authorized**, not production deployment. Prove Docker context/host, target compose project, container/image SHA, external environment and volumes before any command. Never run `up-prod-sequential.sh` or reuse production volumes, secrets or routes for this test. If only actual production stack exists, do not rebuild it: create isolated dev/eval stack from existing approved scripts/ports without touching production.
- Since doc 234 observed local Docker/Ollama/API available but stale, explicitly remediate `STALE_EVIDENCE` by rebuilding **isolated** runtime at evaluated SHA and running E01–E15. If impossible after legitimate attempts, capture exact blocker and complete other tests; `LOCAL_E2E=TEST_NOT_RUN`, not PASS.
- No real material writes; no impersonation, no admin token copying, no credentials in prompts/logs.
- Do not use current production deployment as test or authorization.

### E7. Docs and delivery
- Update ADR / canonical documentation if the actual HEAD requires it; this doc is an execution plan, not phase advancement. Create subsequent numbered **execution report** that records exactly what ran, changed, failed and remains; update ledger only with factual statuses; annotate superseded semantic infrastructure, don't rewrite historic 231–234 as if original tests were new.
- Run focused RED/GREEN, backend full pytest, relevant frontend consumer JSON/NDJSON regression, static architectural import boundaries, fresh clean install/boot, residual search, real model/owner matrix.
- Stage only task paths; preserve concurrent WIP; commit/rebase/push `main` if authorized and HEAD matches; verify push and report SHA.
- If security/authority conflict blocks work: `EXECUTION_DRIFT` or `ARCHITECTURE_DECISION_REQUIRED`, never bypass; complete safe independent portion.

## F. Required accept/rework matrix

| AC | Definition |
|---|---|
| 01 | Pydantic AI is **sole** production semantic investigation runtime; no LangGraph/other planner |
| 02 | No mandatory intent-specific workflow; tool choice and sequencing demonstrably model-driven |
| 03 | Single read succeeds, with proportional model usage, without forced full pre-plan |
| 04 | Independent and dependent multi-tool goals actually complete on relevant owner data |
| 05 | Cross-MCP owner selection and discovery→candidate→READ verified |
| 06 | Agent supports clarification and multi-turn continuity with safe evidence reuse |
| 07 | Native tool schema validation, deps/history, usage bounds, retries and telemetry used where supported |
| 08 | Native feature equivalence + deletion map complete; no redundant semantic call chains remain |
| 09 | Source identity and fact claims are validated against authoritative owner outcome; zero false grounded in executed negative matrix |
| 10 | Heterogeneous material obligations handled; agent omissions cannot silently turn into factual completeness |
| 11 | Core/Domain/Policy/Decision/confirmation/idempotency/Safety unaffected; no unauthorized write or tool |
| 12 | JSON/NDJSON/CRI, deadlines, cancellations, one terminal and response honesty maintained |
| 13 | Testable fresh local runtime SHA matches evaluated SHA; genuine model and owner READs measured |
| 14 | Generalization on previously unseen formulations and different owners, no task-specific routing |
| 15 | Full backend and applicable consumer regressions green; docs/ledger factually updated; pushed SHA verified |

**Decision:** `ACCEPT` only if functional and safety evidence covers criteria; `ACCEPT_WITH_RESIDUAL` only for isolated external blockers with no claim of full functional acceptance; `REWORK` for parallel semantic planner, false grounding, abandoned owner routing or regression; `INCONCLUSIVE` for unverifiable behavior. No production deploy.

## G. Reporting contract

```text
DÉLIA EXECUTION REPORT — PYDANTIC AI NATIVE-FIRST
TASK_ID:
BASE_HEAD:
FINAL_SHA:
ORIGIN_MAIN:
PUSH_VERIFIED:
GIT_STATUS:
AUTHORITIES_READ:
PHASE_CP_RQ:
DECISION_ADR:
EXISTING_EQUIVALENT:
REUSE_DECISION:
FEATURE_API_MATRIX_PINNED_VERSION:
PRODUCT_RUNTIME_BEFORE:
PRODUCT_RUNTIME_AFTER:
NATIVE_AGENT_TOOLSET_CHANGES:
SEMANTIC_CODE_REMOVED:
LEGACY_RETAINED_WITH_CONSUMERS:
TOOLS_SCHEMA_AND_AUTHZ:
MCP_DISCOVERY_AND_CANDIDATE_BINDING:
AGENT_DYNAMIC_MULTISTEP:
AGENT_CROSS_OWNER:
AGENT_CLARIFICATION_RESUME:
EVIDENCE_CLAIM_PROVENANCE:
MATERIAL_OBLIGATION_VERIFICATION:
POLICY_WRITE_SAFETY:
SINGLE_READ:
COMPOSED_GOALS:
GENERALIZATION_RESULTS:
FALSE_GROUNDED_COUNT:
TESTS_RED_GREEN:
BACKEND_FULL_REGRESSION:
CONSUMER_JSON_NDJSON:
EVALUATED_SHA:
LOCAL_RUNTIME_SHA:
LIVE_OWNER_READS:
LLM_REQUESTS_BEFORE_AFTER:
INPUT_OUTPUT_TOKENS:
TOOL_CALLS:
TIME_TO_FIRST_READ:
TOTAL_LATENCY:
BUSINESS_TASK_OUTCOME:
RESIDUAL_SEARCH:
DOCS_ADR_LEDGER:
UNRESOLVED:
ROLLBACK:
VERDICT:
PRODUCTION_DEPLOY: NOT_AUTHORIZED
```

## H. Direct execution instruction

Do not submit a new architecture-only proposal, an endless discovery loop, a generic 'Agent Framework', or another hardcoded comparison workflow. **Implement the full authorized native-first consolidation in one task**: reanchor → prove version/API → write REDs → switch to native Pydantic AI capabilities → remove replaced bespoke code → preserve trusted ports/gates → generalize evidence-aware answers → evaluate real dynamic multi-action tasks → document → commit/push → report. If local E2E remains impossible, say exactly so, with independent tests and no fabricated functional pass.
