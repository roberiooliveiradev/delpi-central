# Minha DELPI Copilot — Governança Documental e Revisão Arquitetural

**Status:** canônico para precedência documental e controle de drift  
**Revisão:** foundation-first + standalone + enterprise intelligence  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Evitar ordens, owners, contracts, patterns, security/privacy/data/automation/model boundaries concorrentes e garantir que toda expansão de produto continue subordinada às mesmas authorities.

## 2. Precedência

Em caso de conflito:

```text
1. instruções oficiais + .cursor rules
2. 16 — ordem/dependências
3. 50 — standalone product/runtime boundary
4. 17 — ownership/primitives/contracts
5. 49 — architecture/patterns
6. 51 — factual platform baseline
7. 52 — repository/bootstrap target
8. 21 — state/persistence
9. 20 — tests/gates
10. 25 — CP requirements
11. 02 — technical target
12. 24 — product target
13. thematic specs 53–66
14. ledger — execution evidence/status
```

Ledger registra estado; não redefine arquitetura.

## 3. Authorities operacionais

| Arquivo | Authority |
|---|---|
| `16` | única ordem C0–C7 |
| `50` | standalone boundary |
| `17` | owners/primitives/contracts |
| `49` | code architecture/patterns |
| `51` | factual platform baseline |
| `52` | physical/bootstrap target |
| `20` | tests/gates |
| `21` | state/persistence/retention |
| `23` | Cursor master prompt |
| `25` | requirements `CP-001…CP-310` |
| ledger | current execution/evidence |

## 4. Specs temáticas ativas

```text
53 multimodal / Meeting / Frontline / industrial
54 biometric identity / Human Observation
55 Internet Research / external connectors
56 Microsoft Teams
57 Event-Driven Autonomous Operations / Automation & Execution Hub
58 Process Intelligence / Process Mining / Task Mining
59 AI Control Tower / Digital Workforce Governance
60 MCP / A2A / agent-tool interoperability
61 Personal Memory / Personalization
62 Semantic Business Layer / governed metrics
63 Analysis Sandbox / Artifact Workspace
64 Predictive / Prescriptive Intelligence / Operational Twin
65 Edge / Offline Industrial Copilot
66 AI Model Lifecycle / Capability Marketplace
```

Todas são subordinadas a `16/17/20/21/25/49/50/51`. Nenhuma cria segunda requirement matrix, phase order, RBAC, workflow, planner ou business authority.

## 5. Reference-only / superseded

```text
31 = antiga migração de agents Chat — SUPERSEDED / REFERENCE_ONLY
45 = antiga extensão de tests — SUPERSEDED / REFERENCE_ONLY
46 = antiga extensão de requirements — SUPERSEDED / REFERENCE_ONLY
47 = antiga extensão de Cursor prompt — SUPERSEDED / REFERENCE_ONLY
```

Não atualizar essas specs como se fossem atuais; apenas manter status/link claramente histórico.

## 6. Findings arquiteturais corrigidos

### F1–F25 — foundations existentes

Já corrigidos anteriormente: single execution authority, shared primitives, standalone boundary, patterns, multimodal/biometric/privacy, safe Internet/connectors, Teams same runtime, Automation Hub not RPA-first, semantic executors, decision paths, event non-authority, verified Outcome, PREPARE!=ACT, capability-scoped autonomy, bounded computer-use.

### F26 — Process Intelligence poderia virar surveillance

`58`: Process Mining mede processo/event traces. Actor data é minimizado; task mining exige governance. Deviation não significa fraude/culpa/personality.

### F27 — Control Tower poderia virar super-admin de negócio

`59`: Control Tower governa ativos, risco, health, evals, cost, rollout, incidents e kill switches; admin da Tower não ganha business permission.

### F28 — MCP/A2A discovery poderia virar auto-trust

`60`: server/agent/tool metadata é untrusted; discovery != approval; allowlist/scopes/data minimization obrigatórios.

### F29 — Personal Memory poderia conflitar com Knowledge/Context

`61`: Personal Memory, Organizational Knowledge, Conversation History e WorkspaceContext são owners/lifecycles distintos. Memory não substitui live truth nem RBAC.

### F30 — Graph poderia virar semantic layer universal

