# DÉLIA — Matriz de Onboarding dos Apps e Domínios

**Status:** inventário inicial / `TO_INVENTORY`  
**Owner factual atual:** `C0.S0` inventory/rebaseline  
**Regra:** nenhum campo sem Evidence vira comprovado por suposição.  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Mapear como a DÉLIA pode descobrir e integrar apps/APIs/domínios sem hardcode central e sem depender do Chat, preservando business readiness e dimensões complementares de contexto, eventos, processo, semântica, artifacts, predictive e Frontline/Edge.

Um readiness scanner futuro, se existir, é `TARGET` e não owner factual.

## 2. Níveis AI-ready de negócio

| Nível | Nome | Critério mínimo |
|---|---|---|
| L0 | NOT_INVENTORIED | não auditado |
| L1 | DISCOVERABLE | app/rotas/permissions discoverable |
| L2 | CONTEXT_READY | EntityRef/deep link + WorkspaceContext quando material |
| L3 | READ_READY | business reads via Domain API/OpenAPI + RBAC + Evidence |
| L4 | WRITE_READY | writes + Decision + idempotency/audit/Outcome |
| L5 | WORKFLOW_READY | safe Durable Work/events when required |

Esses níveis **não são níveis de autonomia** e não provam que DÉLIA esteja em fase correspondente.

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

Não criar escala numérica universal.

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
WorkspaceContext contract/evidence
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

Optional dimensions, only with Evidence:

```text
event sources
process case/activity semantics
governed metrics/glossary
analysis/export/artifact contracts
predictive models/evals
frontline operational refs
procedure/revision/training sources
device/shared-session/media
Edge/offline/network constraints
OT telemetry/safety owner
```

And always:

```text
DELIA_INTEGRATION = API_CONTRACT | PLATFORM_CONTEXT | IFRAME_BRIDGE | GOVERNED_LEGACY_EXECUTOR | NONE
CHAT_RUNTIME_DEPENDENCY_FOR_DELIA = MUST_BE_NONE
```

`GOVERNED_LEGACY_EXECUTOR` é fallback/gap, não equivalente a API-ready L4. Technical execution ownership remains with Automation Hub/approved executor owner where applicable.

## 6. Candidate inventory

Existing candidate app list from prior inventories remains `TO_INVENTORY` until C0 reconciles `plugins/`, Core registrations, APIs e operational reality. No listed wave is proof of readiness.

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

DÉLIA integra o owner por contract; nunca usa Chat como proxy.

## 8. Process/event onboarding

Para process-relevant domain, provar processId/owner, case key, activity/event type, occurredAt, status/outcome, entity refs, provenance, completeness/retention e privacy necessity.

Audit log presence não basta para Process Mining readiness.

## 9. Semantic onboarding

Para material metrics, provar definition/owner/formula/grain/dimensions/unit/source/freshness/version. Não inventar fórmula via LLM.

## 10. Predictive/model onboarding

Model use é separado de app L1–L5. Record owner/version/eval/target/horizon/limitations/deployment/source lineage. Prediction never upgrades a domain fact.

## 11. Frontline / Edge onboarding

Frontline checks device/browser/shared-session/context/procedure/revision/accessibility/noise/media/escalation/training/safety.

Edge additionally checks network/MDM/local runtime/storage/cache/version sync/package/model deployment/offline authority/event reconciliation. Offline never widens authority.

## 12. Meeting onboarding

Meeting does not require domain-specific endpoint. Normal authorized contracts may suffice; session/artifact ownership remains subject to C0/product state decisions.

## 13. Wave selection

Prioritize high-value/low-risk candidates with stable owners/contracts/Evidence. Maintain separate rollout decisions for business reads/writes, process intelligence, semantic metrics, predictive models, frontline and Edge/offline.

## 14. Promotion gates

Business:

```text
L1 → L2 context/entity
L2 → L3 reads + RBAC + Evidence
L3 → L4 governed writes + Decision/idempotency/Outcome
L4 → L5 Durable Work/events where needed
```

Other dimensions become READY only when specific contracts/tests from `20` pass; they do not inherit readiness from L5.

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

No Evidence → `TO_INVENTORY` or `PENDING`, never PASS.

## 16. Foundation rule

Onboarding não cria app-specific primitives, planner branches ou parallel authorities. Gap compartilhado volta para owner/source/consumer/contract/ADR antes de local workaround.
