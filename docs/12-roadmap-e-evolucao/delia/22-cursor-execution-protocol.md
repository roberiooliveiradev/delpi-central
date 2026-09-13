# Minha DELPI Copilot — Protocolo de Execução para o Cursor

**Status:** obrigatório  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Requirements:** `CP-001…CP-310`  
**Specs temáticas:** `53–66`

## 1. Objetivo

Executar o Copilot como aplicação nova, foundation-first, sem Chat runtime dependency, sem architecture-by-feature e sem adiar boundaries de data/process/automation/model/privacy/Edge que depois exigiriam refactor.

## 2. Mandatory reading

Before each substep:

1. official project instructions;
2. applicable `.cursor/rules`;
3. Copilot `README.md` + `INDEX.md`;
4. `16` execution order;
5. `50` standalone boundary;
6. `51` factual baseline;
7. `52` physical/bootstrap target;
8. `17` ownership/contracts;
9. `49` architecture/patterns;
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
Copilot API → Chat runtime/API/tables
Copilot MFE → Chat source imports
Copilot feature → Chat planner/tool/media/provider as mandatory implementation
Copilot progress → Chat refactor dependency
```

Chat is reference-only during inventory.

## 4. C0.S0 — runtime read-only inventory

Inventariar factual evidence for:

```text
Platform: Portal/Core/Keycloak/Gateway/Compose/plugin-ui/MFEs/APIs/OpenAPIs
Media/Biometric/Meeting/Frontline/Devices/OT
Internet/OAuth/External Connectors/Teams/Webhooks
Events/RPA/Automation/Queues/Workers/Service Identities/Outcome Sources
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

Classify:

```text
PLATFORM_REUSE
NEUTRAL_SHARED_REUSE
COPILOT_IMPLEMENT_NEW
EXTEND_PLATFORM_CONTRACT
ADAPTER_REQUIRED
ADR_REQUIRED
NOT_PROVEN
OUT_OF_SCOPE
```

Market availability without DELPI evidence = `NOT_PROVEN`.

No runtime diff in C0.S0.

## 5. Foundation Freeze

No C1+ before all REQUIRED foundation boundaries in `16/20` are PASS, including Process Intelligence, AI Asset governance, MCP/A2A trust, Personal Memory, Semantic Layer, Sandbox/Artifacts, Predictive/Twin, Edge/Offline, Model/Marketplace and OT safety.

## 6. Single phase order

```text
C0 Foundation Freeze
→ C1 Standalone Bootstrap
→ C2 Context/Commands
→ C3 Capability Foundations
→ C4 Governed Reads/Analysis
→ C5 Governed Writes/Executors
→ C6 Product Governance/Experience
→ C7 Advanced Autonomy/Scale
```

No thematic plan changes this order.

## 7. Execution unit

Exactly one `C*.S*` at a time:

```text
SELECT STEP
→ REVALIDATE HEAD/WORKTREE
→ READ AUTHORITIES
→ IDENTIFY OWNER/SOURCE/LAYER
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

Only if previous gates pass and owner/source/layer/pattern/primitive/test/migration/security/privacy/safety are known.

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

If material answer is unresolved: `BLOCKED_WITH_EVIDENCE` or return to foundation/ADR.

## 9. Anti-refactor checklist

Before new schema/service/table/interface/registry/engine/server/sandbox/twin/Edge module/Marketplace:

```text
A owner/source authority?
B existing shared primitive/contract?
C Chat/product coupling?
D layer/pattern?
E Abstraction Gate?
F second RBAC/workflow/planner/Graph/Semantic/Knowledge authority?
G persistence really required?
H next phase redesign obvious?
I sibling/unknown generalization?
J credentials/data bounded?
K read/write/PREPARE/ACT/simulate/apply separated?
L rollback/revoke path?
M user/device/service/worker identities distinct?
N Outcome verified by authoritative source?
O OT safety boundary preserved?
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
Technical Success != Verified Business Outcome
MCP/A2A Discovery != Approval
Marketplace Install != Permission
Device/Biometric/Worker Identity != User Authorization
Edge Offline != Wider Authority
```

## 11. Prohibitions

- Chat dependency/migration;
- duplicate Core/domain authority;
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

First runtime work after C0 is own API/MFE/health/JWT-Core/federation/plugin-ui/manifest/Gateway/Compose/Portal host/independence. No intelligence/process/RPA/MCP/sandbox/twin/Edge/Marketplace runtime before dependencies unlock them.

## 13. Meeting/Frontline/Edge

Same Copilot API/MFE/policy/evidence/work runtime. Edge is a governed deployment/runtime boundary, not another Copilot product. Offline mode is explicit and cannot widen permission.

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

Do not use notifications or RPA UI state as final proof when better authoritative source exists.

## 17. OT rule

Until separate industrial safety gate passes:

```text
telemetry/read → contract-driven possible
free-form physical actuation → BLOCK
```

Enterprise L5 never overrides OT safety.

## 18. Evidence minimum

Record as material:

```text
HEAD_BEFORE/AFTER
files changed
owner/source/layer/pattern
CPs
commands/tests/results
contract/schema/model/metric/executor/package versions
Evidence/Outcome proof
security/privacy/autonomy impact
residual scans
Chat independence
ADR refs
```

## 19. Adversarial review

Ask:

1. Works with Chat offline?
2. Any duplicate authority?
3. Any hidden provider/executor/model/tool branch?
4. Any permission from event/memory/model/package/tool/agent/device?
5. Retry/resume/event duplicate causes duplicate effect?
6. Technical success narrated as business success?
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

## 20. COMPLETE_GATE

Use `20` as sole detailed blocker authority. `PARTIAL/INCONCLUSIVE/PENDING/TEST_NOT_RUN/STALE_EVIDENCE` block closure.

## 21. Report required

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
CP_REQUIREMENTS:
FILES_CHANGED:
OWNERS/SOURCES:
LAYER/PATTERNS:
ABSTRACTION_GATE:
PLATFORM_REUSE:
COPILOT_NEW_CODE:
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

## 22. Continuity

With `COMPLETE_GATE=PASS`, follow next step unlocked by `16` unless a real destructive/missing-authority decision blocks it.

First order remains:

```text
C0.S0 → C0.S1 → C0.S2 → C0.S3 → C0.S4 → C0.S5 → C0.S6 → C0.S7 FOUNDATION_FREEZE → C1.S1
```
