# Minha DELPI Copilot — Governança Documental e Revisão Arquitetural

**Status:** canônico para precedência documental  
**Revisão:** foundation-first + standalone application + multimodal/Meeting/Frontline + biometric/Human Observation boundary  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Evitar que a documentação gere ordens, owners, contracts, patterns ou product/privacy/identity/safety boundaries concorrentes.

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
8. 21 — state/persistence/media/biometric refs
9. 20 — tests/gates
10. 25 — CP requirements
11. 02 — technical target
12. 24 — product target
13. thematic specs, incluindo 53 e 54
14. ledger — current execution/evidence
```

O ledger registra estado; não redefine arquitetura.

`53` detalha a visão multimodal/Meeting/Frontline/industrial. `54` detalha biometric identity e Human Observation. Nenhum dos dois cria ordem paralela ao `16`, permission authority paralela ao Core ou safety authority paralela aos owners industriais.

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
| `21` | state/persistence/media/biometric refs |
| `23` | prompt mestre Cursor |
| `25` | requirements `CP-001…CP-193` |
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
08 security/autonomy/privacy/biometric/safety
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
54 biometric identity/Human Observation governance
```

Specs não podem redefinir `16/50/49`, criar owner paralelo de RBAC/domain/industrial safety ou transformar biometric association em identity/permission authority.

## 6. Superseded/reference only

```text
31 old Chat agent-to-expertise migration plan
45 operational testing extension
46 operational requirements extension
47 Cursor operational extension
```

Esses arquivos existem apenas para compatibilidade/histórico. Não desbloqueiam trabalho nem tornam o Chat dependência do Copilot.

O documento `32` é **ativo** e descreve o runtime nativo de Expertise da Copilot API. O documento `44` também é **ativo como mapa temático**, mas é totalmente subordinado ao `16`. `53` e `54` são **specs temáticas ativas**, com sequência materializada somente por `16`.

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
53 when media/device/privacy/Meeting/Frontline/OT is being inventoried
54 when photo/voice identity, enrollment, biometric storage, liveness or Human Observation is material
```

### State/persistence/media/biometric retention

```text
21
53 when media lifecycle is material
54 when biometric enrollment/template/person-observation lifecycle is material
```

### Feature implementation

Somente specs temáticas do step corrente. Meeting/Frontline/media steps incluem `53`; biometric/Human Observation steps incluem `54`.

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
Portal é host/router/context/Platform Command executor. AI/media/biometric intelligence pertence à Copilot API.

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
Corrigido. Hidden capture, hidden identity recognition e hidden individual scoring/surveillance são blockers. Captura e identity recognition precisam ser explícitas/policy-bound.

### F22 — Proibição total de reconhecimento facial bloquearia casos úteis de identidade
Corrigido. `54` substitui a proibição genérica por uma capability biométrica governada: **closed-set recognition/verification de usuários conhecidos/enrolled**, com purpose, template protection, confidence, unknown fallback, correction, revocation e liveness quando necessário.

Biometric match nunca se torna login/RBAC automaticamente.

### F23 — “Analisar pessoas” poderia virar inferência subjetiva/sensível
Corrigido. Human Observation pode analisar comportamentos **observáveis e relacionados ao processo**, produzindo Evidence/Hypothesis. Personality, honesty/trustworthiness, emotion-as-truth, health/diagnosis, sensitive attributes e global professional fitness ficam fora do comportamento default.

### F24 — Biometria poderia contaminar decisão trabalhista
Corrigido. Biometric/Human Observation não são authority automática de contratação, promoção, punição, remuneração, avaliação formal, suspensão ou desligamento. Evidence operacional pode subsidiar processo humano separado sob owner/governance adequados.

## 9. Foundation invariants

After C0.S7:

```text
one product runtime → Copilot API
one product MFE → Copilot MFE
four surfaces → same runtime/policy/state model
one platform RBAC authority → Core
one corporate identity authority → Keycloak/Core
biometric identity → candidate association only
one navigation authority → Portal
one business source → corresponding Domain API
one action technical source → Domain OpenAPI
one Copilot Action Catalog → derived inside Copilot
one Evidence model → EvidenceRef
one Entity ref model → EntityRef
one workspace context model → WorkspaceContext
MediaRef → only if C0 proves need
Biometric refs → only if C0 proves need
one Decision model → DecisionGate
one Workflow runtime → Copilot durable orchestration
one event envelope → EventEnvelope
one concrete wiring boundary → Composition Root
user identity != device identity
biometric candidate != authenticated session
raw media/template retention → explicit class/policy only
Human Observation → observable process evidence only
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
Biometric/Human Observation: 54 when relevant
```

A thematic doc may not:

- create another phase sequence;
- create another CP matrix;
- create another test matrix;
- create another Cursor master prompt;
- redefine shared primitive silently;
- introduce Chat runtime dependency;
- move AI/media/biometric intelligence into Portal;
- create duplicate Core/domain/user authority;
- create separate Meeting/Frontline business executors;
- create `FrontlineContext` incompatible with WorkspaceContext;
- make capture/identity recognition implicit;
- make raw-media/biometric-template retention default;
- convert device/biometric candidate into user authorization;
- introduce open-world person recognition without explicit new governance decision;
- infer personality/emotion/honesty/health/sensitive attributes from biometrics as product truth;
- create hidden worker scoring/profiling;
- create automatic employment decision from biometrics/Human Observation;
- weaken industrial safety/interlocks;
- infer OT permission from Copilot autonomy.

## 11. Current executable state

```text
C0.S0 platform/monorepo/media/device/biometric/OT inventory
→ C0.S1 standalone boundary/names
→ C0.S2 authorities
→ C0.S3 primitives/MediaRef/biometric-ref decisions
→ C0.S4 architecture/persistence/privacy/media/biometric boundaries
→ C0.S5 integration contracts
→ C0.S6 RED harness incl. privacy/device/biometric/OT negatives
→ C0.S7 FOUNDATION_FREEZE
→ C1.S1 standalone API skeleton
```

No runtime implementation before that sequence permits it.
