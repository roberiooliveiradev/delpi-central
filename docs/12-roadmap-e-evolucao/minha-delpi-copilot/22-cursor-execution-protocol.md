# Minha DELPI Copilot — Protocolo de Execução para o Cursor

**Status:** obrigatório  
**Authority de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Authority de arquitetura/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)

## 1. Objetivo

Evitar:

- execução fora de ordem;
- feature-first prototyping que depois exige refatoração;
- contratos inventados tarde;
- segunda authority;
- duplicação de primitive/state;
- escolha inconsistente de design patterns;
- abstrações/frameworks locais desnecessários;
- business state no frontend;
- fechamento prematuro;
- gasto desnecessário de tokens com retrabalho.

## 2. Ordem documental antes de qualquer step

1. instruções oficiais do projeto;
2. `.cursor/rules/development-standards-index.mdc` + regras específicas;
3. `README.md` do Copilot;
4. `16-execution-master-plan.md`;
5. `17-component-and-contract-map.md`;
6. `49-architecture-and-design-patterns-standard.md` — ler integralmente no C0; depois, no mínimo as seções aplicáveis à subetapa;
7. `21-data-and-state-model.md` quando estado/persistência estiverem no escopo;
8. `20-testing-and-acceptance-matrix.md` nas seções aplicáveis;
9. `25-requirements-traceability.md` nos CPs aplicáveis;
10. documento temático da subetapa;
11. `evidence/execution-ledger.md`.

Depois:

```text
git status
git rev-parse HEAD
```

Registrar `HEAD_BEFORE`.

## 3. Uma única ordem

O Cursor executa somente a próxima subetapa desbloqueada em `16`.

Planos E*/O* não liberam execução independente.

Se algum documento temático sugerir outra ordem:

```text
16-execution-master-plan.md vence
```

Se alguma implementação propuser arquitetura/pattern divergente sem decisão arquitetural aprovada:

```text
49-architecture-and-design-patterns-standard.md vence
```

## 4. C0.S0 é obrigatório e read-only para runtime

C0.S0 deve provar com arquivo/símbolo/contrato/consumer:

- Portal/Core/Chat/AI atuais;
- Action Catalog/planner/executors/policy;
- sessions/persistence;
- agents/skills/handoff;
- apps/MFEs/iframes;
- entity IDs/deep links;
- events/jobs/queues;
- rooms/notifications;
- workflows/approvals;
- audit/provenance;
- model/provider abstractions;
- domain API/OpenAPI/idempotency;
- padrões existentes de `domain/application/interfaces/infrastructure`;
- ports/adapters/repositories/use cases atuais;
- DI/composition root atual;
- error/result taxonomy;
- event/outbox/idempotency/resilience patterns atuais;
- state machines/lifecycle atuais;
- organização `ui/state/data` e server/workspace/local state no frontend;
- mecanismos atuais de migration/strangler/compatibility adapter.

Classificar cada finding:

```text
REUSE
EXTEND
MIGRATE
CREATE_REQUIRED
DEPRECATE
REMOVE
NOT_PROVEN
```

**Nenhum runtime diff do Copilot em C0.S0.**

## 5. FOUNDATION_FREEZE

Nenhum C1+ começa até C0.S6 provar:

```text
INVENTORY=PASS
AUTHORITIES=PASS
SHARED_PRIMITIVES=PASS
PERSISTENCE_BOUNDARIES=PASS
CROSS_CUTTING_SEMANTICS=PASS
CONTRACT_HARNESS=PASS
FOUNDATION_DUPLICATION=0 material

ARCHITECTURE_STYLE=PASS
LAYER_RESPONSIBILITIES=PASS
DEPENDENCY_RULES=PASS
BOUNDED_CONTEXTS=PASS
PATTERN_DECISION_MATRIX=PASS
ERROR_MODEL=PASS
EVENT_MODEL=PASS
STATE_MACHINE_RULES=PASS
PERSISTENCE_RULES=PASS
FRONTEND_STATE_RULES=PASS
RESILIENCE_RULES=PASS
TESTING_PATTERN=PASS
MIGRATION_PATTERNS=PASS
ABSTRACTION_GATE=PASS
ARCHITECTURAL_EXCEPTION_PROCESS=PASS
```

Os critérios arquiteturais são definidos em `49`.

## 6. Unidade de execução

Executar **uma** `C*.S*` por vez:

