# Minha DELPI Copilot — Protocolo de Execução para o Cursor

**Status:** obrigatório  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Architecture/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)

## 1. Objetivo

Implementar o Copilot **como aplicação nova**, em ordem foundation-first, sem herdar runtime/dívida do Minha DELPI Chat e sem inferir arquitetura local a cada step.

## 2. Leitura obrigatória

Antes de cada subetapa:

1. instruções oficiais do projeto;
2. `.cursor/rules` aplicáveis;
3. `README.md` do Copilot;
4. `16-execution-master-plan.md`;
5. `50-standalone-copilot-application-architecture.md`;
6. `51-platform-integration-baseline.md`;
7. `52-standalone-repository-and-bootstrap-plan.md`;
8. `17-component-and-contract-map.md`;
9. `49-architecture-and-design-patterns-standard.md`;
10. `20-testing-and-acceptance-matrix.md` seções aplicáveis;
11. `21-data-and-state-model.md` quando houver state/persistence;
12. `25-requirements-traceability.md` CPs aplicáveis;
13. spec temática do step;
14. `evidence/execution-ledger.md`.

Depois:

```text
git status
git rev-parse HEAD
```

Registrar `HEAD_BEFORE`.

## 3. Boundary obrigatório

O Cursor deve tratar como erro arquitetural qualquer proposta que faça:

```text
minha-delpi-copilot-api → importar minha-delpi-ai-api
plugins/minha-delpi-copilot → importar source de minha-delpi-chat
Copilot migration → alterar Chat tables
Copilot runtime → exigir endpoint/container do Chat
Copilot planner/actions/RAG → delegar ao Chat API como implementação padrão
```

Chat pode ser lido como referência durante C0, nada além disso.

## 4. C0.S0 é read-only para runtime

Inventariar:

- Portal/AuthContext/AppHost/AppLauncher/Router/panel infrastructure;
- Core `/me`, apps, routes, RBAC, manifest, notifications/audit;
- Gateway dev/prod;
- Compose/env/scripts;
- plugin-ui/federation;
- MFEs/manifests/context/deep links;
- Domain APIs/OpenAPIs/auth/idempotency/errors/entities/events;
- rooms/requests/cases/approvals/jobs/workers;
- architecture/layers/DI/errors/state/resilience/migrations;
- Chat apenas como reference/anti-pattern/possible neutral-library evidence.

Classificar:

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

Sem runtime diff em C0.S0.

## 5. FOUNDATION_FREEZE

Nenhum C1+ começa antes de C0.S7 provar:

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

## 6. Ordem única

```text
C0 Foundation Freeze
→ C1 Standalone Bootstrap
→ C2 Portal Context/Commands
→ C3 Intelligence Core
→ C4 Business Reads/Graph
→ C5 Writes/Durable Foundation
→ C6 Product Work/Proactivity/Ecosystem
→ C7 Autonomy/Optimization/Rollout
```

Nenhum plano temático muda essa ordem.

## 7. Unidade de execução

Uma `C*.S*` por vez:

```text
SELECT STEP
→ REVALIDATE HEAD/WORKTREE
→ READ AUTHORITIES
→ IDENTIFY OWNER/LAYER
→ SELECT CANONICAL PATTERN
→ ABSTRACTION GATE
→ DEPENDENCY GATE
→ READY_TO_EXECUTE
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
→ UNLOCK NEXT
```

## 8. READY_TO_EXECUTE

Somente se:

- previous required gate PASS;
- owner/consumer/layer conhecidos;
- pattern conforme `49`;
- abstraction justificada;
- primitive/contract aprovado;
- no second authority;
- no Chat runtime dependency;
- baseline/test definidos;
- migration/storage gap provado;
- security impact classificado;
- material exception has ADR/decision.

Caso contrário: `BLOCKED_WITH_EVIDENCE`.

## 9. Regra anti-refatoração

Antes de criar schema/service/table/interface/registry/framework:

```text
A. É Copilot-owned ou platform/domain-owned?
B. Existe contract/owner atual?
C. Reuse introduziria dependência de produto no Chat?
D. Qual layer/pattern canônico?
E. Passa Abstraction Gate?
F. Duplica Entity/Evidence/Decision/Workflow/Event/Capability?
G. Próxima fase exigiria redesign conhecido?
H. Funciona para sibling/unknown sem hardcode?
I. Persistence é realmente necessária?
J. Shared package tem 2+ consumers neutros reais?
```

Se C, F ou G = sim: parar e corrigir foundation/design.

## 10. Proibições

- editar Chat para “preparar” Copilot;
- copiar pasta/runtime do Chat como ponto de partida;
- usar Chat DB tables;
- usar Chat agent/session model;
- usar Chat API como planner/tool proxy;
- manual app→URL catalog;
- manual endpoint catalog;
- path/opId semantic routing;
- permission própria duplicando Core;
- DOM automation quando API existe;
- business data master no Graph;
- frontend authority de durable state;
- feature-specific Evidence/Entity/Decision/Event;
- second workflow/action executor;
- departmental agent runtime;
- CoT persistence;
- speculative generic framework.

## 11. C1 bootstrap regra especial

A primeira implementação runtime é infraestrutura funcional, não AI feature:

```text
own API skeleton
→ health
→ JWT/Core integration
→ own MFE skeleton
→ plugin-ui/federation
→ own manifest
→ Gateway/Compose
→ Portal full-page mount
→ global host contract
→ independence test with Chat offline
```

Planner/RAG/LLM só começam em C3.

## 12. Evidence mínima

Registrar conforme material:

```text
HEAD_BEFORE/AFTER
files changed
owner/layer/pattern
CP requirements
commands/tests/results
manifest/Gateway/Compose/schema versions
OpenAPI/catalog hashes
provider/config hashes
dependence/residual scans
CHAT_INDEPENDENCE result
ADR refs
```

## 13. Adversarial review

Antes de fechar:

1. Copilot funciona se Chat estiver fora do ar?
2. existe import/table/API Chat escondido?
3. Core/Domain owner foi duplicado?
4. Portal recebeu AI logic indevida?
5. sibling/unknown exige patch central?
6. retry/resume duplica write?
7. untrusted input consegue alterar policy?
8. source permissions permanecem válidas?
9. abstraction é realmente necessária?
10. próxima fase exigirá redesign previsível?

## 14. COMPLETE_GATE blockers

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

## 15. Report obrigatório

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
CP_REQUIREMENTS:
FILES_CHANGED:
CANONICAL_OWNERS:
ARCHITECTURE_LAYER:
PATTERNS:
ABSTRACTION_GATE:
PLATFORM_REUSE:
COPILOT_NEW_CODE:
CHAT_DEPENDENCIES:
BASELINE:
IMPLEMENTATION:
WIRING_PROOF:
TESTS:
SECURITY_RBAC:
GENERALIZATION:
CHAT_INDEPENDENCE:
RESIDUAL_SEARCH:
ARCHITECTURE_CONFORMANCE:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 16. Continuidade

Com `COMPLETE_GATE=PASS`, seguir a próxima subetapa desbloqueada por `16` sem pedir nova confirmação, salvo bloqueio real/destrutivo/decisão ausente.

Primeira ordem:

```text
C0.S0 → C0.S1 → C0.S2 → C0.S3 → C0.S4 → C0.S5 → C0.S6 → C0.S7 FOUNDATION_FREEZE → C1.S1
```