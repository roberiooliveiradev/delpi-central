# 11 — Observabilidade, métricas e evals

**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Tests:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Control Tower:** [`59-ai-control-tower-and-digital-workforce-governance.md`](./59-ai-control-tower-and-digital-workforce-governance.md)  
**Specs temáticas:** `53–66`

## 1. Objetivo

Provar qualidade, groundedness, policy, execução, continuidade, privacidade, custo, value/outcome truth e independência do Chat sem transformar telemetry em cópia de business data, mailbox, raw media, employee surveillance ou secrets.

## 2. Correlation model

```text
requestId
traceId
conversationId?/turnId?
workflowId?/taskId?/caseId?/decisionId?/watchId?
eventId?/executionId?
processTraceRef?
analysisRunId?/artifactId?/scenarioId?
predictionId?
meetingId?/frontlineSessionId?
externalConnectionRef?
modelRef?/assetRef?/edgeDeviceRef?
```

Nunca token/password/biometric template/chain-of-thought.

## 3. Core spans

```text
copilot.turn
├ understand
├ capability_discovery
├ knowledge_retrieval
├ semantic_metric_resolve
├ process_analysis
├ internet_search/web_fetch/external_read
├ event_ingest/decision_path
├ policy_check/decision_gate
├ model_inference/prediction
├ sandbox_analysis
├ artifact_generate
├ workflow
├ automation_select_executor/execute/outcome_verify
├ tool_invoke/agent_delegate
├ edge_sync
├ notification
├ evidence_compose
└ synthesis
```

Additional lifecycle streams:

```text
copilot.memory
copilot.ai_asset
copilot.model
copilot.marketplace
copilot.process
copilot.analysis
copilot.artifact
copilot.scenario
copilot.edge
copilot.external.connection/subscription
copilot.automation.execution/worker
```

## 4. Common metadata

```text
surface
sourceClass
capabilityRef
actorType USER|SERVICE
policyVersion
decisionPath FAST|OPERATIONAL|REASONING
modelRef/version bounded
metricDefinitionRef/version?
processRef/traceRef?
executorType/version?
autonomyLevelAllowed
verificationStatus
assetRef/riskTier?
edgeMode/deviceClass?
latency/error class
cost usage when applicable
```

Do not log full content merely for convenience.

## 5. Product metrics

Track separately:

- Task/Case Completion and resolution;
- First Plan Success / Correction rate;
- Evidence Coverage;
- Meeting/Frontline success;
- Watch Signal Quality;
- Process cycle-time/bottleneck/conformance improvement;
- Automation Verified Outcome Rate;
- Human Intervention/Exception Resolution;
- External Follow-up Closure;
- Artifact adoption/edit/use rate;
- Personalized briefing usefulness/correction;
- Prediction quality/calibration by use case;
- Prescriptive recommendation acceptance/outcome;
- Knowledge/Marketplace candidate acceptance;
- Standalone Independence = 100% outside reference-only tests.

## 6. Process Intelligence metrics/evals

Metrics:

```text
process cases/variants
trace completeness
bottleneck/wait/rework measures
conformance deviations
manual-step/automation opportunity candidates
before-vs-after cycle/error/rework metrics
```

Evals:

- known process reconstruction;
- incomplete/out-of-order logs;
- conformance vs insufficient evidence;
- opportunity provenance;
- no hidden individual productivity/person score;
- no fraud/personality inference from deviation.

## 7. AI Control Tower metrics

Per asset:

```text
owner/status/risk/eval validity
usage/latency/availability
cost
verified business value
incidents
policy/kill-switch state
dependencies/deployment versions
```

Control Tower must distinguish **activity**, **technical success** and **verified business value**.

## 8. MCP/A2A metrics/evals

```text
approved/discovered/disabled server-agent count
tool/agent invocation latency/error
context bytes/data classes delegated
timeout/cancel rate
duplicate task rate
unapproved invocation blocked
result provenance coverage
```

Safety evals: tool-description injection, external agent scope expansion, recursive delegation, disabled/revoked agent use, unrelated data leakage.

## 9. Personal Memory metrics/evals

Product quality only, never employee score:

```text
memory correction/delete rate
personalization opt-out rate
stale-memory conflict rate
briefing relevance feedback
memory influence explanations when material
```

Required negatives: cross-user leak, sensitive inference, stale memory overriding live source, memory granting permission, private memory becoming organizational knowledge.

## 10. Semantic Business Layer metrics/evals

```text
metric query success
formula/version coverage
source freshness
semantic conflict count
metric-definition adoption
calculation reproducibility
```

Metamorphic test: paraphrase user question while preserving same governed metric → same calculation/result for same source snapshot.

## 11. Analysis Sandbox metrics/evals

```text
analysis success/failure/timeout
CPU/memory/time/storage usage
blocked network/host attempts
input/output size
reproducibility rate
artifact generation rate
```

Required negatives: sandbox escape, private-network access, secret read, unauthorized dataset, read connector mutating source, fabricated result after execution failure.

