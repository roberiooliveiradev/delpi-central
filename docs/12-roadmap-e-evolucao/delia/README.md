# DÉLIA — DELPI · Ecossistema de Ligações, Inteligência e Automação

> **Status:** `PLANNED / NOT_STARTED`
> **Produto:** aplicação nova e standalone de Continuous Operational Intelligence
> **Requirements:** `CP-001…CP-316`
> **Specs temáticas:** `53–66`
> **Próxima etapa:** `ARCHITECTURE_REVIEW_C0_S6` (`C0.S0..=C0.S5=APPROVED`; `C0.S6=CANDIDATE_FOR_ARCHITECTURE_REVIEW`; `RED_HARNESS=FROZEN_CANDIDATE`; `C0.S7_AUTHORIZED=NO`)
> **Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)
> **Execution state:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)
> **Naming authority:** [`68-delia-product-identity-and-naming.md`](./68-delia-product-identity-and-naming.md)

## 1. Decisão fundamental

A **DÉLIA não é uma expansão do Minha DELPI Chat**.

```text
Minha DELPI Chat                  DÉLIA
-------------------------------   --------------------------------
plugins/minha-delpi-chat          plugins/delia                      # FROZEN_CANDIDATE C0.S1
minha-delpi-ai-api                delia-api                          # FROZEN_CANDIDATE C0.S1
Chat state/runtime                own state/runtime
Chat release                      independent release

                 NO RUNTIME DEPENDENCY
```

Paths ativos alvo: `delia-api/` + `plugins/delia/` + `/apps/delia*`. Tokens `minha-delpi-copilot*` são `HISTORICAL`/`SUPERSEDED` como target ativo. Não é o nome do produto.

## 2. North Star

> **Uma única DÉLIA para escritório, reuniões, chão de fábrica, fontes externas e operações governadas, capaz de perceber eventos e tempo, entender contexto/dados/processos, pesquisar, analisar, prever, simular, decidir sob políticas, preparar/executar trabalho pontual ou recorrente, verificar resultados, comunicar e aprender sob governança.**

```text
PERCEBER
→ ENTENDER
→ PESQUISAR
→ ANALISAR
→ PREVER/SIMULAR
→ DECIDIR
→ PREPARAR/EXECUTAR
→ VERIFICAR OUTCOME
→ COMUNICAR
→ APRENDER COM GOVERNANÇA
```

Não é “Chat + RAG”.

