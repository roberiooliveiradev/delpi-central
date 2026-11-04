# 230 — DÉLIA · Inventário executivo dos fluxos LangGraph × Pydantic AI × Orquestração Application

**TASK_ID:** DELIA-C3-FRAMEWORK-OVERLAP-RUNTIME-FLOW-INVENTORY-01  
**STATUS:** INVENTORY_COMPLETE — awaiting coordination decision  
**CREATED:** 2026-11-04  
**FILLED:** 2026-11-04  
**BASE_HEAD:** `3496551f30a57af0d5d82d516bf5e8480375abf7`  
**REFERENCE:** doc 229 (auditoria sistêmica), doc 226 (semantic once), doc 228 §§12–20, docs 192–196 (Engine B), doc 220 (Pydantic AI M2), execution ledger  
**SCOPE:** INVENTÁRIO COMPLETO EM UMA ÚNICA ITERAÇÃO — ZERO ALTERAÇÃO PRODUTIVA  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**PRODUCT_CODE_CHANGED:** NO  
**DECISION AUTHORITY:** Coordenação DÉLIA, após evidência neste documento.

> **Missão cumprida neste arquivo:** inventário integral com evidências de código/contratos/consumers no HEAD acima. Nenhuma simplificação, desinstalação, mudança de prompt/contrato/migração/deploy ou ownership foi implementada.

## 0. Reancoragem obrigatória e protocolo

| Campo | Valor | Classificação |
|---|---|---|
| BASE_HEAD | `3496551f30a57af0d5d82d516bf5e8480375abf7` (após `git pull --ff-only origin main` a partir de `a20e26a495`) | PROVEN |
| HEAD/ORIGIN_MAIN at review | sync ff-only no início da task; SHA final após commit desta task no relatório §11 | PROVEN |
| GIT_STATUS | tracked limpo pós-pull; untracked concorrente preservado: `plugins/tv-dashboard-presentation/artifacts/`, `…/kpi-status-capture.spec.ts` — **não staged** | PROVEN |
| AUTHORITIES_READ | `.cursor` constituição + `delia-execution-protocol.mdc`; docs 16, 50, 17, 49, 51, 52, 21, 20, 25 (títulos/posição); docs 192–196, 220, 226, 228, 229; ledger § audit 229 | PROVEN (leitura mínima suficiente) |
| THEMATIC_SPECS/ADRs/DECISIONS | Engine B = stage sequencing only (194/195); Pydantic AI = ModelInvocationPort default (220/M6); semantic-once sticky goal (226) DRIFT_PARTIAL vs runtime (229); CRI response mode not planner (229) | PROVEN |
| PHASE/CP/RQ | C3 MCP contextual intelligence — E4-R6 residuals OPEN (RC-B/C/REF05); fase **não** avançada por esta task | PROVEN ledger |
| DOC229_FINDINGS_REVALIDATED | ≥20 purposes, fragmentation PARTIALLY_PROVEN, FAST/OPERATIONAL/REASONING=telemetry, Option B recommended — **reconfirmados** no HEAD (20 keys em `orchestration_instructions.delpi.json`; `select_decision_path` não encontrado como branch de controle) | PROVEN |
| EXISTING_EQUIVALENT | `OperationalCapabilityOrchestrator` + `SupportsGovernedStageGates` + `ModelInvocationPort`/`InvokeModel` + `SubObjectiveTracker` + Evidence contracts | PROVEN |
| REUSE_DECISION | EXTEND/CONSOLIDATE semantics no Application; **não** trocar frameworks nesta decisão | PROVEN recommendation |
| EXECUTION_DRIFT | **DRIFT_DOCSTRING:** `langgraph_engine.py` L3–7 ainda diz “LOCAL EVALUATION ONLY / Never wired into production composition root”; runtime default = `langgraph` (`settings.py` L276–278; `infra/docker-compose.yml` L2101). **DRIFT_PARTIAL (doc 226):** semantic-once ainda incompleto (doc 229). | PROVEN |

Hierarquia aplicada: instruções/.cursor → 16/50/17/49 → contracts/código HEAD → docs históricos (194 “eval-only” **superado** por Task 07 + settings default).

---

## 1. Pergunta decisória central

**LangGraph e Pydantic AI exercem responsabilidades complementares na DÉLIA ou existe sequenciamento/planejamento/admission/retry/estado duplicado entre eles e o orquestrador Application?**

### Veredito executivo (evidência abaixo)

| Camada | Papel real no HEAD | Sobreposição |
|---|---|---|
| **LangGraph** (`LangGraphCapabilityOrchestrator`) | Sequenciador de estágios (StateGraph + edges). Default de produção via `DELIA_ORCHESTRATION_ENGINE=langgraph`. **Não** chama LLM, **não** seleciona capability, **não** autoriza, **não** grounda. Delega 100% dos gates a `SupportsGovernedStageGates` (= instância de `OperationalCapabilityOrchestrator`). | Alternativa de **sequenciamento** vs Engine A `_attempt` — **um engine por processo**, nunca ambos no mesmo turn. Fan-out/checkpoint são opt-in. |
| **Pydantic AI** (`PydanticAiModelInvocationAdapter`) | Transporte + structured-output atrás de `ModelInvocationPort`. Default `DELIA_MODEL_RUNTIME=pydantic_ai`. Agent **sem tools**, uma `run_sync` por chamada lógica. | Complementar ao Application. `pydantic_arggen` é caminho **eval** (`DELIA_ARGGEN_ENGINE=pydantic_ai`); default arggen = `llm` via `_propose`. |
| **Application** (`OperationalCapabilityOrchestrator`) | Owner de admission, goal, decompose, select, args, discover/bind, invoke, evidence, composition, grounding judgments tipados + retries de estágio. | Autoridade semântica e de gates. |

