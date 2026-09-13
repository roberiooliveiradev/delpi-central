# Minha DELPI Copilot — Modelo de Dados, Estado e Persistência

**Status:** target arquitetural standalone  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Princípio

Todo estado durável do Copilot pertence à **Copilot API nova** ou a um owner corporativo/externo explicitamente referenciado.

```text
REFERENCE
→ refs para entities/users/resources de owners externos

COPILOT RUNTIME STATE
→ conversations/turns/plans/context snapshots

COPILOT DURABLE WORK STATE
→ decision/workflow/task/case/watch/inbox

COPILOT MEDIA/BIOMETRIC STATE
→ meeting/frontline/media/biometric metadata only when required

COPILOT EXTERNAL CONNECTION STATE
→ connection metadata, scopes, sync/subscription state, secretRef

DERIVED INDEX/CACHE
→ capabilities/expertise/graph/search/external caches

DOMAIN DATA
→ permanece nas Domain APIs

EXTERNAL RESOURCE DATA
→ permanece no provider; Copilot guarda refs/cache bounded apenas quando necessário

CORPORATE USER IDENTITY
→ permanece Keycloak/Core-owned
```

Proibido usar Chat tables como foundation, criar shadow user directory, ou replicar mailbox/Drive/WhatsApp como novo system of record.

## 2. Storage ownership

Target:

```text
minha-delpi-copilot-api/migrations/
→ única migration chain do Copilot
```

Mesmo cluster físico não implica mesma authority lógica.

Biometric templates e provider credentials podem exigir storage/keys separados do banco transacional; C0 define owner/adapter antes de criar tabela.

## 3. Regra C0 antes de migrations

Definir:

- naming/IDs/versioning;
- retention/LGPD/data classification;
- media/biometric/external retention classes;
- encryption/key management;
- connection/credential ownership;
- provider token refresh/revoke/delete;
- personal vs organizational source semantics;
- webhook/subscription/sync state;
- external cache TTL/freshness;
- concurrency/idempotency;
- migration/rollback;
- Copilot-owned versus refs/projections;
- MediaRef/biometric refs/external refs somente se necessários.

## 4. Shared references

### CorrelationContext

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

### EntityRef

```text
entityType
entityId
sourceSystem/domain
label?
version/revision?
```

### UserRef

Aponta para Keycloak/Core. Biometric enrollment/candidate aponta para `userRef`; não cria usuário paralelo.

### SourceRef / EvidenceRef / OutcomeRef

Usados transversalmente por Domain API, web, connectors, multimodal, Graph, workflow, Meeting/Frontline e audit.

External `SourceRef` pode conter, quando necessário:

```text
sourceType: web|email|calendar|file|message|external_api|...
providerRef
resourceRef
connectionRef?        # opaque/bounded; sem credential
observedAt/fetchedAt
freshness/version?
```

Nunca guardar token/secret em SourceRef/EvidenceRef.

## 5. MediaRef — candidate foundation

Se C0 provar necessidade:

```text
mediaId/ref
kind
source
capturedAt
sessionRef?
ownerRef?
retentionClass
policyRef?
hash/version?
storageRef?
```

Evidence referencia MediaRef/location sem copiar mídia bruta.

## 6. Workspace Context

Pode carregar:

```text
appId
routeId
EntityRefs[]
SourceRefs[]?         # apenas refs bounded de recursos externos materialmente atuais
filters/selection/dateRange
bounded device/session metadata
```

Nunca persistir como truth:

- DOM/React state;
- JWT/provider tokens/secrets;
- permissions/scopes como authority;
- datasets/mailboxes/files completos;
- biometric candidate como permission truth.

## 7. Device/session metadata

Device identity != user identity.

```text
deviceRef/workstationRef
surface
deviceClass
sessionStartedAt
capability flags
```

## 8. Biometric identity state

Separar:

```text
RAW BIOMETRIC MEDIA
BIOMETRIC ENROLLMENT
BIOMETRIC TEMPLATE
IDENTITY CANDIDATE / ASSOCIATION
```

`BiometricIdentityCandidate != authenticated session != permission grant`.

