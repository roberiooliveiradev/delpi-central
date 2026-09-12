# Prompt mestre — Cursor — Minha DELPI Copilot Standalone

Implemente o **Minha DELPI Copilot como aplicação nova e independente**, do zero até o produto completo. Não evolua nem refatore o Minha DELPI Chat para atingir este objetivo.

A visão alvo inclui **escritório, reuniões e chão de fábrica**, com texto, voz, imagem, câmera, vídeo e documentos quando autorizados. Também inclui **identidade biométrica governada** de usuários conhecidos/enrolled e análise objetiva de padrões de processo conforme `54`. Essas capacidades não criam outro runtime nem bypassam RBAC, policy, Evidence, Decision Gate, privacidade ou segurança industrial.

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
usar Chat API como proxy/planner/tool/media/biometric runtime
usar Chat tables/sessions/agents como Copilot authority
alterar Chat para desbloquear Copilot
esperar roadmap/Onda J do Chat
```

O Chat pode ser lido em C0 somente como referência para patterns, lessons learned e anti-patterns.

## 2. North Star de experiência

O mesmo Copilot deve poder se apresentar como:

```text
GLOBAL      → painel contextual no Portal
WORKSPACE   → página completa
MEETING     → reunião assistida multimodal
FRONTLINE   → operador/posto/máquina
```

Todas as surfaces usam:

```text
same Copilot API
same product identity
same Core/RBAC
same policy/Decision Gate
same Evidence model
same Durable Work runtime
```

Meeting e Frontline **não** são agentes nem backends separados.

Quando biometric identity estiver habilitada:

```text
face/voice sample
→ enrolled-user candidate
→ confidence/policy/correction
→ userRef association
-X→ authentication/permission grant
```

## 3. Ordem de leitura

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc` + regras aplicáveis
3. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`
4. `.../16-execution-master-plan.md`
5. `.../50-standalone-copilot-application-architecture.md`
6. `.../51-platform-integration-baseline.md`
7. `.../52-standalone-repository-and-bootstrap-plan.md`
8. `.../17-component-and-contract-map.md`
9. `.../49-architecture-and-design-patterns-standard.md`
10. `.../53-multimodal-meeting-frontline-and-industrial-copilot.md`
11. `.../54-biometric-identity-and-human-observation-governance.md`
12. `.../20-testing-and-acceptance-matrix.md` seções aplicáveis
13. `.../21-data-and-state-model.md` quando houver state/persistence/media/biometric retention
14. `.../22-cursor-execution-protocol.md`
15. `.../25-requirements-traceability.md` CPs aplicáveis
16. `.../evidence/execution-ledger.md`
17. specs temáticas da etapa.

`16` é a única authority de ordem. `50` é authority do product boundary. `49` é authority de arquitetura/patterns. `53` é a spec temática de media/Meeting/Frontline/industrial safety. `54` governa biometric identity e Human Observation.

## 4. Ordem de construção

```text
C0 Platform + Architecture + Media/Privacy/Biometric/OT Foundation Freeze
→ C1 Standalone App Bootstrap
→ C2 Portal + Operational Context + Platform Commands
→ C3 Intelligence Core + Multimodal/Biometric Foundations
→ C4 Business Reads + Graph
→ C5 Governed Writes + Durable Foundation
→ C6 Product Work + Meeting/Frontline + Proactivity + Ecosystem
→ C7 Advanced Realtime + Autonomy + Optimization + Rollout
```

## 5. Primeira ação — C0.S0

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
- notifications/socket/context patterns;
- responsive/accessibility patterns;
- browser media permission/capture patterns, se existirem.

### Core
- `/me`, `/me/apps`, `/me/routes`;
- RBAC/permission resolver;
- manifest registration/versioning;
- app/route models;
- notification/audit/presence patterns;
- corporate avatar/photo sources;
- device/session registration patterns, se existirem.

### Gateway/Infra
- API/MFE path conventions;
- dev/prod parity;
- Compose profiles/services;
- env examples;
- health/scripts/storage/network;
- SSE/WebSocket/WebRTC/realtime proxy patterns;
- object/media storage;
- encrypted sensitive storage/key-management patterns;
- factory-network constraints quando documentadas.

### MFEs
- manifests;
- mount/unmount;
- federation config;
- plugin-ui usage;
- auth/API clients;
- context/deep links;
- responsive/touch/accessibility patterns;
- mic/camera/file/media usage existente.

### APIs
- existing APIs and OpenAPIs;
- auth/permissions;
- error/pagination envelopes;
- idempotency/write semantics;
- entity IDs;
- events/websockets;
- sources para OP, operação, máquina, produto, lote, material, posto, manutenção e qualidade.

### Collaboration/work infrastructure
- interaction rooms;
- requests/cases;
- notifications/inbox-like concepts;
- approvals/jobs/workers/events;
- meeting/collaboration artifacts;
- procedures/training sources.

### Media/Meeting/Frontline/Biometric
- speech/vision/media providers/configs;
- recording/transcription patterns;
- media/file/object storage;
- privacy/consent/retention owners;
- shared workstations/tablets/kiosks;
- production terminals;
- meeting-room devices/processes;
- accessibility/noise constraints;
- device identity/session patterns;
- corporate avatar/photo sources;
- voice samples, se existirem e forem governados;
- biometric enrollment owner/process;
- biometric template storage/key management;
- face/speaker recognition provider/capability, se existir;
- liveness/anti-spoof support, se existir;
- participant/presence sources;
- governance owner para Human Observation;
- prohibited person-inference classes.

Não assumir que fotos/avatares existentes podem ser usados para enrollment biométrico sem owner/purpose/policy explícitos.

### Industrial/OT — inventário somente
- machine/PLC/CNC/robot/SCADA/MES interfaces;
- telemetry/events owners;
- approved read-only APIs;
- machine command APIs/protocols existentes apenas como fato;
- safety PLC/interlocks/industrial owners;
- IT/OT segmentation/security ownership.

Não assuma que a existência de uma API/protocolo de comando autoriza o Copilot a usá-lo.

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

## 6. Foundation Freeze

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
MEDIA_PRIVACY_BOUNDARIES=PASS
BIOMETRIC_IDENTITY_BOUNDARY=PASS
HUMAN_OBSERVATION_BOUNDARY=PASS
SHARED_DEVICE_BOUNDARY=PASS
OPERATIONAL_CONTEXT_BOUNDARY=PASS
OT_SAFETY_BOUNDARY=PASS
CONFORMANCE_HARNESS=PASS
CHAT_RUNTIME_DEPENDENCY=0
FOUNDATION_DUPLICATION=0 material
```

