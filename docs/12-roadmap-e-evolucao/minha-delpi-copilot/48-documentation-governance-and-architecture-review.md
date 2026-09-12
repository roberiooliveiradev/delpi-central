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
| `25` | requirements `CP-001…CP-154` |
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

## 5. Specs temáticas ativas

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
32 native Expertise runtime
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
44 operational intelligence thematic map
```

Specs não podem redefinir `16/50/49`.

## 6. Superseded/reference only

```text
31 old Chat agent-to-expertise migration plan
45 operational testing extension
46 operational requirements extension
47 Cursor operational extension
```

Esses arquivos existem apenas para compatibilidade/histórico. Não desbloqueiam trabalho nem tornam o Chat dependência do Copilot.

O documento `32` é **ativo** e descreve o runtime nativo de Expertise da Copilot API. O documento `44` também é **ativo como mapa temático**, mas é totalmente subordinado ao `16` e não cria uma segunda ordem.

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

Somente specs temáticas do step corrente.

Isso evita carregar 50+ docs a cada iteração sem perder authorities.

## 8. Architecture review findings

### F1 — Multiple execution authorities
E*/O* tracks podiam ser tratados como roadmaps. `16` é a única authority de ordem.

### F2 — Shared primitives introduced late
Entity/Evidence/Decision/Workflow/Event semantics foram antecipados para C0.

### F3 — Parallel confirmations/evidence/entities/events
Unificados em DecisionGate/EvidenceRef/EntityRef/EventEnvelope.

### F4 — Task/Case/Workflow engine duplication
Durable Workflow é runtime C5; Task/Case são unidades de produto C6 sobre esse runtime.

### F5 — Graph master-data risk
Graph armazena refs/relations/provenance; Domain APIs permanecem data owners. Runtime entra em C4.

### F6 — Architecture/patterns inferred per step
`49` congela layers/pattern matrix/Abstraction Gate antes de runtime features.

### F7 — Overengineering by AI
Interfaces/Strategy/Factory/Registry/etc. exigem evidence ou external boundary justification.

### F8 — Chat mistakenly treated as Copilot base
**Superseded architecture:** Copilot foi documentado inicialmente como evolução de `minha-delpi-ai-api`/`plugins/minha-delpi-chat`, com agent migration e dependência de Onda J.

**Current decision:** Copilot é aplicação standalone nova com API/MFE/persistence/deploy próprios. Chat é apenas sistema vizinho/reference-only.

### F9 — External Chat gate blocked Copilot
Removido. OpenAPI-first/Action Catalog/planner são construídos nativamente na Copilot API em C3/C4.

### F10 — Intelligence before application integration
Corrigido. C1 prova API/MFE/Core/Gateway/Portal independentes antes de C3 Intelligence Core.

### F11 — Portal boundary could become blurred
Portal é host/router/context/Platform Command executor. AI logic pertence à Copilot API.

### F12 — Shared infra versus product code
Reuse permitido para componentes neutros (`plugin-ui`, federation, Core, Gateway, Keycloak, approved shared libraries). Reuso de internals do Chat é proibido.

### F13 — Phase-number drift after standalone rebaseline
Specs temáticas antigas ainda referenciavam C2/C3/C4/C5 do roadmap anterior. A limpeza documental remapeou:

```text
Expertise/Knowledge/Multimodal/Evidence intelligence → C3
Business Reads/Graph → C4
Decision/write/Durable Workflow foundation → C5
Task/Case/Room/Inbox/Watch/Knowledge Learning/Studio → C6
Simulation/Model Router/selected autonomy → C7
```

Qualquer referência futura diferente precisa ser tratada como documentation drift e corrigida contra `16`.

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