**Duplicações PROVEN (implementação alternativa, não double-run):** dois sequenciadores (`_attempt` vs StateGraph) selecionáveis por env.  
**Duplicações NÃO PROVEN no mesmo request (config default):** dois planners LLM; dois admissions; LangGraph tool-agent loop.  
**Complementaridade PROVEN:** LG ordena → Application decide/gates → Pydantic AI materializa proposta tipada → Application valida/autoriza/executa/evidence.

---

## 2. Escopo integral — pesquisa de uso e consumers

### Pins (requirements)

| Pacote | Pin | Arquivo | Status |
|---|---|---|---|
| langgraph | `==1.2.16` | `delia-api/requirements.txt` L13 | PROVEN instalado prod image path |
| langgraph-checkpoint | `==4.3.1` | requirements.txt L14 | PROVEN pin; SqliteSaver via `langgraph-checkpoint-sqlite==3.1.3` em `requirements-eval.txt` L22 + import composition |
| langgraph-prebuilt / sdk | `1.1.1` / `0.4.10` | requirements.txt L15–16 | PROVEN pin; **sem consumer de agents/Cloud** no app (busca residual) |
| langchain-core / protocol | `1.7.1` / `0.0.20` | requirements.txt L17–18 | PROVEN transitive pin |
| pydantic-ai[openai] | `==2.50.0` | requirements.txt L22 | PROVEN default runtime |
| pydantic-ai-slim | `==2.50.0` | requirements-eval.txt L15 | PROVEN eval |

### Busca residual

| Símbolo / pergunta | Resultado | Classificação |
|---|---|---|
| `langgraph` / `StateGraph` em `*.py` fora `delia-api/` | **zero** | NOT_USED fora delia-api |
| Consumers LG em app | só `root_composer.py`, `langgraph_engine.py`, settings + testes/scripts | PROVEN |
| `pydantic_ai` em Application/Domain | **proibido** — só infra (+ testes); enforced `test_pydanticai_structured_output_eval.py` | PROVEN |
| `Agent(` + tools/ModelRetry em delia-api/app | **ausente** no adapter produtivo; Agent só structured output | PROVEN |
| Watch/Work/AutomationHub orchestration | **não** há app layer Watch/Work acionando engines | NOT_USED (F10) |
| plugins/delia / minha-delpi-copilot | sem imports LG/PA/OCO | NOT_USED |
| Feature flags | `DELIA_ORCHESTRATION_ENGINE`, `DELIA_MODEL_RUNTIME`, `DELIA_SUBOBJECTIVE_INVESTIGATION`, `DELIA_SUBOBJECTIVE_FANOUT`, `DELIA_CHECKPOINT_DB`, `DELIA_ARGGEN_ENGINE` | PROVEN settings |

---

## 3. Inventário de fluxos concretos

| FLOW_ID | Entrada real / gatilho | Seleção runtime/flag | Sequencer efetivo | LangGraph etapas | Pydantic AI etapas | Orquestrador Application etapas | Estado/checkpoint | Consumers | Outcome | Evidência | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F01 | `POST /interaction/turns` JSON | `DELIA_ORCHESTRATION_ENGINE` default `langgraph`; `DELIA_MODEL_RUNTIME` default `pydantic_ai` | LG se selected else OCO | preflight→admission→(surface\|conversational\|evidence_session→plan→owner_path) | cada `_propose` / fallback `InvokeModel` | gates: admit, goal, select, args, invoke, evidence, synth | in-memory turn; SqliteSaver só se `DELIA_CHECKPOINT_DB` | HandleInteractiveConversationTurn, MFE DÉLIA | InteractiveTurnResult | `interaction_routes.py` L120+; `handle_interactive_turn.py` L473; `root_composer.py` L68–110, L636–663 | PROVEN |
| F02 | mesmo route + `Accept: application/x-ndjson` | idem | idem | idem (activity sink) | idem | idem + ActivityEvent.v1 | idem | `_stream_interaction_turn` | NDJSON activity + terminal | `interaction_routes.py` L207–415 | PROVEN |
| F03 | admission class conversational/explanation/hypothetical | admission LLM | LG `conversational` node **ou** OCO `_attempt` early return | admission→conversational→END | 1× interaction_admission (+retry contradição) | `_admit_conversational_turn`; depois free-form `InvokeModel` no handler se NOT_APPLICABLE | sem owner evidence | presentation compose | prose não-grounded / CRI mode | OCO L12503–12684; LG L349–366; handler ~L634+ | PROVEN |
| F04 | admission `surface_inquiry` | idem | LG `surface_inquiry` ou OCO branch | admission→surface_inquiry→END | admission propose | `_groups` + `_surface_inquiry_attempt` (determinístico) | listing live | client surface answer | metadata listing, sem invoke | OCO L5333–5343; LG L335–347 | PROVEN |
| F05 | operational single-owner READ | idem | LG owner_path | …→evidence_session→plan(no-op se fanout off)→owner_path | N× stage proposes | `_governed_owner_path` select→args→invoke→assess | attempt ledger / resume checkpoint OCO | Domain/MCP owners | GROUNDED / insuff / denied | OCO L5369+; LG L383–424 | PROVEN |
| F06 | compare / multi-evidence | `comparison_requested` força decompose mesmo com investigation flag off | LG seq + **Application** `_decomposed_investigation` | plan vazio (fanout default off) → owner_path | subobjectives + per-sub stages | `_acquisition_subobjectives` + tracker + composition | SubObjectiveTracker in-memory | VerifiedCompositeEvidence | compare / NON_GROUNDED | OCO L5540–5557, L7091+; doc 229 E03/E04 | PROVEN |
| F07 | candidate-bound capability | live catalog | dentro owner_path | n/a extra | args / candidate_args / select_candidate | discover→token→execute; `_capability_dead_end` | candidate token ephemeral | MCP adapters | authoritative result ou dead-end | orchestration discover path; doc 229 RC-C | PROVEN (path); RC-C OPEN |
| F08 | prior_turns continuity | depth==0 + goal.prior_evidence_sufficient / probe | owner_path early | n/a | turn_goal + continuation/synthesis | `_prior_continuation_attempt` | prior OBSERVATION untrusted | handler prior context | transform / fallthrough | OCO L5417–5557 | PROVEN |
| F09 | timeout/cancel/resume | `max_governed_attempts`, LLM call attempts | `_run_governed_attempts` **compartilhado** por A e B | graph re-invoke se thread_id+checkpointer | adapter timeout map | stage deadline + call retry | `_AttemptCheckpoint` (OCO) e/ou SqliteSaver (LG opt-in) | observability ledger | PROCESSING_TIMEOUT / resume | OCO L5134–5277; LG attempt L807–863 | PROVEN |
| F10 | Watch/Work/scheduled | — | — | — | — | — | — | — | — | busca residual sem entrypoint | NOT_USED |
| F11 | Engine A rollback `DELIA_ORCHESTRATION_ENGINE=delia` | env | OCO `_attempt` direto | **não** entra no graph | idem PA | `_attempt` sequencia localmente | sem LG checkpoint | composition `_resolve_orchestration_attempt` returns gates | parity gates | `root_composer.py` L111; settings L276–278 | PROVEN |
| F12 | LG fan-out `DELIA_SUBOBJECTIVE_FANOUT=1` | flag | LG Send waves | plan→branch*→synthesis | decompose no plan node | cada branch `_governed_owner_path(..., depth=1)` | reducer `sub_results`; opcional SqliteSaver | tests S4/S5 | composite attempt | LG L504–727; default **OFF** | PROVEN opt-in |
| F13 | Arggen eval `DELIA_ARGGEN_ENGINE=pydantic_ai` | flag | n/a | n/a | `pydantic_arggen.propose_arguments` Agent | `_validate_instance` ainda Application | — | eval/scripts | args tipados | `pydantic_arggen.py`; settings L311–313; compose default `llm` | PROVEN eval-only default-off |
| F14 | Dictation NDJSON | separado | **não** usa OCO/LG | — | audio provider | dictation service | session dictation | dictation_routes | transcript | fora escopo intelligence orchestration | NOT_USED p/ esta decisão |

