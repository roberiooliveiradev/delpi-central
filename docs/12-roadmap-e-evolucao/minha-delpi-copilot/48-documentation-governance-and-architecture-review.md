# Minha DELPI Copilot — Governança Documental e Revisão Arquitetural

**Status:** canônico para leitura/precedência documental  
**Revisão:** foundation-first + architecture-pattern freeze  
**Ordem de execução:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Arquitetura/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)

## 1. Objetivo

Evitar que a quantidade de documentos gere:

- instruções duplicadas;
- duas ordens de implementação;
- requisitos com IDs concorrentes;
- matrizes de teste paralelas;
- arquitetura/design patterns inferidos de forma diferente por etapa;
- abstrações concorrentes para o mesmo problema;
- contexto excessivo no Cursor;
- retrabalho/refatoração previsível.

## 2. Precedência

Em caso de conflito:

```text
1. instruções oficiais do projeto + regras .cursor aplicáveis
2. 16-execution-master-plan.md              — ordem/dependências
3. 17-component-and-contract-map.md         — ownership/primitives
4. 49-architecture-and-design-patterns-standard.md — arquitetura de código/patterns
5. 21-data-and-state-model.md               — estado/persistência
6. 20-testing-and-acceptance-matrix.md       — gates/testes
7. 25-requirements-traceability.md           — CP requirements
8. 02-arquitetura.md                         — target técnico
9. 24-product-specification.md               — target funcional
10. specs temáticas da fase
11. evidence/execution-ledger.md             — estado/evidence corrente
```

O ledger não muda a arquitetura; registra o que está realmente executado e desbloqueado.

Uma spec temática não pode redefinir o style/pattern canônico de `49` sem decisão arquitetural explícita.

## 3. Leitura mínima por execução

Para reduzir tokens, o Cursor não precisa carregar todos os documentos em toda subetapa.

### Sempre ler

```text
instruções oficiais
regras .cursor aplicáveis
README
16 plano mestre
17 ownership/contracts
49 arquitetura/patterns — integral no C0; depois seções aplicáveis
20 tests aplicáveis
25 requirements aplicáveis
evidence ledger
```

### Ler quando a etapa tocar estado/persistence

```text
21-data-and-state-model.md
19-rollout-and-migrations.md
```

### Ler specs temáticas somente se no escopo

Exemplos:

- iframe → `26`;
- expertise → `27–33`;
- Business Graph → `35`;
- Tasks/Cases/Rooms → `36`;
- Inbox/Watch → `37`;
- Evidence → `38`;
- Decision/Simulation → `39`;
- Knowledge/Learning → `40`;
- Expertise Studio → `41`;
- Model Router → `42`;
- Durable Workflow → `43`.

## 4. Classificação dos documentos

### Authorities operacionais

| Arquivo | Authority |
|---|---|
| `16` | ordem C0–C7 e substeps |
| `17` | owners/primitives/contracts |
| `49` | architecture style, layers, dependency rules e design patterns |
| `20` | testes/gates |
| `21` | estado/persistência |
| `23` | prompt mestre Cursor |
| `25` | requisitos CP-* |
| ledger | execução/evidence atual |

### Authorities conceituais

| Arquivo | Papel |
|---|---|
| `02` | arquitetura alvo |
| `12` | roadmap macro |
| `13` | catálogo funcional |
| `14` | Definition of Done |
| `15` | integração com plataforma |
| `24` | especificação completa do produto |

### Specs temáticas

```text
03 capabilities
04 platform actions
05 workspace context
06 business parity
07 workflows
08 security
09 UX
10 AI-ready
11 observability
18 app matrix
19 rollout
26 iframe
27–33 single Copilot/expertise/playbooks/multimodal/migration/reference
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
44 operational detail map
```

Specs detalham o tema; não redefinem a ordem do `16` nem o padrão arquitetural do `49`.

### Superseded/reference only

```text
45 operational testing extension
46 operational requirements extension
47 Cursor operational extension
```

Seus conteúdos materiais foram consolidados respectivamente em `20`, `25`, `23`.

## 5. Findings da revisão foundation-first

### F1 — múltiplas autoridades de ordem

**Problema:** C0–C7, E0–E13 e O0–O13 podiam ser lidos como roadmaps independentes.

**Correção:** `16` é a única authority. E*/O* são mapeamentos temáticos.

### F2 — primitives introduzidos tarde

**Problema:** Evidence, Decision Gate, Entity Relationship, Workflow/Task/Case e Event semantics apareciam após features consumidoras.

**Risco:** refatoração de schemas, persistence e UI.

**Correção:** semântica/owner/ports de todos os primitives compartilhados foram movidos para C0. Runtime continua na fase adequada.

### F3 — confirmation e approval separados

**Problema:** write confirmation inicial e approval/Decision Gate posterior poderiam criar dois modelos.

**Correção:** um único `DecisionGate` compartilhado; UI simples de confirmação é uma apresentação desse modelo.

### F4 — Evidence duplicável por feature

**Problema:** multimodal, Graph, Workflow e Case poderiam criar evidence próprios.

**Correção:** `SourceRef/EvidenceRef/OutcomeRef` transversais em C0.

### F5 — Entity identity duplicável

