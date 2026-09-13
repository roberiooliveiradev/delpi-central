# 07 — Workflows Agentic e Durable Work

**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Runtime detail:** [`43-durable-workflow-runtime.md`](./43-durable-workflow-runtime.md)

## 1. Objetivo

Permitir objetivos compostos com múltiplas capabilities/fontes/executors/tools/agents, preservando dependency, policy, Evidence, Decision Gates, idempotency, continuity and Outcome truth.

“Agentic” describes orchestration pattern, not departmental-agent products.

## 2. One durable runtime

`WorkflowPlan/WorkflowStep/TaskRef/CaseRef/waits/correlation` are shared foundations. Do not create separate workflow engine inside provider connector, Automation Hub, MCP/A2A, Process Intelligence, Control Tower or Marketplace.

## 3. Execution model

```text
GOAL / EVENT
→ UNDERSTAND
→ RETRIEVE authorized capabilities/expertise/semantic/process context
→ PLAN DAG
→ CHECK POLICY / AUTONOMY
→ EXECUTE READY STEPS
→ VERIFY Outcome/Evidence
→ CHECKPOINT
→ CONTINUE | REPLAN | WAIT | COMPLETE | BLOCK
```

No CoT persistence.

## 4. WorkflowStep

May reference:

```text
capabilityRef
entity/source refs
dependencies
preconditions/postconditions
actor/service identity
Decision ref
executor/tool/agent/model refs bounded
expected Outcome
time/budget
idempotency/retry metadata
```

Concrete provider/RPA/MCP/A2A mechanics stay behind adapters.

## 5. Parallelism

Safe independent reads may run in parallel. Writes/material side effects are serialized or explicitly coordinated only when contracts prove safety.

## 6. Replanning

Allowed on unavailable capability/provider/executor/model/tool/agent, missing args, changed premise, stale source, policy block, user goal change, partial failure or failed Outcome verification.

Replan never relaxes permission/autonomy/Decision/safety boundaries.

## 7. Clarification

Ask only genuinely missing required data after checking message/context/entities/Evidence/memory/live source. Personal Memory can provide preference/continuity, but stale memory never fills a material business fact silently.

## 8. Durable states

Candidate:

```text
planned
running
waiting_user
waiting_approval
waiting_event
waiting_time
waiting_external_agent
waiting_execution
verifying_outcome
succeeded
partially_succeeded
failed
cancelled
expired
```

Do not add states unless real lifecycle needs them.

## 9. Checkpoint

Persist operational state only:

```text
plan/version
completed/active steps
Outcome/Evidence refs
Decision refs
wait state
attempt/idempotency
error classification
actor/service identity ref
checkpoint version
```

No chain-of-thought or broad provider/tool credentials.

## 10. Retry / idempotency

- reads retry by policy;
- writes only with proven idempotency or safe reconciliation;
- duplicate event/resume cannot duplicate side effect;
- RPA/computer-use timeout after possible commit becomes AMBIGUOUS until verified;
- A2A duplicate delegated task/result is deduped/correlated;
- Edge buffered events sync idempotently.

## 11. Partial / degraded outcomes

Represent truthfully:

```text
SUCCEEDED
PARTIALLY_SUCCEEDED
BLOCKED
FAILED
CANCELLED
WAITING_*
INCONCLUSIVE/AMBIGUOUS when material
```

Source/model/tool unavailable is not “no business data”.

## 12. Decision boundaries

```text
impact preview
+ args hash
+ Evidence refs
+ risk/policy
→ Decision Gate
→ live revalidation
→ execute
→ Outcome verification
```

`PREPARE != ACT`; `SIMULATE != APPLY`.

## 13. Background event workflow

```text
trusted EventEnvelope
→ correlate Watch/Workflow
→ resolve explicit user/service actor
→ revalidate authorities/policy
→ resume/evaluate
```

Event/worker/device identity never grants business authority.

## 14. Automation executor step

Workflow requests semantic capability; Automation Hub resolves executor. Workflow never contains RPA clicks/selectors. Technical result is followed by postcondition verification when required.

## 15. MCP/A2A step

Delegated tool/agent step uses approved capability/agent, bounded inputs, timeout/cancel/budget and normalized result. Write-capable delegation uses same Decision/Outcome gates.

## 16. Analysis / Artifact step

Sandbox analysis can be a workflow step with bounded authorized inputs and artifact outputs. Artifact version/provenance/ACL become workflow refs; external share/send remains a separate action.

## 17. Prediction / Scenario step

Prediction/Scenario outputs are evidence/recommendation inputs, not write authorization. Apply is separate live action step.

## 18. Process Intelligence step

Process Mining/conformance may feed findings/opportunity candidates into Case/Task/PREPARE; no automatic policy/automation deploy.

## 19. Task / Case / Room / Inbox

These are product/work projections over the same durable runtime, not independent planners/executors. Source ACL remains required even if a ref is attached to a Case/Room.

## 20. Budgets

Bound planner rounds, tools/agents, retries, fan-out, elapsed time, tokens/model cost, sandbox compute, external/API rate and workflow lifetime. Budget exhaustion is explicit state.

## 21. Audit

Material step is correlatable by actor/service, request/workflow/task/case, capability/source/entity refs, policy/Decision, executor/tool/agent/model refs, technical result, verified Outcome/Evidence and timestamps.

## 22. Core invariant

```text
one durable workflow runtime
+ replaceable adapters/executors/tools/agents/models
+ explicit waits/checkpoints
+ live authority revalidation
+ verified outcomes
```

No thematic capability may create a hidden parallel orchestration engine.
