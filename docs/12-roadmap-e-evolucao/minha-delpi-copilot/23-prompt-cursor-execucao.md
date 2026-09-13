# Prompt mestre — Cursor — Minha DELPI Copilot Standalone

Implemente o **Minha DELPI Copilot como aplicação nova e independente**, do zero até o produto completo. Não evolua nem refatore o Minha DELPI Chat para atingir este objetivo.

A visão alvo inclui **escritório, reuniões, chão de fábrica e fontes externas autorizadas**, com texto, voz, imagem, câmera, vídeo e documentos quando autorizados. Também inclui **identidade biométrica governada** de usuários conhecidos/enrolled, análise objetiva de padrões de processo, **Internet Research** e **External Connectors** conforme `54` e `55`. Essas capacidades não criam outro runtime nem bypassam RBAC, policy, Evidence, Decision Gate, privacidade, provider scopes ou segurança industrial.

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
usar Chat API como proxy/planner/tool/media/biometric/external runtime
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
same Internet/External Connector governance
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

Quando fonte externa estiver conectada:

```text
provider scope
→ allowed connector capability
→ read/write separation
→ policy/Decision when required
-X→ Core permission elevation
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
12. `.../55-internet-research-and-external-connectors.md`
13. `.../20-testing-and-acceptance-matrix.md` seções aplicáveis
14. `.../21-data-and-state-model.md` quando houver state/persistence/media/biometric/external retention
15. `.../22-cursor-execution-protocol.md`
16. `.../25-requirements-traceability.md` CPs aplicáveis
17. `.../evidence/execution-ledger.md`
18. specs temáticas da etapa.

`16` é a única authority de ordem. `50` é authority do product boundary. `49` é authority de arquitetura/patterns. `53` governa media/Meeting/Frontline/industrial safety. `54` governa biometric identity e Human Observation. `55` governa Internet Research, egress, OAuth, external connectors, external actions/events e external learning.

## 4. Ordem de construção

```text
C0 Platform + Architecture + Media/Privacy/Biometric/External/OT Foundation Freeze
→ C1 Standalone App Bootstrap
→ C2 Portal + Operational Context + Platform Commands
→ C3 Intelligence Core + Multimodal/Biometric/Internet/Connector Foundations
→ C4 Business + External Reads + Graph
→ C5 Governed Business/External Writes + Durable Foundation
→ C6 Product Work + Meeting/Frontline + External Events + Proactivity + Ecosystem
→ C7 Advanced Realtime + External Proactivity + Autonomy + Optimization + Rollout
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
- outbound HTTP/proxy/DNS/egress patterns;
- safe-fetch/SSRF/private-network/metadata protection patterns;
- OAuth callback patterns;
- webhook ingress/signature validation patterns;
- secret/vault owner;
- factory-network constraints quando documentadas.

### MFEs
- manifests;
- mount/unmount;
- federation config;
- plugin-ui usage;
- auth/API clients;
- context/deep links;
- responsive/touch/accessibility patterns;
- mic/camera/file/media usage existente;
- external connections/settings UX, se existir.

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

### Internet/External Connectors
- search/web research providers existentes;
- safe fetch/browser automation infra, se existir;
- Microsoft Graph app registrations/integrations;
- Google Workspace/Gmail app registrations/integrations;
- WhatsApp Business integrations;
- Slack/GitHub/other external connectors;
- OAuth delegated/application/service auth patterns;
- state/nonce/PKCE/callback validation patterns quando aplicáveis;
- provider token storage/rotation/revocation;
- user-delegated vs org-managed/shared/service ownership;
- provider webhook/subscription/push lifecycle;
- scheduler/reconciliation/full-sync fallback;
- attachment download/malware scanning;
- provider terms/compliance/data-classification owners.