```text
SELECT STEP
→ REVALIDATE HEAD/WORKTREE
→ READ OWNERS/CONTRACTS
→ CLASSIFY LAYER + PATTERN
→ ABSTRACTION GATE
→ DEPENDENCY GATE
→ READY_TO_EXECUTE
→ BASELINE
→ IMPLEMENT MINIMAL CORRECT OWNER-LEVEL DIFF
→ WIRE PRODUCER/CONSUMER
→ UNIT/CONTRACT
→ INTEGRATION
→ POSITIVE
→ SIBLING
→ NEGATIVE
→ SECURITY/RBAC
→ GENERALIZATION/METAMORPHIC/UNKNOWN
→ ARCHITECTURAL CONFORMANCE REVIEW
→ ADVERSARIAL REVIEW
→ SEMANTIC RESIDUAL SEARCH
→ POSTCONDITIONS
→ COMPLETE_GATE
→ DOCS + LEDGER
→ UNLOCK NEXT
```

## 7. READY_TO_EXECUTE

Somente se:

- dependências anteriores PASS;
- owner/consumer conhecidos;
- camada correta identificada;
- pattern escolhido pela matriz do `49`;
- abstraction gate justifica interfaces/ports/factories/strategies/repositories novos;
- primitive/contract reutilizado ou aprovado em C0;
- não há second authority;
- baseline/test definido;
- working tree entendido;
- impacto de segurança classificado;
- migration/persistence necessity provada quando houver;
- divergence arquitetural, se necessária, possui decisão/ADR conforme padrão do repo.

Caso contrário: `BLOCKED_WITH_EVIDENCE`.

## 8. Regra anti-refatoração

Antes de criar schema/class/service/table/event enum/abstração:

```text
A. Existe equivalente compartilhado?
B. Quem é owner canônico?
C. Quem consome hoje?
D. Qual camada é dona dessa responsabilidade?
E. Qual pattern da matriz do 49 se aplica?
F. A abstração passa o Abstraction Gate?
G. Isso duplica Entity/Evidence/Decision/Workflow/Event/Capability?
H. A próxima fase conhecida obrigaria alterar este contrato?
I. Isso funciona para sibling/unknown sem branch específica?
J. Existe implementação/pattern equivalente já comprovado no repo?
```

Se G ou H = sim, **não implementar a feature**. Corrigir a foundation/versionar o contrato primeiro.

Se F = não, implementar de forma mais simples sem abstração especulativa.

## 9. Menor diff correto

Correto:

```text
owner canônico
+ camada correta
+ pattern canônico
+ shared primitive existente
+ wiring real via composition root quando aplicável
+ tests
+ migration/cutover quando material
+ cleanup/fallback exit criteria
```

Incorreto:

```text
copiar lógica
novo JSON técnico
local endpoint selector
feature-specific Evidence/Entity/Confirmation type
duplicar executor
hardcodar piloto
mockar security para smoke
instanciar infrastructure dentro de domain/application
criar Factory/Strategy/Repository sem Abstraction Gate
persistir business authority no frontend
```

## 10. Proibições específicas

- manual app→URL catalog;
- manual endpoint catalog;
- path/operationId semantic routing;
- department agent runtime;
- Workspace Context como permission;
- Expertise/Playbook como permission;
- DOM automation quando API/use case existe;
- second Action Catalog;
- second workflow HTTP/tool executor;
- graph duplicando domain data;
- Case-specific Evidence contract;
- confirmation paralelo ao Decision Gate;
- Task engine paralelo;
- Watch event envelope paralelo;
- arbitrary model routing por feature;
- CoT persistence;
- JWT/secret em bridge/state;
- auto-publish de learning;
- `Manager/Helper/Utils/Service` genérico acumulando responsabilidades;
- framework/ORM/client concreto atravessando Domain/Application;
- repository como simples wrapper de qualquer HTTP;
- deep inheritance para compartilhar implementação trivial;
- service locator/singleton mutable de business state;
- Strategy/Factory/Builder/CQRS/Saga/Event Sourcing por moda;
- event bus sem schema/owner;
- retry cego de write;
- regra de negócio server-side duplicada em React.

## 11. Evidence de execução

Nunca declarar PASS sem evidence do candidate correspondente.

Registrar conforme material:

```text
command/test
result
HEAD
contract/schema version
architecture layer
pattern(s) aplicados
abstraction gate result
ADR/exception ref quando houver
config/model/provider hash
OpenAPI/catalog hash
expertise/playbook hash
evidence artifact/path
timestamp
```