Enrollment é versionado/revogável; template é protegido e nunca ordinary log/API data; correction não retraina silenciosamente.

## 9. Human Observation state

Se necessário, `PersonObservationRef` representa somente observações objetivas ligadas ao processo com Evidence/provenance. Não armazenar personality/trust/emotion/health/sensitive-attribute/global employee score.

## 10. ExternalConnection — candidate owned state

C0 deve confirmar o schema final. Conceitualmente:

```text
connectionId
ownerType: USER_DELEGATED|ORG_MANAGED|SHARED_RESOURCE|SERVICE_CONNECTION
ownerRef
providerKey
providerAccount/resource label bounded
status
scopes[]
secretRef                # opaque reference to protected storage
createdAt/updatedAt
expiresAt?
lastValidatedAt?
policyRef
```

Estados conceituais:

```text
PENDING_AUTH
→ ACTIVE
→ EXPIRED | REAUTH_REQUIRED | REVOKED | DISABLED | ERROR
```

Nunca persistir access/refresh token em campo comum quando secret/vault owner puder armazená-lo.

`secretRef` nunca vai para LLM/MFE/SourceRef/Evidence.

## 11. Provider secret/credential state

Credential material pertence a approved secret owner/adapter.

Copilot persistence pode guardar apenas metadata bounded:

```text
secretRef
credentialKind
version?
lastRotatedAt?
status
```

Proibido:

- token plaintext em tabela comum;
- token em logs/telemetry;
- token em conversation/context;
- refresh token no browser/MFE.

## 12. External resource references

Preferir `SourceRef` antes de criar `ExternalResourceRef` novo.

Se C0 provar necessidade transversal:

```text
providerKey
resourceType
resourceId opaque
connectionRef
version/changeKey/etag?
observedAt
```

Não copiar conteúdo integral por default.

## 13. External sync/subscription state

Para providers event-driven/push:

```text
subscriptionId
connectionRef
resourceScope
providerSubscriptionRef
status
expiresAt
lastEventAt?
lastReconciledAt?
syncCursor/deltaRef? bounded
errorCode?
```

Lifecycle:

```text
CREATING → ACTIVE → RENEWING → ACTIVE
                   ├→ REAUTH_REQUIRED
                   ├→ EXPIRED
                   ├→ DISABLED
                   └→ ERROR
```

Cursor/delta token é provider state, não business permission.

## 14. External cache / fetched content

Cache é derivado e invalidável.

Toda persistência external content define:

```text
connection/user scope
sourceRef
fetchedAt
freshness/TTL
content hash/version
classification
retention/delete policy
```

Nunca usar cache entre usuários/conexões se isso quebrar isolation. Personal content não vira shared cache por default.

## 15. Internet Research state

Pesquisa pode ser totalmente transitória.

Se Task/Case/audit exigir persistência:

```text
researchRunRef
query/goals bounded
sourceRefs[]
evidenceRefs[]
fetchedAt
freshness metadata
policy/data-classification metadata
```

Não persistir páginas inteiras sem necessidade. Preferir refs/extracts bounded conforme purpose/licensing/privacy.

## 16. Copilot conversations

Copilot-owned, sem `agent_id/chat_mode` do Chat.

Turn pode referenciar:

```text
workspace snapshot
media/evidence refs
identity candidate refs
external source refs
plan/outcome refs
```

Sem chain-of-thought ou provider credentials.

## 17. Media/Meeting/Frontline sessions

Persistir apenas quando continuity/audit/policy exigir.

Meeting pode referenciar participant identity candidates, transcript, internal/external source refs, decisions/actions/Tasks.

Frontline pode referenciar actor/device/EntityRefs/media/Evidence/process observations, sem virar employee-surveillance datastore.

## 18. Retention classes

Separar pelo menos:

```text
TRANSIENT_MEDIA
TRANSCRIPT
RAW_AUDIO
RAW_VIDEO
SCREEN_CAPTURE
DERIVED_EVIDENCE
BIOMETRIC_ENROLLMENT_MEDIA
BIOMETRIC_TEMPLATE
IDENTITY_CANDIDATE
PERSON_OBSERVATION
WEB_RESEARCH_TRANSIENT
WEB_RESEARCH_EVIDENCE
EXTERNAL_RESOURCE_CACHE
EXTERNAL_MESSAGE_OR_FILE_EVIDENCE
EXTERNAL_CONNECTION_METADATA
EXTERNAL_SUBSCRIPTION_STATE
MEETING_ARTIFACT
FRONTLINE_RECORD
```

