# 11 — Observabilidade, métricas e evals

**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Objetivo

Provar qualidade, groundedness, policy, execução, continuidade, privacidade, custo e independência do Chat — inclusive para Internet Research e External Connectors — sem transformar telemetry em cópia de mailbox, raw media ou secrets.

## 2. Correlation model

```text
requestId
conversationId
turnId
traceId
workflowId?
taskId?
caseId?
decisionId?
watchId?
meetingId?
frontlineSessionId?
mediaSessionId?
externalConnectionRef? bounded/opaque
externalSubscriptionRef? bounded/opaque
```

Nunca token/secret.

## 3. Spans/eventos sugeridos

```text
copilot.turn
├─ understand
├─ capability_discovery
├─ knowledge_retrieval
├─ internet_search
├─ web_fetch
├─ external_connection_check
├─ external_read
├─ external_write_preview
├─ policy_check
├─ decision_gate
├─ external_write
├─ outcome_verify
├─ evidence_compose
└─ synthesis

copilot.external.connection
copilot.external.subscription
copilot.external.event
copilot.workflow/task/case/watch
copilot.media/meeting/frontline
```

## 4. Metadata útil

```text
surface
sourceClass = delpi|public_web|external_connected
providerKey bounded
connectionType
connectionStatus
requiredScopePresent yes/no
externalCapabilityId
source/evidence counts
freshness class
policy/decision outcome
external action status
subscription status
retry/reconciliation flags
latency/error class
token/model/tool usage
```

Não logar message body/file content/raw page/credentials só por observabilidade.

## 5. Métricas de produto

- Task Completion Rate;
- First Plan Success Rate;
- Evidence Coverage;
- Correction/Replan Rate;
- Case Resolution Rate;
- Meeting/Frontline success;
- Internet Research usefulness/source correction rate;
- External Read Success Rate;
- External Draft-to-Send conversion quando relevante;
- External Action Verified Success Rate;
- Watch Signal Quality;
- External Follow-up Closure Rate;
- Knowledge Candidate Acceptance/Reject Rate;
- Standalone Independence Rate = 100% fora reference-only tests.

## 6. Métricas técnicas externas

- search/fetch latency/error;
- blocked external-access attempts;
- external provider latency/error/rate-limit;
- connection refresh/re-auth rate;
- scope-missing rate;
- provider event duplicate/out-of-order rate;
- subscription renewal success;
- reconciliation lag;
- stale subscription duration;
- external action ambiguous-outcome rate;
- duplicate outbound effect prevented;
- cache hit/staleness per source class;
- credential leakage incidents = 0;
- cross-user external data leak = 0;
- implicit send incidents = 0.

## 7. Evals families

Além dos evals de context/action/expertise/multimodal/biometric/workflow:

```text
Internet Research known topic
Internet Research current/fresh topic
conflicting public sources
external prompt injection
safe external-access policy
OAuth connect/cancel/fail/revoke
scope missing / scope upgrade
user-delegated isolation
unknown connector onboarding
external read source provenance
external attachment handling
draft != send
external write Decision/TOCTOU
provider timeout/verified outcome
webhook authenticity/dedupe
subscription expiry/renewal
missed-event reconciliation
personal source sharing/promotion
external Knowledge candidate governance
background/proactive external action limits
```

## 8. Generalization

Novo provider deve poder entrar por adapter/capability contract sem patch semântico no planner.

Metamorphic tests podem trocar provider implementation/technical identifiers preservando semantic capability e esperar comportamento equivalente.

## 9. Safety evals

- external content não altera policy/system;
- external source não concede Core permission;
- provider credential não aparece em LLM/MFE/log;
- user A não acessa connection/cache de user B;
- read scope não permite send;
- scope revogado bloqueia action;
- draft não envia;
- webhook não executa write diretamente;
- personal source não publica organizational Knowledge automaticamente;
- public source não substitui internal authority silenciosamente;
- provider unavailable não é narrado como “sem resultados”;
- WhatsApp connector usa contract suportado;
- kill switch interrompe capability correspondente.

## 10. Evidence quality

Para source externo, medir:

- SourceRef presente;
- freshness/data quando material;
- provider/resource identificável sem credential;
- authoritative/reference/unverified classification adequada;
- conflito/staleness explícito;
- external communication outcome verificável;
- Knowledge candidate ligado à Evidence original.

## 11. External connection evals

Estados mínimos:

```text
PENDING_AUTH
ACTIVE
EXPIRED
REAUTH_REQUIRED
REVOKED
DISABLED
ERROR
```

Testar transitions, reconnect, revoke, cleanup, owner isolation e stale capability invalidation.

## 12. Provider event evals

- valid/invalid event;
- duplicate;
- out-of-order;
- expired subscription;
- renew success/failure;
- missed event + reconciliation;
- revoked connection;
- stale state reflected in UX/Watch.

## 13. External write evals

- draft only;
- send after allowed gate;
- recipient/target change invalidates prior decision when material;
- revoked connection after preview;
- duplicate resume;
- provider timeout and outcome check;
- partial/ambiguous failure truthfulness;
- verified OutcomeRef/Audit.

## 14. Privacy evals

- user-delegated source isolation;
- organizational/shared source policy;
- external content retention/cache TTL;
- explicit sharing to Case/Room;
- explicit promotion to Knowledge;
- delete/revoke behavior;
- no raw sensitive payload in telemetry.

## 15. Dashboards/admin

Visões futuras:

- research usage/quality/cost;
- provider/connection health;
- scope/reauth issues;
- external read/write outcomes;
- subscription/reconciliation health;
- external Watch results;
- knowledge promotion outcomes;
- privacy/security blocks;
- connector readiness/coverage;
- standalone independence violations.

## 16. Release blockers

```text
required safety FAIL/INCONCLUSIVE
credential leakage
cross-user external data leak
implicit send
unverified external success
invalid provider event accepted
stale subscription without truthful degraded state
personal source auto-promoted to org Knowledge
provider-specific planner hardcode
Chat runtime dependency
```

## 17. Regra de privacidade

Observabilidade registra metadata operacional estruturada, não chain-of-thought, JWT, provider tokens, client secrets, full emails/messages/files/pages, raw media ou biometric templates sem purpose/owner/policy explícitos.
