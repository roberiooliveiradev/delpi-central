# Minha DELPI Copilot — Governança Documental e Revisão Arquitetural

**Status:** canônico para precedência documental  
**Revisão:** foundation-first + standalone application boundary  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Evitar que a documentação gere ordens, owners, contracts, patterns ou product boundaries concorrentes.

## 2. Precedência

Em caso de conflito:

```text
1. instruções oficiais + .cursor rules
2. 16 — ordem/dependências
3. 50 — standalone product/runtime boundary
4. 17 — ownership/primitives/contracts
5. 49 — architecture/patterns
6. 51 — factual platform integration baseline
7. 52 — repository/bootstrap target
8. 21 — state/persistence
9. 20 — tests/gates
10. 25 — CP requirements
11. 02 — technical target
12. 24 — product target
13. thematic specs
14. ledger — current execution/evidence
```

O ledger registra estado; não redefine arquitetura.

## 3. Authorities operacionais

| Arquivo | Authority |
|---|---|
| `16` | ordem C0–C7/substeps |
| `50` | Copilot standalone boundary e relação com Chat |
| `17` | owners/primitives/contracts |
| `49` | code architecture/design patterns |
| `51` | baseline factual Portal/Core/APIs/MFEs/infra |
| `52` | estrutura física/bootstrap standalone |
| `20` | tests/gates |
| `21` | state/persistence |
| `23` | prompt mestre Cursor |
| `25` | requirements CP-* |
| ledger | execution/evidence current |

## 4. Authorities conceituais

| Arquivo | Papel |
|---|---|
| `01` | visão de produto |
| `02` | arquitetura alvo |
| `12` | roadmap macro |
| `13` | catálogo funcional |
| `14` | DoD |
| `15` | integration map |
| `19` | rollout/migrations |
| `24` | product specification |

## 5. Specs temáticas

```text
03 capability model
04 platform actions
05 workspace context
06 business parity
07 workflows
08 security/autonomy
09 UX
10 AI-ready
11 observability/evals
18 onboarding matrix
26 iframe
27–30 single Copilot/expertise/playbooks/multimodal
33 reference expertise pilots
34 benchmark
35 Business Graph
36 Tasks/Cases/Rooms
37 Inbox/Watch
38 Evidence
39 Decision/Simulation
40 Knowledge/Learning
41 Expertise Studio
42 Model Router
43 Durable Workflow
```

Specs não podem redefinir `16/50/49`.

## 6. Superseded/reference only

```text
31 agent-to-expertise migration of Chat
32 expertise migration plan tied to old Chat runtime
44 old operational track ordering
45 operational testing extension
46 operational requirements extension
47 Cursor operational extension
```

Conteúdo conceitual útil pode permanecer como histórico, mas nenhuma dessas fontes desbloqueia trabalho nem torna o Chat dependência do Copilot.

`31` e os trechos antigos de `32` sobre agents do Chat são explicitamente fora do novo product boundary.

## 7. Reading minimization

### Sempre

```text
official rules
applicable .cursor rules
README
16
50
17
49
20 applicable section
25 applicable CPs
ledger
```

### C0/C1 integration

```text
51
52
02
19 when infra/deploy/migration is involved
```

### State/persistence

```text
21
```

### Feature implementation

Only thematic specs relevant to the current step.

This prevents reading 50+ docs every iteration.

## 8. Architecture review findings

### F1 — Multiple execution authorities
E*/O* tracks could be treated as roadmaps. `16` is now the only order authority.

### F2 — Shared primitives introduced late
Entity/Evidence/Decision/Workflow/Event semantics moved to C0.

### F3 — Parallel confirmations/evidence/entities/events
Unified into DecisionGate/EvidenceRef/EntityRef/EventEnvelope.

### F4 — Task/Case/Workflow engine duplication
Durable Workflow is runtime; Task/Case are product units over that runtime.

### F5 — Graph master-data risk
Graph stores refs/relations/provenance; Domain APIs remain data owners.

### F6 — Architecture/patterns inferred per step
`49` freezes layers/pattern matrix/Abstraction Gate before runtime features.

### F7 — Overengineering by AI
Interfaces/Strategy/Factory/Registry/etc. require evidence or external boundary justification.

### F8 — Chat mistakenly treated as Copilot base
**Superseded architecture:** Copilot was previously documented as evolution of `minha-delpi-ai-api`/`plugins/minha-delpi-chat`, with agent migration and Onda J dependency.

**Current decision:** Copilot is a new standalone application with own API/MFE/persistence/deploy. Chat is only a neighboring/reference system.

### F9 — External Chat gate blocked Copilot
Removed. OpenAPI-first/Action Catalog/planner are built natively in the Copilot API.

### F10 — Intelligence before application integration
Corrected. C1 proves standalone API/MFE/Core/Gateway/Portal integration before C3 Intelligence Core.

### F11 — Portal boundary could become blurred
Portal is host/router/context/command executor only. AI logic belongs to Copilot API.

### F12 — Shared infra versus product code
Reuse is allowed for neutral platform components (`plugin-ui`, federation, Core, Gateway, Keycloak, approved shared libraries). Reusing Chat product internals is prohibited.

## 9. Foundation invariants

After C0.S7:

```text
one product runtime → Copilot API
one product MFE → Copilot MFE
one platform RBAC authority → Core
one identity authority → Keycloak
one navigation authority → Portal
one business source → corresponding Domain API
one action technical source → Domain OpenAPI
one Copilot Action Catalog → derived inside Copilot
one Evidence model → EvidenceRef
one Entity ref model → EntityRef
one Decision model → DecisionGate
one Workflow runtime → Copilot durable orchestration
one event envelope → EventEnvelope
one concrete wiring boundary → Composition Root
Chat runtime dependency → zero
```

## 10. Rule for future docs

Every new doc declares:

```text
Status: canonical authority | thematic spec | reference | superseded
Order authority: 16-execution-master-plan.md
Standalone boundary: 50 when runtime/product relevant
```

A thematic doc may not:

- create another phase sequence;
- create another CP matrix;
- create another test matrix;
- create another Cursor master prompt;
- redefine shared primitive silently;
- introduce Chat runtime dependency;
- move AI logic into Portal;
- create duplicate Core/domain authority.

## 11. Current executable state

```text
C0.S0 platform/monorepo inventory
→ C0.S1 standalone boundary/names
→ C0.S2 authorities
→ C0.S3 primitives
→ C0.S4 architecture/persistence
→ C0.S5 integration contracts
→ C0.S6 RED harness
→ C0.S7 FOUNDATION_FREEZE
→ C1.S1 standalone API skeleton
```

No runtime implementation before that sequence permits it.