Não assuma que uma conexão ou token existente pode ser reutilizado pelo Copilot. Não assuma que uma conta pessoal pode ser lida organizacionalmente.

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
EXTERNAL_EGRESS_BOUNDARY=PASS
OAUTH_CONNECTION_BOUNDARY=PASS
PROVIDER_SECRET_BOUNDARY=PASS
EXTERNAL_SOURCE_PRIVACY_BOUNDARY=PASS
EXTERNAL_EVENT_BOUNDARY=PASS
EXTERNAL_LEARNING_BOUNDARY=PASS
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

Meeting/Frontline/Biometric/Internet/Connectors belong to these owners. Never create source inside Chat folders or separate product APIs merely because a capability/provider is different.

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

Media/biometric/search/web/provider/secret/connector dependencies sit behind justified ports/adapters. Before creating interface/port/repository/factory/strategy/registry/base class/media service/biometric service/connector framework/web fetcher/realtime gateway, pass the Abstraction Gate in `49`.

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

External connections/settings stay in the same product/MFE. Portal must not contain planner, prompts, RAG, media/biometric/search/connector intelligence, business action routing or Copilot persistence.

## 10. Auth/RBAC, biometria e external scopes

```text
Keycloak → identity/JWT
Core API → platform permissions/apps/routes
Domain API → final business authorization/rules
External Provider OAuth/API → connection-specific scopes
Copilot → cannot elevate any of them
```

MFE receives `getAccessToken` from host. Copilot API validates JWT and uses official Core contracts.

In shared devices:

```text
device identity != user identity
biometric candidate != authenticated user/session
```

External scopes:

```text
provider scope != Core permission
provider scope != permission for another user
user-delegated connection != org-managed connection
```

Biometric identity may assist recognition of a known enrolled user, but never grants permission by itself.

Provider access/refresh tokens never go to LLM/MFE/logs. User switching must clear prior local state/context/media/external-source views.

## 11. Operational/external context

Do not create parallel context models.

Use:

```text
WorkspaceContext
+ EntityRef(OP/machine/product/operation/...)
+ SourceRef for external resources when material
+ bounded device/session metadata
```

Never place provider token, external credential or permission truth in WorkspaceContext.

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

Input modality does not change this pipeline.

Biometric match only contributes identity/context evidence; it does not create a write channel.

## 13. Internet Research rules

Follow `55`.

Target:

```text
research need
→ SearchProviderPort
→ search candidates
→ SafeWebFetchPort
→ extraction
→ SourceRef/EvidenceRef
→ freshness/relevance
→ grounded synthesis/citations
```

Required:

- external web is untrusted content;
- no arbitrary unrestricted HTTP from LLM URL;
- block private/link-local/loopback/metadata targets;
- revalidate redirects;
- type/size/time/concurrency limits;
- no sensitive context/secret exfiltration in search/fetch;
- sources/freshness visible when material;
- public web never silently overrides corporate source authority.

Browser automation is not the default integration. Prefer official API/connector, then structured search/fetch, browser only when justified and sandboxed.

## 14. External Connector rules

Follow `55`.

Connection lifecycle:

```text
connect request
→ official OAuth/API authorization
→ callback validation
→ ExternalConnection
→ protected secretRef
→ provider adapter
→ normalized connector capabilities
```

Distinguish:

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

Required:

- least privilege scopes;
- scope disclosure/consent;
- state/nonce/PKCE/callback validation as applicable;
- token refresh/revoke/reconnect;
- secrets outside LLM/MFE/logs;
- no cross-user connection leak;
- provider-neutral planner;
- provider-specific rules inside adapters;
- kill switches.

WhatsApp: use supported official contracts (not default WhatsApp Web personal-session scraping). Current target is business messaging through official WhatsApp Business Platform contracts when applicable.

## 15. External Read/Write rules

Reads may include, when connected and authorized:

```text
email search/read
calendar read
files search/read
messaging conversation read
```

Writes are separate capabilities:

```text
draft
send
create/update event
message send
file create/update
```

Invariant:

```text
read != write
draft != send
```

External write requires live connection/scope validation, policy/Decision Gate when material, target/payload preview where needed, idempotency/outcome handling and verified provider outcome.

