# Minha DELPI Copilot — Protocolo de Execução para o Cursor

**Status:** obrigatório  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Architecture/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Objetivo

Implementar o Copilot **como aplicação nova**, em ordem foundation-first, sem herdar runtime/dívida do Minha DELPI Chat, sem inferir arquitetura local a cada step e sem adiar boundaries de mídia/device/privacidade/OT que depois exigiriam refatoração.

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
10. `53-multimodal-meeting-frontline-and-industrial-copilot.md` quando media/Meeting/Frontline/device/OT for material;
11. `20-testing-and-acceptance-matrix.md` seções aplicáveis;
12. `21-data-and-state-model.md` quando houver state/persistence/media retention;
13. `25-requirements-traceability.md` CPs aplicáveis;
14. spec temática do step;
15. `evidence/execution-ledger.md`.

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
Copilot planner/actions/RAG/media → delegar ao Chat API como implementação padrão
```

Chat pode ser lido como referência durante C0, nada além disso.

## 4. C0.S0 é read-only para runtime

Inventariar:

### Platform

- Portal/AuthContext/AppHost/AppLauncher/Router/panel infrastructure;
- Core `/me`, apps, routes, RBAC, manifest, notifications/audit;
- Gateway dev/prod;
- Compose/env/scripts;
- plugin-ui/federation;
- MFEs/manifests/context/deep links;
- Domain APIs/OpenAPIs/auth/idempotency/errors/entities/events;
- rooms/requests/cases/approvals/jobs/workers.

### Media/Meeting/Frontline

- browser mic/camera/screen/media APIs;
- current streaming/SSE/WebSocket/WebRTC patterns;
- file/object/media storage;
- speech/vision providers/configs existentes;
- recording/transcription patterns;
- privacy/consent/retention owners;
- shared workstations/tablets/kiosks;
- meeting-room devices/processes;
- production terminals;
- procedures/training sources;
- network constraints relevant to factory devices;
- accessibility/noise constraints.

### Operational/OT

- sources/IDs para OP, operation, machine, product, lot, material, workstation;
- production/maintenance/quality APIs/events;
- OT telemetry interfaces;
- safety/interlock owners;
- existing machine command APIs/protocols **only as inventory**;
- IT/OT security boundary.

### Architecture

- layers/DI/errors/state/resilience/migrations;
- media/provider boundaries;
- shared-device session patterns;
- retention/data-minimization patterns;
- industrial safety patterns.

### Chat reference only

- inspect architecture/providers/RAG/multimodal/actions only to avoid repeating debt;
- never classify Chat runtime as `REUSE` for Copilot.

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
MEDIA_PRIVACY_BOUNDARIES=PASS
SHARED_DEVICE_BOUNDARY=PASS
OPERATIONAL_CONTEXT_BOUNDARY=PASS
OT_SAFETY_BOUNDARY=PASS
CONFORMANCE_HARNESS=PASS
CHAT_RUNTIME_DEPENDENCY=0
FOUNDATION_DUPLICATION=0 material
```

## 6. Ordem única

