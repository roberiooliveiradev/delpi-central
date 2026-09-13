# 02 — Arquitetura do Minha DELPI Copilot

**Status:** arquitetura alvo canônica  
**Boundary de produto:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Baseline da plataforma:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Estrutura física:** [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Decisão principal

Minha DELPI Copilot é aplicação nova com API/MFE/persistência/deploy próprios. Chat permanece sistema separado/reference-only.

```text
Portal/Core/Gateway/Keycloak/Domain APIs = platform/business foundations
Copilot API + Copilot MFE                = standalone intelligent product
Global/Workspace/Meeting/Frontline       = same product surfaces
Internet/External Connectors             = governed external information plane
```

## 2. Arquitetura macro

```text
Users / Devices / Meeting / Frontline
                │
                ▼
          Portal / Copilot Host
                │
                ▼
        Copilot Federated MFE
                │
                ▼
          Gateway / Nginx
                │
                ▼
       Copilot Standalone API
                │
 ┌──────────────┼───────────────┬────────────────┐
 ▼              ▼               ▼                ▼
Core API     Domain APIs    Public Internet   External Providers
/RBAC        /OpenAPI       Search/Fetch      OAuth/API/Webhooks
 └──────────────┬───────────────┬────────────────┘
                ▼
  Knowledge / Evidence / Graph / Work
                │
                ▼
       Copilot-owned persistence
```

AI/media/biometric providers e secret/vault owner também ficam atrás de adapters apropriados.

## 3. Authority Matrix

| Conceito | Authority |
|---|---|
| autenticação | Keycloak |
| usuário/apps/rotas/RBAC | Core API |
| navegação | Portal |
| business data/rules | Domain APIs |
| business technical actions | Domain OpenAPI |
| public web resource | external source/site |
| external account/resource | corresponding provider |
| external connection lifecycle | Copilot API |
| provider auth/scopes | provider contract + connection owner |
| provider credential material | approved secret/vault owner |
| external source privacy/sharing | connection owner + privacy/security policy |
| Internet Research orchestration | Copilot API |
| planner/expertise/knowledge/evidence | Copilot API |
| Business Graph projection | Copilot API; source owners remain authoritative |
| Decision/Workflow/Task/Case/Watch | Copilot API |
| media/biometric processing | Copilot adapters; Core remains user authority |
| industrial machine truth/safety | OT/domain/safety owners |

## 4. Clean Architecture

```text
Domain
↑
Application
↑
Interfaces / Adapters
↑
Infrastructure
```

### Application examples

```text
ResearchExternalInformation
ConnectExternalSource
ReadExternalResource
DraftExternalMessage
SendExternalMessage
HandleProviderEvent
ReconcileExternalSubscription
PromoteExternalKnowledgeCandidate
```

Provider names/endpoints/tokens do not belong in Domain/Application.

### Infrastructure examples

```text
Core/Domain HTTP adapters
OpenAPI executor
LLM/RAG/media/biometric adapters
Search Provider adapter
Safe Web Fetch adapter
Microsoft/Google/WhatsApp/other provider adapters
Secret/Vault adapter
Webhook/subscription adapters
storage/cache/telemetry
```

## 5. Frontend architecture

```text
ui
state
data
features/contracts/adapters as needed
```

Frontend presents source/connection/scopes/draft/send/Decision UX but never stores provider refresh tokens or owns durable ExternalConnection state.

## 6. Internet Research

```text
research need
→ SearchProviderPort
→ candidate sources
→ SafeWebFetchPort
→ extraction
→ SourceRef/EvidenceRef
→ freshness/authority classification
→ synthesis
```

Rules:

- no arbitrary unrestricted HTTP from LLM URL;
- protected/internal destinations blocked;
- redirect revalidation;
- bounded content/time/concurrency;
- external content is untrusted;
- provenance/freshness preserved;
- public source never silently overrides internal authority.

## 7. External Connector architecture

```text
connect request
→ provider authorization
→ callback validation
→ ExternalConnection
→ secretRef
→ Provider Adapter
→ semantic capabilities
→ Planner/Policy
```

Connection types:

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

Provider scope != Core permission.

## 8. Provider-neutral capability architecture

Planner sees semantic capabilities, not provider names:

```text
communication.email.search/read/draft/send
calendar.events.read/create/update
files.search/read/create/update
messaging.conversations.read
messaging.message.send
```

Provider adapter maps semantic operation to Microsoft Graph, Google Workspace, WhatsApp Business or future contract.

## 9. External Reads

```text
authorized capability
→ connection/scope validation
→ provider adapter
→ normalized SourceRef/EvidenceRef
→ correlation/presentation
```

Do not replicate mailbox/file/message stores as Copilot master data.

## 10. External Writes

```text
intent
→ draft/preview when applicable
→ Policy/Decision Gate
→ connection/scope revalidation
→ provider adapter
→ verified outcome
→ Evidence/Audit
```

`read != write` and `draft != send`.

## 11. Provider Events

```text
provider webhook/push/subscription
→ interface/provider validation
→ EventEnvelope
→ dedupe/correlation
→ Watch/Workflow/Inbox
```

Subscription renewal/reconciliation is explicit lifecycle state. Event payload never grants permission or executes write directly.

## 12. External Knowledge

```text
external source/evidence
→ transient use OR candidate
→ privacy/freshness/licensing review
→ owner/eval/version
→ publish
```

Personal source never becomes organizational Knowledge automatically.

## 13. Workspace Context

```text
appId
routeId
EntityRef[]
SourceRef[]? bounded
filters/selection/dateRange
bounded device/session metadata
```

No JWT/provider token/scopes as authority.

## 14. Multimodal/Biometric/Meeting/Frontline

All remain same runtime/contracts:

- media → Evidence/provenance;
- biometric match → candidate userRef, not auth/RBAC;
- Meeting → transcript + internal/external sources + decisions/actions;
- Frontline → operational EntityRefs + approved sources;
- Human Observation → observable process Evidence only.

## 15. Business Graph

Graph relates EntityRefs/RelationshipRefs/SourceRefs without replicating external/internal masters. Source fetch always returns to canonical owner/adapter under current permission.

## 16. Durable Work

One Workflow runtime coordinates internal and external capabilities:

```text
plan
→ reads
→ decisions
→ writes/sends
→ waits/events
→ resume/revalidate
→ verified outcome
```

No provider-specific workflow engine.

## 17. Security boundaries

```text
external content = untrusted
provider token → protected secret boundary only
personal source != organizational source
provider event != authorization
biometric match != authorization
Copilot L5 != unrestricted external write
Copilot L5 != OT permission
```

## 18. WhatsApp boundary

Current architectural target is official supported business contracts, especially WhatsApp Business Platform where applicable. Personal WhatsApp Web scraping/session automation is not a default integration strategy.

## 19. Deploy/infra

Copilot owns Docker/service/config/migrations/health/routes/manifest/tests/observability/rollback. Egress, callback/webhook paths, provider credentials and external policies are versioned/configured without creating another product backend.

## 20. Generalization

Architecture must onboard without planner core patch:

- new Domain OpenAPI;
- new app/entity/relation;
- new Expertise/Playbook;
- new media/biometric provider;
- new search provider;
- new external connector/provider exposing equivalent semantic capabilities.

## 21. Sequência arquitetural

```text
C0 platform/media/biometric/external/OT foundations
↓
C1 standalone bootstrap
↓
C2 Portal/context
↓
C3 intelligence + Internet/connector foundations
↓
C4 business/external reads + graph
↓
C5 governed business/external writes + durable runtime
↓
C6 product work + external events + Meeting/Frontline + learning
↓
C7 selected external proactivity + advanced autonomy/realtime
```

## 22. Critério de sucesso estrutural

O Copilot está corretamente arquitetado quando consegue combinar fontes DELPI, internet e contas conectadas sem duplicar authorities, sem provider hardcode no planner, sem expor credentials, sem vazar dados entre usuários, sem envio implícito, com provenance/freshness, e continua totalmente independente do Minha DELPI Chat.
