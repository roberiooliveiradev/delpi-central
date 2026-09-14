# DÉLIA — Protocolo de Execução para o Cursor

**Status:** obrigatório  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Requirements:** `CP-001…CP-316`  
**Specs temáticas:** `53–66`

## 1. Objetivo

Executar a DÉLIA como aplicação nova, foundation-first, sem Chat runtime dependency, sem architecture-by-feature e sem adiar boundaries de data/process/automation/model/privacy/Edge que depois exigiriam refactor.

## 2. Mandatory reading

Before each substep:

1. official project instructions;
2. applicable `.cursor/rules`;
3. DÉLIA `README.md` + `INDEX.md`;
4. `16` execution order;
5. `50` standalone boundary;
6. `17` ownership/contracts;
7. `49` architecture/patterns;
8. `51` factual baseline;
9. `52` physical/bootstrap target;
10. `21` state/persistence when applicable;
11. `20` tests/gates;
12. `25` applicable CP requirements;
13. applicable thematic specs `53–66`;
14. execution ledger.

Then:

```text
git status
git rev-parse HEAD
```

Record `HEAD_BEFORE`.

## 3. Standalone boundary

Treat as architectural error:

```text
DÉLIA API → Chat runtime/API/tables
DÉLIA MFE → Chat source imports
DÉLIA feature → Chat planner/tool/media/provider as mandatory implementation
DÉLIA progress → Chat refactor dependency
```

Chat is reference-only during inventory.

## 4. C0.S0 — runtime read-only inventory

Inventariar factual evidence for:

```text
Platform: Portal/Core/Keycloak/Gateway/Compose/plugin-ui/MFEs/APIs/OpenAPIs
Media/Biometric/Meeting/Frontline/Devices/OT
Internet/OAuth/External Connectors/Teams/Webhooks
Events/RPA/Automation Hub/Queues/Workers/Service Identities/Outcome Sources
Schedulers/Timers/Cron/Polling/Recurring Job Definitions/Timezone/Misfire/Overlap
Process Logs/Process Owners/Task Mining
AI Assets/Models/Evals/Cost/Incidents/Control mechanisms
MCP/A2A/Tools/Agents/Delegation identities
Personal Memory/Profile/Preferences/Privacy controls
Semantic KPIs/Glossary/BI models
Sandbox/Query/File/Artifact infrastructure
Predictive/Optimization/Simulation/Twin
Edge/Offline/Devices/MDM/Local inference
Model Registry/MLOps/Marketplace/Package Supply Chain
```

Para recurring work, separar obrigatoriamente:

```text
DÉLIA RecurringWorkDefinition/lifecycle/correlation owner
!=
physical scheduler/timer/job runtime owner
```

Inventariar também background identity/AuthZ/revoke, timezone/DST/calendar, missed-run/misfire/reconciliation, overlap/concurrency e idempotência por ocorrência. Não criar scheduler novo apenas porque nenhum foi encontrado na primeira busca.

Classify factual state only as:

```text
PROVEN
TO_INVENTORY
PLANNED
TARGET
```

Then, separately if useful, record treatment decision:

```text
PLATFORM_REUSE
NEUTRAL_SHARED_REUSE
IMPLEMENT_NEW
EXTEND_PLATFORM_CONTRACT
ADAPTER_REQUIRED
ADR_REQUIRED
OUT_OF_SCOPE
```

Market availability without DELPI evidence = `TO_INVENTORY`, never `PROVEN`.

No runtime diff in C0.S0.

## 4.1 Evidence discovery rule

GitHub/code search é discovery/residual, não prova canônica de ausência.

```text
search hit
→ localizar fonte candidata
→ abrir authority por path no HEAD relevante
→ verificar owner/contract/requirement
→ classificar

search miss
!= ausência no repositório
!= ausência na documentação
!= TO_INVENTORY automaticamente
```

Antes de afirmar que uma capability/requisito “não existe” ou “não está previsto”, abrir diretamente as authorities prováveis, `25` e a spec temática aplicável.

Separar sempre:

```text
PRODUCT/CAPABILITY INTENT
CONTRACT / FIRST-CLASS REQUIREMENT
PHYSICAL MECHANISM / OWNER
RUNTIME IMPLEMENTATION
```

Exemplo: `timers/schedules` pode ser `TARGET`; scheduler físico pode continuar `TO_INVENTORY`; runtime segue não `PROVEN` até evidence. Não propagar o estado de uma camada para outra.

## 5. Foundation Freeze

