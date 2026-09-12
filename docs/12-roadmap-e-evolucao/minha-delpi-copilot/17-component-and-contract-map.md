# Minha DELPI Copilot — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura canônica de ownership  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)

## 1. Owners canônicos

| Responsabilidade | Authority / owner | Consumidores | Proibido |
|---|---|---|---|
| identidade corporativa | Keycloak + Core integration | Portal, Copilot API, Domain APIs | identity própria/superuser do Copilot |
| associação biométrica a usuário conhecido | Copilot Biometric subsystem apontando para Core `userRef` | Meeting/Frontline | biometric match virar user authority |
| enrollment biométrico/template | Copilot Biometric + Security/Governance owner | Biometric adapters | template em log/MFE/raw DB genérico |
| permissões efetivas da plataforma | Core API/RBAC | Portal, Copilot API | permission derivada de prompt/context/pack/media/biometria |
| apps/rotas | Core API | Portal, Copilot | catálogo manual app→URL |
| navegação | Portal Router/AppHost | Copilot MFE/commands | URL livre do LLM |
| Copilot UI | `plugins/minha-delpi-copilot` | usuário/Portal/devices | implementar Copilot no Chat MFE |
| Copilot runtime | `minha-delpi-copilot-api` | Copilot MFE/Portal adapters | usar `minha-delpi-ai-api` como runtime |
| Copilot persistence | Copilot API migration chain | Copilot runtime | Chat tables/sessions/agents como authority |
| negócio | Domain APIs/use cases | UI/Copilot | duplicar regra na Copilot API/LLM |
| integrações DELPI/TOTVS | `api-delpi` quando owner | Copilot/other apps | copiar integração para Copilot |
| technical Business Action contract | OpenAPI da Domain API | Copilot Action Catalog/executor | endpoint catalog manual |
| workspace visual/operacional | Portal + MFE/iframe/device adapters | Copilot API | contexto como authorization |
| device identity/session | platform/device owner + Copilot bounded adapter | Frontline/Meeting | device identity substituir user identity |
| entity identity | domain owner + Copilot `EntityRef` projection | Context/Graph/Case/Evidence | IDs paralelos |
| relationships | domain owner + Copilot Graph projection | traversal/analysis | replicar datasets masters |
| capability projection | Copilot API derivada de authorities | retrieval/planner/UX | virar source técnica independente |
| expertise | Copilot Expertise Catalog | runtime/admin | permission/tool grant |
| playbook | Copilot Playbook Catalog | planner/workflows | endpoint como authority |
| knowledge visibility | source ACL + Copilot policy adapter | RAG | projeto/pack ampliar ACL |
| media capture controls | Copilot MFE + browser/device permissions | Copilot media adapters | hidden capture |
| media perception | Copilot media/extractor adapters | Evidence | OCR/VLM/STT como conclusão authoritative |
| face/speaker recognition | Copilot biometric adapters | identity candidates | open-world identity/permission authority |
| Human Observation | Copilot bounded observation adapter + governance | Evidence/Knowledge candidates | personality/emotion/character/employment scoring |
| raw media storage | approved media/storage owner if persistence required | Copilot | guardar indiscriminadamente no DB |
| biometric template storage | approved protected storage + security owner | biometric adapters only | template em ordinary application logs/API |
| media retention/consent | security/privacy governance + Copilot policy enforcement | Meeting/Frontline/Media | uma retention genérica para toda mídia |
| meeting semantics | Copilot API | Meeting MFE/Task/Case/Room | meeting backend paralelo |
| frontline assistance semantics | Copilot API | Frontline MFE/Task/Case | operator-agent runtime paralelo |
| industrial machine truth | OT/domain owner | Copilot read adapters when allowed | Copilot DB como machine authority |
| industrial safety/interlocks | OT/safety owner | machine systems | LLM/Copilot substituir interlock |
| evidence/provenance | Copilot Evidence contract + source authority | synthesis/Case/Meeting/Frontline/audit | claim material sem source quando disponível |
| policy/decision | Copilot Policy/Decision owner + final Domain API auth | writes/workflows | LLM relaxar policy |
| workflow/task/case/watch | Copilot API | MFE/Portal surfaces | engines paralelos |
| room/collaboration | existing owner if reusable; adapter from Copilot | Case/Room UX | membership conceder source ACL |
| inbox semantics | Copilot API | Copilot MFE/Portal | Portal virar workflow engine |
| notification delivery | Core/Portal shared owner quando aplicável | usuário | duplicar canal sem gap |
| model/compute policy | Copilot API infrastructure/policy | runtime | model selection espalhada em features |
| audit/evals | Copilot observability + platform audit where required | admin/security | CoT/secrets/JWT/raw media/templates in logs |

## 2. Componentes físicos alvo

