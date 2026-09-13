# 02 — Arquitetura do Minha DELPI Copilot

**Status:** arquitetura alvo canônica  
**Boundary de produto:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Baseline da plataforma:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Estrutura física:** [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Decisão principal

Minha DELPI Copilot é aplicação nova com API/MFE/persistência/deploy próprios. Chat permanece sistema separado/reference-only.

```text
Portal/Core/Gateway/Keycloak/Domain APIs = platform/business foundations
Copilot API + Copilot MFE                = standalone intelligent product
Global/Workspace/Meeting/Frontline       = same product surfaces
Internet/External Connectors/Teams       = governed external information plane
Event/Signal Plane                       = governed perception
Automation & Execution Hub               = execution boundary
```

Copilot = inteligência/contexto/decisão/orquestração. O Hub executa capabilities; não cria segundo planner/AI/workflow authority.

## 2. Arquitetura macro

```text
Users / Devices / Meetings / Frontline / Background Events
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
      Portal / Copilot Host     Event / Signal Sources
              │                     │
              ▼                     ▼
      Copilot Federated MFE     Event Adapters
              │                     │
              └──────────┬──────────┘
                         ▼
                 Gateway / Nginx
                         │
                         ▼
              Copilot Standalone API
                         │
   ┌─────────────────────┼──────────────────────────────┐
   ▼                     ▼                              ▼
Context / Graph /     Policy / Decision             Knowledge / AI
Evidence              FAST|OPERATIONAL|REASONING     Expertise/LLM
   └─────────────────────┼──────────────────────────────┘
                         ▼
                  Durable Workflow
                         │
              semantic capability
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
   Domain APIs     Automation &         Human Task
                  Execution Hub
                   ┌────┼─────┐
                   ▼    ▼     ▼
                Function RPA Computer-Use
                   │
                   ▼
             legacy/external UI
                         │
                         ▼
               Outcome Verification
                         │
             Evidence / Audit / Notify
```

Public Internet, External Providers, AI/media/biometric providers e Secret/Vault owners permanecem atrás de adapters apropriados.

## 3. Authority Matrix

| Conceito | Authority |
|---|---|
| autenticação | Keycloak |
| usuário/apps/rotas/RBAC | Core API |
| navegação | Portal |
| business data/rules | Domain APIs |
| business technical actions | Domain OpenAPI/use cases |
| public web resource | external source/site |
| external account/resource | corresponding provider |
| external connection lifecycle | Copilot API |
| provider auth/scopes | provider contract + connection owner |
| provider credential material | approved secret/vault owner |
| event factual source | source system/provider |
| event correlation/watch semantics | Copilot Work/Event runtime |
| Decision Intelligence | Copilot Policy/Application using authoritative facts |
| planner/expertise/knowledge/evidence | Copilot API |
| Business Graph projection | Copilot API; source owners remain authoritative |
| Decision/Workflow/Task/Case/Watch | Copilot API |
| automation capability mapping | Copilot/neutral platform owner as frozen in C0 |
| executor mechanics | API/function/RPA/computer-use adapter owner |
| RPA worker/package/session | RPA infrastructure owner |
| background actor/service identity | Keycloak/Core/service identity owner + Copilot Policy |
| business outcome/postcondition | corresponding Domain/provider/source authority |
| autonomy policy | Copilot Policy/Admin |
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
HandleProviderEvent
HandleOperationalEvent
EvaluateOperationalReadiness
SelectDecisionPath
PrepareAutomationAction
ExecuteAutomationCapability
VerifyAutomationOutcome
EscalateAutomationException
PromoteKnowledgeCandidate
```

Provider names/endpoints/tokens/RPA selectors do not belong in Domain/Application.

### Infrastructure examples

```text
Core/Domain HTTP adapters
OpenAPI executor
LLM/RAG/media/biometric adapters
Search/Safe Web Fetch adapters
Microsoft/Google/WhatsApp provider adapters
Secret/Vault adapters
Event/webhook/subscription adapters
API/Function/RPA/Computer-Use executor adapters
Outcome verification adapters
Notification adapters
storage/cache/telemetry
```

## 5. Frontend architecture

```text
ui
state
data
features/contracts/adapters as needed
```

Frontend can present source/connection/Decision/Automation Admin/execution/outcome state, but never stores provider/RPA credentials or owns Durable Workflow.

## 6. Information + Event planes

### Internet Research

```text
research need
→ SearchProviderPort
→ SafeWebFetchPort
→ SourceRef/EvidenceRef
→ freshness/authority
→ synthesis
```

### External Connectors

```text
connect
→ provider authorization
→ ExternalConnection
→ secretRef
→ Provider Adapter
→ semantic capabilities
```

### Event/Signal Plane

```text
Domain/provider/MES/Watch source
→ authenticity/trust validation
→ EventEnvelope
→ dedupe/order/correlation
→ Watch / Workflow / Decision
```

Polling is bounded fallback only when supported event delivery is unavailable.

Event != authorization.

## 7. Decision Intelligence

```text
DecisionPathPolicy
├─ FAST        deterministic Policy/State Machine
├─ OPERATIONAL bounded reads/rules + optional classifier
└─ REASONING   Graph/Knowledge/Expertise/LLM
```

Known material readiness rules use deterministic Policy/Specification over authoritative facts whenever possible.

## 8. Semantic capability + executor architecture

Planner works with semantic capabilities:

```text
billing.invoice.issue
maintenance.request.create
production.report.validate
communication.email.send
inventory.read
```

Execution preference:

```text
API official
→ native supported integration
→ deterministic function/script
→ RPA
→ computer-use
→ Human Task
```

Planner never receives click/selector/coordenada/package-specific UI mechanics.

## 9. Automation & Execution Hub

```text
semantic capability
→ Policy/Decision/Autonomy
→ Durable Workflow
→ capability-to-executor mapping
→ AutomationExecution
→ ExecutorPort
→ concrete Adapter
→ technical result
→ OutcomeVerifier
→ authoritative business Outcome
```

AutomationExecution lifecycle:

```text
QUEUED → RUNNING → SUCCEEDED|FAILED|AMBIGUOUS|CANCELLED|TIMED_OUT
```

Hub does not imply another microservice. C0 decides ownership/physical split.

## 10. RPA / Computer Use boundaries

RPA is Infrastructure adapter/worker integration and never business authority. When used, require package/version, queue/lease, worker health, environment/session isolation, protected credential injection, idempotency and artifact retention.

Computer-use is advanced sandboxed/allowlisted fallback only when API/RPA deterministic options do not adequately solve the problem.

## 11. Outcome verification

Invariant:

```text
technical executor success != verified business outcome
```

Postcondition is verified against an authoritative source when material before declaring completion or notifying success.

## 12. Watch / Autonomy

```text
C6: OBSERVE | ADVISE | PREPARE
C7: ACT
```

`PREPARE != ACT`.

Autonomy is scoped by capability + actor/service identity + context + risk + limits + environment + policy.

```text
L5_DEFAULT = OFF
GLOBAL_UNRESTRICTED_L5 = FORBIDDEN
```

## 13. Provider-neutral external architecture

External read/write remains connection/scope governed, with `read != write` and `draft != send`. Teams is Microsoft 365 capability family, not separate Copilot runtime.

## 14. Workspace Context

```text
appId
routeId
EntityRef[]
SourceRef[]? bounded
filters/selection/dateRange
bounded device/session/execution refs
```

No JWT/provider/RPA secret, scope or autonomy truth in context.

## 15. Multimodal/Biometric/Meeting/Frontline

All remain same runtime/contracts:

- media → Evidence/provenance;
- biometric match → candidate userRef, not auth/RBAC;
- Meeting → sources + transcript + human decisions + candidate actions;
- Frontline → EntityRefs + approved sources + governed action/escalation;
- Human Observation → observable process Evidence only.

## 16. Business Graph / Evidence

Graph relates EntityRefs/RelationshipRefs/SourceRefs without replicating masters. RPA/Computer-Use output is Evidence/technical result, not authoritative master data.

## 17. Durable Work

One Workflow runtime coordinates reads, decisions, business/external/automation writes, waits/events, resume/revalidation and Outcome verification.

No provider/RPA-specific workflow engine.

## 18. Security boundaries

```text
external/event/RPA screen content = untrusted for policy
event != authorization
worker/device/biometric identity != business permission
provider/RPA credential → protected secret boundary only
PREPARE != ACT
technical result != verified Outcome
global L5 = forbidden
Copilot/Automation Hub L5 != OT permission
```

## 19. Deploy/infra

Copilot owns Docker/service/config/migrations/health/routes/manifest/tests/observability/rollback. Specific queue/broker/RPA orchestrator/worker infrastructure is not assumed until C0 proves reuse/create direction.

## 20. Generalization

Architecture must onboard without planner core patch:

- new Domain OpenAPI/app/entity/relation;
- new Expertise/Playbook;
- new media/biometric/search/external provider;
- new executor implementing equivalent semantic capability;
- RPA→API migration for a capability.

## 21. Sequência arquitetural

```text
C0 platform/media/biometric/external/automation/OT foundations
↓
C1 standalone bootstrap
↓
C2 Portal/context
↓
C3 intelligence + Event/Decision foundations
↓
C4 business/external reads + Graph + operational read intelligence
↓
C5 governed execution + executor/outcome foundation
↓
C6 product work + Automation Hub + PREPARE + Meeting/Frontline/learning
↓
C7 selected autonomous ACT + advanced realtime/external proactivity
```

## 22. Critério de sucesso estrutural

O Copilot está corretamente arquitetado quando consegue combinar DELPI + internet + fontes conectadas + eventos operacionais; selecionar entre regras determinísticas e raciocínio; coordenar semantic capabilities por APIs/functions/RPAs/computer-use/humans; verificar Outcomes; e fazer tudo isso sem duplicar authorities, sem provider/executor hardcode no planner, sem expor credentials, sem global L5, sem bypass de OT safety e totalmente independente do Minha DELPI Chat.