### Call chains concretos (fluxos ativos)

#### F01/F02 — Interaction turn (produção típica: engine=langgraph)

```text
HTTP interaction_routes.register → HandleInteractiveConversationTurn.execute
  → capability_orchestration.attempt(...)          # LangGraphCapabilityOrchestrator
       → gates._run_governed_attempts(attempt_once) # SHARED runner (budgets/resume)
            → compiled_graph.invoke(state)
                 preflight → admission
                    gates._admit_conversational_turn  # 1 LLM via _propose → InvokeModel → PydanticAi
                 [conversational|surface_inquiry|evidence_session]
                 evidence_session → subobjective_plan (no-op se fanout off)
                 → owner_path → gates._governed_owner_path
                      turn_goal? / decompose(compare)? / select_* / arguments /
                      MCP discover|execute / assessment / composition
  → se NOT_APPLICABLE+admission conversational: InvokeModel free-form (PA)
  → compose_presentation / CRI boundary
```

**Prova “não chama OCO.attempt”:** `test_governed_attempt_contract.py` spy em `_attempt` (~L576–587); módulo LG L24–26.

**Logs admission:** uma chamada LLM de admission por turn (retry só em contradição surface_inquiry). Log `decision=conversational` no path LG vem do **nó** LG L352–357; path Engine A loga em `_attempt` L5345–5350. **Não** são duas admissions — são duas implementações de sequencer + log no boundary. Classificação: COMPLEMENTARY_PROVEN (camadas), não DUPLICATE admission.

#### F06 — Compare (fanout OFF, produção)

```text
LG: admission(None/owner) → evidence_session → plan{} → owner_path
Application._governed_owner_path:
  goal (se prior) / se comparison_requested → _decomposed_investigation
    → _decompose_objective (_propose subobjectives)
    → _investigate_subobjectives (depth+1 per sub; re-select per sub)
    → composition / VerifiedCompositeEvidence
```

#### F12 — Fan-out ON (opt-in)

```text
LG plan: gates._decompose_objective
Send → branch: gates._governed_owner_path(sub.goal, depth=1)  # sem re-decompose
→ synthesis node (coverage S6)
```

Risco se **fanout ON + comparison path** no mesmo turn sem depth: mitigado porque branches usam `depth=1`. Se fanout OFF, só Application decompõe.

---

## 4. Matriz de responsabilidades / sobreposições

