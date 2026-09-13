# 08 — Segurança, autonomia e auditoria da DÉLIA

**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Tests:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Specs temáticas:** `53–66`

## 1. Invariante principal

```text
DÉLIA effective capabilities
⊆
user/service effective authorities
+ explicitly approved external/tool scopes
+ capability/policy constraints
```

Nenhum prompt, model, memory, asset, tool, agent, device, event, package, provider scope ou admin catalog cria permission por si só.

Authorities permanecem separadas:

```text
Keycloak = identity / SSO
Core = apps / routes / RBAC / governance
Domain APIs = business rules / final domain authorization
DÉLIA = intelligence / Evidence / Policy / Decision / Work orchestration
Automation Hub = technical execution
Providers = external-resource authority
OT/Safety = machine / industrial safety authority
```

## 2. Authorization flow

```text
identity / service actor
→ Core effective permissions
→ source/domain/provider/tool scopes
→ authorized capability projection
→ DÉLIA policy/risk/context
→ Decision Gate when required
→ Work orchestration
→ approved adapter / Automation Hub / Domain API executor
→ final owner validation
→ authoritative postcondition verification
→ Outcome / Evidence / Audit
```

JWT identifica contexto; não é permission truth final. Provider/tool scope também não substitui Core/domain authorization.

## 3. Untrusted boundaries

Treat as untrusted for system/policy:

- user prompts and attachments;
- web/RAG/API/tool results;
- email/messages/files/calendar;
- provider webhooks/events;
- media/transcripts/biometric/Human Observation;
- RPA/computer-use screen/result;
- MCP tool descriptions/resources/results;
- A2A agent messages/artifacts;
- Personal Memory candidates;
- model predictions/recommendations;
- sandbox generated code/output;
- marketplace/package metadata;
- Edge buffered events/device metadata;
- WorkspaceContext/iframe/Room/Meeting content.

None can alter RBAC, system instructions, provider scopes, autonomy allowlists, retention, package trust, Decision Gates or safety boundaries.

## 4. Autonomy

```text
L0 explain
L1 observe
L2 advise
L3 prepare
L4 governed execute
L5 allowlisted autonomous execute within explicit limits
```

Phase semantics:

```text
L3 PREPARE
→ may exist before ACT; no side effect

L4 GOVERNED EXECUTE
→ C5-capable when a capability is explicitly authorized
→ live AuthZ + Policy/Decision + idempotency + audit + required Outcome verification

L5 AUTONOMOUS EXECUTE
→ C7 only
→ OFF by default
→ explicit capability/context/risk allowlist and limits
```

C7 does not introduce the concept of ACT; it introduces advanced autonomous ACT. Watch autonomous ACT remains C7. C6 Watch is `OBSERVE|ADVISE|PREPARE` by default.

Autonomy is capability/context/risk/actor/environment/materiality/reversibility/limit scoped; never one global switch.

## 5. Risk classes

At minimum consider:

```text
read
write
sensitive_write
admin/destructive
external_communication
financial/material
personal_data
biometric_sensitive
media_capture
personal_external_source
provider/tool/model credential
model prediction/prescription
sandbox/code execution
marketplace executable package
Edge/offline action
industrial_safety
```

Risk class alone does not grant or deny permission; it informs deterministic policy/gate selection together with actor, capability, context and current authority.

## 6. Decision Gates / TOCTOU

Available gates:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Immediately before material execute/apply/retry/resume, revalidate relevant:

- Core/domain permission/state;
- policy/autonomy limits;
- evidence/source freshness;
- semantic metric/model version;
- external/tool/agent connection/approval;
- recipient/target/arguments;
- executor availability/version;
- package/model/device status;
- idempotency/concurrency state;
- kill switch;
- industrial preconditions.

A previous Decision does not permanently authorize a future material action when material inputs, permissions, policy, model/semantic version or state changed.

## 7. Internet / External / Teams security

Keep strict safe egress, SSRF/private/link-local/metadata blocking, redirect revalidation, least-privilege OAuth, protected secret/vault, user/org connection ownership, source ACL, `read != write`, `draft != send`, provider event authenticity/dedupe/reconciliation, and external Knowledge candidate governance.

