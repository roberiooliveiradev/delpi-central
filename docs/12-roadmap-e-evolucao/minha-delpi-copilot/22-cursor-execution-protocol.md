# Minha DELPI Copilot — Protocolo de Execução para o Cursor

**Status:** obrigatório  
**Authority de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Evitar:

- execução fora de ordem;
- feature-first prototyping que depois exige refatoração;
- contratos inventados tarde;
- segunda authority;
- duplicação de primitive/state;
- fechamento prematuro;
- gasto desnecessário de tokens com retrabalho.

## 2. Ordem documental antes de qualquer step

1. instruções oficiais do projeto;
2. `.cursor/rules/development-standards-index.mdc` + regras específicas;
3. `README.md` do Copilot;
4. `16-execution-master-plan.md`;
5. `17-component-and-contract-map.md`;
6. `21-data-and-state-model.md`;
7. `20-testing-and-acceptance-matrix.md`;
8. `25-requirements-traceability.md`;
9. documento temático da subetapa;
10. `evidence/execution-ledger.md`.

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
- domain API/OpenAPI/idempotency.

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
```

## 6. Unidade de execução

Executar **uma** `C*.S*` por vez:

```text
SELECT STEP
→ REVALIDATE HEAD/WORKTREE
→ READ OWNERS/CONTRACTS
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
- primitive/contract reutilizado ou aprovado em C0;
- não há second authority;
- baseline/test definido;
- working tree entendido;
- impacto de segurança classificado;
- migration/persistence necessity provada quando houver.

Caso contrário: `BLOCKED_WITH_EVIDENCE`.

## 8. Regra anti-refatoração

Antes de criar schema/class/service/table/event enum:

```text
A. Existe equivalente compartilhado?
B. Quem é owner canônico?
C. Quem consome hoje?
D. Isso duplica Entity/Evidence/Decision/Workflow/Event/Capability?
E. A próxima fase conhecida obrigaria alterar este contrato?
F. Isso funciona para sibling/unknown sem branch específica?
```

Se D ou E = sim, **não implementar a feature**. Corrigir a foundation/versionar o contrato primeiro.

## 9. Menor diff correto

Correto:

```text
owner canônico
+ shared primitive existente
+ wiring real
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
- auto-publish de learning.

## 11. Evidence de execução

Nunca declarar PASS sem evidence do candidate correspondente.

Registrar conforme material:

```text
command/test
result
HEAD
contract/schema version
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
10. foundation drift foi introduzido?.

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
- manter commit/evidence coerentes.

## 17. Quando parar

Somente por bloqueio real:

- secret/dado obrigatório indisponível;
- risco destrutivo real;
- working-tree conflict não resolvível com segurança;
- decisão de produto realmente ausente;
- dependência externa impedindo evidence;
- foundation contradiction que precisa ser resolvida antes da feature.

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