| Responsabilidade | LangGraph | Pydantic AI | Application | Owner canônico | Mesmo input >1×? | Dependência legítima? | Evidência | Decisão |
|---|---|---|---|---|---|---|---|---|
| Admission | Nó chama gate; routing condicional | Transport da proposta tipada | `_admit_conversational_turn` + schema | Application | Retry só contradição | Sim (PA=transport) | OCO L12503; LG L305–321 | KEEP split |
| Intent + typed goal | Não | Transport | `_understand_goal` / `_TurnGoal` | Application | **Sim** per-sub (doc 229 GOAL×N) | PA transport | OCO goal stages; doc 229 | CONSOLIDATE semantics (App) |
| Decomposition / planning | Opt-in plan node / Send | Transport | `_decompose_objective` + tracker | Application (+ LG schedule opt-in) | Fan-out vs sequential = **duas schedulers** | LG schedule only | LG L504–527; OCO L5540+ | CONSOLIDATE schedule ownership |
| Subgoal classification | Não | Transport | per-sub turn_goal / analytical filter | Application | Sim | — | doc 228/229 | CONSOLIDATE |
| Owner/group selection | Não | Transport | select_group/_select_target | Application | Per-sub | — | instructions + OCO | KEEP App; fix RC-B later |
| Capability selection | Não | Transport | select_capability + retries | Application | Per-sub + repair | — | OCO | KEEP App |
| Tool schema / arguments | Não | Default via `_propose`; opt `pydantic_arggen` | validate + build | Application | ARGS↔CAND_ARGS | PA structured útil | adapter + arggen | KEEP PA transport; arggen CONSOLIDATE/eval |
| MCP discover / bind | Não | Não | discover/candidate/execute | Application + Domain adapters | Retries possíveis | Adapter deve own protocol | RC-C OPEN | KEEP App/adapters |
| Execution orchestration | **Sequencing** | Não | gates invoke | Application authority; LG order | Um sequencer/process | Sim | LG+OCO | KEEP both roles |
| Retry / deadlines | Usa `_run_governed_attempts` | timeout map | stage + LLM call retries | Application | Camadas distintas | Sim | OCO L5134; adapter `_map_error` | KEEP; não somar cegamente |
| State / checkpoint / resume | SqliteSaver opt-in S5 | Stateless per call | `_AttemptCheckpoint` in-memory | App primary; LG durable opt-in | Dois mecanismos | Checkpoint LG exclusivo p/ fan-out resume | LG L199–203; OCO checkpoint | KEEP App; LG checkpoint REMOVE_CANDIDATE se unused prod |
| Policy / AuthZ / writes | Nunca | Nunca | Core live + write gates | Core/Domain | — | — | platform security | KEEP |
| Evidence / grounding | Synthesis coverage report only (S6) | Nunca FACT | VerifiedCompositeEvidence | DÉLIA Evidence + Domain | — | — | domain evidence | KEEP |
| Synthesis / projection | Concat limitations em fan-out synth | Free-form fallback transport | grounded_synthesis / CRI / presentation | Application + presentation | CMP↔EVID_COMP | — | doc 229 | CONSOLIDATE prompts |
| Streaming / NDJSON | Não | Não | activity sink + HTTP | Interaction HTTP | — | — | routes L207+ | KEEP |
| Observability | `last_node_trace` | duration/usage payload | ModelCallLedger / logs | Application | — | — | turn_observability | KEEP |

**Conceito verificado:** LangGraph **apenas** sequencia; Pydantic AI **apenas** chama/valida LLM structured — **COMPLEMENTARY_PROVEN** no default. Dois wrappers no stack ≠ dois planners.

---

## 5. Inventário de uso real por framework

### 5A. LangGraph

- **Package/version:** langgraph==1.2.16 (+ checkpoint 4.3.1; sqlite saver 3.1.3 eval/opt-in).
- **Files with imports (completo app+tests+scripts):**  
  `app/infrastructure/orchestration/langgraph_engine.py`, `app/composition/root_composer.py`, `app/infrastructure/config/settings.py`,  
  testes: `test_governed_attempt_contract.py`, `test_engine_production_selection.py`, `test_engine_b_architecture_isolation.py`, `test_engine_b_recovery_reuse.py`, `test_engine_b_recovery_hardening.py`, `test_subobjective_fanout.py`, `test_subobjective_resume.py`, `test_integrated_investigation.py`, `test_native_assessment_status_contract.py`, `test_recovery_opportunity_observability.py`,  
  scripts: `engine_ab_eval.py`, `engine_ab_real_model_eval.py`, `_s4_fanout_benchmark.py`, `_s5_resume_probe.py`.
- **Builders/factories:** `_resolve_orchestration_attempt` (`root_composer.py` L68–111); settings default `langgraph` L276–278; compose `${DELIA_ORCHESTRATION_ENGINE:-langgraph}`.
- **Nós:** preflight, admission, confirmation, surface_inquiry, conversational, evidence_session, subobjective_plan, subobjective_branch, subobjective_synthesis, owner_path (`langgraph_engine.py` L211–224).
- **Arestas:** START→preflight; condicional confirmation|admission; admission→surface|conversational|evidence_session; evidence→plan; plan/synthesis→Send|owner_path|END (`L226–255`, `L456–502`).
- **Consumer concreto:** `HandleInteractiveConversationTurn._capability_orchestration.attempt` quando engine=langgraph.
- **StateGraph chamado?** **SIM** — `graph.compile(...).invoke` em `attempt` L844–849. PROVEN.
- **Checkpointer persistente?** Somente se `DELIA_CHECKPOINT_DB` set — SqliteSaver (`root_composer.py` L91–104). Default **None** (settings L292–294). Durabilidade real: **opt-in**, não default prod compose. PROVEN config; live path com DB **INCONCLUSIVE** sem env prod inspect nesta task.
- **Store/memory LG?** Não usado além do checkpointer opcional. NOT_USED.
- **Interrupt/HITL?** Confirmation é nó separado alimentado por request.confirmation — não LG interrupt API. PARTIALLY_PROVEN (confirmation path Application).
- **Retry/durability/fan-out?** Retry = `_run_governed_attempts`; fan-out = flag default off.
- **Admission duplicada?** Uma gate call; logs podem diferir por engine. COMPLEMENTARY.
- **Exclusividades vs Application:** typed graph edges; Send fan-out paralelo; SqliteSaver resume por `thread_id`. Application não oferece Send nativo.
- **Retirada quebraria:** com default `langgraph`, remover LG sem apontar `delia` quebra composition; com engine=`delia`, LG é morto no processo.
- **Docstring stale:** L3–7 “never wired production” = **EXECUTION_DRIFT** documental.

### 5B. Pydantic AI

- **Package:** pydantic-ai[openai]==2.50.0.
- **Files:** `pydantic_ai_adapter.py`, `arggen/pydantic_arggen.py`, `root_composer.py`, `settings.py`, testes listados na busca, scripts eval.
- **Instanciação:** por invoke no adapter (`Agent` L190–217); composer seleciona adapter L652–663.
- **Agentes usados:** Adapter produtivo = Agent structured **sem tools**. Arggen Agent só se flag.
- **run_sync:** adapter L213; arggen L117.
- **Tool calls nativas?** **NÃO** no path produtivo. PROVEN.
- **Validators/retries:** schema dinâmico `_proposal_model`; retries de call = Application `governed_retries` / `_model_stage_proposal`, não ModelRetry PA.
- **Provider boundary:** OpenAIProvider base_url/api_key; secrets em settings; egress guard.
- **Estado entre etapas:** nenhum no adapter (history só `prior_context` do request).
- **Wrapper fino vs agent loop:** **wrapper fino** ModelInvocationPort. PROVEN docstring L1–13.
- **Tracing PA:** duration_ms + usage se provider expõe; ledger Application. PARTIALLY_PROVEN.
- **Features exclusivas dependentes:** structured output typing; legacy adapter permanece rollback `DELIA_MODEL_RUNTIME=legacy`.