## 3. Surfaces

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
TEAMS future surface
BACKGROUND Watches/Workflows/Recurring Work
ADMIN governance surfaces
```

Mesma identidade de produto, Policy/Decision/Work semantics e runtime da DÉLIA quando cada surface for implementada. Surface não cria segundo planner, workflow ou permission authority.

## 4. Capability map

```text
Conversation / Context
Expertise / Playbooks / Knowledge
Personal Memory / Personalization
Multimodal / Voice / Biometric
Internet Research / External Connectors / Teams
Business Actions / Business Graph
Semantic Business Layer
Event / Decision Intelligence
Process Intelligence / Process Mining
Automation Hub / RPA / Computer-use execution boundaries
Durable Work / Recurring Governed Work / Tasks / Cases / Rooms / Inbox / Watch
Analysis Sandbox / Artifact Workspace
Predictive / Prescriptive Intelligence
Operational Twin / Simulation
MCP / A2A interoperability
AI Control Tower
AI Model Lifecycle / MLOps
Capability Marketplace
Edge / Offline Industrial
Meeting / Frontline
Evidence / Outcome / Evals / Governance
```

## 5. Fundamental boundaries

```text
Keycloak = identity / SSO
Core API = apps / routes / RBAC / governance
Domain APIs = business data / rules / final domain authority
Portal = host / navigation / published workspace context
DÉLIA = intelligence / operational context / Evidence / Policy / Decision / Work orchestration
Automation Hub = technical execution
Physical scheduler/timer = technical time-trigger mechanism; owner to inventory in C0
External providers = external-resource authority
OT/safety systems = machine/safety authority
```

E:

```text
Personal Memory != Organizational Knowledge
Business Graph != Semantic Business Layer
Prediction != FACT
Recommendation != Authorization
Simulate != Apply
Twin != source of truth
PREPARE != ACT
Read != Write
Draft != Send
Schedule != Permission
Stored Schedule Intent != Eternal Authorization
Recurring Governed Work != Watch Autonomous ACT
Technical Success != Verified Business Outcome
MCP/A2A Discovery != Approval
Marketplace Install != Permission
Edge Offline != Wider Authority
```

## 6. Automation principle

DÉLIA decide/orquestra sob policy; Automation Hub executa tecnicamente. Um scheduler/timer, quando comprovado, apenas materializa o trigger temporal; ele não possui Work, business decision ou permission authority.

Preferência default de executor:

```text
Official API
→ native integration
→ deterministic function/script
→ RPA
→ governed computer-use
→ Human Task
```

Planner usa capabilities semânticas, nunca clicks/selectors.

C5 pode liberar `ACT` governado para capabilities explicitamente autorizadas. Isso inclui Recurring Governed Work bounded quando cada ocorrência revalida identidade/AuthZ/Policy/Decision/idempotência/Outcome. C6 mantém Watch sem ACT autônomo por default. C7 adiciona autonomia avançada/Watch autonomous ACT/L5 capability-scoped; não é o primeiro momento em que qualquer ACT pode existir.

Exemplo target de primeira classe:

```text
“todos os dias às 09:00 gere o relatório de produção do dia anterior e envie por email”
→ Recurring Governed Work persistente
→ deterministic time trigger
→ live authorization per occurrence
→ current authorized reads
→ report artifact
→ separate governed communication.email.send
→ verified Outcome/Evidence/Audit
```

A capability é `TARGET`; o scheduler físico/owner permanece `TO_INVENTORY` até C0 provar a infraestrutura e o contrato. Documentação não prova runtime implementado.

## 7. Process / Data intelligence

```text
Business Graph       → relações
Semantic Layer       → significado/cálculo oficial de métricas
Process Intelligence → comportamento real do processo a partir de eventos válidos
Operational Twin     → projeção/cenário
```

Cada responsabilidade permanece separada e nenhuma vira master data apenas por conveniência.

## 8. AI governance

AI Control Tower governa assets/models/automations/connectors/tools/agents/Edge deployments com owner/risk/evals/health/cost/value/incidents/rollout/kill switches.

Model lifecycle e Marketplace assets são versionados/reviewed/revocable. Acesso administrativo/catalog não concede business permission.

## 9. Personalization

Personal Memory pode lembrar preferências e continuidade de trabalho quando governada. Permanece privada por default e nunca substitui live business facts, Policy ou RBAC.

Knowledge organizacional segue `Evidence → candidate → owner/review → eval → version → publish`; nada vira corporate truth automaticamente.

## 10. Industrial/Edge direction

Frontline pode usar voice/camera/current procedures/operational context e, se fases futuras provarem necessidade e segurança, Edge/offline cache/inference/event buffering governados.

DÉLIA/Edge/RPA **não são safety controllers**. Free-form LLM/voice/vision → PLC/CNC/robot/machine e AI safety override são proibidos por default.

## 11. Canonical authorities

Ler nesta ordem:

1. official project instructions + `.cursor` rules;
2. [`16`](./16-execution-master-plan.md) — single C0–C7 order;
3. [`50`](./50-standalone-copilot-application-architecture.md) — standalone boundary;
4. [`17`](./17-component-and-contract-map.md) — owners/contracts;
5. [`49`](./49-architecture-and-design-patterns-standard.md) — code architecture/patterns;
6. [`51`](./51-platform-integration-baseline.md) — factual baseline;
7. [`52`](./52-standalone-repository-and-bootstrap-plan.md) — physical/bootstrap target;
8. [`21`](./21-data-and-state-model.md) — state/persistence;
9. [`20`](./20-testing-and-acceptance-matrix.md) — tests/gates;
10. [`25`](./25-requirements-traceability.md) — `CP-*` authority;
11. technical architecture / product spec;
12. thematic specs `53–66`;
13. execution ledger — actual execution evidence/status.

Full index: [`INDEX.md`](./INDEX.md).

## 12. Thematic specs

```text
53 Multimodal / Meeting / Frontline / Industrial
54 Biometric Identity / Human Observation
55 Internet Research / External Connectors
56 Microsoft Teams
57 Event-Driven Autonomous Operations / Automation Hub / Recurring Governed Work
58 Process Intelligence / Process Mining
59 AI Control Tower
60 MCP / A2A / Tool-Agent Interoperability
61 Personal Memory / Personalization
62 Semantic Business Layer
63 Analysis Sandbox / Artifact Workspace
64 Predictive / Prescriptive / Operational Twin
65 Edge / Offline Industrial
66 AI Model Lifecycle / Capability Marketplace
```

Cross-cutting views:

```text
67 Market Capability Expansion / Intelligence Platform Map
68 DÉLIA Product Identity / Naming Authority
```

## 13. Current execution state

```text
PROGRAM = PLANNED / NOT_STARTED
C0 = NOT_STARTED
C0.S0 = APPROVED
C0.S1 = APPROVED
C0.S2 = APPROVED
C0.S3 = APPROVED
C0.S4 = APPROVED
C0.S5 = APPROVED
SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED
INTEGRATION_CONTRACTS = FROZEN_ACCEPTED
C0.S6 = CANDIDATE_FOR_ARCHITECTURE_REVIEW
RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS = FROZEN_CANDIDATE
C0.S7_AUTHORIZED = NO
FOUNDATION_FREEZE = NOT APPROVED
RUNTIME_DIFF = NONE
NEW_RUNTIME_ABSTRACTIONS = NONE
NEXT = ARCHITECTURE_REVIEW_C0_S6
```

A formalização de `CP-311–CP-316` é documentação/planejamento. Não altera os estados acima nem prova scheduler, email provider ou Recurring Work runtime.