WhatsApp personal-session scraping remains forbidden by default.

Provider scope = access requirement to provider resources; provider scope != Core/domain permission.

## 8. Automation / RPA / Computer-use security

DÉLIA planner receives semantic capability/schema, not UI mechanics. Automation Hub/executor adapters own technical execution details.

- API preferred over RPA when authoritative supported contract exists;
- background action uses explicit user/service identity;
- RPA credentials injected through protected boundary;
- worker/session isolation;
- ambiguous write no blind retry;
- technical success must not be announced as verified business success;
- computer-use sandbox/app/network allowlists;
- user takeover/emergency stop where required;
- screenshots/artifacts classified/redacted/retained by policy;
- executor metadata never grants permission;
- Automation Hub must not become second planner, Policy authority or business-rule authority.

## 9. Event-driven security

Event source authenticity/trust, dedupe/order/correlation and stale handling are mandatory. Event payload cannot grant permission, switch autonomy, modify Policy/Decision Gates, or directly authorize a write.

A trusted event can trigger evaluation; it cannot skip live authorization and policy gates.

Polling fallback uses same normalized EventEnvelope path.

## 10. Process Intelligence / Task Mining security

Process Mining is process analytics, not employee surveillance.

Default prohibitions:

```text
secret productivity leaderboard
fraud/intent inference from process deviation
personality/trust scoring
disciplinary profile
continuous unrestricted desktop capture
```

Task Mining, if ever enabled, requires purpose, explicit governance, app/domain allowlist, redaction, minimal capture and retention controls.

## 11. AI Control Tower security

Control Tower may enable/disable AI assets, manage rollout/risk/evals/budgets/kill switches, but **Control Tower admin != business permission**.

Asset registry metadata never contains broad secrets and never grants declared permissions/scopes.

Control Tower is not a second planner or second Work runtime.

## 12. MCP / A2A security

```text
discovery != approval
metadata/description != policy
agent result != authority
```

Required:

- allowlisted approved servers/agents/capabilities;
- minimum delegated context;
- scoped/time-bounded credentials when needed;
- schema validation;
- no hidden conversation/CoT dumping;
- recursion/delegation bounds;
- timeout/cancel/budget;
- same Decision/Outcome semantics for writes;
- disable/revoke enforcement.

External agents/tools cannot recursively expand authority beyond the explicitly delegated capability scope.

## 13. Personal Memory security/privacy

Personal Memory is user-owned/private by default.

Prohibited:

- cross-user memory access;
- sensitive/personality/health/trust inference;
- memory as business/RBAC truth;
- hidden employee profile;
- auto-promotion to Organizational Knowledge.

User must have view/correct/delete/disable controls according to policy.

Personal Memory can influence relevance/presentation; it never grants authorization.

## 14. Semantic Business Layer security

Semantic definitions do not grant source data access. Every query revalidates source/domain permissions.

Material metric has owner/version/formula/grain/dimensions/freshness. Same-name conflicting metrics are explicit; LLM may not silently select or invent a material business formula.

## 15. Analysis Sandbox security

Sandbox is isolated and read-only toward sources by default:

- no unrestricted host/private-network access;
- no broad DB/provider credentials;
- quotas/timeouts/storage limits;
- package/library policy;
- safe file ingestion;
- no arbitrary DDL/DML via read analysis connector;
- output/content size and classification limits;
- teardown/cleanup.

Generated code is untrusted execution input.

Sandbox is not a bypass for Domain API, Core, provider permissions or normal secret boundaries.

## 16. Artifact security

Artifact keeps owner/version/ACL/provenance/sensitivity/retention. Human edits must not be silently replaced.

External share/send is a separate governed action. Generated file content may itself be untrusted for downstream systems.

## 17. Predictive / Prescriptive security

```text
prediction != FACT
recommendation != authorization
```

Model output must include applicability/freshness/limitations and cannot by itself authorize a high-impact action. Protected/sensitive-person features require separate governance and are forbidden by default for employment decisions.