### 5C. Orquestrador Application

- **Entrypoints:** `OperationalCapabilityOrchestrator.attempt` (engine=delia) **ou** métodos de gate via LG; HTTP via HandleInteractiveConversationTurn.
- **Decompose/select/args/candidate/read/composition:** todos em `orchestration.py` (~15k LOC owner).
- **Quem decide fluxo:** Application gates + (se LG) edges determinísticas; modelo só propõe structured fields.
- **Estado/retries/timeouts:** TurnDeadline, `_AttemptCheckpoint`, `DELIA_LLM_CALL_MAX_ATTEMPTS`, stage timeout 60s, interaction total budget.
- **Sobreposições:** sequencer dual A/B; decompose Application vs LG fan-out schedule; NÃO overlap com PA planning.
- **Complexity vs security:** admission/select retries = accidental complexity candidates; AuthZ/evidence fail-closed = security-critical KEEP.
- **Ports:** `SupportsGovernedCapabilityAttempt`, `SupportsGovernedStageGates`, `ModelInvocationPort`, MCP providers.

---

## 6. Call sites de LLM e medição

**Recontagem HEAD:** `orchestration_instructions.delpi.json` = **20** purposes; `self._propose(` = **25** call sites estáticos; `instruction_id=` sites = **26** (inclui retries); fallback interaction `delia.interaction.turn` fora desse resource (doc 229).

| ID | Path:função:região | Flow | Framework executor | Instruction/model | Trigger | Output schema | Retry owner | Invocações obs. | Duplica info anterior? | Tokens/latência | Evidência |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L001 | orchestration `_admit_conversational_turn` ~12544 | F01–F04 | PA via `_propose` | interaction_admission | todo turn sem confirmation | requires_owner_surface, interaction_class | App (+1 contradição) | 1–2 | ADM↔GRP (intent) | NOT_MEASURED | L12503+ |
| L002 | `_understand_goal` / GOAL | F05–F08 | PA | turn_goal | prior_turns ou fused select | _TurnGoal fields | App | 0–N | GOAL×N per sub | NOT_MEASURED | doc 229 |
| L003 | `_decompose_objective` | F06/F12 | PA | subobjectives | compare ou flag investigation / LG plan | subobjectives[] | App (+1 compare) | 0–2 | plan vs sticky goal | NOT_MEASURED | L6973+ |
| L004 | select_group | F05–F07 | PA | select_group | owner path / recovery | group id | App | per-sub | overlaps ADM | NOT_MEASURED | instructions |
| L005 | select_capability (±with_goal) | F05–F07 | PA | select_capability#… | após group | remote_name | App + repair | per-sub+ | — | NOT_MEASURED | 6 static CAP sites |
| L006 | arguments | F05–F07 | PA (ou arggen PA) | arguments | após cap | arguments object | App | per invoke | ARGS↔CAND | NOT_MEASURED | |
| L007 | candidate_arguments / select_candidate | F07 | PA | candidate_* | discovery bind | token/args | App | 0–N | overlaps L006 | NOT_MEASURED | |
| L008 | index_probe / index_select | niche | PA | index_* | index surfaces | ids | App | 0–N | — | NOT_MEASURED | |
| L009 | native_assessment | recovery | PA | native_assessment | pós seleção | status enum | App + LG reuse ledger | 0–N | reuse B1 | NOT_MEASURED | LG evidence_session |
| L010 | foreign_selection | recovery | PA | foreign_selection | foreign needed | foreign_capability_id | App | 0–1 | — | NOT_MEASURED | |
| L011 | goal_evidence_relevance | recovery | PA | goal_evidence_relevance | mismatch | relevance | App | ≤1 round | reopens select | NOT_MEASURED | doc 142 |
| L012 | comparison / evidence_composition | F06 | PA | comparison / evidence_composition | fan-in | structured compare | App | 0–2 | CMP↔EVID_COMP | NOT_MEASURED | doc 229 |
| L013 | grounded_synthesis / continuation / clarification | F03/F05/F08 | PA | synthesis/continuation/clarification | answer path | prose/fields | App | 0–2 | SYN_PRIOR↔OUT | NOT_MEASURED | |
| L014 | select_resolver | enrichment | PA | select_resolver | resolver need | id | App | 0–1 | — | NOT_MEASURED | |
| L015 | HandleInteractive free-form | F03 | PA InvokeModel | delia.interaction.turn | NOT_APPLICABLE conversational | free text | handler call retry | 1 | após admission | NOT_MEASURED | handler |
| L016 | pydantic_arggen | F13 | PA Agent direto | schema-derived | flag arggen | args model | adapter | eval | bypass L006 transport | NOT_MEASURED | eval |

**Por fluxo (ordem de grandeza — doc 229 live, não re-medido aqui):**

| Fluxo | LLM até 1ª READ | até evidência verificada | até terminal | Fonte |
|---|---|---|---|---|
| E01 SIPOC (F03) | admission (+ fallback) | n/a | ~90s client timeout obs. | doc 229 STALE_EVIDENCE p/ esta task |
| E02 READ | admit+goal?+group+cap+args (≥4) | pós owner | NOT_MEASURED aqui | code path PROVEN |
| E03/E04 compare | dezenas (per-sub) | frequentemente 0 material | 175–300s | doc 229 PARTIALLY_PROVEN |

