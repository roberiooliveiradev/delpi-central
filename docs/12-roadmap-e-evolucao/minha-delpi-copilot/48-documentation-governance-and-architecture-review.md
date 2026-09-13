# Minha DELPI Copilot — Governança Documental e Revisão Arquitetural

**Status:** canônico para precedência documental  
**Revisão:** foundation-first + standalone + multimodal/biometric/external/automation/industrial boundaries  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Evitar ordens, owners, contracts, patterns, security/privacy/external/automation boundaries concorrentes.

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
13. thematic specs, including 53/54/55/56/57
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
| `21` | state/persistence/media/biometric/external/automation refs |
| `23` | Cursor master prompt |
| `25` | requirements `CP-001…CP-248` |
| ledger | current execution/evidence |

## 4. Specs temáticas relevantes

```text
53 multimodal/Meeting/Frontline/industrial
54 biometric identity/Human Observation
55 Internet Research/external connectors/OAuth/external learning
56 Microsoft Teams connector/meeting integration
57 Event-Driven Autonomous Operations + Automation & Execution Hub
```

Specs temáticas não criam outra ordem, outra requirement matrix ou outro planner/workflow authority. Sua implementação é materializada exclusivamente por `16`.

## 5. Findings arquiteturais corrigidos

### F1 — Multiple execution authorities
`16` é única authority de ordem.

### F2 — Shared primitives tardios
Entity/Evidence/Decision/Workflow/Event antecipados para foundation.

### F3 — Chat tratado como base
Superseded: Copilot é standalone API/MFE/persistence/deploy próprios.

### F4 — Architecture inferred by feature
`49` congela layers/patterns/Abstraction Gate.

### F5 — Multimodal/Frontline tardio
Media/privacy/device/OT boundaries entram em C0.

### F6 — Biometric identity poderia virar auth paralela
`54`: biometric match é candidate association; Core/Keycloak continuam authority.

### F7 — Human Observation poderia virar worker profiling
`54`: somente sinais observáveis do processo; no sensitive/psychological inference or automatic employment decision.

### F8 — Internet poderia virar HTTP irrestrito
`55`: pesquisa passa por Search + Safe Fetch + egress policy; external content é untrusted.

### F9 — Connectors poderiam hardcodar provider no planner
`55` + `49`: semantic connector capabilities + provider adapters.

### F10 — OAuth scope poderia ser confundido com RBAC
Provider scope é connection-specific e não altera Core permissions.

### F11 — Tokens poderiam contaminar state/LLM/MFE
Secret/Vault boundary + `secretRef`; credentials nunca são prompt/context/ordinary log data.

### F12 — Conta pessoal poderia virar source corporativo
Connection ownership/visibility classes impedem promoção implícita.

### F13 — Read e send poderiam convergir cedo demais
Read/write capabilities separadas; `draft != send`; writes usam Policy/Decision/outcome verification.

### F14 — Webhooks poderiam virar action channel paralelo
Provider/domain event → validation → EventEnvelope → dedupe/correlation → Watch/Workflow. Event nunca autoriza write.

### F15 — External learning poderia auto-publicar truth
Transient research ou Knowledge candidate; publish exige governance/freshness/privacy/licensing.

### F16 — Teams poderia criar outro Copilot
`56`: Teams é capability family/surface do mesmo Copilot runtime.

### F17 — “Hub de RPAs” poderia virar arquitetura RPA-first
`57`: produto alvo é **Automation & Execution Hub**; executor preference é API → native integration → function → RPA → computer-use → human.

### F18 — RPA poderia absorver regra/decisão
`57` + `49`: Copilot/Domain owners decidem; RPA é adapter/executor substituível.

### F19 — Planner poderia carregar clicks/selectors
Corrigido: semantic capability contract; UI mechanics ficam exclusivamente no executor adapter.

### F20 — Todo evento poderia chamar LLM
Corrigido: DecisionPathPolicy `FAST | OPERATIONAL | REASONING`; deterministic path quando suficiente.

### F21 — Evento poderia ser confundido com autoridade
Corrigido: event payload/source não concede permission nem ACT.

### F22 — Technical success poderia ser narrado como business success
Corrigido: Outcome Verification distingue executor result de postcondition autoritativa.

### F23 — Watch PREPARE poderia executar implicitamente
Corrigido: `PREPARE != ACT`; ACT somente C7 sob AutonomyPolicy.

### F24 — Autonomy poderia virar flag global
Corrigido: capability/context/risk-scoped; L5 OFF por default, allowlist/budgets/kill switch.

### F25 — Computer-use poderia virar desktop/network irrestrito
Corrigido: advanced sandboxed/allowlisted fallback, nunca default executor.

## 6. Foundation invariants

Após C0.S7:

```text
one Copilot runtime/API
one Copilot MFE
Core = platform authorization authority
Keycloak = identity authority
Domain API = business authority
External provider = external resource authority
RPA/executor = execution mechanism, not business authority
Event source = signal authority only for its factual event, not permission
Durable Workflow = one canonical work runtime
Automation Hub = execution bounded context, not second planner/workflow
semantic capability != concrete executor
planner contains no RPA UI mechanics
background ACT has explicit user/service identity
technical success != verified business outcome
Watch PREPARE != ACT
Autonomy = capability/context/risk scoped
L5 default = OFF
OT safety remains external authority
Chat runtime dependency = 0
```

## 7. Documentation update rules

Any material architecture change must update, in this order where applicable:

```text
16 order/phase mapping
17 owner/contracts
49 architecture/patterns
51 factual baseline if evidence changed
21 state model
20 tests/gates
25 CP traceability
23 Cursor prompt
product/thematic specs
ledger
```

Documentation-only planning does not advance runtime status.

## 8. New technology/provider rule

Do not record a market capability/tool as platform fact merely because it exists externally.

Example:

```text
UiPath/Automation Anywhere/Power Automate exists in market
!=
DELPI currently has a reusable RPA platform
```

Only C0 repo/infra evidence can produce `PLATFORM_REUSE` or `NEUTRAL_SHARED_REUSE`.

## 9. Anti-drift checklist

Search/review for:

```text
old CP upper range
Chat runtime dependency
provider/executor hardcode
RPA-first wording
second workflow/planner
click/selector in semantic planner contracts
event == permission/action
every event == LLM
technical success == business completion
PREPARE == ACT
global L5
computer-use unrestricted
OT actuation implied by enterprise autonomy
```

Any occurrence is reviewed against `16/17/20/25/49/57`.

## 10. Current governance state

```text
PROGRAM = PLANNED / NOT_STARTED
REQUIREMENTS = CP-001…CP-248
NEXT = C0.S0
RUNTIME_DIFF = NONE
```

C0.S0 is factual inventory only, now including events/RPA/executors/workers/service identities/outcome sources/autonomy boundaries. It does not create Automation Hub runtime.