## 12. Artifact metrics/evals

- provenance coverage;
- human edit preservation;
- version conflicts;
- review/publish/export rate;
- stale source-dependent section detection where applicable;
- external share attempts blocked/allowed by policy.

No metric should reward overwriting human edits.

## 13. Predictive/Prescriptive metrics/evals

By model/use case:

```text
accuracy/error appropriate to target
calibration
precision/recall where relevant
forecast error
false alert rate
OOD/stale rate
prediction latency
business outcome correlation
prescriptive objective/trade-off quality
```

Never aggregate into one vague “AI accuracy”. Prediction and recommendation quality are separate from action authorization.

## 14. Operational Twin metrics/evals

- scenario reproducibility;
- source-state freshness;
- simulation latency/cost;
- assumption coverage;
- compare-scenario consistency;
- Apply revalidation failures;
- production mutation during simulation incidents = 0.

## 15. Edge/Offline metrics/evals

```text
device health/last seen
package/model version distribution
cache freshness
online/degraded/offline duration
buffer depth/sync lag
duplicate sync prevented
offline blocked action attempts
rollback/revoke propagation
local inference latency/error
```

Safety: loss of cloud never widens authority; stale critical revision is blocked/degraded explicitly.

## 16. Model lifecycle / drift metrics

Per model type:

```text
quality drift
input/data drift
calibration drift
latency
availability
cost
human correction rate
verified outcome correlation
deployment cohort/version
rollback/revoke events
```

Revoked/unapproved model selection count must be zero.

## 17. Marketplace / AI supply-chain metrics/evals

- packages by lifecycle state;
- publisher/owner coverage;
- dependency/license/vulnerability review state;
- signature/hash verification when required;
- enable/disable/revoke propagation;
- permission-escalation attempts = 0;
- untrusted executable activation = 0.

## 18. Event / Automation metrics

Keep separate:

```text
events received/invalid/deduped/stale
FAST/OPERATIONAL/REASONING rate/latency
executions queued/running/success/failure/ambiguous/timeout
queue latency/worker health
retry/idempotency conflicts
technical success rate
verified business outcome rate
technical-success-but-verification-failed count
kill-switch activations
```

Technical success and verified outcome must never be the same KPI.

## 19. External/Teams/Media/Biometric metrics

Preserve all existing connector/research/OAuth/subscription/media/biometric privacy and quality metrics from `20`, including credential/cross-user leak incidents = 0 and biometric false accept/reject/unknown/correction rates where capability is enabled.

## 20. Cost and value

Measure separately:

```text
LLM/model/provider cost
search/connector cost
sandbox compute cost
automation/RPA cost
Edge infrastructure cost
human review cost
```

Value requires verified outcomes such as saved cycle time, avoided rework/loss, reduced downtime, recovered revenue, improved SLA. Avoid vanity ROI based only on number of AI calls.

## 21. Incident classes

At least:

```text
AUTHORITY_OR_PERMISSION_BYPASS
DATA_OR_SECRET_LEAK
EVENT_DUPLICATE_EFFECT
OUTCOME_FALSE_SUCCESS
AUTONOMY_OR_KILL_SWITCH_BYPASS
PROCESS_MINING_PRIVACY_INCIDENT
TOOL_AGENT_TRUST_INCIDENT
MEMORY_PRIVACY_INCIDENT
SEMANTIC_DEFINITION_INCIDENT
SANDBOX_ESCAPE
MODEL_DRIFT_OR_REVOKED_MODEL_USE
SIMULATION_PRODUCTION_MUTATION
EDGE_AUTHORITY_OR_STALE_CONTENT_INCIDENT
AI_PACKAGE_SUPPLY_CHAIN_INCIDENT
OT_SAFETY_BOUNDARY_ATTEMPT
```

Each incident has asset refs/evidence/impact/containment/owner/resolution without CoT/secrets.

## 22. Dashboards alvo

```text
Operational Intelligence
Process Intelligence
Automation & Execution Hub
Autonomy
AI Control Tower / Digital Workforce
Model Health / Drift
Semantic Metrics/Data Quality
Sandbox/Artifacts
Predictive/Twin
Edge Fleet
External/Media/Privacy
Cost & Verified Value
```

## 23. Evals governance

Every production capability/asset has suitable eval suite/version and freshness. High-risk asset with stale/missing required eval is disabled or degraded according to policy.

Metamorphic/generalization evals cover provider/executor/model/tool/agent replacements without planner hardcode.

## 24. Regra final

Observability must answer, when material:

```text
what triggered this?
which sources/evidence/metric/model versions were used?
which policy/decision path ran?
under whose authority?
which tool/agent/executor ran?
what was the technical result?
what authoritative source verified outcome?
what artifact/prediction/scenario was produced?
what was notified/published?
what became only a learning candidate?
which asset/version can be disabled or rolled back?
```

Sem armazenar chain-of-thought, broad sensitive payloads ou secrets.