Tokens reais nesta task: **NOT_MEASURED** (sem probe novo autorizado além de inventário).

---

## 7. Estado, side effects, ownership e fluxo de falhas

| Mecanismo | Estado | Owner | Durabilidade | Notas |
|---|---|---|---|---|
| TurnDeadline / interaction budget | in-memory monotonic | Application | request | compartilhado A/B |
| `_AttemptCheckpoint` | in-memory resume | Application `_run_governed_attempts` | request | CP4 |
| LG `_GovernedTurnState` | TypedDict por invoke | LangGraph | ephemeral unless SqliteSaver | serde `deadline_data` |
| SqliteSaver | sqlite file | Infra opt-in | process/restart | `DELIA_CHECKPOINT_DB` |
| SubObjectiveTracker | in-memory investigation | Application | turn | |
| `_NATIVE_ASSESSMENT_LEDGER` | ContextVar | Application; LG bind no owner_path | attempt | B1 reuse |
| Candidate tokens | ephemeral | Application/adapters | turn | ≠ authorization |
| AuthN/AuthZ | Keycloak + Core live | Platform | — | frameworks never authority |
| Evidence | Domain outcomes → VerifiedComposite | DÉLIA Evidence | turn/session projection | model ≠ FACT |

**Retries por camada:** (1) provider/transport timeout map PA; (2) `DELIA_LLM_CALL_MAX_ATTEMPTS` por logical call; (3) stage proposal repair; (4) `_run_governed_attempts` turn resume; (5) selection/arg re-propose. Cumulativo pode multiplicar latência — **PROVEN estrutura**, contagem live NOT_MEASURED.

### Traces anotados

| Trace | Status | Evidência |
|---|---|---|
| A) “O que é SIPOC?” | **STALE_EVIDENCE** (doc 229 E01): admission→conversational; client TimeoutError ~90s; FAST path não curto | doc 229 §eval; **TEST_NOT_RUN** replay nesta task |
| B) READ 90260147 | **TEST_NOT_RUN** aqui; path F05 PROVEN no código | call graph §3 |
| C) Compare 90260147×90260148 | **STALE_EVIDENCE** doc 229/228: decompose→per-sub select; material_satisfied=0 residual RC-B/C | ledger E4-R6 |
| D) candidate-bound | **TEST_NOT_RUN** live; path F07 PROVEN + RC-C OPEN | doc 229 |

HASH código inventário: `3496551f30`. Model/config prod: ledger histórico `DELIA_ORCHESTRATION_ENGINE=langgraph`, Kimi/OpenRouter — **não re-verificado** em container nesta task (INCONCLUSIVE live image).

---

## 8. Prova de duplicação e critérios de descarte

### D1 — Sequenciamento Engine A `_attempt` vs LangGraph graph

1. Paths: `orchestration.py` `_attempt` L5279 vs `langgraph_engine.py` `_build_graph` L211.  
2. Mesmo request? **Não** — `DELIA_ORCHESTRATION_ENGINE` escolhe **um**.  
3. Overlap: mesma ordem lógica admission→owner_path; mesmos gates.  
4. Autoridade: gates Application; sequencer pluggable (docs 192–195 + Task 07).  
5. Consolidar: manter um sequencer default + rollback.  
6. Teste equivalência: conformance suite já A/B (`test_governed_attempt_contract`, engine_ab_eval).  
7. **DUPLICATE_PROVEN (implementação alternativa) / COMPLEMENTARY_PROVEN (runtime exclusão mútua).**

### D2 — Admission “dupla”

1. Suspeita: dois logs interaction_admission.  
2. Mesmo request: uma chamada `_admit_conversational_turn`; segundo log é nó LG ou branch `_attempt`, não segunda proposta.  
3. **COMPLEMENTARY_PROVEN** (observability layers). Não REMOVE admission.

### D3 — Decompose Application vs LG fan-out

1. Application `_decomposed_investigation` (compare/flag) vs LG `_subobjective_plan_node`+Send.  
2. Default prod: fanout OFF → só Application. Ambos ON: plan LG + depth=1 branches evita double decompose.  
3. **PARTIAL** — duas schedulers de subobjetivos; risco de confusão operacional.  
4. Autoridade de proposta: Application `_decompose_objective`; LG só agenda.  
5. **CONSOLIDATE** schedule ownership (escolher um scheduler).  
7. **PARTIAL / CONSOLIDATE_CANDIDATE.**

### D4 — Pydantic AI vs Application “planner”

1. PA Agent vs OCO stages.  
2. PA não planeja — só `run_sync` structured.  
3. **COMPLEMENTARY_PROVEN.** Remover PA exigiria legacy adapter; não remove calls LLM.

### D5 — pydantic_arggen vs `_propose` arguments

1. Dois caminhos de arggen.  
2. Flag mutual (`DELIA_ARGGEN_ENGINE`). Default `llm`.  
3. **DUPLICATE_PROVEN (alt engines) / COMPLEMENTARY at runtime.** Arggen PA = REMOVE_CANDIDATE se eval não justificar.

### Remoção

Não aprovar remoção de LangGraph só por “Application também sequencia”: default prod **é** LG; rollback `delia` é o equivalente. Não remover Pydantic AI: default model runtime. Não remover gates Application.

---

## 9. Matriz final de decisão