No C1+ before all REQUIRED foundation boundaries in `16/20` are PASS, including Recurring Governed Work, Process Intelligence, AI Asset governance, MCP/A2A trust, Personal Memory, Semantic Layer, Sandbox/Artifacts, Predictive/Twin, Edge/Offline, Model/Marketplace and OT safety.

## 6. Single phase order

```text
C0 Foundation Freeze
→ C1 Standalone Bootstrap
→ C2 Context/Commands
→ C3 Capability Foundations
→ C4 Governed Reads/Analysis
→ C5 Governed ACT/Executors/Durable Work/Recurring Work
→ C6 Product Governance/Experience
→ C7 Advanced Autonomy/Scale
```

C5 may enable L4 governed execute for explicitly authorized capabilities, including bounded Recurring Governed Work occurrences that revalidate live gates. C6 does not autonomously trigger Watch ACT by default. C7 adds selected Watch ACT/L5 under explicit limits; L5 remains OFF by default.

No thematic plan changes this order.

## 7. Execution unit

Exactly one `C*.S*` at a time:

```text
SELECT STEP
→ REVALIDATE HEAD/WORKTREE
→ READ AUTHORITIES
→ IDENTIFY RESPONSIBILITY/OWNER/SOURCE
→ IDENTIFY CONSUMERS/CONTRACT
→ CANONICAL PATTERN
→ ABSTRACTION + DEPENDENCY GATES
→ BASELINE
→ MINIMAL CORRECT DIFF
→ WIRE PRODUCER/CONSUMER
→ UNIT/CONTRACT/INTEGRATION
→ POSITIVE/SIBLING/NEGATIVE
→ SECURITY/RBAC/PRIVACY/OUTCOME/SAFETY
→ GENERALIZATION/METAMORPHIC/UNKNOWN
→ CHAT-INDEPENDENCE
→ ARCHITECTURE CONFORMANCE
→ RESIDUAL SEARCH
→ COMPLETE_GATE
→ DOCS/LEDGER
→ NEXT
```

## 8. READY_TO_EXECUTE

Only if previous gates pass and owner/source/consumers/contract/layer/pattern/primitive/test/migration/security/privacy/safety are known.

For new thematic capability also answer:

```text
Does this duplicate a source/system of record?
Does it create a new permission authority?
Does it collapse Graph/Semantic/Memory/Knowledge/Twin distinctions?
Does it require provider/executor/model/tool hardcode?
What is the revoke/rollback/kill-switch path?
What verifies actual business outcome?
What happens stale/offline/unavailable?
Could it create employee surveillance?
Can sibling implementation work by adapter?
```

For recurring/scheduled work additionally answer:

```text
Who owns RecurringWorkDefinition?
Who owns the physical timer/scheduler runtime?
What is the canonical recurrence + IANA timezone contract?
What are DST/misfire/missed-run/overlap semantics?
How is occurrence idempotency derived?
Which identity is resolved at execution time?
How are live AuthZ/Policy/provider revoke revalidated per occurrence?
What prevents paused/cancelled definitions from firing?
```

If material answer is unresolved: `BLOCKED_WITH_EVIDENCE` or return to foundation/ADR.

## 9. Anti-refactor checklist

Before new schema/service/table/interface/registry/engine/server/sandbox/twin/Edge module/Marketplace/scheduler:

```text
A owner/source authority?
B real consumers/contract?
C existing shared primitive/contract?
D Chat/product coupling?
E layer/pattern?
F Abstraction Gate?
G second RBAC/workflow/planner/Graph/Semantic/Knowledge authority?
H persistence really required and owned?
I next phase redesign obvious?
J sibling/unknown generalization?
K credentials/data bounded?
L read/write/PREPARE/ACT/simulate/apply separated?
M rollback/revoke path?
N user/device/service/worker/scheduler identities distinct?
O Outcome verified by authoritative source?
P OT safety boundary preserved?
```

Stop and redesign on material violation.

## 10. Semantic invariants to review every relevant step

```text
Personal Memory != Organizational Knowledge
Business Graph != Semantic Business Layer
Prediction != FACT
Recommendation != Authorization
SIMULATE != APPLY
PREPARE != ACT
Read != Write
Draft != Send
Schedule != Permission
Stored Schedule Intent != Eternal Authorization
Recurring Governed Work != Watch Autonomous ACT
Physical Scheduler != DÉLIA Work/Policy Authority
L4 governed execute != L5 autonomous execute
Technical Success != Verified Business Outcome
MCP/A2A Discovery != Approval
Marketplace Install != Permission
Device/Biometric/Worker/Scheduler Identity != User Authorization
Edge Offline != Wider Authority
```