Cada classe define purpose, access, retention, redaction/encryption, revoke/delete/anonymize e provider handling.

## 19. Evidence

Evidence pode apontar para fontes internas, públicas ou conectadas:

```text
evidenceId
sourceRef
entityRefs[]
userRef? only when necessary
kind
valueRef/value bounded
location?
mediaRef?
observedAt
freshness
confidence?
limitations[]
extractor/model/version?
```

Public web, email ou message não vira FACT apenas porque foi recuperado; authority/freshness/context importam.

## 20. Decision Gate

Pode referenciar Business Action ou External Action.

```text
actionRef
argumentsHash
impactPreview
evidenceRefs
risk/sensitivity
status
actor/approver refs
connectionRef? bounded
```

Connection scope é revalidado no execute; Decision antiga não sobrevive a material change/revocation.

## 21. Durable Workflow

Workflow/Step continua runtime único para business e external capabilities.

Step externo pode guardar somente refs bounded:

```text
capabilityRef
connectionRef?
target/resourceRef?
idempotencyKey?
resultRef/errorCode
```

Nunca token.

## 22. Task / Case / Room / Inbox

Podem referenciar external SourceRefs/EvidenceRefs. Regras:

- source permission continua necessária;
- Room membership não concede mailbox/file access;
- personal source compartilhado exige ação/policy explícita;
- revogação de connection sanitiza/limita acesso conforme retention/purpose;
- conteúdo integral fica com owner sempre que possível.

## 23. Event / Watch

`EventEnvelope` normaliza eventos internos/externos.

External provider event state nunca concede permission. Watch ACT revalida Core/domain/policy/connection/scope no disparo.

## 24. Organizational Knowledge

External source pode produzir:

```text
TRANSIENT_RESEARCH
SESSION_EVIDENCE
USER_KNOWLEDGE_CANDIDATE
ORGANIZATIONAL_KNOWLEDGE_CANDIDATE
```

Organizational publish exige provenance, owner, review/eval, freshness, privacy/licensing e versioning conforme policy.

Não existe `external message → production truth` automático.

## 25. Idempotência/concurrency

Business write e external send/update precisam proteger replay/resume/ambiguous outcome.

`draft != send`. Provider timeout após write exige outcome verification antes de retry quando possível.

## 26. Shared-device isolation

Troca de usuário limpa auth/context/media/external-resource local state. Connection de user A nunca fica utilizável por user B.

## 27. OT/machine state

Machine truth permanece no owner OT/domain. External connectors não são atalho para physical actuation.

## 28. Migration strategy

Copilot migrations independentes:

```text
EXPAND → compatible readers → writers → optional backfill → CUTOVER → CLEANUP
```

Provider/connector migration deve ocorrer por adapters/versioned contracts, sem reescrever Domain/Application.

## 29. State machines relevantes

```text
ExternalConnection:
PENDING_AUTH → ACTIVE → EXPIRED|REAUTH_REQUIRED|REVOKED|DISABLED|ERROR

ExternalSubscription:
CREATING → ACTIVE → RENEWING → ACTIVE|EXPIRED|REAUTH_REQUIRED|DISABLED|ERROR

Decision/Workflow/Meeting/Media/Biometric:
conforme lifecycles canônicos aplicáveis
```

Só persistir state machine quando lifecycle real justificar.

## 30. Explicitamente proibido

- Chat state/tables como Copilot storage;
- token/provider secret em prompt/log/MFE/SourceRef/Evidence;
- shadow copy de mailbox/Drive/WhatsApp como master data;
- cross-user external cache/state leak;
- personal source promovida implicitamente para organizational Knowledge;
- connection scope persistido como Core permission;
- external resource duplicated as permanent master without owner/purpose;
- biometric/employee-surveillance dataset por default;
- free-form machine-control state como Copilot authority.