| Mecanismo / fluxo | Necessidade legítima? | Equivalente existente? | Consumers reais | Dependência exclusiva? | Risco de retirada | Decisão proposta | Evidência | Teste de equivalência |
|---|---|---|---|---|---|---|---|---|
| LangGraph runtime engine | Sim — sequencer prod default + fan-out/checkpoint opt-in | Engine A `_attempt` | HandleInteractiveTurn via composer | Fan-out Send + SqliteSaver resume | Alto se remover sem set `delia` | **KEEP** (role sequencing); docstring fix doc-only later | settings+compose+LG module | A/B conformance already |
| Pydantic AI model adapter | Sim — default ModelInvocationPort | legacy OpenAI adapter | InvokeModel all stages | Structured Agent typing | Alto (quebra default runtime) | **KEEP** | adapter+composer M6 | test_pydantic_ai_adapter |
| Application orchestrator | Sim — semantic+gates owner | nenhum | todos F01–F09 | AuthZ/Evidence/select | Crítico | **KEEP** | orchestration.py | suites E4/RC |
| Admission (todos) | Sim | — | F01–F04 | — | Médio se “otimizar” mal | **KEEP**; consolidar overlap ADM↔GRP via Option B (doc 229) sem novo framework | L12503 | conversational baseline tests |
| Retry/deadline | Sim (governed) | — | all | safety | Alto se colapsar errado | **KEEP**; inventariar budgets (doc 229 R5) | `_run_governed_attempts` | ceiling tests |
| State/checkpoint/continuity | Continuity App sim; SqliteSaver **não** demonstrada default | `_AttemptCheckpoint` | opt-in LG | durable fan-out resume | Baixo remover se unused | App **KEEP**; LG checkpoint **REMOVE_CANDIDATE** se prod nunca seta DB | settings L292–294 | S5 tests if retained |
| Decompose/classify/select | Sim | — | F05–F07 | — | Alto | **CONSOLIDATE** semantic once (doc 226/229 Option B) — **não** mover p/ LG/PA | doc 229 | R1–R5 roadmap |

### Recomendação final

- **LangGraph: KEEP** — motivo: engine de produção para **stage sequencing only**; exclusividades Send/checkpoint opt-in; **não** é segundo cérebro. Proof: `langgraph_engine.py` L17–41, L305–424; `root_composer.py` L68–110; compose default langgraph.  
- **Pydantic AI: KEEP** — motivo: adapter canônico ModelInvocationPort; sem tool-loop. Proof: `pydantic_ai_adapter.py` L1–13, L190–217; settings default `pydantic_ai`.  
- **Application orchestrator: KEEP** (+ **CONSOLIDATE** decisões semânticas internas per doc 229 Option B, fora desta task).  
- **Responsabilidades duplicadas PROVEN:** (1) dual sequencer implementation A/B; (2) dual subobjective schedulers (App sequential vs LG fan-out); (3) dual arggen engines flagados. **Double-run no mesmo request:** NÃO PROVEN no default.  
- **Funções exclusivas a preservar:** Application gates/Evidence/AuthZ; PA structured transport; LG optional parallel schedule/durable resume **se** produto ativar.  
- **Menor caminho de simplificação (sem arquitetura nova):**  
  1) Tratar LG estritamente como sequencer (corrigir docstring drift; documentar flags);  
  2) Consolidar semantic-once no Application (sticky `_TurnGoal` / obligations — doc 229 R1–R2) — **não** adicionar planner LG/PA;  
  3) Decidir explicitamente fan-out+checkpoint: ativar com testes S4/S5 **ou** marcar REMOVE_CANDIDATE do surface prod até haver consumer.  
- **ADR necessário?** **ARCHITECTURE_DECISION_REQUIRED=YES** — coordenação deve congelar: (a) LG permanece default sequencer? (b) fan-out/checkpoint on/off política; (c) arggen pydantic_ai eval retirement. Não altera decisões AuthZ/Evidence.  
- **Risco principal / fallback:** remover LG sem `DELIA_ORCHESTRATION_ENGINE=delia` derruba boot; colapsar PA para legacy ok via env; mexer gates sem Option B reabre FALSE_GROUNDED/RC-A.  
- **Ordem ≤3 passos (não implementar):**  
  1. ADR curto: roles KEEP acima + corrigir docstring drift (doc-only).  
  2. Option B semantic consolidation no Application (doc 229) com testes equivalência E02/E03/E06.  
  3. Política fan-out/checkpoint/arggen-eval: enable com gate S4/S5 **ou** retire da superfície operacional.

---

## 10. Qualidade / prevenção contra nova rodada

- Fluxos F01–F14 inventariados; F10 NOT_USED justificado.  
- Nenhum TO_INVENTORY residual material sem motivo: live image env tokens = INCONCLUSIVE/NOT_MEASURED; checkpoint prod usage = INCONCLUSIVE.  
- Chat Minha DELPI **fora** do ownership — apenas ausência residual confirmada.  
- RC-A/B/C/REF05: esta task **não** fecha funcionais; risco de consolidação malfeita = reabrir FALSE_GROUNDED — preservar evidence gates.  
- Staging: **apenas** este doc + linha ledger; untracked tv-dashboard preservado.

### Call-graph permalinks (SHA base `3496551f30`)

- https://github.com/roberiooliveiradev/delpi-central/blob/3496551f30a57af0d5d82d516bf5e8480375abf7/delia-api/app/infrastructure/orchestration/langgraph_engine.py#L162-L255  
- https://github.com/roberiooliveiradev/delpi-central/blob/3496551f30a57af0d5d82d516bf5e8480375abf7/delia-api/app/composition/root_composer.py#L68-L111  
- https://github.com/roberiooliveiradev/delpi-central/blob/3496551f30a57af0d5d82d516bf5e8480375abf7/delia-api/app/infrastructure/model_invocation/pydantic_ai_adapter.py#L84-L217  
- https://github.com/roberiooliveiradev/delpi-central/blob/3496551f30a57af0d5d82d516bf5e8480375abf7/delia-api/app/application/capability_provision/orchestration.py#L5279-L5367  
- https://github.com/roberiooliveiradev/delpi-central/blob/3496551f30a57af0d5d82d516bf5e8480375abf7/delia-api/app/application/interaction/handle_interactive_turn.py#L468-L485  
- https://github.com/roberiooliveiradev/delpi-central/blob/3496551f30a57af0d5d82d516bf5e8480375abf7/infra/docker-compose.yml#L2100-L2104  

### Contraprovas / negativos