Evidence stale não fecha step.

## 12. Residual search

Depois de cutover/cleanup, procurar conceito em:

- Python/TS/TSX;
- JSON/YAML/config;
- prompts/content;
- fixtures/generators;
- tests;
- scripts/CI;
- caches/indexes;
- manifests;
- docs.

Buscar especialmente:

```text
app hardcode
endpoint/path selector
parallel Evidence/Entity/Confirmation types
userActivatedAgent
switch_agent_and_resend
agentId routing
legacy fallback
feature-specific workflow executor
framework import em domain/application
new concrete client dentro de use case
local event envelope
frontend durable business state
unjustified repository/factory/strategy/base class
```

## 13. Adversarial review

Antes de COMPLETE_GATE responder:

1. funciona com sibling/unknown sem core patch?;
2. existe second authority?;
3. usuário não autorizado consegue forçar payload?;
4. data/tool/context/pack/event hostil altera policy?;
5. retry/reload/resume duplica write?;
6. source permission é preservada em Graph/Case/Room/Inbox?;
7. fallback material ainda existe?;
8. próxima fase conhecida exigirá redesign do que acabou de ser criado?;
9. migration é realmente necessária?;
10. foundation drift foi introduzido?;
11. responsabilidade foi colocada na camada correta?;
12. o pattern usado é o padrão do `49` ou há ADR explícita?;
13. alguma abstração existe apenas por especulação?;
14. o frontend virou authority de dado/regra durável?;
15. dependency rule foi violada?.

## 14. COMPLETE_GATE

Bloqueantes quando materiais:

```text
PARTIAL
ATENDIDO_PARCIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY
TEST_NOT_RUN
STALE_EVIDENCE
DUPLICATE_AUTHORITY
FOUNDATION_DRIFT
UNKNOWN_CONSUMER material
ARCHITECTURE_PATTERN_DRIFT
DEPENDENCY_RULE_VIOLATION
UNJUSTIFIED_ABSTRACTION
UNDOCUMENTED_ARCHITECTURAL_EXCEPTION
```

## 15. Reporte obrigatório

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
REQUIREMENTS_CP:
FILES_CHANGED:
CANONICAL_OWNERS:
PRODUCERS_CONSUMERS:
ARCHITECTURE_LAYER:
DESIGN_PATTERNS_APPLIED:
ABSTRACTION_GATE:
ARCHITECTURAL_EXCEPTION_ADR:
REUSED_FOUNDATIONS:
NEW_FOUNDATIONS_CREATED:
BASELINE:
IMPLEMENTATION:
WIRING_PROOF:
TESTS:
POSITIVE:
SIBLING:
NEGATIVE:
SECURITY_RBAC:
GENERALIZATION:
ARCHITECTURAL_CONFORMANCE:
RESIDUAL_SEARCH:
ADVERSARIAL_REVIEW:
FOUNDATION_DRIFT:
DRIFTS:
POSTCONDITIONS:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 16. Commit/push

Seguir `.cursor/rules/test-and-commit.mdc`.

- preservar mudanças não relacionadas;
- não misturar refactors fora do step;
- não “arrumar aproveitando” áreas adjacentes sem requirement;
- manter commit/evidence coerentes;
- não introduzir novo architectural style/pattern local sem decisão documentada.

## 17. Quando parar

Somente por bloqueio real:

- secret/dado obrigatório indisponível;
- risco destrutivo real;
- working-tree conflict não resolvível com segurança;
- decisão de produto realmente ausente;
- dependência externa impedindo evidence;
- foundation contradiction que precisa ser resolvida antes da feature;
- architecture/pattern contradiction sem decisão aprovada.

Registrar `BLOCKED_WITH_EVIDENCE`, não PASS parcial.

## 18. Continuidade

Quando o usuário já autorizou o plano e a subetapa fecha `COMPLETE_GATE=PASS`, continuar para a próxima desbloqueada em `16`.

Primeira ordem:

```text
C0.S0
→ C0.S1
→ C0.S2
→ C0.S3
→ C0.S4
→ C0.S5
→ C0.S6 FOUNDATION_FREEZE
→ C1.S1
```

No C0, o `49` deve sair validado contra o código real e os padrões existentes do repositório antes do `FOUNDATION_FREEZE`.