```text
C0 Foundation Freeze
→ C1 Standalone Bootstrap
→ C2 Portal + Operational Context/Commands
→ C3 Intelligence + Multimodal Foundations
→ C4 Business Reads/Graph
→ C5 Writes/Durable Foundation
→ C6 Product Work/Meeting/Frontline/Proactivity/Ecosystem
→ C7 Advanced Realtime/Autonomy/Optimization/Rollout
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
→ SECURITY/RBAC/PRIVACY/SAFETY
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
- security/privacy/safety impact classificado;
- media retention/capture policy conhecida quando aplicável;
- shared-device identity boundary conhecida quando aplicável;
- OT responsibility classificada quando aplicável;
- material exception has ADR/decision.

Caso contrário: `BLOCKED_WITH_EVIDENCE`.

## 9. Regra anti-refatoração

Antes de criar schema/service/table/interface/registry/framework/media pipeline/realtime gateway/device context/OT adapter:

```text
A. É Copilot-owned ou platform/domain/industrial-owner?
B. Existe contract/owner atual?
C. Reuse introduziria dependência de produto no Chat?
D. Qual layer/pattern canônico?
E. Passa Abstraction Gate?
F. Duplica Entity/Evidence/Decision/Workflow/Event/Capability?
G. WorkspaceContext/EntityRef já resolvem o contexto?
H. Próxima fase exigiria redesign conhecido?
I. Funciona para sibling/unknown sem hardcode?
J. Persistence é realmente necessária?
K. Raw media precisa ser persistida?
L. Modality cria bypass de RBAC/Decision?
M. Device identity está sendo confundida com user identity?
N. Business Action está sendo confundida com physical machine actuation?
```

Se C, F, H, L, M ou N = sim: parar e corrigir foundation/design.

## 10. Proibições

- editar Chat para “preparar” Copilot;
- copiar pasta/runtime do Chat como ponto de partida;
- usar Chat DB tables;
- usar Chat agent/session model;
- usar Chat API como planner/tool/media proxy;
- manual app→URL catalog;
- manual endpoint catalog;
- path/opId semantic routing;
- permission própria duplicando Core;
- DOM automation quando API existe;
- business data master no Graph;
- frontend authority de durable state;
- feature-specific Evidence/Entity/Decision/Event;
- `FrontlineContext` paralelo a WorkspaceContext sem gap provado;
- second workflow/action executor;
- departmental agent runtime;
- CoT persistence;
- speculative generic framework;
- hidden camera/mic/screen capture;
- raw media retention sem purpose/policy;
- facial recognition/emotion detection/hidden worker surveillance por default;
- voice-specific permission bypass;
- direct free-form LLM→PLC/CNC/robot command;
- Copilot substituindo safety interlock.

## 11. C1 bootstrap regra especial

A primeira implementação runtime é infraestrutura funcional, não AI/media feature:

```text
own API skeleton
→ health
→ JWT/Core integration
→ own MFE skeleton
→ plugin-ui/federation
→ responsive/accessibility/media-permission baseline
→ own manifest
→ Gateway/Compose
→ Portal full-page mount
→ global host contract
→ independence test with Chat offline
```

Planner/RAG/LLM/voice/vision começam somente quando `16` liberar C3.

## 12. Meeting/Frontline regra especial

Meeting/Frontline não podem ser implementados como produtos paralelos.

```text
same Copilot MFE/API
same WorkspaceContext/EntityRef
same Evidence
same Decision Gate
same Durable Work
same RBAC/policy
```

Ações extraídas de reunião/voz/câmera são **candidates** até passarem pelo governance pipeline.

Process observation gera knowledge candidate; nunca production rule automática.

## 13. OT regra especial

Enquanto não houver safety gate específico aprovado:

```text
industrial telemetry/read → potentially allowed by contract
free-form machine actuation → BLOCK
```

Autonomy L5 não muda isso.

## 14. Evidence mínima

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
media/provider/retention policy versions
device/session class
industrial safety boundary evidence
dependence/residual scans
CHAT_INDEPENDENCE result
ADR refs
```

## 15. Adversarial review

Antes de fechar:

1. Copilot funciona se Chat estiver fora do ar?
2. existe import/table/API Chat escondido?
3. Core/Domain owner foi duplicado?
4. Portal recebeu AI logic indevida?
5. sibling/unknown exige patch central?
6. retry/resume duplica write?
7. untrusted input/media consegue alterar policy?
8. source permissions permanecem válidas?
9. abstraction é realmente necessária?
10. próxima fase exigirá redesign previsível?
11. mic/camera/screen pode iniciar ocultamente?
12. raw media está sendo retida sem purpose/policy?
13. shared device vaza usuário/contexto anterior?
14. voice/camera muda autorização em relação ao texto?
15. visual finding foi promovido a fact/quality decision sem source oficial?
16. process observation virou surveillance/auto-learning?
17. há qualquer caminho LLM→machine command sem safety architecture?

## 16. COMPLETE_GATE blockers

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
HIDDEN_MEDIA_CAPTURE
UNDEFINED_MEDIA_RETENTION
SHARED_DEVICE_STATE_LEAK
VOICE_PERMISSION_BYPASS
VISUAL_FINDING_AS_UNVALIDATED_FACT
HIDDEN_WORKER_SURVEILLANCE
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
```

## 17. Report obrigatório

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
MEDIA_DEVICE_OT_IMPACT:
BASELINE:
IMPLEMENTATION:
WIRING_PROOF:
TESTS:
SECURITY_RBAC:
PRIVACY_RETENTION:
INDUSTRIAL_SAFETY:
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

## 18. Continuidade

Com `COMPLETE_GATE=PASS`, seguir a próxima subetapa desbloqueada por `16` sem pedir nova confirmação, salvo bloqueio real/destrutivo/decisão ausente.

Primeira ordem:

```text
C0.S0 → C0.S1 → C0.S2 → C0.S3 → C0.S4 → C0.S5 → C0.S6 → C0.S7 FOUNDATION_FREEZE → C1.S1
```