- LG **não** importa OCO class — só Protocol gates (LG L27–30; isolation tests).  
- PA **não** executa MCP.  
- Engine B spy: `_attempt` não chamado sob LG.  
- Fan-out default OFF → produção atual ≈ Application intelligence + LG thin sequencing.

---

## 11. Gate de saída e relatório

| AC | Status |
|---|---|
| AC-01 reanchor | PASS |
| AC-02 mapa entradas/consumers | PASS |
| AC-03 F01–F10 + F11–F14 | PASS |
| AC-04 mapa real 3 camadas | PASS |
| AC-05 execução vs import | PASS (invoke/compile/run_sync provados) |
| AC-06 duplicações | PASS (D1–D5 classificados) |
| AC-07 LLM sites | PASS (matriz §6; tokens NOT_MEASURED) |
| AC-08 estado/checkpoint | PASS |
| AC-09 AuthZ/Evidence preservados | PASS (recomendação não relaxa) |
| AC-10 matrix KEEP/CONSOLIDATE/REMOVE_CANDIDATE | PASS |
| AC-11 traces | PASS com STALE/TEST_NOT_RUN explícitos |
| AC-12 sem implementação produtiva | PASS |
| AC-13 doc/ledger/commit | (após push) |
| AC-14 ≤3 bounded next | PASS §9 |
| AC-15 sem avanço de fase | PASS |

~~~text
DÉLIA FRAMEWORK FLOW INVENTORY REPORT
TASK_ID: DELIA-C3-FRAMEWORK-OVERLAP-RUNTIME-FLOW-INVENTORY-01
BASE_HEAD: 3496551f30a57af0d5d82d516bf5e8480375abf7
FINAL_HEAD: (set after commit)
ORIGIN_MAIN: (set after push)
PUSH_VERIFIED: (set after push)
AUTHORITY_REANCHOR: YES (.cursor + docs 16/50/17/49/51/52/21/20/25 + 192-196/220/226/228/229 + ledger)
CP_RQ: C3 E4-R6 residuals OPEN; phase not advanced
DOC_PATH: docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/230-langgraph-pydantic-ai-runtime-flow-inventory-and-consolidation-decision.md
FLOW_COUNT: 14 (F01–F14; F10 NOT_USED)
LANGGRAPH_ACTIVE_FLOWS: F01 F02 F03 F04 F05 F06 F07 F08 F09 F11(rollback off) F12(opt-in)
PYDANTIC_AI_ACTIVE_FLOWS: all model stages F01–F09 + F13(opt-in arggen) + F03 free-form
APPLICATION_ACTIVE_FLOWS: F01–F09 F11 (gates always)
LANGGRAPH_EXCLUSIVE_FUNCTIONS: StateGraph conditional sequencing; Send fan-out; optional SqliteSaver thread resume
PYDANTIC_AI_EXCLUSIVE_FUNCTIONS: Agent structured-output transport behind ModelInvocationPort; optional schema arggen Agent
DUPLICATIONS_PROVEN: dual sequencer impl (A/B exclusive); dual subobjective schedulers (PARTIAL); dual arggen engines (flag exclusive)
COMPLEMENTARITIES_PROVEN: LG sequences → App decides/gates/evidence → PA materializes structured proposals
SUSPECTED_BUT_UNPROVEN: production DELIA_CHECKPOINT_DB in use; live token totals this HEAD
LLM_ACTIVE_CALL_SITES: 25× self._propose + free-form interaction + optional arggen; 20 instruction purposes
RETRY_LAYER_COUNT: 5 (transport; per-call; stage repair; turn resume; selection re-propose)
CHECKPOINT_DURABILITY_EVIDENCE: SqliteSaver wired only if DELIA_CHECKPOINT_DB set; default None (PROVEN code; live INCONCLUSIVE)
RUNTIME_TRACES: A/C STALE_EVIDENCE doc229; B/D TEST_NOT_RUN this task
TOKEN_USAGE: NOT_MEASURED
STATE_OWNERS: Application (deadline/checkpoint/tracker/ledger); LG state ephemeral+opt saver; PA stateless
AUTHZ_AND_EVIDENCE_GATES: unchanged — frameworks never authority; Domain/Core/Evidence KEEP
EXISTING_EQUIVALENT: OperationalCapabilityOrchestrator + SupportsGovernedStageGates + ModelInvocationPort + SubObjectiveTracker + VerifiedCompositeEvidence
REUSE_DECISION: KEEP three layers with clarified roles; CONSOLIDATE semantics inside Application (doc229 Option B); no new framework
LANGGRAPH_RECOMMENDATION: KEEP (sequencer)
PYDANTIC_AI_RECOMMENDATION: KEEP (model port adapter)
APPLICATION_RECOMMENDATION: KEEP (+ CONSOLIDATE internal semantic once)
MINIMAL_CONSOLIDATION_PATH: (1) ADR roles+docstring drift (2) Option B sticky goal/obligations in App (3) fan-out/checkpoint/arggen-eval policy enable-or-retire
TEST_OF_EQUIVALENCE_REQUIRED: engine A/B conformance; E02/E03/E06 after Option B; S4/S5 if fan-out retained
ARCHITECTURE_DECISION_REQUIRED: YES (sequencer default + fan-out/checkpoint/arggen policy)
EXECUTION_DRIFT: langgraph_engine module docstring still says eval-only while default prod=langgraph; doc226 semantic-once DRIFT_PARTIAL
INCONCLUSIVE_ITEMS_WITH_REASON: live container env/tokens (no prod inspect); whether CHECKPOINT_DB set in srv-api
FILES_CHANGED: doc 230 + execution-ledger entry
PRODUCT_CODE_CHANGED: NO
PRODUCTION_DEPLOY: NOT_AUTHORIZED
NEXT_BOUND_STEP: Coordination ADR on KEEP roles; then authorize doc229 Option B implementation separately
~~~

**PARADA:** Inventário submetido à coordenação. Nenhuma implementação de consolidação nesta task.