## 11. Prohibitions

- Chat dependency/migration;
- duplicate Keycloak/Core/domain authority;
- DÉLIA bypassing Automation Hub technical-execution ownership with ad hoc executor internals;
- DÉLIA duplicating physical scheduler job/lease/worker truth without proven ownership;
- schedule/timer/cron metadata as permission or ACT authority;
- stale authorization snapshot reused for future recurring occurrences;
- paused/cancelled recurring Work continuing to fire;
- silent misfire catch-up of material ACT;
- manual endpoint/app/provider/executor/model/tool routing in planner;
- DOM business automation as default when API exists;
- RPA clicks/selectors in planner;
- second workflow engine by capability;
- hidden capture/surveillance;
- Process Mining employee leaderboard;
- Personal Memory as organization truth;
- LLM-invented material KPI formula;
- unbounded sandbox/host/network access;
- prediction as fact;
- scenario/twin mutating production;
- MCP/A2A auto-trust;
- Marketplace/package permission grant;
- Edge offline authority expansion;
- global unrestricted L5;
- CoT persistence;
- arbitrary LLM/RPA/Edge→machine actuation.

## 12. C1 special rule

First runtime work after C0 is own API/MFE/health/JWT-Core/federation/plugin-ui/manifest/Gateway/Compose/Portal host/independence. No intelligence/process/RPA/MCP/sandbox/twin/Edge/Marketplace/recurring ACT runtime before dependencies unlock them.

## 13. Meeting/Frontline/Edge

Same DÉLIA API/MFE/policy/evidence/work runtime. Edge is a governed deployment/runtime boundary, not another DÉLIA product. Offline mode is explicit and cannot widen permission.

## 14. Process/people rule

Process Intelligence describes process variants/facts. Human Observation/Task Mining cannot infer personality/trust/intent/fraud or become hidden employee score. Candidate improvements require review/evidence.

## 15. Model/tool/asset rule

Model/tool/agent/package metadata is untrusted. Approval, eval, data scope, version, risk and revoke state must be explicit. Revoked asset cannot remain selectable.

## 16. Outcome rule

Every material execution asks:

```text
Was technical execution attempted/completed?
Was expected business postcondition observed in authoritative source?
```

Do not use notifications, scheduler fire or RPA UI state as final proof when better authoritative source exists.

## 17. Automation and recurring-work ownership rule

```text
DÉLIA = intelligence + Policy + Decision + Work/orchestration + RecurringWork definition/correlation + Outcome coordination
Automation Hub = technical execution
Physical scheduler/timer owner = technical time-trigger materialization
```

C0 must prove whether physical Hub/scheduler runtimes/contracts already exist. Lack of implementation evidence does not transfer technical execution authority into DÉLIA.

A Recurring Work occurrence may reach C5 L4 governed ACT only after live identity/Core/domain AuthZ/Policy/Decision/provider/source revalidation. It does not require C7 L5, and it does not enable C6 Watch autonomous ACT.

## 18. OT rule

Until separate industrial safety gate passes:

```text
telemetry/read → contract-driven possible
free-form physical actuation → BLOCK
```

Enterprise L5 never overrides OT safety.

## 19. Evidence minimum

Record as material:

```text
HEAD_BEFORE/AFTER
files changed
owner/source/consumers/contract/layer/pattern
CPs
commands/tests/results
contract/schema/model/metric/executor/package versions
recurring definition/version/timezone/misfire/overlap policy when applicable
occurrence/idempotency/AuthZ/revoke evidence when applicable
Evidence/Outcome proof
security/privacy/autonomy impact
residual scans
Chat independence
ADR refs
```

## 20. Adversarial review

Ask:

1. Works with Chat offline?
2. Any duplicate authority?
3. Any hidden provider/executor/model/tool branch?
4. Any permission from event/memory/model/package/tool/agent/device/schedule?
5. Retry/resume/event/timer duplicate causes duplicate effect?
6. Technical success or timer fire narrated as business success?
7. Process/user data becoming surveillance?
8. Memory overriding live source?
9. Metric formula reproducible/owned?
10. Sandbox can escape/write?
11. Prediction shown as fact?
12. Simulation writes production?
13. Edge/offline widens authority?
14. Revoked asset still usable?
15. Marketplace install grants permission?
16. Any LLM→machine path without safety architecture?
17. Any stale/missing evidence being hidden?
18. Any DÉLIA technical executor bypassing Automation Hub ownership?
19. Any DÉLIA scheduler implementation duplicating a platform owner without inventory/Abstraction Gate?
20. Does a recurring occurrence revalidate current authorization instead of trusting creation-time permission?
21. Do pause/cancel/revoke/misfire/overlap semantics actually work under restart/duplicate trigger?

