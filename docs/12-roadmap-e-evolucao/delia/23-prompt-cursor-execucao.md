# Prompt mestre — Cursor — DÉLIA Standalone

Implemente a **DÉLIA — DELPI · Ecossistema de Ligações, Inteligência e Automação como aplicação nova e independente**, do zero até o produto completo. Não evolua nem refatore o Minha DELPI Chat para atingir este objetivo.

A visão alvo é **Continuous Operational Intelligence** para escritório, reuniões, chão de fábrica, fontes externas e operações governadas. Não é Chat+RAG.

## 1. Decisão inegociável

```text
DÉLIA backend  = nova API própria; freeze candidato delia-api (C0.S1; PLANNED/FROZEN_CANDIDATE)
DÉLIA frontend = novo MFE próprio; freeze candidato plugins/delia (C0.S1; PLANNED/FROZEN_CANDIDATE)
Chat backend/MFE = sistemas separados/reference-only
```

Proibido importar/depender de runtime/API/tables/source do Chat ou criar runtimes paralelos por Teams, RPA, Scheduler, Process Mining, MCP/A2A, Twin, Edge, Marketplace ou outro tema sem C0/ADR provar boundary real.

## 2. North Star

A mesma DÉLIA deve suportar:

```text
GLOBAL      → painel contextual
WORKSPACE   → full-page work/analysis
MEETING     → meeting assistance
FRONTLINE   → operator/shopfloor assistance
TEAMS       → future surface of same runtime
BACKGROUND  → governed Watches/Workflows/Recurring Work reacting to events/time
```

E deve evoluir para:

```text
PERCEBER
→ ENTENDER
→ PESQUISAR
→ ANALISAR
→ PREVER/SIMULAR
→ DECIDIR
→ PREPARAR/EXECUTAR
→ VERIFICAR OUTCOME
→ COMUNICAR
→ APRENDER SOB GOVERNANÇA
```