**Problema:** Workspace, Graph, Deep Link e Case poderiam usar IDs/types incompatíveis.

**Correção:** `EntityRef` compartilhado + domain adapters; `RelationshipRef` para Graph.

### F6 — Workflow, Task e Case como motores distintos

**Problema:** risco de três orchestrators/persistences.

**Correção:** Durable Workflow é runtime; Task/Case são unidades/organizações de trabalho sobre o mesmo runtime/refs.

### F7 — Watch com event model próprio

**Problema:** Watch e wait_event poderiam divergir.

**Correção:** `EventEnvelope` compartilhado em C0.

### F8 — agents como gate técnico

**Problema:** operational tools e skills estavam acoplados a agent activation/handoff.

**Correção:** single Copilot; expertise orienta; availability vem de capabilities + RBAC + policy. Cutover ocorre somente após gates.

### F9 — Business Graph tarde demais

**Problema:** Graph estava em C5, depois de análises cross-domain que poderiam inventar outra entity-linking abstraction.

**Correção:** contracts de Entity/Relationship em C0 e runtime mínimo de Graph em C3 junto de reads.

### F10 — Decision Gates tarde demais

**Problema:** writes poderiam nascer com confirmation simples e migrar depois.

**Correção:** contract C0; engine C4 antes do primeiro write production-ready.

### F11 — Model Router cedo demais seria premature optimization

**Decisão:** permanece C7 após métricas reais de qualidade/custo/latência/privacy.

### F12 — Simulation sem owner de modelo

**Decisão:** permanece C7 e somente por domínio com cálculo/modelo reproduzível.

### F13 — design patterns e layering inferidos durante implementação

**Problema:** mesmo com bons contratos, cada subetapa poderia escolher `Service`, `Repository`, `Factory`, `Strategy`, evento, state handling ou organização frontend de forma diferente.

**Risco:** abstrações locais concorrentes, infra vazando para application/domain, overengineering, business state no frontend e refatorações estruturais posteriores.

**Correção:** `49` tornou-se authority normativa e C0 deve congelar style, layers, dependency rules, pattern matrix, error/event/state/persistence/frontend/testing/migration rules e Abstraction Gate.

### F14 — overengineering pela IA

**Problema:** modelos tendem a criar interfaces/factories/strategies registries “para o futuro”.

**Correção:** `Abstraction Gate` + Rule of Three para abstrações internas; boundary externo pode justificar Port desde a primeira implementação.

### F15 — migração legada sem padrão uniforme

**Problema:** agent migration e outras compatibilidades poderiam usar dual-read/fallbacks distintos.

**Correção:** Anti-Corruption Layer + Adapter + Strangler Fig + exit criteria + residual search são o padrão de migração.

## 6. Foundation invariants

Após C0.S6:

```text
um conceito compartilhado → um contrato canônico
um dado de negócio → um owner de domínio
um action técnico → OpenAPI/Action Catalog
uma permission → Core/RBAC/domain backend
um workflow runtime → orchestration canônica
um evidence model → EvidenceRef
um entity reference model → EntityRef
um decision model → DecisionGate
um event envelope → EventEnvelope
uma dependência externa → port/adapter quando boundary justificar
um lifecycle complexo → state machine owner
um wiring concreto → composition root/DI
um estado durável de negócio → backend owner
uma exceção arquitetural → decisão/ADR explícita
```

Qualquer feature que precisar quebrar essas invariantes deve abrir mudança arquitetural/versionada, não criar um tipo/pattern local silenciosamente.

## 7. Token efficiency

Para minimizar contexto no Cursor:

- executar uma subetapa por vez;
- usar `16` para saber **o que** vem agora;
- usar `17/21` para saber **quais foundations/state** reutilizar;
- usar `49` para decidir **como estruturar a implementação**, lendo só as seções aplicáveis após C0;
- usar somente a spec temática do step;
- usar `20` apenas nas seções aplicáveis;
- usar `25` apenas nos CP do step;
- ledger carrega somente evidence/status necessário;
- não reenviar o roadmap inteiro em todo prompt;
- não pedir à IA para “escolher a melhor arquitetura” se o padrão já estiver congelado.

## 8. Regra para documentos futuros

Novo documento precisa declarar no cabeçalho:

```text
Status: canonical authority | thematic spec | reference | superseded
Order authority: 16-execution-master-plan.md
Architecture authority: 49-architecture-and-design-patterns-standard.md quando houver runtime/code design
```

Novo documento temático não pode:

- criar nova sequência de fases;
- criar nova matriz CP;
- criar nova matriz de testes;
- criar outro prompt mestre do Cursor;
- redefinir primitive compartilhado sem versionamento/ADR;
- introduzir architectural style/pattern concorrente sem decisão explícita.

## 9. Estado após esta revisão

A documentação está conceitualmente organizada para iniciar por:

```text
C0.S0 inventory + architecture pattern inventory
→ C0.S1 authorities/bounded contexts
→ C0.S2 shared primitives
→ C0.S3 persistence/ports boundaries
→ C0.S4 cross-cutting semantics + architecture/pattern freeze
→ C0.S5 contract/conformance harness
→ C0.S6 FOUNDATION_FREEZE
```

Nenhuma feature runtime deve ser iniciada antes desse gate.