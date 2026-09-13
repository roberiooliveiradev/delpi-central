# 15 — Mapa de integração com a Minha DELPI

**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Mapa macro

```text
                           Keycloak / Core
                         identity / RBAC
                               │
                               ▼
Portal ───────────────→ Copilot MFE ───────────────→ Gateway
                               │                       │
                               └──────────┬────────────┘
                                          ▼
                                Copilot Standalone API
                                          │
       ┌──────────────────────┬───────────┼───────────────┬──────────────────┐
       ▼                      ▼           ▼               ▼                  ▼
 Domain APIs/OpenAPI     Public Internet External       Event/Signal       AI/Media/
 business authority     Search/SafeFetch Providers     Sources            Biometric
       │                      │           │               │                  │
       └──────────────────────┴───────────┼───────────────┴──────────────────┘
                                          ▼
                          Context / Graph / Evidence
                          Policy / Decision Intelligence
                                          │
                                          ▼
                                  Durable Workflow
                                          │
                              semantic capability
                                          │
             ┌────────────────────────────┼────────────────────────────┐
             ▼                            ▼                            ▼
       Domain/API Executor       Automation & Execution Hub       Human Task
                                      │      │
                                    RPA    Computer-Use
                                      │
                                      ▼
                                  legacy UIs
                                      │
                                      ▼
                              Outcome Verification
                                      │
                              Evidence / Notify
```

## 2. Portal ↔ Copilot

Portal hospeda/navega/contextualiza. Copilot MFE conversa com Copilot API. Portal não contém planner, connector/executor credentials, RPA logic ou automation workflow engine.

## 3. Copilot ↔ Core

Core continua authority de apps/routes/RBAC/user context. External scope, event source, worker/device identity ou autonomy level não modificam Core permissions.

Background action usa user/service identity explícita conforme foundation.

## 4. Copilot ↔ Domain APIs

```text
OpenAPI
→ Action Catalog
→ authorized semantic capability
→ Planner/Policy
→ Domain/API executor
→ Outcome/Evidence
```

Quando a Domain API expõe action autoritativa adequada, ela é preferida antes de RPA.

## 5. Copilot ↔ Public Internet

Research → SearchProviderPort → SafeWebFetchPort → SourceRef/EvidenceRef → synthesis, com egress validation/provenance/freshness.

## 6. Copilot ↔ External Providers / Teams

```text
Connect
→ OAuth/API authorization
→ ExternalConnection
→ secretRef
→ Provider Adapter
→ semantic connector capabilities
```

Teams permanece capability family Microsoft 365. Provider token nunca vai ao planner/LLM/MFE.

## 7. Event / Signal Sources ↔ Copilot

```text
Domain event / provider webhook / MES signal / Watch timer
→ source adapter/authenticity validation
→ EventEnvelope
→ dedupe/order/correlation
→ Watch / Workflow / Decision
```

Polling/scheduler only bounded fallback. Event payload never directly executes a material write.

## 8. Decision Intelligence

```text
Event / user intent
→ FAST | OPERATIONAL | REASONING
→ structured finding/decision candidate
```

FAST uses deterministic Policy/Specification where sufficient. REASONING uses Graph/Knowledge/Expertise/LLM only when necessary.

## 9. Copilot ↔ Automation & Execution Hub

Integration contract is semantic:

```text
capabilityRef
+ actor/service identity
+ validated arguments
+ correlation/idempotency
+ policy/decision context
→ executor mapping
→ AutomationExecution
```

Planner never sends clicks/selectors/coordinates.

The Hub may be a Copilot-owned bounded module or neutral platform service only after C0 ownership evidence; no separate brain/planner.

## 10. Executor integrations

Preferred order:

```text
Domain/API
→ native supported integration
→ deterministic function/script
→ RPA
→ computer-use
→ Human Task
```

### RPA integration

```text
AutomationExecutorPort
→ RPA Adapter
→ Orchestrator/Queue
→ Worker/Session
→ legacy UI
```

When RPA exists, integration includes worker health, lease/concurrency, package/version, protected credentials, session isolation, timeout/cancel and artifact retention.

### Computer-use integration

Sandboxed/allowlisted fallback only; no unrestricted intranet/desktop access.

## 11. Outcome Verification ↔ authorities

```text
technical execution result
→ OutcomeVerifier
→ Domain/provider/authoritative record/event
→ VERIFIED_SUCCESS | VERIFIED_FAILURE | PENDING | INCONCLUSIVE
```

RPA click/HTTP 200 is not business completion by itself.

## 12. Notifications ↔ channels

Truthful Event/Outcome state may drive:

```text
Minha DELPI
email
Teams
WhatsApp Business
Interaction Room
other approved channel
```

Recipients/severity/dedupe/SLA/escalation follow policy. Notification is not proof of outcome.

## 13. External Reads/Writes

External read requires active connection/scope; write is separate capability and revalidates scope/policy. `draft != send`.

## 14. Secret/Vault integration

Provider/RPA/service credentials use protected Secret/Vault owner and are consumed only inside concrete adapter/runtime boundaries.

Never LLM/MFE/ordinary logs.

## 15. Source/Evidence / Business Graph

Internal, external, event and automation outputs converge on SourceRef/EvidenceRef/OutcomeRef contracts without copying masters.

Automation artifact may support Evidence; business truth still comes from authoritative source.

## 16. Meeting/Frontline

Meeting and Frontline invoke the same semantic capabilities, Decision/Workflow and executor architecture. They do not create separate business/RPA action paths.

## 17. Knowledge / Learning

```text
Event + Context + Decision + Action + verified Outcome
→ Evidence
→ candidate pattern/optimization
→ review/eval
→ publish
```

No automatic policy change from one successful automation run.

## 18. Failure boundaries

Distinguish:

```text
Core/Domain unavailable
external connection missing/revoked
provider unavailable
invalid/stale/duplicate event
semantic capability unavailable
executor unavailable
worker unavailable
execution timeout
execution ambiguous
outcome not verified
Decision required
AutonomyPolicy blocked
kill switch active
```

No false success narrative.

## 19. Kill switches

Independent controls for Internet/provider/connections/external writes/webhooks/background sync, individual automation/capability/executor, autonomous ACT and future browser/computer-use. OT integration remains separately governed.

## 20. Anti-pattern integration graph

```text
Portal ─X→ provider/RPA token
LLM ─X→ unrestricted HTTP/desktop
Planner ─X→ provider/executor-specific UI mechanics
Event ─X→ direct write authority
Worker ─X→ user permission authority
RPA ─X→ business-rule authority
Technical success ─X→ automatic business success
PREPARE ─X→ implicit ACT
Global L5 ─X→ unrestricted execution
Automation Hub ─X→ second planner/workflow engine
Copilot ─X→ Chat runtime
Copilot/RPA ─X→ direct free-form machine actuation
```

## 21. C0 inventory requirement

C0.S0 must map actual evidence for:

```text
egress/OAuth/secrets/connectors/Teams
event sources/brokers/webhooks/schedulers
RPA tools/orchestrators/licences/bots/packages
scripts/functions/jobs
queues/workers/desktop sessions
service/background identities
credential injection/storage
rule/BPM/process engines
business postcondition/outcome sources
notification/escalation channels
kill switches/automation governance
OT/safety boundaries
```

No provider/executor infrastructure is treated as `REUSE` without evidence.