## 7. Target physical structure

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

Meeting/Frontline/Biometric belong to these owners. Never create source inside Chat folders or separate product APIs merely because the surface/capability is different.

## 8. Architecture rules

```text
Clean Architecture
+ Ports & Adapters
+ pragmatic DDD
+ Event-Driven only with real event owner
+ State Machines for nontrivial lifecycle
+ light CQRS only when justified
```

External dependencies are adapters. Concrete wiring happens in Composition Root. Durable state is backend-owned.

Media/biometric providers, transport and storage also sit behind justified ports/adapters. Before creating interface/port/repository/factory/strategy/registry/base class/media service/biometric service/realtime gateway, pass the Abstraction Gate in `49`.

## 9. Portal integration

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

Meeting/Frontline:

```text
same Copilot MFE/API
→ different surface/layout/device capabilities
→ same auth/policy/state contracts
```

Portal must not contain planner, prompts, RAG, media/biometric intelligence, business action routing or Copilot persistence.

## 10. Auth/RBAC e biometria

```text
Keycloak → identity/JWT
Core API → platform permissions/apps/routes
Domain API → final business authorization/rules
Copilot → cannot elevate any of them
```

MFE receives `getAccessToken` from host. Copilot API validates JWT and uses official Core contracts.

In shared devices:

```text
device identity != user identity
biometric candidate != authenticated user/session
```

Biometric identity may assist recognition of a known enrolled user, but never grants permission by itself.

The current user/session must remain explicit and user switching must clear prior local state/context/media cache.

## 11. Operational context

Do not create a parallel industrial context model.

Use:

```text
WorkspaceContext
+ EntityRef(OP)
+ EntityRef(machine)
+ EntityRef(product)
+ EntityRef(operation)
+ EntityRef(lot/material/workstation when applicable)
+ bounded device/session metadata
```

Device/biometric context never grants permission.

## 12. Business Actions — build natively in Copilot

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

Input modality does not change this pipeline:

```text
text | voice | meeting transcript | frontline | visual finding | human observation
→ candidate intent/action
→ same validation/policy/Decision/executor
```

Biometric match only contributes identity/context evidence; it does not create a write channel.

## 13. Multimodal/media rules

Progressive scope:

```text
document/image
→ voice/audio
→ short video/screen
→ sampled/realtime only when justified
```

Required principles:

- explicit capture state;
- visible mic/camera/screen/identity-recognition indicators;
- no silent auto-resume after reload;
- provider behind adapters;
- size/duration/concurrency budgets;
- provenance: page/region/frame/time range;
- confidence/limitations;
- raw media persistence is optional, not default;
- transcript/raw audio/raw video/screen/derived Evidence/biometric template have distinct retention classes.

`MediaRef` and biometric refs are candidate primitives; create/freeze only if C0 proves transversal need.

## 14. Biometric Identity rules

Follow `54`.

Allowed target:

```text
explicit enrollment
→ protected biometric template
→ face/voice sample
→ closed-set match against approved enrolled users
→ candidateUserRef + confidence
→ threshold/policy/liveness when required
→ correctable association
```

Required:

- unknown/ambiguous stays unknown or requires confirmation;
- enrollment is explicit/revocable/versioned;
- template/embedding is protected and never ordinary log data;
- correction does not silently retrain enrollment;
- revoke/delete prevents future use;
- liveness/anti-spoof when purpose requires higher trust;
- biometric match never replaces login/session/Core RBAC/Decision Gate.

Do not implement open-world/indiscriminate face identification by default.

## 15. Human Observation rules

Copilot may analyze **observable process-related behavior**, e.g.:

- executed/missed step;
- tool/machine/material interaction;
- repeated motion/rework;
- time between steps;
- process-relevant movement;
- request for help;
- PPE/ergonomic observation only when formally defined by an owner/method.

Output is Evidence/Hypothesis/process candidate, not psychological truth.

Do not infer from face/voice/behavior:

```text
personality
honesty/trustworthiness
moral intent/loyalty
emotion as truth
health/diagnosis
sensitive attributes
global professional fitness
disciplinary propensity
```

Do not use biometrics/Human Observation as automatic authority for hiring, promotion, punishment, pay, formal performance evaluation, suspension or dismissal.

## 16. Meeting Mode rules

Meeting Mode must be a surface of the same Copilot.

When implemented:

```text
explicit start/stop
→ mic/transcription/camera/identity-recognition/screen status visible
→ optional governed participant/speaker association
→ authorized live data queries
→ facts/evidence
→ decisions/pending topics
→ candidate actions
→ ata viva
→ Task/Case/Room linkage
```

Keep semantics distinct:

```text
transcript != summary != biometric candidate != confirmed human decision != candidate action != executed action
```

A sentence in a meeting never becomes a write merely because the Copilot understood it.

## 17. Frontline rules

Frontline must prioritize operator reality:

- large touch targets;
- hands-free voice;
- touch/text fallback;
- current OP/machine/product/operation context;
- optional governed biometric identity assistance;
- drawing/procedure/revision freshness;
- camera/image assistance;
- bounded Human Observation of process patterns;
- safe degradation under network/provider failure;
- issue/escalation via governed Domain Actions;
- training assistance without conferring qualification automatically.

Observation of operator/process produces **candidate knowledge**, not automatic production behavior or secret worker profile.

## 18. Privacy and people-analysis rules

Default prohibitions:

- hidden mic/camera/screen/identity recognition;
- raw media or biometric-template retention without explicit purpose/policy;
- open-world/indiscriminate facial recognition;
- emotion/personality/honesty/character inference from face/voice;
- sensitive attribute inference;
- hidden individual productivity/person scoring;
- automatic employment decisions based on biometric/Human Observation;
- reusing media/biometric data for an unrelated purpose without governance.

Use data minimization by default.

## 19. Industrial/OT safety rule

Copilot is not a safety controller.

Default:

```text
OT telemetry/read → adapter → Evidence/context → analysis/recommendation
free-form LLM output → machine command = BLOCK
voice command → direct machine actuation = BLOCK
Copilot L5 → implicit OT permission = BLOCK
```

Any future physical actuation requires a **separate explicitly approved industrial safety gate** with deterministic typed commands, allowlist, machine state/preconditions, industrial owner, independent safety PLC/interlocks, human authorization as required, simulation/test environment, fail-safe/kill switch and audit.

Do not wire generic Business Action executor directly to PLC/CNC/robot control.

## 20. Quality/computer vision rule

Visual finding is normally:

```text
Evidence/Hypothesis
```

not automatically:

```text
official quality approval/rejection
```

