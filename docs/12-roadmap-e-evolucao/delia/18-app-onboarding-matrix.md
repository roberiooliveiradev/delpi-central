# Minha DELPI Copilot — Matriz de Onboarding dos Apps e Domínios

**Status:** inventário inicial / `TO_INVENTORY`  
**Owner factual:** C0.S0 + future readiness scanner  
**Regra:** nenhum campo sem evidence vira comprovado por suposição.  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Mapear como o Copilot standalone descobre e integra apps/APIs/domínios sem hardcode central e sem depender do Chat, preservando readiness de negócio e dimensões complementares de contexto, eventos, processo, semântica, artifacts, predictive e Frontline/Edge.

## 2. Níveis AI-ready de negócio

| Nível | Nome | Critério mínimo |
|---|---|---|
| L0 | NOT_INVENTORIED | não auditado |
| L1 | DISCOVERABLE | app/rotas/permissions discoverable |
| L2 | CONTEXT_READY | EntityRef/deep link + WorkspaceContext quando material |
| L3 | READ_READY | business reads via Domain API/OpenAPI + RBAC + Evidence |
| L4 | WRITE_READY | writes + Decision Gate + idempotency/audit/Outcome |
| L5 | WORKFLOW_READY | safe Durable Workflow/events when required |

Esses níveis **não são níveis de autonomia**.

## 3. Iframe class

```text
I0 PORTAL_ONLY
I1 CONTEXTUAL
I2 INTERACTIVE
I3 AI_READY
```

I3 exige Business Actions reais por API/use case; visual bridge não substitui domínio.

## 4. Readiness dimensions ortogonais

Além de L1–L5, registrar apenas quando aplicável:

```text
EVENT_READY
PROCESS_INTELLIGENCE_READY
SEMANTIC_READY
ARTIFACT_READY
PREDICTIVE_READY
FRONTLINE_READY
EDGE_READY
```

Não criar uma escala numérica universal para todas essas dimensões.

### EVENT_READY

- owner/event schema/version;
- eventId/dedupe/replay;
- entity/case refs;
- occurredAt/freshness;
- authenticity/security;
- bounded payload/ref.

### PROCESS_INTELLIGENCE_READY

- process/case business key;
- activity/timestamp/status semantics;
- process owner;
- historical completeness;
- event provenance;
- privacy boundary for actor/task data.

### SEMANTIC_READY

- governed metrics/concepts;
- owner/formula/grain/dimensions/unit;
- source/freshness;
- version/security classification;
- conflicts explicit.

### ARTIFACT_READY

- structured read/export refs;
- source provenance;
- attach/download/upload contracts;
- ACL/version/retention when relevant.

### PREDICTIVE_READY

- approved model/use case;
- target/horizon;
- source/features lineage;
- ground truth/eval;
- model/version/freshness/limitations;
- owner/rollback.

### FRONTLINE_READY / EDGE_READY

Frontline context/device/media/workflow readiness and, separately, Edge/network/cache/package/offline readiness. Edge readiness never implies OT actuation authority.

## 5. Fields mínimos por app/domain

```text
appId/name
manifest/version/render mode
backend/domain owner
Core registration/routes/permissions
canonical entity IDs/deep links
WorkspaceContext
OpenAPI source/version/quality
business reads/writes
risk/sensitivity owner
Decision/Autonomy inputs
idempotency/concurrency
authoritative Outcome/postcondition source
Evidence/freshness
owner/team
wave candidate
blockers
evidence paths/hashes/timestamp
```

Optional dimensions, only with evidence:

```text
event sources
process case/activity semantics
governed metrics/glossary
analysis/export/artifact contracts
predictive models/evals
frontline operational entity refs
procedure/revision/training sources
device/shared-session/media
Edge/offline/network constraints
OT telemetry/safety owner
```

And always:

```text
COPILOT_INTEGRATION = API_CONTRACT | PLATFORM_CONTEXT | IFRAME_BRIDGE | GOVERNED_LEGACY_EXECUTOR | NONE
CHAT_DEPENDENCY_FOR_COPILOT = MUST_BE_NONE
```

`GOVERNED_LEGACY_EXECUTOR` is a gap/fallback path, not equivalent to API-ready L4.

## 6. Candidate inventory

Existing candidate app list from prior inventories remains **TO_INVENTORY** until C0 reconciles `plugins/`, Core registrations, APIs and operational reality. No listed wave is proof of readiness.

Suggested starting areas remain commercial/supplies/my-requests for administrative read pilots and a separate evidence-driven selection for Frontline/process pilots.

## 7. API inventory per domain

```text
API service
Gateway path
OpenAPI source/hash
JWT/auth/permission model
errors/pagination
entity IDs
read/write operations
idempotency/postconditions
events/websockets
health
```

Copilot integrates API owner directly, never via Chat.

## 8. Process/event onboarding

For process-relevant domain, prove:

```text
processId/owner
case/business key
activity/event type
occurredAt
status/outcome
entity refs
source/audit provenance
completeness/retention
actor data necessity/privacy
```

Audit logs that cannot reconstruct case/activity are not automatically Process Mining-ready.

## 9. Semantic onboarding

For business metrics, prove definition/owner/formula/grain/dimensions/unit/source/freshness/version. Do not let separate UIs expose conflicting unnamed formulas.

## 10. Predictive/model onboarding

Model use is separate from app L1–L5. Record model owner/version/eval/target/horizon/limitations/deployment and source lineage. Prediction never upgrades a domain fact.

## 11. Frontline / Edge onboarding

Frontline checks device/browser/shared-session/context/procedure/revision/accessibility/noise/media/escalation/training/safety.

Edge additionally checks network reliability/MDM/local runtime/storage/cache/version sync/package/model deployment/offline authority and event reconciliation.

## 12. Meeting onboarding

Meeting does not require domain-specific meeting endpoint. Normal authorized reads/actions/Entity/Evidence contracts are enough; meeting session/ata belongs to Copilot.

## 13. Wave selection

Prioritize high-value/low-risk candidates with stable owners/contracts/evidence. Maintain separate rollout decisions for:

```text
business reads/writes
process intelligence
semantic metrics
predictive models
frontline
Edge/offline
```

Do not force all dimensions into the same pilot.

## 14. Promotion gates

Business:

```text
L1 → L2 context/entity
L2 → L3 reads + RBAC + Evidence
L3 → L4 writes + Decision/idempotency/Outcome
L4 → L5 Durable Workflow/events where needed
```

Other dimensions become READY only when their specific contracts/tests from `20` pass; they do not inherit readiness from L5.

## 15. Evidence record

At minimum:

```text
gitSha
manifest/Core registration/OpenAPI hashes
permission/Entity/Context evidence
Decision/idempotency/Outcome contract
optional event/process/semantic/model/Frontline/Edge evidence
owner
smoke/evals
lastVerifiedAt
```

No evidence → `TO_INVENTORY`.

## 16. Foundation rule

Onboarding does not create app-specific primitives, planner branches or parallel authorities. If an app reveals a shared-contract gap, return to the versioned foundation/ADR before implementing a local workaround.
