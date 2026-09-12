# Minha DELPI Copilot — Governança Documental e Revisão Arquitetural

**Status:** canônico para precedência documental  
**Revisão:** foundation-first + standalone application + multimodal/Meeting/Frontline boundary  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Evitar que a documentação gere ordens, owners, contracts, patterns ou product/privacy/safety boundaries concorrentes.

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
8. 21 — state/persistence/media refs
9. 20 — tests/gates
10. 25 — CP requirements
11. 02 — technical target
12. 24 — product target
13. thematic specs, incluindo 53
14. ledger — current execution/evidence
```

O ledger registra estado; não redefine arquitetura.

`53` detalha a visão multimodal/Meeting/Frontline/industrial, porém não cria ordem paralela ao `16` nem authority de safety diferente dos owners industriais.

## 3. Authorities operacionais

| Arquivo | Authority |
|---|---|
| `16` | ordem C0–C7/substeps |
| `50` | Copilot standalone boundary e relação com Chat |
| `17` | owners/primitives/contracts |
| `49` | code architecture/design patterns |
| `51` | baseline factual Portal/Core/APIs/MFEs/infra + gaps a inventariar |
| `52` | estrutura física/bootstrap standalone |
| `20` | tests/gates |
| `21` | state/persistence/media refs |
| `23` | prompt mestre Cursor |
| `25` | requirements `CP-001…CP-181` |
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
08 security/autonomy/privacy/safety
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
53 multimodal/Meeting/Frontline/industrial Copilot
```

Specs não podem redefinir `16/50/49` nem criar owner paralelo de RBAC/domain/industrial safety.

## 6. Superseded/reference only

```text
31 old Chat agent-to-expertise migration plan
45 operational testing extension
46 operational requirements extension
47 Cursor operational extension
```

Esses arquivos existem apenas para compatibilidade/histórico. Não desbloqueiam trabalho nem tornam o Chat dependência do Copilot.

O documento `32` é **ativo** e descreve o runtime nativo de Expertise da Copilot API. O documento `44` também é **ativo como mapa temático**, mas é totalmente subordinado ao `16`. O documento `53` é **ativo como spec temática** e sua sequência é materializada somente por `16`.

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
53 when media/device/privacy/Meeting/Frontline/OT is being inventoried (C0.S0 includes it)
```

### State/persistence/media retention

```text
21
53 when media lifecycle is material
```

### Feature implementation

Somente specs temáticas do step corrente; Meeting/Frontline/media steps sempre incluem `53`.

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
Portal é host/router/context/Platform Command executor. AI/media intelligence pertence à Copilot API.

### F12 — Shared infra versus product code
Reuse permitido para componentes neutros (`plugin-ui`, federation, Core, Gateway, Keycloak, approved shared libraries/media infrastructure). Reuso de internals do Chat é proibido.

### F13 — Phase-number drift after standalone rebaseline
Specs temáticas antigas ainda referenciavam fases do roadmap anterior. A limpeza documental remapeou tudo contra `16`.

### F14 — Multimodalidade poderia nascer como adição tardia
Corrigido. Media provider boundaries, consent/retention, realtime direction, shared-device isolation e provenance entram no C0 foundation inventory/freeze, mesmo que Meeting/Frontline completos só sejam entregues em C6/C7.

### F15 — Frontline poderia criar um segundo contexto/modelo de identidade
Corrigido. Contexto operacional reutiliza `WorkspaceContext + EntityRef`; device identity é separada de user identity e não concede permission. `FrontlineContext` paralelo é anti-pattern por default.

### F16 — Meeting poderia criar action executor paralelo
Corrigido. Fala/transcript/meeting action vira candidate e converge para o mesmo planner/Decision Gate/generic executor de C5.

### F17 — Mídia poderia virar armazenamento indiscriminado
Corrigido. `MediaRef` é apenas candidate primitive até C0 provar necessidade; transcript/raw-audio/raw-video/screen/derived Evidence têm retention classes próprias e data minimization é default.

### F18 — “Aprender com operador” poderia virar auto-learning não governado
Corrigido. Meeting/process/frontline observation gera candidate knowledge/Experience com Evidence → review → eval → version/publish.

### F19 — Autonomia empresarial poderia ser confundida com comando de máquina
Corrigido. Copilot não é safety controller; L5 não concede OT. Free-form LLM→PLC/CNC/robot é `BLOCK` até existir iniciativa industrial separada com deterministic commands, interlocks independentes, industrial owner e safety gate.

### F20 — Computer vision poderia virar authority de qualidade sem validação
Corrigido. Visual finding é Evidence/Hypothesis por default; critério oficial de inspeção/medição/quality owner permanece authoritative salvo capability automática explicitamente validada.

### F21 — Frontline poderia virar vigilância implícita
Corrigido. Hidden capture, facial recognition, emotion detection e hidden individual scoring/surveillance ficam fora do default scope e são blockers quando introduzidos sem decisão/policy explícita.

## 9. Foundation invariants

After C0.S7:

```text
one product runtime → Copilot API
one product MFE → Copilot MFE
four surfaces → same runtime/policy/state model
one platform RBAC authority → Core
one identity authority → Keycloak
one navigation authority → Portal
one business source → corresponding Domain API
one action technical source → Domain OpenAPI
one Copilot Action Catalog → derived inside Copilot
one Evidence model → EvidenceRef
one Entity ref model → EntityRef
one workspace context model → WorkspaceContext
MediaRef → only if C0 proves need
one Decision model → DecisionGate
one Workflow runtime → Copilot durable orchestration
one event envelope → EventEnvelope
one concrete wiring boundary → Composition Root
user identity != device identity
raw media retention → explicit class/policy only
process learning → candidate only until governed publish
industrial safety authority → external industrial owner
free-form LLM machine actuation → blocked
Chat runtime dependency → zero
```

## 10. Rule for future docs

Every new doc declares:

```text
Status: canonical authority | thematic spec | reference | superseded
Order authority: 16-execution-master-plan.md
Standalone boundary: 50 when runtime/product relevant
Multimodal/Meeting/Frontline: 53 when relevant
```

A thematic doc may not:

- create another phase sequence;
- create another CP matrix;
- create another test matrix;
- create another Cursor master prompt;
- redefine shared primitive silently;
- introduce Chat runtime dependency;
- move AI/media intelligence into Portal;
- create duplicate Core/domain authority;
- create separate Meeting/Frontline business executors;
- create `FrontlineContext` incompatible with WorkspaceContext;
- make capture implicit;
- make raw-media retention default;
- convert device identity into user authorization;
- create hidden surveillance;
- weaken industrial safety/interlocks;
- infer OT permission from Copilot autonomy.

## 11. Current executable state

```text
C0.S0 platform/monorepo/media/device/OT inventory
→ C0.S1 standalone boundary/names
→ C0.S2 authorities
→ C0.S3 primitives/MediaRef decision
→ C0.S4 architecture/persistence/privacy/media boundaries
→ C0.S5 integration contracts
→ C0.S6 RED harness incl. privacy/device/OT negatives
→ C0.S7 FOUNDATION_FREEZE
→ C1.S1 standalone API skeleton
```

No runtime implementation before that sequence permits it.