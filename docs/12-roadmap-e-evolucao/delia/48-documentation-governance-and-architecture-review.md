# DÉLIA — Governança Documental e Revisão Arquitetural

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
| `21` | state/persistence/retention |
| `20` | tests/gates |
| `23` | Cursor master prompt |
| `25` | requirements `CP-001…CP-316` |
| `67` | cross-cutting market/intelligence capability map |
| `68` | naming/product identity |
| ledger | current execution/evidence |

## 4. Specs temáticas ativas

```text
53 multimodal / Meeting / Frontline / industrial
54 biometric identity / Human Observation
55 Internet Research / external connectors
56 Microsoft Teams
57 Event-Driven Autonomous Operations / Automation Hub / Recurring Governed Work
58 Process Intelligence / Process Mining / Task Mining
59 AI Control Tower / Digital Workforce Governance
60 MCP / A2A / agent-tool interoperability
61 Personal Memory / Personalization
62 Semantic Business Layer / governed metrics
63 Analysis Sandbox / Artifact Workspace
64 Predictive / Prescriptive Intelligence / Operational Twin
65 Edge / Offline Industrial
66 AI Model Lifecycle / Capability Marketplace
```

Todas são subordinadas à precedência da seção 2. Nenhuma cria segunda requirement matrix, phase order, RBAC, workflow, planner ou business authority.

Cross-cutting docs fora da sequência temática:

```text
67 Market Capability Expansion / Intelligence Platform Map
68 DÉLIA Product Identity / Naming Authority
```

## 5. Reference-only / superseded

```text
31 = antiga migração de agents Chat — SUPERSEDED / REFERENCE_ONLY
45 = antiga extensão de tests — SUPERSEDED / REFERENCE_ONLY
46 = antiga extensão de requirements — SUPERSEDED / REFERENCE_ONLY
47 = antiga extensão de Cursor prompt — SUPERSEDED / REFERENCE_ONLY
```

Não atualizar essas specs como se fossem atuais; apenas manter status/link claramente histórico.

## 6. Authority boundaries não negociáveis

```text
Keycloak = identity / SSO
Core API = apps / routes / RBAC / governance
Domain APIs = dados / regras / autoridade final do domínio
Portal = host / navigation / published workspace context
DÉLIA = intelligence / operational context / Evidence / Policy / Decision / Work/RecurringWork orchestration
Automation Hub = technical execution
Physical scheduler/timer = technical time-trigger mechanism; owner proven in C0
External providers = external resource authority
OT/Safety = machine / industrial safety authority
```

Nenhum documento inferior pode fundir essas authorities por conveniência local.

Especialmente:

```text
schedule != permission
stored schedule intent != eternal authorization
physical scheduler != DÉLIA Work/Policy authority
Recurring Governed Work != Watch autonomous ACT
```

## 7. Findings arquiteturais corrigidos

### F1–F25 — foundations existentes

Já corrigidos anteriormente: single execution authority, shared primitives, standalone boundary, patterns, multimodal/biometric/privacy, safe Internet/connectors, Teams same runtime, Automation Hub not RPA-first, semantic executors, decision paths, event non-authority, verified Outcome, PREPARE!=ACT, capability-scoped autonomy e bounded computer-use.

### F26 — Process Intelligence poderia virar surveillance

`58`: Process Mining mede processo/event traces. Actor data é minimizado; task mining exige governance. Deviation não significa fraude/culpa/personality.

### F27 — Control Tower poderia virar super-admin de negócio

`59`: Control Tower governa assets, risk, health, evals, cost, rollout, incidents e kill switches; admin da Tower não ganha business permission.

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

### F38 — ACT governado confundido com autonomia avançada

`16/20/21/ledger`: C5 pode liberar `ACT` material para capabilities explicitamente autorizadas, com AuthZ, Decision/Policy, idempotência, audit e Outcome verification. C6 não habilita Watch autonomous ACT por default. C7 adiciona autonomia avançada/capability-scoped L5; não é o primeiro ponto em que qualquer ACT pode existir.

### F39 — documentação confundia produto e namespace técnico

Produto user-facing = **DÉLIA**. Freeze candidato C0.S1: `delia-api` / `plugins/delia` / `/apps/delia*`. Tokens `minha-delpi-copilot*` são `HISTORICAL`/`SUPERSEDED` como target ativo. Documentação em `docs/.../delia/` já usa namespace físico DÉLIA.

### F40 — prefixos `58/59` duplicavam responsabilidades distintas

A sequência temática foi normalizada para manter `58 = Process Intelligence` e `59 = AI Control Tower`. A visão transversal de expansão passou a `67` e a authority de naming passou a `68`, eliminando a colisão sem alterar a ordem temática `53–66`.

### F41 — scheduling previsto arquiteturalmente, mas não rastreado como produto de primeira classe

`57` já previa `timers/schedules`, `16` já inventariava schedulers e `55` já previa `communication.email.send`, porém faltavam lifecycle/contract/requirements explícitos para **Recurring Governed Work criado e gerenciado pelo usuário**.