## 21. COMPLETE_GATE

Use `20` as sole detailed blocker authority. `PARTIAL/INCONCLUSIVE/PENDING/TEST_NOT_RUN/STALE_EVIDENCE` block closure.

## 22. Report required

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
ABSTRACTION_GATE:
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
RESIDUAL_SEARCH:
ARCHITECTURE_CONFORMANCE:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 23. Continuity

With `COMPLETE_GATE=PASS`, follow next step unlocked by `16` unless a real destructive/missing-authority decision blocks it.

First order remains:

```text
C0.S0 → C0.S1 → C0.S2 → C0.S3 → C0.S4 → C0.S5 → C0.S6 → C0.S7 FOUNDATION_FREEZE → C1.S1
```

## 24. Requirements completeness gate

Toda unidade de implementação precisa provar não só o que foi feito, mas também o que **faltou**.

Antes do diff, decompor o escopo autorizado em requisitos atômicos `RQ-*` e acceptance criteria `AC-*`. Requisitos materiais que pertencem ao produto devem mapear para `CP-*` da authority `25-requirements-traceability.md`.

Estados permitidos por `RQ-*`:

```text
IMPLEMENTED
PARTIAL
NOT_IMPLEMENTED
BLOCKED
NOT_APPLICABLE
```

Regras obrigatórias:

- todo `RQ-*` do brief aparece no relatório final;
- nenhum requisito pode ser removido, fundido implicitamente ou considerado atendido sem evidence;
- `PARTIAL` não conta como implementado;
- `NOT_APPLICABLE` exige rationale explícito e não pode mascarar requisito obrigatório;
- requisito material descoberto durante execução vira `DRQ-*` / `DISCOVERED_REQUIREMENT`;
- se um requisito material descoberto não possui `CP-*` correspondente, registrar `TRACEABILITY_GAP`; não declarar completude global até a matriz `25` ser reconciliada;
- cada `RQ-*` aponta, quando aplicável, para `CP-*`, `AC-*`, teste/postcondition e evidence.

Métricas da tarefa:

```text
APPLICABLE_RQ = TOTAL_RQ - NOT_APPLICABLE
TASK_IMPLEMENTED = count(RQ = IMPLEMENTED)
TASK_VERIFIED_COVERAGE_PCT = 100 * TASK_IMPLEMENTED / APPLICABLE_RQ
TASK_REMAINING_PCT = 100 - TASK_VERIFIED_COVERAGE_PCT
CRITICAL_RQ_TOTAL = count(RQ critical)
CRITICAL_RQ_IMPLEMENTED = count(critical RQ = IMPLEMENTED)
```

Não conceder crédito fracionário a `PARTIAL`. A porcentagem mede cobertura verificada de requisitos, não esforço ou tempo consumido.

`TASK_COMPLETENESS = COMPLETE` somente quando:

```text
todos os RQ obrigatórios = IMPLEMENTED
nenhum RQ crítico = PARTIAL | NOT_IMPLEMENTED | BLOCKED
todos AC obrigatórios = PASS
todos testes/evals obrigatórios = PASS
residual search sem gap material
planned scope = actual diff
contract/security/postcondition gates resolvidos
EXECUTION_DRIFT aberto = NONE
```

O relatório final deve incluir:

```text
REQUIREMENTS COMPLETENESS
RQ | Critical | CP | Status | Evidence
TOTAL_RQ
APPLICABLE_RQ
IMPLEMENTED_RQ
PARTIAL_RQ
NOT_IMPLEMENTED_RQ
BLOCKED_RQ
TASK_VERIFIED_COVERAGE_PCT
TASK_REMAINING_PCT
CRITICAL_COVERAGE
TASK_COMPLETENESS
DISCOVERED_REQUIREMENTS
TRACEABILITY_GAPS
```

## 25. Program-wide verified completion

Para saber quanto falta para a DÉLIA estar **100% implementada no escopo previsto**, usar a matriz `25-requirements-traceability.md` como denominador canônico e o execution ledger como autoridade de estado.

Não medir progresso global por commits, arquivos, linhas, quantidade de código, fases iniciadas ou declaração do agente.

Definições:

