# 10 — Padrão AI-ready para apps, APIs e domínios

**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Todo app/domínio deve evoluir para uso pela UI e pela DÉLIA **sem hardcode central e sem contratos paralelos**, contribuindo também para Event/Process/Semantic/Outcome readiness quando aplicável.

## 2. Base AI-ready

```text
App/Domain
├ manifest/routes/permissions
├ APIs/use cases
├ OpenAPI
├ EntityRef/deep-link metadata
├ Workspace Context adapter
├ Evidence/provenance-friendly responses
├ sensitivity/Decision/idempotency semantics
├ authoritative postcondition/outcome sources
├ optional visual capabilities
├ optional trusted events
├ optional process-event semantics
└ optional governed metric definitions
        ↓
       DÉLIA
```

## 3. App/route/business contract

- stable app/route IDs;
- real backend use cases;
- accurate OpenAPI/security/error schemas;
- Keycloak/Core/domain authority preserved;
- no URL/path/operationId semantics hardcoded in AI core;
- UI is not business contract.

## 4. Shared foundations

Reuse when applicable and proven:

```text
EntityRef / SourceRef / EvidenceRef / OutcomeRef
WorkspaceContext
PlatformCommand
DecisionGate
EventEnvelope
CapabilityProjection
```

Do not create app-specific incompatible equivalents. Presence in this list does not prove current implementation.

## 5. Context readiness

Publish only bounded entity/filter/period/selection/view/data refs. No React state/DOM/token/full dataset. Context never grants permission.

## 6. Entity/deep-link readiness

App declares logical entity→route mapping. Portal resolves/revalidates under the platform contract.

## 7. Visual capabilities

Visual verbs can support open/select/focus/filter/refresh. They never replace material create/update/approve/cancel Business Actions.

## 8. Action readiness

Material action should expose, as applicable:

```text
business owner
input/output schema
permission/domain validation
risk/sensitivity
Decision/Autonomy policy inputs
idempotency/concurrency
preconditions/postconditions
authoritative Outcome verifier
errors/audit/correlation
```

If no API exists, `57` may allow a governed legacy executor through the Automation Hub technical-execution boundary, but the app/domain remains not fully API-ready; RPA/UI mechanics do not enter planner contracts and do not move business authority to the Hub.

## 9. Evidence / Outcome readiness

Responses/events should expose enough facts for source identity, timestamps/freshness, entity relations, status and verification. Adapter may normalize to Evidence/Outcome; API need not emit DÉLIA-specific DTOs.

## 10. Event readiness

When domain owns events:

```text
eventId/type/version
case/entity refs
occurredAt
source owner
dedupe/replay semantics
bounded payload/ref
authenticity/security model
```

Trusted event can feed Watch/Workflow/Process Intelligence. Event never grants action permission.

## 11. Process Intelligence readiness

Where process mining is relevant, domain should make real process events correlatable by business/case key, activity and timestamp without inventing person-surveillance telemetry.

Audit log presence alone is insufficient unless activity/case semantics are usable.

## 12. Semantic readiness

For material KPI/concepts, domain/BI owner should define:

```text
metric meaning/formula
grain/dimensions/unit
source/freshness
owner/version
security classification
```

Do not make each plugin define conflicting hidden KPI formulas.

## 13. Predictive/model readiness

If app/domain owns model output, expose model/version/horizon/freshness/limitations and source/features lineage sufficient for Evidence. Prediction is not domain FACT unless a separate authoritative record says so.

## 14. Artifact readiness

Apps can expose refs/export contracts usable by Sandbox/Artifact Workspace; do not make DÉLIA scrape DOM tables when structured read/export exists.

## 15. Iframe readiness

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

AI_READY requires real API/use case for business operations; postMessage alone is not enough.

## 16. Readiness levels

```text
L1 DISCOVERABLE
L2 CONTEXT_READY
L3 READ_READY
L4 WRITE_READY
L5 WORKFLOW_READY
```

These are app/business readiness levels, **not autonomy levels** and not Edge/Process/Model maturity scores.

## 17. Optional readiness dimensions

Orthogonal dimensions may be tracked separately:

```text
EVENT_READY
PROCESS_INTELLIGENCE_READY
SEMANTIC_READY
ARTIFACT_READY
PREDICTIVE_READY
FRONTLINE_READY
EDGE_READY
```

Do not overload L1–L5 to encode all of them.

## 18. Minimum matrix

| Item | Status |
|---|---|
| app/routes/permissions | |
| EntityRef/deep link | |
| WorkspaceContext | |
| Business APIs/OpenAPI | |
| read Evidence/freshness | |
| write risk/Decision | |
| idempotency/retry | |
| postcondition/Outcome verifier | |
| Automation Hub execution contract if legacy executor is needed | |
| events if relevant | |
| process event semantics if relevant | |
| governed metrics if relevant | |
| visual capabilities if needed | |
| help/knowledge | |
| evals | |

Populate from real code/contracts. Unknown implementation/readiness stays `TO_INVENTORY`; documentation alone does not make an item ready.

## 19. Tests

As applicable: auth/context/deep-link, read/write, Decision/TOCTOU, idempotency, postcondition verification, sibling/unknown onboarding, event duplicate/authenticity, process event mapping, semantic metric reproducibility, Automation Hub contract/substitution when relevant and iframe security.

## 20. Definition of Ready AI

```text
[ ] UI/DÉLIA converge to same authoritative use cases
[ ] shared foundations reused only when proven/appropriate
[ ] OpenAPI/discovery is sufficient
[ ] no endpoint/provider/executor hardcode added centrally
[ ] permissions remain with canonical owners
[ ] Entity/Context/navigation are typed
[ ] writes have Decision/idempotency/Outcome semantics
[ ] technical automation execution respects Automation Hub boundary when applicable
[ ] relevant events/metrics/process refs are owner-driven
[ ] tests/evals pass for declared readiness dimensions
```

AI-readiness is ecosystem architecture, not handcrafted per-app AI glue.