## 3. Ordem obrigatória de leitura

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc` + regras aplicáveis
3. `docs/12-roadmap-e-evolucao/delia/README.md`
4. `16-execution-master-plan.md`
5. `50-standalone-copilot-application-architecture.md`
6. `17-component-and-contract-map.md`
7. `49-architecture-and-design-patterns-standard.md`
8. `51-platform-integration-baseline.md`
9. `52-standalone-repository-and-bootstrap-plan.md`
10. `21-data-and-state-model.md`
11. `20-testing-and-acceptance-matrix.md`
12. `25-requirements-traceability.md`
13. `53–66` specs temáticas aplicáveis
14. `22-cursor-execution-protocol.md`
15. `evidence/execution-ledger.md`

Precedência é definida por `48`. `16` é a única authority de ordem. `25` é a única authority `CP-*` (`CP-001…CP-332`).

## 4. Specs temáticas ativas

```text
53 multimodal / Meeting / Frontline / industrial
54 biometric identity / Human Observation
55 Internet Research / external connectors
56 Microsoft Teams
57 Event-Driven Autonomous Operations / Automation Hub integration / Recurring Governed Work
58 Process Intelligence / Process Mining / Task Mining
59 AI Control Tower / Digital Workforce Governance
60 MCP / A2A / tool-agent interoperability
61 Personal Memory / Personalization
62 Semantic Business Layer / governed metrics
63 Analysis Sandbox / Artifact Workspace
64 Predictive / Prescriptive Intelligence / Operational Twin
65 Edge / Offline Industrial
66 AI Model Lifecycle / Capability Marketplace
```

`67` é visão transversal de expansão de capabilities e `68` é authority de naming. `31/45/46/47` são superseded/reference-only e nunca redefinem arquitetura atual.

## 5. Ordem C0–C7

```text
C0 Foundation Freeze
→ C1 Standalone Bootstrap
→ C2 Portal/Context/Commands
→ C3 Intelligence + capability foundations
→ C4 Governed reads + analysis/discovery
→ C5 Governed ACT + executors + durable/recurring work
→ C6 Product work + governance/experience ecosystem
→ C7 Advanced autonomy + scale/optimization/rollout
```

C5 pode liberar L4/governed execute para capabilities explicitamente autorizadas, inclusive ocorrências bounded de Recurring Governed Work que revalidem live gates. C6 não libera Watch ACT autônomo por default. C7 adiciona L5/Watch autonomous ACT selecionado sob policy/limits/kill switch/verified Outcome.

Nunca pular fase porque um SDK/provider/tool/scheduler já existe no mercado.

## 6. Primeira ação: execute apenas C0.S0

Antes de runtime diff:

```text
git status
git rev-parse HEAD
```

C0.S0 é **inventário factual read-only + docs/ledger**, sem criar runtime da DÉLIA.

### 6.1 Platform baseline

Inventarie Portal/Core/Keycloak/Gateway/Compose/federation/plugin-ui, manifests, auth/RBAC, routes/context, APIs/OpenAPIs/errors/idempotency/events, workers/schedulers, storage/network/secrets, notifications/rooms/requests/workflows.

### 6.2 Media/Biometric/Meeting/Frontline

Inventarie speech/vision/media providers, capture/storage/retention, devices/kiosks/production terminals, biometric enrollment/templates/liveness, participant/presence and OT safety owners.

### 6.3 Internet/External/Teams

Inventarie egress/search/safe fetch, OAuth/vault, Microsoft Graph/Google/WhatsApp/Slack/GitHub, webhooks/subscriptions/reconciliation, attachment scanning, Entra/Teams scopes/artifacts/app/tab/bot/privacy.

### 6.4 Automation/Event/RPA/Scheduling

Inventarie:

```text
Automation Hub implementation/owner/runtime/contracts if any
RPA platforms/licenses/orchestrators/bots/packages
scripts/functions/jobs
queues/workers/heartbeats/leases
schedulers/timers/cron/polling/event buses/topics/webhooks
existing recurring job/work definitions + owners
timezone/DST/calendar semantics
misfire/missed-run/reconciliation semantics
overlap/concurrency semantics
service accounts/background identities
background AuthZ/revocation patterns
credential injection/storage
VDI/desktop/session infrastructure
existing rule/decision/process engines
business postcondition/outcome sources
notification/escalation channels
kill switches/emergency stop
support/SLA/ownership
```

Separar factual e explicitamente:

```text
DÉLIA RecurringWorkDefinition/lifecycle/correlation owner
!=
physical scheduler/timer/job runtime owner
```

Não assumir ferramenta RPA, scheduler ou implementação física do Automation Hub. A authority semântica permanece: DÉLIA decide/orquestra e possui o Work; Automation Hub executa tecnicamente; scheduler/timer apenas materializa trigger temporal conforme contrato e nunca concede permission.

### 6.5 Process Intelligence

Inventarie event logs/audit trails, case/business keys, activities/timestamps/statuses, BPMN/process docs, process owners/KPIs, data quality/completeness, task-mining/desktop telemetry and privacy policy.

### 6.6 AI Control Tower / Model Governance

Inventarie AI/model/automation assets, provider accounts, model registries/MLOps, eval suites/datasets, prompt/policy registries, cost/usage telemetry, incidents/change management, feature flags/kill switches, package catalogs/signing/supply-chain controls.

### 6.7 MCP/A2A

Inventarie MCP servers/clients, agent frameworks/protocols, tool registries, service/delegation identities, approved external agents, credentials/scopes, network/egress and protocol/security versions.

### 6.8 Personal Memory

Inventarie Core/profile/preferences/favorites/recent usage, notification preferences, existing personalization/memory stores, privacy/retention/export/delete owners and shared-device constraints.

### 6.9 Semantic Business Layer

Inventarie BI semantic models, KPI formulas in APIs/frontends/spreadsheets, business glossary, warehouse/lake/SQL/Power BI definitions, owners, grain/dimensions/freshness and conflicting meanings.

### 6.10 Analysis Sandbox / Artifacts

Inventarie Python/Jupyter/code execution, sandbox/container infra, query engines, file/object storage/scanning, document/spreadsheet/presentation generation, collaboration/versioning/export/share systems.

### 6.11 Predictive / Twin

Inventarie forecasting/anomaly/optimization models, datasets/ground truth/evals, simulation/twin tools, MES/IoT/historian, planning/capacity models, solvers and manual what-if models.

### 6.12 Edge / Offline

Inventarie factory network reliability, Edge platforms/gateways, devices/MDM, GPU/NPU/CPU, local storage/inference, procedure/drawing distribution, time sync, offline continuity and OT segmentation.

### 6.13 Chat reference-only

Inspect only for lessons/anti-patterns/neutral shared conventions. Never classify Chat runtime as reuse dependency.

### 6.14 Finding classification

Use a taxonomia factual canônica:

```text
PROVEN
TO_INVENTORY
PLANNED
TARGET
```

Para decisões de tratamento após inventário, registrar separadamente quando aplicável:

```text
PLATFORM_REUSE
NEUTRAL_SHARED_REUSE
IMPLEMENT_NEW
EXTEND_PLATFORM_CONTRACT
ADAPTER_REQUIRED
ADR_REQUIRED
OUT_OF_SCOPE
```

A segunda lista não substitui o estado factual. Market availability without repo/infra evidence = `TO_INVENTORY`, nunca `PROVEN`.

### 6.15 Evidence discovery

GitHub/code search é descoberta/residual. Nunca usar `0 results` como prova de ausência.

```text
search miss
!= feature ausente
!= documentação ausente
!= TO_INVENTORY automaticamente
```

Quando uma conclusão depender de ausência, abra diretamente owner/authority provável, `25` e spec temática. Separe capability/product target, requirement/contract, physical mechanism e runtime implementation.

## 7. Foundation Freeze before C1

At minimum:

```text
PLATFORM_INVENTORY=PASS
STANDALONE_BOUNDARY=PASS
AUTHORITIES=PASS
SHARED_PRIMITIVES=PASS
ARCHITECTURE_PATTERNS=PASS
PERSISTENCE_BOUNDARIES=PASS
MEDIA/BIOMETRIC/EXTERNAL BOUNDARIES=PASS
EVENT/AUTOMATION/OUTCOME/AUTONOMY BOUNDARIES=PASS
RECURRING_WORK_BOUNDARY=PASS
PROCESS_INTELLIGENCE_BOUNDARY=PASS
AI_ASSET_GOVERNANCE_BOUNDARY=PASS
MCP_A2A_TRUST_BOUNDARY=PASS
PERSONAL_MEMORY_BOUNDARY=PASS
SEMANTIC_LAYER_BOUNDARY=PASS
SANDBOX_ARTIFACT_BOUNDARY=PASS
PREDICTIVE_TWIN_BOUNDARY=PASS
EDGE_OFFLINE_BOUNDARY=PASS
MODEL_MARKETPLACE_BOUNDARY=PASS
OT_SAFETY_BOUNDARY=PASS
CONFORMANCE_HARNESS=PASS
CHAT_RUNTIME_DEPENDENCY=0
FOUNDATION_DUPLICATION=0 material
```

## 8. Architecture rules

```text
Clean Architecture
+ Ports & Adapters
+ pragmatic DDD
+ Event-Driven only with real event owner
+ State Machines for nontrivial lifecycle
+ Policy/Specification for deterministic decisions
+ light CQRS only when justified
```

Follow `49`. Concrete providers/executors/models/tools/schedulers live in Infrastructure. Composition Root wires them.

No speculative microservice/framework/registry/scheduler before Abstraction Gate.

## 9. Authorities

```text
Keycloak = identity/SSO
Core = platform apps/routes/RBAC/governance
Portal = host/navigation/published context
Domain APIs = business data/rules/actions
External providers = external resources/scopes
DÉLIA = intelligence/context/Evidence/Policy/Decision/Work/RecurringWork/orchestration/outcome coordination
Automation Hub = technical execution, not business/permission authority
Physical scheduler = technical time-trigger materialization, owner TO_INVENTORY until C0 proof
Control Tower = governance plane, not business authority
OT/safety systems = machine truth/safety
```

## 10. Fundamental semantic distinctions

Never collapse:

```text
Personal Memory != Organizational Knowledge
Conversation History != WorkspaceContext
Business Graph != Semantic Business Layer
Prediction != FACT
Recommendation != Authorization
Simulation/Twin State != Production State
SIMULATE != APPLY
PREPARE != ACT
Read != Write
Draft != Send
Schedule != Permission
Stored Schedule Intent != Eternal Authorization
Recurring Governed Work != Watch Autonomous ACT
Physical Scheduler != Work/Policy Authority
L4 governed execute != L5 autonomous execute
Technical Execution Success != Verified Business Outcome
MCP/A2A Discovery != Approval
Marketplace Install != Permission Grant
Device/Biometric/Worker/Scheduler Identity != User Authorization
```

## 11. Event / Decision Intelligence

```text
source event
→ authenticate/validate
→ EventEnvelope
→ dedupe/order/correlation
→ DecisionPathPolicy
   FAST | OPERATIONAL | REASONING
