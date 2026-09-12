# Prompt mestre — Cursor — Minha DELPI Copilot Standalone

Implemente o **Minha DELPI Copilot como aplicação nova e independente**, do zero até o produto completo. Não evolua nem refatore o Minha DELPI Chat para atingir este objetivo.

## 1. Decisão inegociável

```text
Copilot backend  = nova minha-delpi-copilot-api
Copilot frontend = novo plugins/minha-delpi-copilot
Chat backend     = sistema separado
Chat frontend    = sistema separado
```

Proibido:

```text
importar runtime do minha-delpi-ai-api
importar source do plugins/minha-delpi-chat
usar Chat API como proxy/planner/tool runtime
usar Chat tables/sessions/agents como Copilot authority
alterar Chat para desbloquear Copilot
esperar roadmap/Onda J do Chat
```

O Chat pode ser lido em C0 somente como referência para patterns, lessons learned e anti-patterns.

## 2. Ordem de leitura

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc` + regras aplicáveis
3. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`
4. `.../16-execution-master-plan.md`
5. `.../50-standalone-copilot-application-architecture.md`
6. `.../51-platform-integration-baseline.md`
7. `.../52-standalone-repository-and-bootstrap-plan.md`
8. `.../17-component-and-contract-map.md`
9. `.../49-architecture-and-design-patterns-standard.md`
10. `.../20-testing-and-acceptance-matrix.md` seções aplicáveis
11. `.../21-data-and-state-model.md` quando houver state/persistence
12. `.../22-cursor-execution-protocol.md`
13. `.../25-requirements-traceability.md` CPs aplicáveis
14. `.../evidence/execution-ledger.md`
15. specs temáticas da etapa.

`16` é a única authority de ordem. `50` é authority do product boundary. `49` é authority de arquitetura/patterns.

## 3. Ordem de construção

```text
C0 Platform + Architecture Foundation Freeze
→ C1 Standalone App Bootstrap
→ C2 Portal Context + Platform Commands
→ C3 Intelligence Core
→ C4 Business Reads + Graph
→ C5 Governed Writes + Durable Foundation
→ C6 Product Work + Proactivity + Ecosystem
→ C7 Autonomy + Optimization + Rollout
```

## 4. Primeira ação — C0.S0

Antes de qualquer runtime diff:

```text
git status
git rev-parse HEAD
```

Inventarie com paths/symbols/contracts/evidence:

### Portal
- AuthContext/Keycloak;
- AppHost federated lifecycle;
- AppLauncher/Router;
- global layout/drawer/panel infrastructure;
- getAccessToken host contract;
- federation share scope;
- notifications/socket/context patterns.

### Core
- `/me`, `/me/apps`, `/me/routes`;
- RBAC/permission resolver;
- manifest registration/versioning;
- app/route models;
- notification/audit/presence patterns.

### Gateway/Infra
- API/MFE path conventions;
- dev/prod parity;
- Compose profiles/services;
- env examples;
- health/scripts/storage/network.

### MFEs
- manifests;
- mount/unmount;
- federation config;
- plugin-ui usage;
- auth/API clients;
- context/deep links.

### APIs
- existing APIs and OpenAPIs;
- auth/permissions;
- error/pagination envelopes;
- idempotency/write semantics;
- entity IDs;
- events/websockets.

### Collaboration/work infrastructure
- interaction rooms;
- requests/cases;
- notifications/inbox-like concepts;
- approvals/jobs/workers/events.

### Chat reference only
- inspect architecture/providers/RAG/multimodal/actions only to avoid repeating debt;
- never classify Chat runtime as `REUSE` for Copilot.

Classify findings:

```text
PLATFORM_REUSE
NEUTRAL_SHARED_REUSE
COPILOT_IMPLEMENT_NEW
EXTEND_PLATFORM_CONTRACT
ADAPTER_REQUIRED
ADR_REQUIRED
NOT_PROVEN
OUT_OF_SCOPE
```

No runtime changes in C0.S0.

## 5. Foundation Freeze

Before C1:

```text
PLATFORM_INVENTORY=PASS
STANDALONE_BOUNDARY=PASS
NAMES_PATHS=PASS
AUTHORITIES=PASS
SHARED_PRIMITIVES=PASS
ARCHITECTURE_PATTERNS=PASS
PERSISTENCE_BOUNDARIES=PASS
INTEGRATION_CONTRACTS=PASS
CONFORMANCE_HARNESS=PASS
CHAT_RUNTIME_DEPENDENCY=0
FOUNDATION_DUPLICATION=0 material
```

## 6. Target physical structure

Recommended, unless C0 evidence/ADR changes it:

```text
minha-delpi-copilot-api/
  app/domain
  app/application
  app/interfaces
  app/infrastructure
  app/composition
  migrations/tests/docs/scripts

plugins/minha-delpi-copilot/
  src/ui
  src/state
  src/data
  src/features
  src/contracts
  src/adapters
```

Never create Copilot source inside Chat folders.

## 7. Architecture rules

```text
Clean Architecture
+ Ports & Adapters
+ pragmatic DDD
+ Event-Driven only with real event owner
+ State Machines for nontrivial lifecycle
+ light CQRS only when justified
```