When official process requires measurement/tolerance/equipment/authorized inspector, use those owners. Only explicitly validated inspection capabilities may make automated quality decisions.

## 21. Shared code policy

Reuse platform-neutral code only when:

- owner is already shared; or
- extraction to a neutral package is justified by 2+ real consumers and independent contracts/tests.

Never turn `minha-delpi-ai-api` or `minha-delpi-chat` into a library for Copilot.

## 22. C1 special rule

First runtime work is bootstrap, not intelligence/media/biometric feature:

```text
own API skeleton
→ health/config/logging
→ JWT/Core integration
→ own MFE skeleton
→ federation/plugin-ui
→ responsive/accessibility/media-permission baseline
→ own manifest
→ Gateway/Compose
→ Portal full-page mount
→ global host contract
→ Chat-offline independence test
```

LLM/planner/RAG/media/biometric intelligence start only in C3 after corresponding foundation gates.

## 23. Generic implementation protocol

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
→ SECURITY/RBAC/PRIVACY/BIOMETRIC/SAFETY
→ GENERALIZATION/METAMORPHIC/UNKNOWN
→ CHAT-INDEPENDENCE CHECK
→ ARCHITECTURE CONFORMANCE
→ RESIDUAL SEARCH
→ COMPLETE_GATE
→ DOCS/LEDGER
→ NEXT STEP
```

## 24. Prohibitions

- Chat runtime dependency;
- Chat DB authority;
- Chat agent/session migration;
- second RBAC/user authority;
- business rules in MFE/LLM;
- Portal AI/media/biometric intelligence;
- manual app URL catalog;
- manual endpoint catalog;
- DOM business automation;
- Graph as operational master database;
- feature-specific Entity/Evidence/Decision/Event types;
- `FrontlineContext` duplicating WorkspaceContext;
- Task executor parallel to Workflow runtime;
- Meeting-specific business action executor;
- voice-specific RBAC;
- biometric match as authentication/permission grant;
- biometric shadow user directory;
- open-world/indiscriminate face recognition by default;
- emotion/personality/trustworthiness inference from face/voice;
- automatic employment decisions from biometric/Human Observation;
- CoT persistence;
- secrets/JWT/templates in logs;
- speculative abstractions;
- hidden media/identity recognition capture;
- undefined raw-media/template retention;
- shared-device state leakage;
- hidden worker profiling/scoring;
- visual finding promoted to official fact without authority;
- arbitrary LLM→PLC/CNC/robot command;
- safety-interlock bypass.

## 25. Required tests

Use `20` as authority. In addition to feature tests, every relevant release boundary includes:

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

When media/Meeting/Frontline/Biometric apply:

```text
NO_HIDDEN_CAPTURE
RETENTION_POLICY_ENFORCED
MODALITY_RBAC_PARITY
SHARED_DEVICE_ISOLATION
BIOMETRIC_MATCH_NOT_AUTHORITY
UNKNOWN_IDENTITY_REMAINS_UNKNOWN
BIOMETRIC_TEMPLATE_PROTECTED
NO_SENSITIVE_PERSON_INFERENCE
NO_AUTOMATIC_EMPLOYMENT_DECISION_FROM_BIOMETRICS
VISUAL_EVIDENCE_SEMANTICS
NO_HIDDEN_WORKER_PROFILING
NO_ARBITRARY_OT_COMMAND
```

## 26. Complete Gate blockers

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
BIOMETRIC_PERMISSION_ELEVATION
LOW_CONFIDENCE_FORCED_IDENTITY
REVOKED_BIOMETRIC_STILL_ACTIVE
BIOMETRIC_TEMPLATE_LEAK
EMOTION_PERSONALITY_CHARACTER_INFERENCE
AUTOMATIC_EMPLOYMENT_DECISION_FROM_BIOMETRICS
HIDDEN_WORKER_PROFILING
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
```

## 27. Report format

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
MEDIA_DEVICE_BIOMETRIC_OT_IMPACT:
WIRING_PROOF:
TESTS:
SECURITY_RBAC:
PRIVACY_RETENTION:
BIOMETRIC_HUMAN_OBSERVATION:
INDUSTRIAL_SAFETY:
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

## 28. Start here

Execute only:

```text
C0.S0
```

Do not create the Copilot API/MFE, media/biometric runtime, Meeting Mode or Frontline Mode until C0.S7 `FOUNDATION_FREEZE=PASS`. After the freeze, start C1.S1 with the standalone API skeleton.
