# 11 — Observabilidade, métricas e evals

**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Objetivo

Provar qualidade, groundedness, policy, execução, continuidade, privacidade, custo, outcome truth, automação e independência do Chat sem transformar telemetry em cópia de business data, mailbox, raw media, desktop screenshots ou secrets.

## 2. Correlation model

```text
requestId
conversationId?
turnId?
traceId
workflowId?
taskId?
caseId?
decisionId?
watchId?
eventId?
executionId?
meetingId?
frontlineSessionId?
externalConnectionRef? opaque
executorRef? bounded
```

Nunca token/password/secret/biometric template.

## 3. Spans/eventos sugeridos

```text
copilot.turn
├─ understand
├─ capability_discovery
├─ knowledge_retrieval
├─ internet_search / web_fetch
├─ external_read/write
├─ event_ingest
├─ decision_path
├─ policy_check / decision_gate
├─ workflow
├─ automation_select_executor
├─ automation_execute
├─ outcome_verify
├─ notification
├─ evidence_compose
└─ synthesis

copilot.event
copilot.watch
copilot.automation.execution
copilot.automation.worker
copilot.external.connection
copilot.external.subscription
copilot.workflow/task/case
copilot.media/meeting/frontline
```

## 4. Metadata útil

```text
surface
sourceClass
capabilityRef
actorType USER|SERVICE
policyVersion
decisionPath FAST|OPERATIONAL|REASONING
eventSourceClass/eventTrustResult
eventDedupeResult
executorType API|FUNCTION|RPA|COMPUTER_USE|HUMAN_TASK
executorVersion bounded
executionStatus
attempt
queueLatency
workerClass/environment bounded
outcomeVerificationStatus
notificationStatus
autonomyLevelAllowed
autonomyPolicyVersion
killSwitchState
latency/error class
model/tool/token/cost usage when applicable
```

Não logar message body/full page/raw screenshot/credential apenas por observabilidade.

## 5. Métricas de produto

- Task Completion Rate;
- First Plan Success Rate;
- Evidence Coverage;
- Correction/Replan Rate;
- Case Resolution Rate;
- Meeting/Frontline success;
- Internet Research usefulness;
- External Action Verified Success Rate;
- Watch Signal Quality;
- **Operational Detection-to-Decision Time**;
- **Decision-to-Execution Time**;
- **Automation Verified Outcome Rate**;
- **Human Intervention Rate**;
- **Exception Resolution Time**;
- **Autonomous Completion Rate por capability**;
- **False/Unnecessary Automation Rate**;
- Knowledge Candidate Acceptance/Reject Rate;
- Standalone Independence Rate = 100% fora reference-only tests.

Nunca usar uma métrica agregada de “autonomia” sem separar capability/risco/contexto.

## 6. Métricas Event / Decision Intelligence

```text
events received
invalid/untrusted events rejected
duplicate events suppressed
out-of-order/stale events
watch matches
FAST path rate/latency
OPERATIONAL path rate/latency
REASONING path rate/latency
LLM avoided by deterministic path
readiness PASS|NOT_READY|INCONCLUSIVE distribution
policy blocks
Decision Gate frequency
```

Decision path metadata é bounded telemetry, não CoT.

## 7. Métricas Automation & Execution Hub

```text
executions queued/running/completed
execution success/failure/ambiguous/cancelled/timeout
technical success rate
verified business outcome success rate
technical-success-but-verification-failed count
ambiguous outcome rate
retry rate
idempotency conflicts prevented
duplicate execution prevented
queue latency
executor latency
worker online/busy/offline/draining when RPA exists
worker utilization
package/executor version distribution
RPA UI/selector failure class
computer-use takeover/stop rate
kill-switch activations
cost per execution/capability when material
```

Technical success and verified outcome must be separate charts/metrics.

## 8. Notification/escalation metrics

- notification requested/sent/failed;
- dedupe suppression;
- acknowledgement time;
- SLA escalation count/time;
- channel fallback when policy allows;
- incorrect “success” notification incidents = 0.

## 9. External/connector metrics

- search/fetch latency/error;
- blocked external-access attempts;
- provider latency/rate limit;
- connection refresh/re-auth rate;
- scope-missing rate;
- event duplicate/out-of-order rate;
- subscription renewal/reconciliation lag;
- external ambiguous-outcome rate;
- credential leak incidents = 0;
- cross-user data leak = 0;
- implicit send incidents = 0.

## 10. Evals families — Event/Automation