```

FAST uses deterministic rules. OPERATIONAL uses bounded reads/rules + optional small model. REASONING uses Graph/Knowledge/Expertise/LLM.

Not every event calls an LLM.

A timer occurrence only proves that configured time was reached under its trigger contract. It does not authorize ACT.

## 12. Automation / Executors

```text
DÉLIA = decide/orchestrate
Automation Hub = technical execute
```

Preference:

```text
official API
→ native integration
→ deterministic function/script
→ RPA
→ computer-use
→ human task
```

Planner sees semantic capability, never click/selector/coordinate/package UI mechanics.

RPA is replaceable adapter behind the approved execution boundary. Computer-use is advanced sandboxed fallback.

### 12.1 Recurring Governed Work

`CP-311–CP-316` make Recurring Governed Work a first-class target.

Target:

```text
user/owner creates bounded RecurringWorkDefinition
→ persistent independent of chat session
→ physical scheduler materializes deterministic occurrence
→ occurrence correlation + idempotency
→ current user/service identity
→ live Core/domain AuthZ + Policy/Decision
→ current authorized data
→ PREPARE or C5 L4 governed ACT
→ executor/provider
→ authoritative Outcome + Evidence + Audit
```

Required lifecycle target:

```text
CREATE
INSPECT/LIST
PAUSE
RESUME
CANCEL
```

Contract must make explicit IANA timezone, recurrence/calendar, start/end, DST when applicable, misfire/missed-run, overlap/concurrency, failure/retry, idempotency and revoke semantics.

C5 can execute bounded recurring L4 ACT after live gates. C6 can expose schedule/admin UX but Watch remains `OBSERVE|ADVISE|PREPARE` by default. C7 is not required for this bounded governed recurring ACT.

## 13. Outcome verification

```text
technical result
→ authoritative postcondition verification
→ VERIFIED_SUCCESS|VERIFIED_FAILURE|PENDING|INCONCLUSIVE
```

Never announce material success solely from HTTP 200, scheduler fire, RPA Save click or provider accepted response when final outcome is not confirmed.

## 14. Process Intelligence

Process Mining uses authorized event logs and preserves source/provenance/completeness.

Prohibited by default:

```text
secret employee productivity score
fraud/intent/personality inference from deviation
unrestricted desktop task capture
automatic RPA deployment from opportunity
```

Opportunity → candidate/PREPARE → owner validation.

## 15. AI Control Tower

Govern assets, owners, risk, scopes, versions, evals, health, cost, verified value, incidents, dependencies, rollout and kill switches.

Control Tower admin does not grant domain/business permission.

## 16. MCP / A2A

Servers/tools/agents require lifecycle approval and capability allowlists. Metadata/results are untrusted. Delegate minimum context, no CoT dump, scoped credentials, timeout/cancel/budget.

Writes use same Policy/Decision/idempotency/Outcome semantics.

## 17. Personal Memory

User-owned/private by default. User can inspect/correct/delete/disable. Memory affects relevance/presentation, never permissions or live business truth. No hidden sensitive/personality/employee profiling.

## 18. Semantic Business Layer

Material metric has `owner + formula + grain + dimensions + unit + source + freshness + version + security classification`.

LLM interprets question; structured definition/calculation produces metric. Same-name conflicts stay explicit.

## 19. Analysis Sandbox / Artifact Workspace

Sandbox:

- isolated/quota-bounded;
- no unrestricted host/private network;
- authorized read data only by default;
- safe file ingest;
- no broad credentials;
- reproducibility metadata;
- truthful failure.

Artifacts are versioned/provenanced/ACL-controlled. Human edits are not silently overwritten. External share/send remains separate action.

## 20. Predictive / Prescriptive / Twin

Prediction preserves model/version/horizon/confidence/freshness/limitations and is not FACT.

Prescription shows objectives/constraints/assumptions/trade-offs and yields recommendation/PREPARE, not authorization.

Operational Twin is a projection/scenario. Simulation never mutates production. Apply revalidates live state/permissions/policy.

## 21. Edge / Offline

Edge is governed extension of same product, not second unrestricted DÉLIA.

Explicit modes, revision/freshness, versioned packages/models, buffered events with idempotent sync, device/user separation, no authority widening offline, OT safety independent.

## 22. Model lifecycle / Marketplace

Every production model has owner/version/eval/risk/deployment/rollback/revoke traceability. Model Router selects only approved assets.

Marketplace assets declare requirements/dependencies/data scopes; publish/enable/install never grants RBAC/provider scope. Executable assets follow supply-chain review/integrity controls.

## 23. Security/privacy

Follow `08/20` exactly. Treat all external/tool/model/package/generated/scheduler metadata as untrusted for authorization. Secrets never reach LLM/MFE/logs. Biometric/Human Observation and employee privacy boundaries remain.

## 24. OT safety

```text
free-form LLM/model/vision/voice/RPA/computer-use
-X→ PLC/CNC/robot/machine actuation
```

Physical actuation requires separate industrial safety initiative/gate.

## 25. C1 rule

First runtime work after Foundation Freeze is standalone API/MFE bootstrap. No Process Mining engine, Control Tower, MCP/A2A runtime, sandbox, Twin, Edge, Marketplace, RPA runtime, Recurring Work ACT or autonomous ACT before foundations and phase dependencies.

## 26. Generic execution protocol

For exactly one `C*.S*`:

```text
REVALIDATE HEAD/WORKTREE
→ READ AUTHORITIES + APPLICABLE SPECS
→ IDENTIFY OWNER/SOURCE/BORDER
→ IDENTIFY CONSUMERS + CONTRACT
→ ABSTRACTION + DEPENDENCY GATES
→ BASELINE
→ MINIMAL CORRECT DIFF
→ WIRE PRODUCER/CONSUMER
→ UNIT/CONTRACT/INTEGRATION
→ POSITIVE/SIBLING/NEGATIVE
→ SECURITY/PRIVACY/RBAC/OUTCOME/SAFETY
→ GENERALIZATION/METAMORPHIC/UNKNOWN
→ CHAT-INDEPENDENCE
→ ARCHITECTURE CONFORMANCE
→ RESIDUAL SEARCH
→ COMPLETE_GATE
→ DOCS/LEDGER
→ NEXT
```

## 27. Required test families

Use `20` as sole test authority. Never weaken tests to pass candidate.

Always include relevant negatives for:

```text
permission elevation
source/data leak
prompt/tool/agent injection
unsafe egress
memory isolation
semantic metric reproducibility
sandbox escape/write
prediction-as-fact
simulation→production mutation
Edge authority expansion
revoked asset still active
Marketplace permission escalation
schedule/timer permission elevation
scheduled occurrence without live AuthZ
schedule duplicate/retry/restart duplicate ACT
paused/cancelled schedule executes
implicit timezone/undefined misfire/overlap
RPA duplicate/credential leak
unverified success
PREPARE→ACT bypass
ACT without live AuthZ/idempotency/audit
Watch autonomous ACT before C7
global L5
OT command
Chat dependency
```

## 28. Report format

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
CP_REQUIREMENTS:
FILES_CHANGED:
OWNERS/SOURCES:
CONSUMERS/CONTRACTS:
LAYER/PATTERNS:
PLATFORM_REUSE:
DELIA_NEW_CODE:
CHAT_DEPENDENCIES:
WIRING_PROOF:
TESTS:
SECURITY_RBAC_PRIVACY:
DATA_STATE_RETENTION:
PROCESS_INTELLIGENCE:
SEMANTIC_LAYER:
MEMORY_PERSONALIZATION:
SANDBOX_ARTIFACTS:
PREDICTIVE_TWIN:
AUTOMATION_EXECUTION_OUTCOME:
RECURRING_WORK_SCHEDULING:
MCP_A2A:
MODEL_CONTROL_TOWER_MARKETPLACE:
EDGE_OFFLINE:
INDUSTRIAL_SAFETY:
GENERALIZATION:
CHAT_INDEPENDENCE:
ARCHITECTURE_CONFORMANCE:
RESIDUAL_SEARCH:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 29. Start here

Execute only:

```text
C0.S0
```

Do not create runtime code before `C0.S7 FOUNDATION_FREEZE=PASS`. Documentation-only inventory/evidence updates are allowed in C0.S0.