Generated text is never sent merely because it was drafted.

## 16. External Events / Webhooks

When provider supports events:

```text
provider push/webhook/subscription
→ authenticity validation
→ normalize
→ EventEnvelope
→ dedupe/correlation
→ Watch/Inbox/Workflow
```

Handle:

- duplicate/out-of-order events;
- subscription expiry/renewal;
- missed events/reconciliation;
- revoked permission;
- disabled connection;
- stale/degraded state.

Do not let webhook payload alter system policy or execute ungoverned write.

## 17. External Learning rules

Classify:

```text
TRANSIENT_RESEARCH
SESSION_EVIDENCE
USER_KNOWLEDGE_CANDIDATE
ORGANIZATIONAL_KNOWLEDGE_CANDIDATE
```

Never:

```text
web/email/message/file
→ automatic corporate truth
```

Durable promotion requires source/provenance/freshness/privacy/licensing checks plus owner/review/eval/version/publish as appropriate.

Personal mailbox/message/file does not become shared Knowledge/Case/Room content without explicit authorized sharing/promotion.

## 18. Multimodal/media rules

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

External attachments also pass safe download/type/size/malware policy before extraction.

## 19. Biometric Identity rules

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

## 20. Human Observation rules

Copilot may analyze observable process-related behavior only, as specified in `54`.

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

## 21. Meeting Mode rules

Meeting Mode must be a surface of the same Copilot.

When implemented:

```text
explicit start/stop
→ mic/transcription/camera/identity-recognition/screen status visible
→ optional governed participant/speaker association
→ authorized live internal/external queries
→ facts/evidence
→ decisions/pending topics
→ candidate actions
→ ata viva
→ Task/Case/Room linkage
```

Keep semantics distinct:

```text
transcript != summary != biometric candidate != external source != confirmed human decision != candidate action != executed action
```

A sentence in a meeting never becomes a write merely because the Copilot understood it.

## 22. Frontline rules

Frontline must prioritize operator reality and preserve the same security/external-source governance. External sources are supplementary, not a replacement for current internal procedure/revision authority.

Observation of operator/process produces **candidate knowledge**, not automatic production behavior or secret worker profile.

## 23. Privacy and people/external-data rules

Default prohibitions:

- hidden mic/camera/screen/identity recognition;
- raw media/biometric/external sensitive retention without explicit purpose/policy;
- open-world/indiscriminate facial recognition;
- emotion/personality/honesty/character inference from face/voice;
- sensitive attribute inference;
- hidden individual productivity/person scoring;
- automatic employment decisions based on biometric/Human Observation;
- unrestricted web fetch/browser access;
- provider credentials/tokens in prompt/LLM/MFE/logs;
- cross-user external data leakage;
- personal-source auto-promotion to organization;
- implicit external send;
- reusing external data for unrelated purpose without governance.

Use data minimization by default.

## 24. Industrial/OT safety rule

Copilot is not a safety controller.

Default:

```text
OT telemetry/read → adapter → Evidence/context → analysis/recommendation
free-form LLM output → machine command = BLOCK
voice command → direct machine actuation = BLOCK
Copilot L5 → implicit OT permission = BLOCK
```

Any future physical actuation requires a separate explicitly approved industrial safety gate.

## 25. Shared code policy

Reuse platform-neutral code only when owner is already shared or extraction is justified by real consumers and independent contracts/tests.

Never turn Chat into a library. Do not create one universal connector framework before real boundaries/providers justify it.

## 26. C1 special rule

First runtime work is bootstrap, not intelligence/media/biometric/Internet/connector feature:

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

LLM/planner/RAG/media/biometric/Internet/connector runtime starts only in later phases after corresponding foundation gates.

## 27. Generic implementation protocol

For one `C*.S*` at a time:

```text
REVALIDATE HEAD
→ READ AUTHORITIES INCLUDING 55 WHEN EXTERNAL IS MATERIAL
→ IDENTIFY OWNER/LAYER/PATTERN
→ ABSTRACTION GATE
→ DEPENDENCY GATE
→ BASELINE
→ MINIMAL CORRECT DIFF
→ WIRE PRODUCER/CONSUMER
→ UNIT/CONTRACT/INTEGRATION
→ POSITIVE/SIBLING/NEGATIVE
→ SECURITY/RBAC/PRIVACY/BIOMETRIC/EXTERNAL/SAFETY
→ GENERALIZATION/METAMORPHIC/UNKNOWN
→ CHAT-INDEPENDENCE CHECK
→ ARCHITECTURE CONFORMANCE
→ RESIDUAL SEARCH
→ COMPLETE_GATE
→ DOCS/LEDGER
→ NEXT STEP
```

## 28. Prohibitions

- Chat runtime dependency;
- Chat DB authority;
- Chat agent/session migration;
- second RBAC/user authority;
- business rules in MFE/LLM;
- Portal AI/media/biometric/external intelligence;
- manual app URL catalog;
- manual endpoint catalog;
- provider hardcode in planner;
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
- unrestricted URL fetch/browser;
- SSRF/private-network/metadata access;
- provider token/secret in LLM/MFE/log;
- cross-user external source leak;
- read scope used as write scope;
- generated draft sent implicitly;
- external message/web content changing policy;
- personal source auto-promoted to org Knowledge;
- WhatsApp Web personal-session scraping as default connector;
- CoT persistence;
- speculative abstractions;
- hidden media/identity recognition capture;
- undefined raw-media/template/external retention;
- shared-device state leakage;
- hidden worker profiling/scoring;
- visual finding promoted to official fact without authority;
- arbitrary LLM→PLC/CNC/robot command;
- safety-interlock bypass.

## 29. Required tests

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

When Internet/External Connectors apply:

```text
SAFE_WEB_FETCH_SSRF_BLOCK
EXTERNAL_CONTENT_UNTRUSTED
OAUTH_LEAST_PRIVILEGE
OAUTH_CALLBACK_VALIDATION
NO_PROVIDER_TOKEN_LEAK
EXTERNAL_CONNECTION_ISOLATION
DRAFT_NOT_SEND
EXTERNAL_WRITE_DECISION_GATE
VERIFIED_EXTERNAL_OUTCOME
WEBHOOK_AUTH_DEDUPE_RECONCILIATION
NO_PERSONAL_SOURCE_AUTO_PROMOTION
UNKNOWN_CONNECTOR_NO_PLANNER_PATCH
WHATSAPP_SUPPORTED_CONTRACT_ONLY
```

## 30. Complete Gate blockers

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
UNSAFE_WEB_FETCH
SSRF_PRIVATE_NETWORK_ACCESS
EXTERNAL_PROMPT_INJECTION_POLICY_CHANGE
PROVIDER_TOKEN_LEAK
CROSS_USER_EXTERNAL_DATA_LEAK
EXTERNAL_WRITE_WITHOUT_GATE
DRAFT_SENT_IMPLICITLY
INVALID_WEBHOOK_ACCEPTED
PERSONAL_SOURCE_AUTO_PROMOTED_TO_ORG_KNOWLEDGE
UNSUPPORTED_WHATSAPP_SESSION_AUTOMATION
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
```

## 31. Report format

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
MEDIA_DEVICE_BIOMETRIC_EXTERNAL_OT_IMPACT:
WIRING_PROOF:
TESTS:
SECURITY_RBAC:
PRIVACY_RETENTION:
BIOMETRIC_HUMAN_OBSERVATION:
EXTERNAL_CONNECTIONS_EGRESS:
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

## 32. Start here

Execute only:

```text
C0.S0
```

Do not create the Copilot API/MFE, media/biometric/Internet/connector runtime, Meeting Mode or Frontline Mode until C0.S7 `FOUNDATION_FREEZE=PASS`. After the freeze, start C1.S1 with the standalone API skeleton.