| Componente | Responsabilidade |
|---|---|
| Portal Shell | host global, Router, current workspace, Copilot panel host |
| Core API | apps/routes/RBAC/governance/shared notifications/user authority |
| Keycloak | SSO/identity |
| Gateway | single public entry/routing |
| `plugins/plugin-ui` | shared UI components/design system |
| `plugins/minha-delpi-copilot` | Global/Workspace/Meeting/Frontline Copilot UX |
| `minha-delpi-copilot-api` | complete Copilot intelligence/work/media/biometric runtime |
| Copilot OpenAPI importer/index | derive action contracts from Domain APIs |
| Copilot Action Catalog | operational action representation derived from OpenAPI |
| Capability Projection | authorized semantic index |
| Expertise/Playbook Catalogs | dynamic specialization/methodology |
| Knowledge/RAG adapters | authorized knowledge retrieval |
| Media/Multimodal adapters | documents/images/audio/video/screen perception |
| Biometric adapters | closed-set face/speaker identity candidates, enrollment/liveness when approved |
| Human Observation adapter | process-grounded observable activity evidence |
| Media storage adapter | optional persisted media by policy |
| Protected biometric storage | enrollment/template refs when required |
| Policy/Decision subsystem | allow/deny/gates/autonomy/privacy/biometric constraints |
| Durable Workflow Runtime | steps/checkpoints/waits/resume |
| DELPI Business Graph projection | permission-aware references/relations |
| Task/Case/Watch services | persistent Copilot work semantics |
| Meeting service/module | meeting session/artifact semantics inside Copilot API |
| Frontline service/module | assistance session semantics inside Copilot API |
| Domain APIs | actual business data/rules/actions |
| OT/domain systems | machine/process truth and industrial safety ownership |
| Observability | Copilot traces/metrics/audit/evals |

`minha-delpi-ai-api` and `plugins/minha-delpi-chat` are **not components of this runtime graph**.

Meeting/Frontline/Biometric são módulos/capabilities do mesmo produto, não backends paralelos por default.

## 3. Primitive registry — frozen in C0

Names below are conceptual until C0 confirms final schemas.

### `CorrelationContext`
```text
requestId
conversationId
turnId
workflowId?
taskId?
caseId?
meetingId?
frontlineSessionId?
mediaSessionId?
traceId?
```

### `EntityRef`
```json
{
  "entityType": "product",
  "entityId": "90264238",
  "sourceSystem": "api-delpi",
  "label": "90264238"
}
```

Máquina, OP, operação, produto, lote, material, posto e ferramenta reutilizam `EntityRef` quando houver domain identity.

Usuário corporativo não é recriado como aggregate paralelo; biometric subsystem aponta para `userRef`/Core identity.

### `RelationshipRef`
```text
from EntityRef
relationshipType
to EntityRef
authority/sourceRef
confidence/provenance
```

### `SourceRef`
```text
sourceType
sourceId/provider
entityRef?
action/result/document/media ref?
timestamp/freshness
```

### `EvidenceRef`
```text
evidenceId
sourceRef
kind
value/ref
location?  # page/region/frame/time-range
mediaRef?
observedAt
freshness
confidence?
limitations[]
```

Epistemic classification:
```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

### `OutcomeRef`
Actual capability/action outcome reference with status/result/entity/evidence refs.

### Platform contracts
- `PlatformCommand`
- `PlatformCommandResult`
- `WorkspaceContext`
- `IframeBridgeEnvelope`

Targets are logical IDs/refs, never arbitrary URLs.

`WorkspaceContext` também carrega contexto operacional por `EntityRef`; não criar `FrontlineContext` paralelo por default.

### Candidate `MediaRef`

Somente se C0 provar necessidade transversal:

```text
mediaId/ref
kind
source
capturedAt
sessionRef?
retentionClass
consentPolicyRef?
hash/version?
storageRef?
```

MediaRef referencia mídia; Evidence continua o modelo canônico de interpretação/provenance.

### Candidate biometric/person observation contracts

Somente se C0 provar necessidade:

```text
BiometricEnrollmentRef
BiometricIdentityCandidate
PersonObservationRef
```

Semântica candidata:

```text
candidateUserRef
modality: face|voice
confidence
source/mediaRef
session/device ref
model/template version
policyRef
correction/revocation state
```

`BiometricIdentityCandidate` nunca representa autenticação ou permission grant.

`PersonObservationRef` descreve somente observação objetiva do processo, com Evidence/provenance; não é perfil psicológico.

### Capability/specialization
- `CapabilityProjection`
- `ExpertisePack`
- `ExpertiseSelection`
- `ExpertiseContext`
- `DomainPlaybook`
- `MultimodalEvidenceRef` quando ainda necessário após unificação com Evidence/Media refs

### Decision
- `DecisionGateRequest`
- `DecisionGateDecision`

Levels:
```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

### Durable work
- `WorkflowPlan`
- `WorkflowStep`
- `TaskRef`
- `CaseRef`
- checkpoint/wait state contracts

### Events/Audit
- `EventEnvelope`
- canonical AuditEvent/equivalent

### Meeting/Frontline

Não congelar um novo primitive global só por existir feature. Meeting/Frontline devem compor primitives acima.

