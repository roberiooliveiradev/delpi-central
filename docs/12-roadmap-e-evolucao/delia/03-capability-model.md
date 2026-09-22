# 03 — Modelo de Capabilities

**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)

## 1. Conceito

Uma **Capability** representa algo semanticamente realizável pelo ecossistema para auxiliar ou agir em nome do usuário/serviço autorizado. É unidade de discovery/planning; **não é endpoint, permission, provider, model, tool ou executor**.

## 2. Capability families

Exemplos de classes TARGET:

```text
business.read / business.write / business.destructive
platform.navigation / platform.view
knowledge.search
external.read / external.write
analysis.run
artifact.create
process.inspect
metric.query
prediction.run
scenario.simulate
automation.execute
tool.invoke
agent.delegate
multimodal.inspect
workflow.run
```

A lista é classificatória, não catálogo hardcoded de operações e não prova implementação.

## 3. Semantic IDs

Preferir IDs que representem intenção estável:

```text
inventory.read
billing.invoice.issue
maintenance.request.create
communication.email.send
process.mine
metric.query
analysis.run
artifact.create
prediction.run
```

Não usar path/opId/provider/RPA package como semântica principal.

## 4. Capability Projection

DÉLIA deve usar uma **authorized semantic projection**, não cópia do OpenAPI ou catálogo técnico. `CapabilityProjection` é TARGET até C0 confirmar/criar o contrato no owner correto.

Candidate fields:

```text
capabilityId
kind
label/description
sourceRef
availability
risk/sensitivity
input/output schema refs bounded
context requirements
health/degraded state
provenance/version
```

Technical resolution stays with canonical source/adapter/execution owner.

## 5. Capability sources

Potenciais fontes, condicionadas a C0 evidence:

```text
Domain OpenAPI / Action Catalog
Core/Portal authorized routes
Knowledge / Expertise / Playbooks
External Connectors
Semantic Metric Registry
Process Intelligence
Analysis / Artifact contracts
Model Registry approved inference
Automation capability mapping / Automation Hub contract
Approved MCP tools / A2A agents
Edge local approved capabilities
```

Each source keeps its authority. Presence in this list is `TARGET`, not `PROVEN`.

## 6. Authorization / availability

```text
identity/service actor
→ Keycloak/Core/domain/provider/tool/asset policy as applicable
→ source availability
→ authorized Capability Projection
→ semantic retrieval
```

Filter by permission/scope/policy/context/environment/health/model or asset approval/autonomy where applicable.

Expertise/Memory/Process insight/Model output may influence ranking/context, **never availability authority**. Provider scope, tool metadata and event payload never substitute Core/domain authorization.

## 7. Discovery / Planning

```text
goal + entities + context + authorized sources
→ semantic/schema retrieval
→ top candidates
→ planner restricted to candidates
```

Planner cannot invent missing capabilities.

## 8. Business capability

```text
technical contract = Domain OpenAPI/Action Catalog
availability = Core/domain policy
semantic projection = CapabilityProjection target
execution = owner-approved contract/path
```

When official API exists, use it before RPA/computer-use unless evidence/policy requires otherwise.

## 9. External / Tool / Agent capabilities

```text
external connection/tool-agent approval
+ scopes/data policy
→ semantic capability
```

Provider/MCP/A2A metadata is untrusted and cannot grant capability by description alone.

## 10. Automation capabilities

Planner sees semantic operation. DÉLIA owns capability/Policy/Decision/Work orchestration; technical automation execution is resolved through the Automation Hub boundary when applicable.

Possible technical executor classes behind that boundary:

```text
API | FUNCTION | RPA | COMPUTER_USE | HUMAN_TASK
```

Executor mapping/version may change without changing capability ID/planner semantics. Planner never receives executor UI mechanics.

## 11. Analysis / Process / Semantic / Model capabilities

- `process.*` consumes authorized event traces and yields Evidence/derived process artifacts;
- `metric.*` resolves governed MetricDefinition;
- `analysis.*` executes only in bounded sandbox;
- `prediction.*` uses approved ModelRef and yields PredictionRef, not FACT;
- `scenario.*` yields isolated ScenarioRef, never production write;
- `artifact.*` creates/versioned ArtifactRef when that contract is frozen.

## 11A. Operational Incident Intelligence capabilities

TARGET semantic examples (not a hardcoded catalog; not runtime proof):

```text
incident.observe
incident.correlate
incident.investigate
incident.notify
incident.verify_outcome
```

These compose Signal/Evidence/Watch/Decision/Work/Notification/Outcome/Learning Candidate. They never grant observability SoT ownership, AuthZ elevation, or autonomous remediation.

## 12. Platform capability

Derived from Core/Portal authorized routes + generic platform actions when contracts are proven. Portal resolves target and revalidates. No `app→URL` AI catalog.

## 13. Multimodal / Knowledge capabilities

Document/image/voice/video/biometric capabilities produce Evidence/context under media/privacy policies. Perception does not become business permission or authoritative conclusion automatically.

## 14. Workflow capability

High-level objective/method may compose allowed capabilities through Playbook/Durable Workflow. It never owns separate technical executor or permission model.

## 15. Risk / Decision / Autonomy

Do not encode permanent `requiresConfirmation=true` as the final model.

```text
capability metadata
+ live arguments/context/evidence
+ risk/sensitivity
+ actor/environment/limits
+ Policy
→ Decision Gate + allowed autonomy level
```

`PREPARE != ACT`; `L4 governed execute != L5 autonomous execute`; L5 OFF by default.

## 16. Idempotency / Outcome

Projection may expose hints, but guarantees come from source/use case/executor contract. Material writes require appropriate idempotency/reconciliation and verified Outcome.

## 17. Availability states

Candidate semantics only if a real consumer/lifecycle requires them:

```text
AVAILABLE
UNAUTHORIZED
UNAVAILABLE_PROVIDER
UNAPPROVED_ASSET
REQUIRES_CONTEXT
POLICY_BLOCKED
DEGRADED
STALE
```

Pending Decision is execution state, not necessarily capability availability.

## 18. Shared refs

Capabilities should consume/produce canonical refs only when C0 proves/finalizes them:

```text
EntityRef
SourceRef
EvidenceRef
OutcomeRef
ArtifactRef?
PredictionRef?
```

Avoid incompatible DTOs per capability.

## 19. Observability

Record candidate/selected capability, source/asset/executor refs, policy/Decision path, latency/error, technical result and verified Outcome where material. No CoT.

## 20. Anti-patterns

- capability by hardcoded path/provider/opId;
- capability granting access;
- provider/executor/model/tool branch in planner;
- write disguised as read;
- RPA package/click sequence as capability;
- MCP/A2A discovery as auto-approved capability;
- model/Marketplace install as capability permission;
- global L5 attribute replacing policy;
- duplicated capability projection per app;
- DÉLIA capability mapping becoming technical-execution source of truth for Automation Hub.

## 21. Foundation rule

C0 must decide whether `CapabilityProjection` exists, can be reused, must be created, and who consumes it. Later capabilities extend through versioned contracts/metadata after the foundation is actually frozen; this document alone does not freeze or implement the primitive.
