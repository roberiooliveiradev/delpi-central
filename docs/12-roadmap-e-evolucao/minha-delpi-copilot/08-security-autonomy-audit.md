# 08 — Segurança, autonomia e auditoria

**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Tests:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Specs temáticas:** `53–66`

## 1. Invariante principal

```text
Copilot effective capabilities ⊆ user/service effective authorities + explicitly approved external/tool scopes
```

Nenhum prompt, model, memory, asset, tool, agent, device, event, package ou admin catalog cria permission por si só.

## 2. Authorization flow

```text
identity
→ Core effective permissions
→ source/domain/provider/tool scopes
→ authorized capability projection
→ policy/risk/context
→ Decision Gate when required
→ adapter/executor/agent/model
→ final owner validation
→ verified Outcome/Evidence/Audit
```

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

None can alter RBAC, system instructions, provider scopes, autonomy allowlists, retention, package trust or safety boundaries.

## 4. Autonomy

```text
L0 explain
L1 observe
L2 advise
L3 prepare
L4 governed execute
L5 allowlisted autonomous execute within explicit limits
```

L5 OFF by default. Autonomy is capability/context/risk/actor/environment/limit scoped; never one global switch.

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
- executor availability;
- package/model/device status;
- kill switch;
- industrial preconditions.

## 7. Internet / External / Teams security

Keep strict safe egress, SSRF/private/link-local/metadata blocking, redirect revalidation, least-privilege OAuth, protected secret/vault, user/org connection ownership, source ACL, `read != write`, `draft != send`, provider event authenticity/dedupe/reconciliation, and external Knowledge candidate governance.

WhatsApp personal-session scraping remains forbidden by default.

## 8. Automation / RPA / Computer-use security

- semantic capability, not UI mechanics, reaches planner;
- API preferred over RPA when authoritative supported contract exists;
- background action uses explicit user/service identity;
- RPA credentials injected through protected boundary;
- worker/session isolation;
- ambiguous write no blind retry;
- technical success must not be announced as verified success;
- computer-use sandbox/app/network allowlists;
- user takeover/emergency stop;
- screenshots/artifacts classified/redacted/retained by policy.

## 9. Event-driven security

Event source authenticity/trust, dedupe/order/correlation and stale handling are mandatory. Event payload cannot grant permission, switch autonomy, or directly execute a write.

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

Control Tower may enable/disable assets, manage rollout/risk/evals/budgets/kill switches, but **Control Tower admin != business permission**.

Asset registry metadata never contains broad secrets and never grants the declared permissions/scopes.

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

## 13. Personal Memory security/privacy

Personal Memory is user-owned/private by default.

Prohibited:

- cross-user memory access;
- sensitive/personality/health/trust inference;
- memory as business/RBAC truth;
- hidden employee profile;
- auto-promotion to organizational Knowledge.

User must have view/correct/delete/disable controls according to policy.

## 14. Semantic Business Layer security

Semantic definitions do not grant source data access. Every query revalidates source/domain permissions.

Material metric has owner/version/formula/grain/dimensions/freshness. Same-name conflicting metrics are explicit; LLM may not silently select or invent a formula.

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

## 16. Artifact security

Artifact keeps owner/version/ACL/provenance/sensitivity/retention. Human edits must not be silently replaced.

External share/send is a separate governed action. Generated file content may itself be untrusted for downstream systems.

## 17. Predictive / Prescriptive security

```text
prediction != FACT
recommendation != authorization
```

Model output must include applicability/freshness/limitations and cannot by itself authorize a high-impact action. Protected/sensitive-person features require separate governance and are forbidden by default for employment decisions.

## 18. Operational Twin / Simulation security

```text
SIMULATED_STATE != PRODUCTION_STATE
SIMULATE != APPLY
```

Scenario changes never mutate source systems. Apply creates a fresh live read/revalidation/Decision/action flow.

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

## 20. Model lifecycle / Marketplace / supply-chain security

- only approved model/deployment can be selected;
- revoked/unapproved model unavailable;
- eval/version/owner/risk traceable;
- Marketplace manifest declares dependencies/data scopes/required permissions but **does not grant them**;
- executable packages require trusted publisher/integrity/dependency/license/vulnerability controls as applicable;
- revoke/rollback path mandatory;
- external marketplace never auto-activates production code.

## 21. Biometric / Human Observation / people security

Biometric match remains candidate identity, not auth/RBAC. Templates protected/revocable. Human Observation limited to observable process evidence; no psychological/sensitive inference or autonomous employment decision.

## 22. Knowledge / Graph / Case / Room security

Membership/relationship/reference never grants access to original source. Personal/external/process/model outputs become durable organizational Knowledge only via candidate/review/eval/publish.

## 23. Industrial / OT boundary

Copilot is not a safety controller.

```text
free-form LLM/model/vision/voice/Edge output
-X→ direct PLC/CNC/robot/machine actuation
```

Any future actuation requires separate approved industrial safety architecture/gate.

## 24. Audit requirements

Material audit can reconstruct:

```text
trigger/actor
source/evidence refs
policy/decision version
semantic metric/model/tool/agent/executor versions
arguments hash
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
Copilot writes
Internet Research/fetch
provider/connection/external send
webhook/sync
Watch ACT/autonomy
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
