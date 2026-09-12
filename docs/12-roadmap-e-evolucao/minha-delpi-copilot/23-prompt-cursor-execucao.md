# Prompt mestre — Cursor — Minha DELPI Copilot

Você deve implementar o **Minha DELPI Copilot** em ordem foundation-first, seguindo a documentação canônica e evitando refatoração previsível, arquitetura paralela e consumo desnecessário de tokens.

## 1. Fonte de verdade e ordem de leitura

Leia antes de qualquer alteração:

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc`
3. regras `.cursor` aplicáveis a planning/execution/tests/security/OpenAPI/AI/Clean Architecture
4. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`
5. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/02-arquitetura.md`
6. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md`
7. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md`
8. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md`
9. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md`
10. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/22-cursor-execution-protocol.md`
11. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md`
12. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md`
13. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md`
14. documentos temáticos da subetapa em execução.

### Regra crítica

`16-execution-master-plan.md` é a **única authority da ordem de implementação**.

Os planos `E*` e `O*` são detalhamento temático. Eles não desbloqueiam etapa independentemente.

## 2. Missão do produto

Construir um único Copilot capaz de:

```text
PERGUNTAR
FAZER
ACOMPANHAR
TRABALHAR
```

sobre as mesmas APIs, permissions e regras de negócio da Minha DELPI.

Especialização ocorre por Expertise Packs/Playbooks/Knowledge/Multimodal, não por agentes departamentais separados.

## 3. Ordem obrigatória

```text
C0 Foundations
→ C1 Platform/Context
→ C2 Intelligence Core
→ C3 Business Reads + Graph
→ C4 Governed Writes
→ C5 Durable Work
→ C6 Proactivity/Ecosystem/Learning
→ C7 Optimization/Autonomy/Rollout
```

Não implemente C1 antes de `FOUNDATION_FREEZE=PASS`.

## 4. Primeira ação obrigatória — C0.S0

Antes de runtime diff:

```text
git status
git rev-parse HEAD
```

Registrar `HEAD_BEFORE`.

Inventariar com evidence:

### Portal/Core
- Router/Auth/AppHost/AppLauncher;
- `/me`, `/me/apps`, `/me/routes`;
- manifests/routes/permissions;
- MFE/iframe/external lifecycle;
- rooms/notifications existentes.

### AI API
- understanding/planner;
- Action Catalog/importer/index;
- executors;
- policy/confirmation;
- RAG/ACL;
- session/turn persistence;
- send/stream/simulate;
- multimodal;
- models/providers;
- observability/evals.

### Agents/skills legados
- entities/repos/controllers/admin;
- specialization;
- workspace activation;
- soft handoff;
- skill registry;
- `agent_id`, `chat_mode`;
- project default agent;
- knowledge/actions/tools dependentes de agent;
- UI correspondente.

### Operação corporativa
- entity IDs;
- relationships;
- event bus/types;
- workers/queues/jobs;
- workflows/approvals;
- rooms/inbox/notifications;
- audit/provenance;
- cases/requests reutilizáveis;
- idempotency support;
- knowledge lifecycle.

Classificar:

```text
REUSE
EXTEND
MIGRATE
CREATE_REQUIRED
DEPRECATE
REMOVE
NOT_PROVEN
```

Sem C0.S0 completo: **não editar runtime do Copilot**.

## 5. C0 foundation freeze

C0 precisa estabilizar/reutilizar equivalentes para:

```text
CorrelationContext
EntityRef
RelationshipRef
SourceRef
EvidenceRef
OutcomeRef
CapabilityProjection
PlatformCommand
WorkspaceContext
ExpertisePack/Selection/Context
DomainPlaybook
MultimodalEvidenceRef
DecisionGate Request/Decision
WorkflowPlan/Step
TaskRef
CaseRef
EventEnvelope
IframeBridgeEnvelope
AuditEvent ou integração equivalente
```

Não significa criar todas as tabelas em C0. Significa congelar **semântica, owner, versionamento, ports e boundaries** antes das features.

## 6. Regra anti-refatoração previsível

Antes de criar qualquer schema/service/table/event:

1. existe primitive compartilhado em C0?
2. existe owner/repository equivalente no código atual?
3. isso cria segunda authority?
4. isso duplica Entity/Evidence/Decision/Workflow/Event?
5. já sabemos que fase seguinte exigirá alterar este contrato?
6. funciona com sibling/unknown sem branch específica?

Se 3, 4 ou 5 = sim, **pare a implementação e corrija a fundação**.

## 7. Arquitetura obrigatória

### Business Actions

```text
OpenAPI
→ Action Catalog
→ allowed actions
→ Capability Projection
→ retrieval/planner
→ policy/Decision Gate
→ generic executor
→ domain API
→ Outcome/Evidence
```

### Platform Actions

```text
Core /me/apps
→ authorized route projection
→ PlatformCommand
→ CopilotBridge
→ Portal/MFE/Iframe
```

### Intelligence

```text
understanding
→ capability retrieval
→ expertise/playbook retrieval
→ knowledge/multimodal evidence
→ bounded context
→ planner
```

### Durable Work

```text
WorkflowPlan
→ canonical executors
→ checkpoint/waits
→ Task/Case/Inbox/Room/Watch surfaces
```

Não criar segundo HTTP/tool executor.

## 8. Proibições

- agente por departamento como runtime final;
- second planner/executor;
- manual endpoint catalog;
- path/operationId semantic selector;
- app→URL hardcode;
- permission própria do Copilot;
- Workspace Context como authorization;
- Expertise/Playbook concedendo permission;
- DOM automation quando API/use case existe;
- graph copiando tabelas de domínio;
- Evidence model diferente por feature;
- confirmation paralela ao Decision Gate;
- Task engine paralela ao Workflow runtime;
- Watch polling app-specific no core se houver event owner melhor;
- CoT persistence;
- JWT/refresh token em iframe bridge/state;
- production learning automático por feedback.

## 9. Onda J / OpenAPI-first

C0–C2 podem avançar sem Business Actions production-ready.

C3+ que dependa de actions reais precisa dos gates OpenAPI-first aplicáveis `PASS` no candidate vigente.

Não mascarar dependência com mocks/fallbacks.

## 10. Protocolo de cada subetapa

```text
SELECT C*.S*
→ REVALIDATE HEAD/WORKTREE
→ read owners/contracts
→ dependency gate
→ READY_TO_EXECUTE
→ baseline
→ minimal correct owner-level diff
→ producer/consumer wiring
→ unit/contract
→ integration
→ positive/sibling/negative
→ security/RBAC
→ generalization/metamorphic/unknown
→ adversarial review
→ semantic residual scan
→ postconditions
→ COMPLETE_GATE
→ docs/ledger
→ unlock next
```

Execute **uma subetapa por vez**.

## 11. COMPLETE_GATE

Bloqueantes:

```text
PARTIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK material
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY material
TEST_NOT_RUN
STALE_EVIDENCE
DUPLICATE_AUTHORITY
FOUNDATION_DRIFT
```

## 12. Testes

Use `20-testing-and-acceptance-matrix.md` como única matriz canônica.

Não use `45-*` como segunda authority; ele é referência histórica/temática.

Obrigatório conforme fase:

- positive/sibling/negative;
- unauthorized/TOCTOU;
- injection;
- send/stream;
- reload/restart;
- unknown app/provider/pack/iframe/relation;
- true metamorphic rename;
- Decision Gate/idempotency;
- workflow crash/resume;
- graph permission traversal;
- evidence/provenance;
- R1–R11 aplicáveis.

Nunca enfraquecer threshold/test para passar.

## 13. Rastreabilidade

Use `25-requirements-traceability.md` como única authority `CP-*`.

`46-*` é referência temática; não manter requisito novo apenas lá.

Todo requisito novo:

```text
CP-ID
owner
canonical C phase
gate
status
```

## 14. Relatório obrigatório

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
REQUIREMENTS_CP:
CANONICAL_OWNERS:
REUSED_FOUNDATIONS:
NEW_FOUNDATIONS_CREATED:
FILES_CHANGED:
BASELINE:
IMPLEMENTATION:
WIRING_PROOF:
TESTS:
POSITIVE:
SIBLING:
NEGATIVE:
SECURITY_RBAC:
GENERALIZATION:
RESIDUAL_SEARCH:
ADVERSARIAL_REVIEW:
FOUNDATION_DRIFT:
POSTCONDITIONS:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 15. Continuidade

Se `COMPLETE_GATE=PASS`, prossiga para a próxima subetapa desbloqueada pelo `16-execution-master-plan.md`.

Não comece por UI final, Business Graph, Cases, Watch ou Model Router.

Comece por:

```text
C0.S0
→ C0.S1
→ C0.S2
→ C0.S3
→ C0.S4
→ C0.S5
→ C0.S6 FOUNDATION_FREEZE
```

Somente então `C1.S1`.