Persisted records específicos só surgem quando C0/C6 provarem lifecycle/durable need.

## 4. Producer → consumer graph

```text
Keycloak/Core user authority
→ Portal/Core/Copilot API identity validation

Approved biometric enrollment
→ protected template store
→ face/speaker adapter
→ BiometricIdentityCandidate(userRef, confidence)
→ policy/correction
→ session/context association
-X→ permission grant

Core /me/apps/routes
→ Platform Capability Projection
→ Copilot planner
→ PlatformCommand
→ Portal validator/Router/MFE/Iframe

Domain OpenAPI
→ Copilot OpenAPI importer/index
→ Copilot Action Catalog
→ authorized Capability Projection
→ retrieval/planner
→ Policy/Decision Gate
→ generic executor
→ Domain API
→ OutcomeRef/EvidenceRef

Portal/MFE/Iframe/Device
→ WorkspaceContext
→ Copilot API understanding/retrieval

Documents/Images/Audio/Video/Screen
→ Copilot media adapters
→ MediaRef? + EvidenceRef
→ expertise/playbook/analysis

Visible human/process activity
→ Human Observation adapter
→ PersonObservationRef/Evidence
→ process analysis / Knowledge candidate
-X→ automatic employment decision

Meeting
→ media/transcript + participant identity candidates + authorized business reads
→ Evidence/decisions/candidate actions
→ Task/Case/Room/Workflow

Frontline
→ user/session + optional biometric candidate + device + operational EntityRefs + voice/camera
→ Knowledge/API/Graph reads
→ Evidence/guidance
→ governed escalation/action
→ Task/Case/Knowledge candidate

EntityRefs + RelationshipRefs
→ Copilot Business Graph traversal
→ Domain API source fetch
→ EvidenceRef

WorkflowPlan
→ Copilot Durable Runtime
→ Task/Case/Watch
→ Inbox/Room/notification adapters
```

## 5. Industrial/OT graph

Default:

```text
OT/domain system
→ approved telemetry/read adapter
→ EntityRef/Evidence
→ Copilot analysis/recommendation
```

Not default:

```text
LLM free text
-X→ PLC/CNC/robot command
```

Future OT actuation, if ever approved, requires separate deterministic command contract and industrial safety owner; it does not reuse generic Business Action execution blindly.

## 6. Independence graph

Must remain true:

```text
Copilot MFE ─X→ minha-delpi-chat source
Copilot API ─X→ minha-delpi-ai-api modules/endpoints as required runtime
Copilot DB  ─X→ Chat tables as authority
Copilot Media/Biometric ─X→ Chat media runtime as required dependency
```

Shared dependencies must be neutral platform components:

```text
Portal
Core
Keycloak
Gateway
plugin-ui
shared federation config
Domain APIs
approved shared libraries
approved neutral media/storage infrastructure
```

## 7. Anti-duplication rules

Do not create:

- another Core/RBAC/user authority;
- biometric shadow user directory as source of truth;
- manual app→URL registry;
- manual endpoint/action authority;
- `CaseEntityRef` incompatible with `EntityRef`;
- `FrontlineContext` incompatible with `WorkspaceContext`;
- feature-specific Evidence model;
- meeting-specific authorization model;
- voice-specific write executor;
- confirmation model parallel to Decision Gate;
- Task engine parallel to Workflow runtime;
- Watch-specific event envelope;
- Graph master copies of Domain API objects;
- Chat compatibility layer inside Copilot;
- departmental agent tool registries;
- raw-media/template persistence without policy/need;
- person profile model based on inferred personality/emotion/trustworthiness;
- automatic employment decision engine sourced from biometric/Human Observation;
- machine state master inside Copilot;
- generic LLM→OT command executor.

## 8. C0 ownership inventory questions

Before creating a component/schema:

```text
Who owns the source truth today?
Is this platform-shared or Copilot-owned?
Does an official contract already exist?
Would reuse introduce Chat product coupling?
Who produces and consumes it?
Does it need persistence/versioning?
Can the Domain API remain owner while Copilot stores only refs/projections?
Is a new shared package justified by 2+ real consumers?
Does WorkspaceContext/EntityRef/EvidenceRef already model this?
Does media need persistence or only transient processing?
Who owns consent/retention?
Who owns corporate user identity?
Is biometric enrollment explicit/revocable?
Could biometric result be confused with authentication/permission?
Is Human Observation objective/process-related or subjective person profiling?
Is the device shared and how is user isolation enforced?
Is this business automation or physical machine actuation?
Who owns industrial safety?
```

Unknown = `NOT_PROVEN`, not assumption.

## 9. Stabilization order

```text
platform/media/device/biometric/OT inventory
→ standalone boundaries
→ authorities
→ primitives
→ ports/persistence/privacy/biometric/integration contracts
→ architecture conformance
→ FOUNDATION_FREEZE
→ standalone bootstrap
→ intelligence/multimodal/biometric foundations
→ business features
→ Meeting/Frontline
→ advanced realtime/autonomy
```

No feature may redefine a frozen primitive silently.