External dependencies are adapters. Concrete wiring happens in Composition Root. Durable state is backend-owned.

Before creating interface/port/repository/factory/strategy/registry/base class, pass the Abstraction Gate in `49`.

## 8. Portal integration

Copilot MFE is `federated`.

Full page:

```text
Core app/route
→ Portal AppHost
→ remoteEntry
→ Copilot MFE mount
```

Global panel:

```text
Portal thin host
→ same Copilot MFE/package
→ WorkspaceContext
→ typed PlatformCommands
```

Portal must not contain planner, prompts, RAG, business action routing or Copilot persistence.

## 9. Auth/RBAC

```text
Keycloak → identity/JWT
Core API → platform permissions/apps/routes
Domain API → final business authorization/rules
Copilot → cannot elevate any of them
```

MFE receives `getAccessToken` from host. Copilot API validates JWT and uses official Core contracts.

## 10. Business Actions — build natively in Copilot

Do not inherit Chat Action Catalog/runtime.

```text
Domain OpenAPI
→ Copilot importer/normalizer/index
→ Copilot Action Catalog
→ permission-aware Capability Projection
→ semantic retrieval/planner
→ schema/argument validation
→ policy/Decision Gate
→ generic executor
→ Domain API
→ verified Outcome/Evidence
```

No manual endpoint catalog. No path/opId semantic hardcode.

## 11. Shared code policy

Reuse platform-neutral code only when:

- owner is already shared; or
- extraction to a neutral package is justified by 2+ real consumers and independent contracts/tests.

Never turn `minha-delpi-ai-api` or `minha-delpi-chat` into a library for Copilot.

## 12. C1 special rule

First runtime work is bootstrap, not intelligence:

```text
own API skeleton
→ health/config/logging
→ JWT/Core integration
→ own MFE skeleton
→ federation/plugin-ui
→ own manifest
→ Gateway/Compose
→ Portal full-page mount
→ global host contract
→ Chat-offline independence test
```

LLM/planner/RAG start only in C3.

## 13. Generic implementation protocol

For one `C*.S*` at a time:

```text
REVALIDATE HEAD
→ READ AUTHORITIES
→ IDENTIFY OWNER/LAYER/PATTERN
→ ABSTRACTION GATE
→ DEPENDENCY GATE
→ BASELINE
→ MINIMAL CORRECT DIFF
→ WIRE PRODUCER/CONSUMER
→ UNIT/CONTRACT/INTEGRATION
→ POSITIVE/SIBLING/NEGATIVE
→ SECURITY/RBAC
→ GENERALIZATION/METAMORPHIC/UNKNOWN
→ CHAT-INDEPENDENCE CHECK
→ ARCHITECTURE CONFORMANCE
→ RESIDUAL SEARCH
→ COMPLETE_GATE
→ DOCS/LEDGER
→ NEXT STEP
```

## 14. Prohibitions

- Chat runtime dependency;
- Chat DB authority;
- Chat agent/session migration;
- second RBAC;
- business rules in MFE/LLM;
- Portal AI logic;
- manual app URL catalog;
- manual endpoint catalog;
- DOM business automation;
- Graph as operational master database;
- feature-specific Entity/Evidence/Decision/Event types;
- Task executor parallel to Workflow runtime;
- CoT persistence;
- secrets/JWT in context/logs;
- speculative abstractions.

## 15. Required tests

Use `20` as authority. In addition to feature tests, every release boundary must include:

```text
NO_CHAT_IMPORT
NO_CHAT_API_DEP
NO_CHAT_DB_AUTHORITY
CHAT_OFFLINE_INDEPENDENCE
PORTAL_HOST_ONLY
CORE_RBAC_AUTHORITY
DOMAIN_API_AUTHORITY
DEV_PROD_ROUTE_PARITY
INDEPENDENT_ROLLBACK
```

## 16. Complete Gate blockers

```text
PARTIAL
INCONCLUSIVE
PENDING
TEST_NOT_RUN
STALE_EVIDENCE
DUPLICATE_AUTHORITY
FOUNDATION_DRIFT
ARCHITECTURE_PATTERN_DRIFT
UNJUSTIFIED_ABSTRACTION
CHAT_RUNTIME_IMPORT
CHAT_API_REQUIRED
CHAT_DATABASE_AUTHORITY
CHAT_MIGRATION_DEPENDENCY
PORTAL_AI_LOGIC_LEAK
DOMAIN_RULE_DUPLICATION
```

## 17. Report format

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
CP_REQUIREMENTS:
FILES_CHANGED:
OWNERS:
LAYER/PATTERNS:
PLATFORM_REUSE:
COPILOT_NEW_CODE:
CHAT_DEPENDENCIES:
WIRING_PROOF:
TESTS:
SECURITY_RBAC:
GENERALIZATION:
CHAT_INDEPENDENCE:
ARCHITECTURE_CONFORMANCE:
RESIDUAL_SEARCH:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 18. Start here

Execute only:

```text
C0.S0
```

Do not create the Copilot API/MFE until C0.S7 `FOUNDATION_FREEZE=PASS`. After the freeze, start C1.S1 with the standalone API skeleton.