Any prescriptive Apply creates a fresh live action context and re-runs applicable Policy/Decision/AuthZ checks.

## 18. Operational Twin / Simulation security

```text
SIMULATED_STATE != PRODUCTION_STATE
SIMULATE != APPLY
```

Scenario changes never mutate source systems. Apply creates a fresh live read/revalidation/Decision/action flow.

Twin is not a source of truth.

## 19. Edge / Offline security

Loss of cloud connectivity never expands authority.

Required:

- explicit online/degraded/offline mode;
- source revision/freshness in cache;
- encrypted sensitive local state where needed;
- no broad long-lived secret;
- package/model version/hash/signature policy;
- remote revoke/disable where feasible;
- user switch cleanup;
- buffered-event idempotent reconciliation;
- OT network segmentation respected.

Edge runtime cannot infer physical authority from enterprise autonomy level.

## 20. Model lifecycle / Marketplace / supply-chain security

- only approved model/deployment can be selected;
- revoked/unapproved model unavailable;
- eval/version/owner/risk traceable;
- Marketplace manifest declares dependencies/data scopes/required permissions but **does not grant them**;
- executable packages require trusted publisher/integrity/dependency/license/vulnerability controls as applicable;
- revoke/rollback path mandatory;
- external marketplace never auto-activates production code.

## 21. Biometric / Human Observation / people security

Biometric match remains candidate identity, not auth/RBAC. Templates are protected/revocable. Human Observation is limited to observable process evidence; no psychological/sensitive inference or autonomous employment decision.

Unknown/low-confidence remains unknown or requires correction/confirmation; match does not authenticate or authorize.

## 22. Knowledge / Graph / Case / Room security

Membership/relationship/reference never grants access to original source. Personal/external/process/model outputs become durable Organizational Knowledge only via:

```text
Evidence
→ candidate
→ owner/review
→ eval
→ version
→ publish
```

## 23. Industrial / OT boundary

DÉLIA is not a safety controller.

```text
free-form LLM/model/vision/voice/Edge output
-X→ direct PLC/CNC/robot/machine actuation
```

Prohibited by default:

- unrestricted model/voice/vision → physical command;
- AI safety interlock override;
- implicit OT permission derived from Core/provider/autonomy level.

Any future actuation requires separate approved industrial safety architecture/gate.

## 24. Audit requirements

Material audit can reconstruct:

```text
trigger/actor
source/evidence refs
policy/decision version
semantic metric/model/tool/agent/executor versions
arguments hash
idempotency/correlation refs
execution/result
verified outcome
notifications
artifact/scenario refs
asset/kill-switch changes
```

No chain-of-thought or secret storage.

## 25. Prohibited data in ordinary logs/state

- JWT/refresh tokens;
- provider/tool/agent/service/RPA credentials;
- passwords/API keys/client secrets;
- biometric templates;
- chain-of-thought;
- raw sensitive payload without purpose;
- raw media/screenshots outside appropriate protected storage;
- unrestricted Personal Memory values in aggregate telemetry.

## 26. Emergency controls

Independent disable/kill switches should exist where material for:

```text
DÉLIA governed writes
Internet Research/fetch
provider/connection/external send
webhook/sync
Watch autonomous ACT / L5 autonomy
specific automation/executor/RPA worker class
MCP server/A2A agent
model/deployment
sandbox/code execution
Marketplace asset
Edge package/device capability
media/biometric capture
OT integration
```

Kill switch is admin/policy owned, never prompt controlled.

## 27. Security success criteria

Security is correct when every new intelligence/automation capability can add value **without becoming a parallel authority** and when compromise/prompt injection/stale memory/model error/provider error/device outage cannot silently widen permissions, send/execute actions, mutate production state, leak secrets/data or cross industrial safety boundaries.

C5 L4 governed ACT and C7 L5 autonomous ACT must satisfy the same fundamental authorization, idempotency, audit and Outcome invariants; C7 adds autonomous triggering/limits/kill-switch requirements rather than weakening C5 controls.
