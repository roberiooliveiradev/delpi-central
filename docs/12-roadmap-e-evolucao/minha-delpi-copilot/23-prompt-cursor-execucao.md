# Prompt mestre — Cursor — Minha DELPI Copilot

Você deve implementar o **Minha DELPI Copilot** de forma incremental, seguindo integralmente a documentação canônica do repositório, sem criar arquitetura paralela e sem pular gates.

## 1. Autoridades obrigatórias

Leia antes de qualquer alteração:

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`;
2. `.cursor/rules/development-standards-index.mdc` e regras aplicáveis de planning, execution, tests, security, OpenAPI, AI e Clean Architecture;
3. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`;
4. `16-execution-master-plan.md`;
5. `17-component-and-contract-map.md`;
6. `18-app-onboarding-matrix.md`;
7. `19-rollout-and-migrations.md`;
8. `20-testing-and-acceptance-matrix.md`;
9. `21-data-and-state-model.md`;
10. `22-cursor-execution-protocol.md`;
11. `24-product-specification.md`;
12. `25-requirements-traceability.md`;
13. `26-iframe-copilot-bridge.md`;
14. `27-single-copilot-specialization-architecture.md`;
15. `28-expertise-pack-specification.md`;
16. `29-domain-playbooks-specification.md`;
17. `30-multimodal-expertise-and-drawing-analysis.md`;
18. `31-agent-to-expertise-migration-plan.md`;
19. `32-expertise-runtime-implementation-plan.md`;
20. `33-reference-expertise-packs-quality-engineering.md`;
21. `34-market-benchmark-and-product-north-star.md`;
22. `35-delpi-business-graph.md`;
23. `36-copilot-tasks-cases-and-interaction-rooms.md`;
24. `37-copilot-inbox-watch-and-proactive-work.md`;
25. `38-evidence-provenance-and-epistemic-ux.md`;
26. `39-decision-gates-and-what-if-simulation.md`;
27. `40-organizational-knowledge-and-governed-learning.md`;
28. `41-expertise-studio-governance.md`;
29. `42-model-router-and-compute-policy.md`;
30. `43-durable-workflow-runtime.md`;
31. `44-operational-intelligence-implementation-plan.md`;
32. `45-operational-intelligence-testing-gates.md`;
33. `46-operational-intelligence-requirements.md`;
34. `47-cursor-operational-intelligence-extension.md`;
35. `evidence/execution-ledger.md`.

Também leia a documentação vigente do componente real que será alterado.

## 2. North Star

Construir o Copilot como **camada inteligente operacional da Minha DELPI**:

```text
PERGUNTAR
→ entender / pesquisar / explicar / analisar

FAZER
→ abrir / consultar / criar / alterar / aprovar / executar

ACOMPANHAR
→ monitorar / detectar / lembrar / alertar / reagir

TRABALHAR
→ investigar / colaborar / planejar / acompanhar ações / concluir
```

O chat é a interface de linguagem natural, não a única unidade de trabalho.

## 3. Copilot único

O produto final possui **um único Minha DELPI Copilot**.

Não criar agentes por departamento como novo core.

```text
usuário
→ Copilot único
→ understanding
→ authorized capability retrieval
→ expertise retrieval
→ playbook retrieval
→ knowledge / multimodal tools
→ planner
→ policy
→ execution
```

Engenharia, Qualidade, Suprimentos, Comercial, Financeiro, RH, TI e outros entram como:

- Expertise Packs;
- Domain Playbooks;
- knowledge scopes;
- terminology/guidance;
- capabilities autorizadas;
- multimodal tools;
- project preferences quando aplicável.

Nenhum desses itens concede permission.

## 4. Arquitetura obrigatória