```text
ACTIVE_CP = todo CP-* da matriz cujo status != OUT_OF_SCOPE_WITH_DECISION
PASS_CP = ACTIVE_CP cujo status = PASS
REMAINING_CP = ACTIVE_CP - PASS_CP
VERIFIED_PROGRAM_COMPLETION_PCT = 100 * PASS_CP / ACTIVE_CP
VERIFIED_PROGRAM_REMAINING_PCT = 100 - VERIFIED_PROGRAM_COMPLETION_PCT
```

`PLANNED | REVALIDATE | TO_INVENTORY | LOCKED | IN_PROGRESS | BLOCKED_WITH_EVIDENCE | FAIL` continuam no denominador e valem zero no numerador. Isso evita transformar trabalho parcial em progresso comprovado.

`OUT_OF_SCOPE_WITH_DECISION` é excluído do denominador porque deixou formalmente o escopo ativo; o ID permanece histórico.

A mesma métrica deve ser calculada por fase `C0…C7`:

```text
PHASE_ACTIVE_CP
PHASE_PASS_CP
PHASE_REMAINING_CP
PHASE_VERIFIED_COMPLETION_PCT
PHASE_REMAINING_PCT
```

A porcentagem é **Verified Scope Completion**: cobertura de escopo previsto comprovadamente concluída. Não é estimativa de esforço, custo ou calendário.

### Gate de 100%

Mesmo com `VERIFIED_PROGRAM_COMPLETION_PCT = 100`, declarar `PROGRAM_COMPLETE = TRUE` somente se, no SHA/config/evidence aplicável:

```text
todos ACTIVE_CP = PASS
C0…C7 gates obrigatórios = PASS
20-testing-and-acceptance-matrix gates obrigatórios = PASS
nenhum PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE material aberto
nenhum EXECUTION_DRIFT material aberto
nenhum TRACEABILITY_GAP material aberto
postconditions/outcomes autoritativos exigidos = verificados
documentação/ledger = reconciliados com runtime comprovado
```

Se uma spec trouxer capability/requisito material que ainda não esteja mapeado em `25`, isso é `TRACEABILITY_GAP`; o programa não pode permanecer “100%” até canonizar o requisito ou removê-lo formalmente do escopo com `OUT_OF_SCOPE_WITH_DECISION`.

Após toda implementação aceita que altere status `CP-*`, atualizar/recalcular no relatório:

```text
PROGRAM PROGRESS
ACTIVE_CP_TOTAL
PASS_CP_TOTAL
REMAINING_CP_TOTAL
VERIFIED_PROGRAM_COMPLETION_PCT
VERIFIED_PROGRAM_REMAINING_PCT
CURRENT_PHASE
CURRENT_PHASE_ACTIVE_CP
CURRENT_PHASE_PASS_CP
CURRENT_PHASE_COMPLETION_PCT
CURRENT_PHASE_REMAINING_PCT
PROGRAM_COMPLETE = TRUE | FALSE
```

Assim há duas respostas objetivas diferentes:

```text
Quanto desta implementação específica terminou?
→ TASK_VERIFIED_COVERAGE_PCT / TASK_COMPLETENESS

Quanto da DÉLIA inteira prevista terminou?
→ VERIFIED_PROGRAM_COMPLETION_PCT / PROGRAM_COMPLETE
```

## 26. Recurring Governed Work — execution specialization

Para qualquer tarefa que envolva schedule/timer/recurrence/background report/job, carregar obrigatoriamente `16`, `17`, `20`, `21`, `25` (`CP-311–CP-316`) e `57`.

O brief deve separar explicitamente:

```text
PRODUCT CAPABILITY = Recurring Governed Work
DÉLIA STATE = definition/lifecycle/occurrence correlation
PHYSICAL SCHEDULER = TO_INVENTORY until C0 proof
MATERIAL ACT = only after per-occurrence live gates
```

O Cursor não pode concluir “scheduling não está previsto” porque um code search retornou zero resultados. Também não pode concluir que scheduling está implementado porque encontrou cron/job infrastructure.

Evidence necessária varia por camada:

```text
TARGET/PLANNED
→ authority/CP/spec

PROVEN platform mechanism
→ factual path/config/owner/contract evidence

PASS runtime
→ implementation + wiring + tests + restart/duplicate/revoke/misfire cases + outcome evidence
```

Anchor obrigatório quando `CP-315` for implementado:

```text
user creates recurring daily report
→ survives session/restart
→ deterministic occurrence at IANA timezone
→ live AuthZ/Policy
→ current authorized reads
→ grounded report artifact
→ separate email.send ACT
→ no duplicate send on duplicate/retry/restart
→ verified provider/business outcome when contract supports
→ Evidence/Audit/Outcome
```