```text
trusted event positive
forged/untrusted event negative
duplicate event
event replay after workflow resume
stale event
FAST path deterministic condition
OPERATIONAL bounded condition
REASONING complex condition
equivalent condition with LLM unavailable
readiness positive/negative/inconclusive
planner no RPA click/selector
API executor preferred over RPA when supported
RPA fallback when API unavailable by approved mapping
executor swap RPA→API without planner patch
worker offline/busy/lease conflict
credential/session isolation
executor timeout before side effect
executor timeout after possible side effect → AMBIGUOUS
outcome verification success/failure/pending
notification only after truthful outcome
PREPARE no side effect
ACT requires capability-scoped autonomy
kill switch before ACT
policy revocation during wait
computer-use allowlist negative
```

## 11. External/Media/Biometric evals

Manter famílias de Internet Research, OAuth/connectors, Teams, multimodal, biometric/Human Observation, source ACL, external Knowledge promotion, Meeting/Frontline e privacy conforme `20`.

## 12. Generalization

Novo provider ou executor equivalente deve entrar por adapter/capability mapping sem patch semântico no planner.

Metamorphic tests devem poder trocar:

```text
Microsoft ↔ another supported provider
RPA executor ↔ API executor
technical executor identifiers/package versions
```

preservando semantic capability e policy/outcome expectations.

## 13. Safety evals

- event content não altera policy;
- event/worker identity não concede permission;
- external/RPA content não concede Core permission;
- provider/RPA credential não aparece em LLM/MFE/log/artifact;
- RPA screenshot não vaza unrelated sensitive data;
- read scope não permite write;
- PREPARE não executa;
- global L5 não existe;
- L5 disabled by default;
- kill switch blocks ACT independent of LLM;
- ambiguous write not blindly retried;
- technical success not presented as business success;
- computer-use cannot access non-allowlisted app/network;
- biometric/worker profiling prohibitions remain;
- arbitrary OT command blocked.

## 14. Outcome quality

Para cada material execution medir/provar:

```text
capabilityRef
technical result
expected postcondition
verification source authority
verification status
verifiedAt
Evidence/Outcome refs
```

Se verification source estiver indisponível, state deve ser `PENDING|INCONCLUSIVE`, não success inventado.

## 15. RPA observability privacy

Quando RPA existir:

- screenshots somente quando necessário;
- classification/retention/redaction explícitos;
- no password/token capture;
- worker/session identifiers bounded;
- no person productivity score derived from bot/desktop telemetry;
- support artifact access audited.

## 16. Autonomy metrics

Medir por capability/policy version:

```text
L0/L1/L2/L3/L4/L5 usage
L5 eligible vs executed
policy-blocked ACT
human-confirmed ACT
autonomous ACT
kill-switch block
budget/limit block
post-ACT verification failure
manual override/correction
```

Não usar autonomia como permission authority.

## 17. Incident classes

```text
EVENT_AUTH_FAILURE
EVENT_DUPLICATE_EFFECT
BACKGROUND_IDENTITY_ERROR
EXECUTION_DUPLICATE
RPA_CREDENTIAL_LEAK
RPA_SESSION_LEAK
OUTCOME_FALSE_SUCCESS
AUTONOMY_SCOPE_BYPASS
KILL_SWITCH_BYPASS
COMPUTER_USE_BOUNDARY_BYPASS
EXTERNAL_DATA_LEAK
BIOMETRIC_PRIVACY_INCIDENT
OT_SAFETY_BOUNDARY_ATTEMPT
```

Incident metrics devem ter correlation/evidence sem guardar secret/CoT.

## 18. Dashboards alvo

### Operational Intelligence
Events → Watches → decision path → detections → decisions → latency.

### Automation Hub
Queued/running/failed/ambiguous → executors/workers → technical success → verified outcome → exceptions.

### Autonomy
Capabilities/policy levels → PREPARE/ACT → blocks/kill switches → verified outcomes.

### External/Media
Provider health, research/connectors, source provenance, privacy/retention incidents.

## 19. Release blocking metrics

Material incident/eval failures block release when involving:

```text
permission elevation
duplicate material execution
unverified success narrative
credential leak
cross-user/source leak
PREPARE→ACT bypass
global autonomy bypass
kill-switch failure
computer-use boundary breach
OT safety boundary breach
```

## 20. Regra final

Observability must answer:

```text
what event/intent triggered this?
which facts/evidence were used?
which decision path/policy version ran?
which capability/executor/version executed?
under whose authority?
what was the technical result?
what authoritative source verified the business outcome?
who was notified?
what was learned only as candidate?
```

without storing chain-of-thought or secrets.