```text
Business Actions
→ OpenAPI + Action Catalog
→ validator/policy/Decision Gate
→ executor genérico

Platform Actions
→ /me/apps + authorized routes
→ Platform Capability Projection
→ PlatformCommand
→ CopilotBridge
→ Router/MFE/IframeBridge

Workspace Context
→ MFE OU IframeBridge
→ Portal context store
→ bounded structured context

Expertise/Playbooks
→ semantic retrieval
→ bounded specialization context
→ planner

Business Graph
→ EntityRef/RelationshipRef
→ planning/traversal
→ source APIs remain data authorities

Evidence Layer
→ source result/document
→ EvidenceRef/Claim
→ analysis/case/artifact

Tasks/Cases/Rooms
→ product work containers
→ WorkflowPlan / Durable Workflow

Inbox/Watch
→ pending work / events / advice / controlled act

Durable Workflow Runtime
→ checkpoints / wait / resume / revalidate
```

## 5. Não criar

- segundo motor de IA/planner/tools;
- agente independente por departamento como arquitetura final;
- catálogo manual central de endpoints;
- lista manual app→URL;
- selector semântico baseado em path/operationId/provider;
- DOM automation quando existe API/use case;
- permission model próprio do Copilot;
- novo HTTP executor paralelo para workflows;
- Business Graph duplicando datasets inteiros;
- Case duplicando domínio existente sem inventário;
- event bus paralelo sem provar necessidade;
- Watch por polling app-specific como arquitetura final;
- confirmação antiga válida para payload novo;
- Simulation que executa write;
- auto-publicação de Experience Knowledge;
- Expertise Studio como agent builder;
- Model Router sem baseline/evals;
- memória paralela por app;
- chain-of-thought persistida;
- transmissão de JWT/refresh token pelo iframe bridge.

## 6. Dependência OpenAPI-first

A iniciativa vigente de desacoplamento LLM/OpenAPI está documentada com gates ainda abertos.

Não mascarar isso.

```text
C0-C2
→ podem avançar

C3 scaffolding/tests
→ pode avançar sem declarar production-ready

C3+ Business Actions production-ready
→ dependem dos gates OpenAPI-first/tool/eval relevantes PASS
```

Não reimplementar a correção dentro do Copilot.

## 7. Ordem obrigatória

Comece sempre em:

```text
C0.S0 — Rebaseline e inventário real
```

Depois siga o grafo de `16-execution-master-plan.md`.

Os componentes estratégicos `O0–O13` de `44-operational-intelligence-implementation-plan.md` são **extensão dependente** do plano C0–C7 e não substituem essa ordem.

## 8. C0.S0 — inventário obrigatório

Antes de editar runtime:

1. capture `git status` e HEAD;
2. inventarie Portal, Core, AI API, Chat MFE, manifests, APIs e infraestrutura real;
3. inventarie apps iframe/external;
4. inventarie agents/skills/specialization/handoff existentes;
5. inventarie canonical entity IDs e relações cross-domain;
6. inventarie event bus/eventos;
7. inventarie background jobs/queues/workers;
8. inventarie notification/inbox patterns;
9. inventarie interaction rooms/chats existentes;
10. inventarie approval/confirmation models;
11. inventarie workflow persistence/checkpoints;
12. inventarie audit/provenance metadata;
13. inventarie knowledge sources/lifecycle;
14. inventarie model/provider abstractions e métricas;
15. identifique producer/consumer/owner;
16. atualize matrizes/docs/ledger com evidence;
17. somente então libere C0.S1.

Onde não houver prova, use `TO_INVENTORY`/`NOT_PROVEN`.

Classifique estruturas potencialmente reutilizáveis:

```text
REUSE
EXTEND
MIGRATE
CREATE_REQUIRED
DEPRECATE
REMOVE
NOT_PROVEN
OUT_OF_SCOPE_WITH_DECISION
```

## 9. Reuse-first

Antes de criar componentes novos, procurar e avaliar:

- Minhas Solicitações para Task/Case-like state;
- salas de interação existentes;
- notification/event-driven infrastructure;
- background workers/workflows existentes;
- Core audit logs;
- entity/deep-link contracts;
- current AI memory/result refs;
- confirmation/policy atual;
- existing model config/services.

A visão estratégica não justifica duplicação.

## 10. Capability Projection

Business capability:

```text
Action Catalog authority
→ projection para discovery/retrieval/UX
→ sourceRef
→ executor volta à authority
```

Platform capability:

```text
Core /me/apps
+ tipos genéricos do Shell
→ projection
```

Não copiar path/method/operationId/schema para catálogo manual de capability.

## 11. Expertise e Playbooks

Expertise responde **como analisar**; Capability responde **o que pode executar**; Playbook responde **como conduzir um método/processo**.

```text
Capability = operação
Expertise = conhecimento/metodologia
Playbook = método/processo
Workflow = execução concreta
```

Expertise/Playbook não concedem autorização e não armazenam catálogo técnico de APIs.

## 12. Business Graph

Regras:

- graph contém refs/relationships;
- APIs owners continuam fontes atuais;
- relation possui provenance/confidence;
- inferred ≠ authoritative;
- traversal respeita RBAC;
- novo relation/entity type não exige patch no planner central.

## 13. Evidence/Provenance

Toda análise material deve distinguir:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Preservar quando aplicável:

```text
sourceRef
entityRef
observedAt
freshness
confidence
limitations
```

Não inventar evidence/source inexistente.

## 14. Iframe Copilot Bridge

Classifique cada app:

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

- validar origin/source/appId/protocol/version/session/schema;
- contexto do iframe não é permission;
- comando visual não substitui Business Action;
- JWT/refresh token não viaja pelo bridge;
- segundo iframe compatível deve funcionar sem patch específico.

## 15. Tasks / Cases / Rooms

- Task: objetivo multi-step delimitado;
- Case: investigação/processo persistente;
- Room: colaboração ligada a Task/Case;
- persistir estado operacional, evidence e decisões, não CoT;
- acesso ao Case/Room não concede acesso às entidades fonte;
- lifecycle/audit obrigatórios.

## 16. Inbox / Watch

Inbox:

```text
waiting_for_user
working
completed
alerts
```

Watch:

```text
OBSERVE
ADVISE
ACT
```

- preferir eventos a polling;
- dedupe/cooldown;
- revalidar permission no trigger;
- `ACT` somente após autonomy/Decision Gate correspondente.

## 17. Durable Workflow

Long-running flow deve usar estado/checkpoint:

```text
execute
→ checkpoint
→ wait_user | wait_approval | wait_event | wait_time
→ revalidate
→ resume
```

Não manter request aberto por horas e não reexecutar prompt inteiro como estratégia de resume.

Writes:

```text
retry somente com idempotência/verification
```

## 18. Decision Gates

Migrar confirmação conforme risco:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Alteração material em args/evidence/policy invalida gate anterior.

## 19. Simulation

```text
baseline
+ explicit assumptions
+ governed model/calculation
→ projected outputs
```

- preferir regra/modelo determinístico owner;
- LLM explica/estrutura, não inventa números;
- `simulate` nunca faz write;
- `apply` é Business Action separada e revalidada.

## 20. Organizational Knowledge

Separar:

```text
Reference
Operational
Decision
Experience
Semantic
```

Feedback não altera produção automaticamente.

Experience/Solution Pattern:

```text
candidate
→ review
→ eval
→ versioned publish
```

## 21. Expertise Studio

Não é agent builder.

Lifecycle:

```text
DRAFT → REVIEW → TESTING → APPROVED → PUBLISHED → DEPRECATED/RETIRED
```

Publish exige schema/evals/version/audit/rollback.

## 22. Model Router

Somente após baseline de qualidade/custo/latência.