Correção:

```text
CP-311–CP-316
+ 16 phase mapping
+ 17 ownership
+ 20 acceptance gates
+ 21 state candidates
+ 57 target semantics
+ 12/13/14/22/23/24/README/INDEX/ledger alignment
```

Resultado semântico:

```text
Recurring Governed Work = TARGET first-class capability
physical scheduler owner = TO_INVENTORY until C0 evidence
C5 = bounded recurring L4 governed ACT when live gates pass
C6 = schedule/admin UX; Watch remains no autonomous ACT by default
C7/L5 = not required for bounded C5 recurring ACT
runtime implementation = not PROVEN by documentation
```

A busca indexada por código/documentação não é authority de ausência: `search miss != feature absent`. Ausência material exige leitura direta das authorities prováveis antes de classificar.

## 8. Foundation invariants após C0.S7

```text
one DÉLIA API/runtime boundary
one DÉLIA MFE/product identity
Keycloak/Core/Domain/External/OT authorities preserved
Durable Work = one canonical DÉLIA work/orchestration authority
Recurring Governed Work = DÉLIA Work definition/lifecycle/correlation authority
Physical scheduler = technical time trigger only, not permission/Work authority
Automation Hub = technical execution, not second planner/workflow authority
Schedule != Permission
Stored Schedule Intent != Eternal Authorization
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
C5 governed ACT != C7 advanced autonomous ACT
Recurring Work C5 != Watch autonomous ACT C7
L5 default = OFF
OT safety remains external authority
Chat runtime dependency = 0
```

## 9. Documentation update protocol

Material architecture/product change updates, when applicable:

```text
16 order/phase mapping
17 owner/contracts
49 architecture/patterns
51 factual baseline if evidence changed
52 repository/bootstrap if physical target changed
21 state model
20 tests/gates
25 CP traceability
22 execution protocol
23 Cursor prompt
02/12/13/24/15 product/architecture/roadmap/catalog/integration views
08/09/11/14 security/UX/observability/DoD
relevant thematic specs
67/68 cross-cutting views when affected
README/INDEX
audit evidence
ledger
```

Documentation-only planning does not advance runtime phase.

## 10. Evidence taxonomy

Baseline factual:

```text
PROVEN
TO_INVENTORY
```

Planning/target:

```text
PLANNED
TARGET
```

Execution/test evidence:

```text
PASS
FAIL
PENDING
INCONCLUSIVE
TEST_NOT_RUN
STALE_EVIDENCE
```

Não usar documentação como prova de runtime. Nova evidência que invalida premissa anterior deve ser registrada como `EXECUTION_DRIFT`.

## 11. Market capability rule

External market availability != DELPI platform fact.

```text
Celonis Process Mining exists
!= DELPI has reusable process-mining runtime

MCP/A2A exist
!= repo contains approved infrastructure

Edge AI exists
!= factory devices/network support it

scheduler technology exists
!= DELPI has an approved reusable scheduler owner/contract
```

Somente evidência factual de repo/infra/contrato pode produzir `PROVEN` para foundations existentes. Reuse/implementação futura continua `TO_INVENTORY | PLANNED | TARGET` até decisão e prova correspondentes.

## 12. Anti-drift review checklist

Search/review all docs for:

```text
Minha DELPI Copilot used as product name instead of DÉLIA
old documentation path minha-delpi-copilot/
old CP upper range (<316)
old thematic range ending at 57
Chat runtime dependency
multiple execution order authorities
Keycloak/Core identity authority conflation
provider/executor/model/tool/scheduler hardcode in planner
RPA-first wording
second workflow/planner/RBAC
DÉLIA state duplicating Automation Hub technical execution state
DÉLIA state duplicating physical scheduler technical job truth
schedule/timer metadata treated as permission
stored schedule authorization treated as eternal
Recurring Work conflated with Watch autonomous ACT
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
all ACT incorrectly deferred to C7
Watch autonomous ACT before C7
global unrestricted L5
OT actuation implied by enterprise autonomy
broken/superseded links presented as active
duplicate numeric prefixes presented as one canonical sequence
```

## 13. Current governance state

```text
PROGRAM = PLANNED / NOT_STARTED
REQUIREMENTS = CP-001…CP-316
THEMATIC_SPECS = 53–66
CROSS_CUTTING = 67–68
C0.S0 = APPROVED
C0.S1 = APPROVED
C0.S2 = APPROVED
C0.S3 = APPROVED
C0.S4 = APPROVED
SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED
C0.S5 = CANDIDATE_FOR_ARCHITECTURE_REVIEW
INTEGRATION_CONTRACTS = FROZEN_CANDIDATE
C0.S6_AUTHORIZED = NO
FOUNDATION_FREEZE = NOT APPROVED
NEXT = ARCHITECTURE_REVIEW_C0_S5
RUNTIME_DIFF = NONE
```

C0.S0–C0.S4 estão aceitos. C0.S5 integration contracts está persistido como candidato (não aceito). Não autoriza C0.S6; não cria runtimes temáticos.