`62`: Graph representa relações; Semantic Business Layer define significado/fórmula/grain/dimensions de métricas. Conceitos permanecem separados.

### F31 — Sandbox poderia virar shell corporativo irrestrito

`63`: isolated runtime, bounded data/egress/quotas; source access read-only by default; no broad DB/host credentials.

### F32 — Artifact generation poderia perder lineage/human edits

`63`: artifact has version/provenance/ACL; regeneration não sobrescreve silentemente edição humana; share/send é action separada.

### F33 — Prediction poderia virar fato/autoridade

`64`: prediction != FACT; recommendation != authorization. Model output preserves version/horizon/confidence/limitations.

### F34 — Digital/Operational Twin poderia virar source of truth

`64`: twin é projection/scenario. `SIMULATED_STATE != PRODUCTION_STATE`; Apply é novo live action flow.

### F35 — Edge/offline poderia ampliar autoridade

`65`: offline mode é explícito e nunca aumenta permission. Cache tem revision/freshness; Edge não vira safety controller.

### F36 — Model Router sem lifecycle governado

`66`: Model Registry/lifecycle/evals/drift/deployment/rollback/revoke precedem advanced routing/deployment.

### F37 — Marketplace poderia conceder permissions/supply-chain bypass

`66`: package manifest declara requirements, não grants. Publish/enable usa review/evals/compatibility/integrity/supply-chain controls.

## 7. Foundation invariants após C0.S7

```text
one Copilot API/runtime
one Copilot MFE/product identity
Core/Keycloak/Domain/External/OT authorities preserved
Durable Workflow = one canonical work runtime
Graph != Semantic Layer
Personal Memory != Organizational Knowledge
Process Mining != employee scoring
Control Tower != business permission authority
MCP/A2A discovery != approval
Sandbox != unrestricted shell
Prediction != FACT
Recommendation != authorization
Simulate != Apply
Twin != source of truth
Edge offline != wider authority
Model/Marketplace install != permission
technical success != verified business Outcome
L5 default = OFF
OT safety remains external authority
Chat runtime dependency = 0
```

## 8. Documentation update protocol

Material architecture/product change updates, when applicable:

```text
16 order/phase mapping
17 owner/contracts
49 architecture/patterns
51 factual baseline if evidence changed
21 state model
20 tests/gates
25 CP traceability
23 Cursor prompt
02/24/12/15 product/architecture/roadmap/integration views
08/09/11/14 security/UX/observability/DoD
relevant thematic specs
README/INDEX
audit evidence
ledger
```

Documentation-only planning does not advance runtime phase.

## 9. Market capability rule

External market availability != DELPI platform fact.

```text
Celonis Process Mining exists
!= DELPI has reusable process-mining runtime

MCP/A2A exist
!= repo contains approved infrastructure

Edge AI exists
!= factory devices/network support it
```

Only C0 repo/infra evidence can produce `PLATFORM_REUSE | NEUTRAL_SHARED_REUSE`; otherwise `NOT_PROVEN/COPILOT_IMPLEMENT_NEW/...`.

## 10. Anti-drift review checklist

Search/review all docs for:

```text
old CP upper range (<310)
old thematic range ending at 57
Chat runtime dependency
multiple execution order authorities
provider/executor/model/tool hardcode in planner
RPA-first wording
second workflow/planner/RBAC
Process Mining as employee score
Memory == Knowledge or permission
Graph == Semantic Layer
MCP/A2A auto-trust
Sandbox unrestricted access
Prediction == fact
Recommendation == authorization
Simulate == Apply
Twin == system of record
Edge offline permission expansion
Model/Marketplace install == permission
revoked asset still usable
technical success == business completion
PREPARE == ACT
global L5
OT actuation implied by enterprise autonomy
broken/superseded links presented as active
```

## 11. Current governance state

```text
PROGRAM = PLANNED / NOT_STARTED
REQUIREMENTS = CP-001…CP-310
THEMATIC_SPECS = 53–66
NEXT = C0.S0
RUNTIME_DIFF = NONE
```

C0.S0 is factual inventory only and now includes platform/media/biometric/external/automation/process/AI-assets/tools-agents/memory/semantics/sandbox/predictive/twin/Edge/model-marketplace/OT boundaries. It does not create any of those runtimes.