Classes conceituais:

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
```

Routing deve respeitar privacy/provider policy; fallback não relaxa safety.

## 23. Workspace Context

Contexto bounded e tipado:

```text
appId
routeId
entityRefs
filters
selection
dateRange
visibleDataRefs
```

Não enviar estado React/DOM inteiro. Contexto não é permission.

## 24. Business Actions

```text
intenção
→ grounded args
→ schema validation
→ RBAC/policy
→ preview/Decision Gate
→ revalidation
→ generic execute
→ verify outcome
→ evidence/audit
```

UI e Copilot convergem no mesmo API/use case.

## 25. Workflows

Representar plano operacional, não raciocínio privado.

Cada step possui:

- capabilityRef;
- dependencies;
- status;
- confirmation/decision boundary;
- expected outcome;
- evidence/result refs quando aplicável.

Paralelizar apenas reads independentes e seguros.

## 26. Testes

Use `20-testing-and-acceptance-matrix.md` e `45-operational-intelligence-testing-gates.md`.

Conforme a etapa, provar:

- positive;
- sibling;
- negative;
- unauthorized;
- TOCTOU;
- injection;
- send/stream parity;
- reload/F5;
- unknown OpenAPI;
- true metamorphic rename;
- required/type/enum/path/query/body;
- confirmation/idempotency;
- compound/partial failure;
- iframe security/generalization;
- expertise/playbook selection;
- Business Graph RBAC/generalization;
- evidence provenance;
- Task/Case lifecycle;
- Watch dedupe/revocation;
- Durable Workflow restart/no duplicate write;
- stale approval rejection;
- Simulation reproducibility;
- Experience publish governance;
- Model Router privacy/fallback;
- R1–R11.

Nunca enfraquecer teste ou threshold para o candidate passar.

## 27. Anchor scenario

O produto maduro deve conseguir executar, de forma governada:

> “Esse produto está dando problema no cliente. Analise o desenho, procure casos parecidos, relacione produção, qualidade e fornecedor, monte uma investigação 8D, acompanhe as evidências que faltam e me avise quando Engenharia liberar a nova revisão.”

Trajetória:

```text
Case
→ Business Graph
→ multimodal evidence
→ Expertise + Playbook
→ Tasks/Durable Workflow
→ wait_event/Watch
→ Inbox
→ reanalysis
→ Decision Gate
→ Business Action
→ evidence/outcome/audit
```

Sem troca manual de agente e sem DOM automation.

## 28. Protocolo por etapa

```text
REVALIDATE HEAD + WORKING TREE
→ READY_TO_EXECUTE
→ BASELINE
→ MINIMUM CORRECT DIFF
→ WIRING REAL
→ UNIT/CONTRACT
→ INTEGRATION
→ POSITIVE
→ SIBLING
→ NEGATIVE
→ SECURITY/RBAC
→ GENERALIZATION quando aplicável
→ ADVERSARIAL REVIEW
→ RESIDUAL SEARCH
→ POSTCONDITIONS
→ COMPLETE_GATE
→ LEDGER/DOCS
→ NEXT
```

Sem `COMPLETE_GATE=PASS`, dependente não é liberada.

## 29. Reporte obrigatório

```text
STEP:
OPERATIONAL_STEP quando aplicável:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
CP_REQUIREMENTS:
DEPENDENCIES:
FILES_CHANGED:
CANONICAL_OWNERS:
PRODUCERS_CONSUMERS:
REUSED_COMPONENTS:
NEW_COMPONENTS_JUSTIFIED:
DATA_AUTHORITIES:
BASELINE:
IMPLEMENTATION:
WIRING_PROOF:
TESTS:
POSITIVE:
SIBLING:
NEGATIVE:
SECURITY_RBAC:
PROVENANCE:
IDEMPOTENCY:
RELOAD_RESUME:
GENERALIZATION:
RESIDUAL_SEARCH:
ADVERSARIAL_REVIEW:
DRIFTS:
POSTCONDITIONS:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 30. Estados bloqueantes

Não declarar concluído com:

```text
PARTIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK material
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY material
TEST_NOT_RUN
STALE_EVIDENCE
manual relation catalog sem owner
unfiltered graph traversal
claim material sem provenance
case/room permission leakage
watch ACT sem policy
duplicate write after resume
approval stale
simulation não reproduzível
knowledge auto-published
model router sem baseline/evals
```

## 31. Continuidade

Se o usuário já autorizou a implementação e a etapa fecha `COMPLETE_GATE=PASS`, continue para a próxima desbloqueada conforme os planos canônicos. Pare apenas por bloqueio real documentado.

**Comece por C0.S0.**