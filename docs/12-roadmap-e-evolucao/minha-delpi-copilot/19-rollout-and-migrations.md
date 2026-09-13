# Minha DELPI Copilot — Rollout, Migrações e Implantação

**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary standalone:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Princípio

Rollout não é desculpa para manter duas authorities ou duas arquiteturas permanentes.

As capacidades externas entram progressivamente, sempre reutilizando os contracts canônicos de Source/Evidence/Policy/Decision/Workflow.

## 2. Ordem de rollout do produto

```text
Foundation
→ Standalone Bootstrap
→ Context/Navigation
→ Internal Intelligence/Reads
→ Internet Research
→ External Connected Reads
→ Governed Business Writes
→ Governed External Drafts/Writes
→ External Events/Watch
→ Meeting/Frontline with external sources
→ Selected External Proactivity
```

Não liberar send/proatividade antes de provar read/isolation/connection lifecycle.

## 3. External provider rollout

Cada provider entra como candidate independente:

```text
inventory/contract
→ connection/auth integration
→ read-only pilot
→ source/evidence validation
→ write disabled
→ draft capability
→ selected write capability
→ event/subscription integration
→ proactive capability only if justified
```

Novo provider não altera planner architecture.

## 4. Connection rollout classes

Preferência de menor risco primeiro:

```text
ORG_MANAGED read-only pilot
or
USER_DELEGATED read-only pilot with narrow scopes
```

Depois, conforme evidence:

```text
SHARED_RESOURCE
SERVICE_CONNECTION
write scopes
background subscriptions
ACT automation
```

A ordem exata é policy/owner-dependent; C0/C3 evidence decide.

## 5. Internet Research rollout

```text
internal users / allowlisted cohort
→ read-only public search
→ safe fetch/citations
→ freshness/conflict evals
→ wider cohort
→ Task/Case integration
→ background research only after C7 gate
```

Browser automation não entra junto com basic research; exige necessidade separada.

## 6. External communication rollout

Para email/messaging:

```text
read/search
→ draft only
→ draft + explicit send confirmation
→ risk-based Decision Gate
→ selected allowlisted automation only much later
```

`draft != send` em todas as fases.

## 7. Provider event rollout

```text
manual/read polling baseline if necessary
→ provider subscription/webhook pilot
→ authenticity/dedupe
→ renewal/reconciliation
→ Watch OBSERVE
→ Watch ADVISE
→ ACT only in C7 when explicitly allowlisted
```

Event delivery incompleta não pode ser tratada como monitoramento garantido.

## 8. Knowledge rollout

```text
transient external research
→ Case/Task Evidence
→ user knowledge candidate
→ organizational candidate
→ review/eval/freshness/privacy/licensing
→ versioned publish
```

Never bulk-ingest a personal mailbox or chat history into organizational Knowledge by default.

## 9. DB/schema migration pattern

```text
EXPAND
→ compatible readers
→ writers
→ optional backfill
→ cutover
→ monitor
→ cleanup
```

ExternalConnection/Subscription schemas follow same pattern when owned by Copilot.

No migration from Chat DB is required.

## 10. Provider/credential migration

Provider swap or app-registration change:

```text
new adapter/config
→ new connection version / reauthorization if required
→ canary connections
→ observe errors/scopes
→ cutover
→ revoke old credentials
→ cleanup old adapter/config
```

Never copy plaintext credentials between stores as a migration shortcut.

## 11. Subscription migration

When webhook/subscription contract changes:

```text
create compatible new subscription
→ run overlap with dedupe
→ validate reconciliation
→ cut over
→ cancel old subscription
→ residual scan
```

Avoid event gaps and duplicate effects.

## 12. Cache/index migration

External caches are derived. Prefer rebuild/invalidate over complex migration when possible, preserving user/connection isolation.

## 13. Feature flags

Flags may control rollout but cannot create permanent split authorities.

Examples:

```text
internet_research_enabled
provider_<x>_enabled
external_reads_enabled
external_writes_enabled
provider_events_enabled
external_watch_enabled
browser_fallback_enabled
```

Flags have owner, purpose, exit criteria and rollback plan.

## 14. Kill switches

Operationally independent kill switches for:

- Internet Research;
- provider;
- specific connection;
- external writes/messaging;
- webhook ingestion;
- background sync/watch;
- browser automation;
- Copilot writes generally.

## 15. Rollback

Rollback must preserve:

- no credential exposure;
- connection metadata integrity;
- no duplicate send/write;
- provider subscriptions either safely active or explicitly disabled;
- stale state visible;
- source/Evidence refs remain interpretable;
- Chat remains irrelevant to rollback.

## 16. Provider terms/scopes change

Provider contracts evolve independently of DELPI.

At each rollout/release:

- revalidate scopes;
- revalidate provider limits/terms;
- revalidate webhook/subscription lifecycle;
- revalidate data handling/retention requirements;
- run provider contract tests.

Do not assume a provider behavior from a previous release remains valid indefinitely.

## 17. Cohort strategy

Possible sequence:

```text
TI/admin internal
→ selected power users
→ selected departments
→ wider authenticated users
→ external writes for approved roles
→ Meeting/Frontline external reads where useful
→ selected proactive external actions
```

Provider connections remain owner-specific even when feature flag is broad.

## 18. Metrics before expansion

Require suitable evidence for:

- research quality/source correction rate;
- provider read success;
- connection refresh/re-auth errors;
- scope issues;
- external action verified success;
- duplicate effect prevented;
- subscription renewal/reconciliation;
- privacy incidents = 0 target;
- credential leakage = 0;
- cross-user data leak = 0;
- implicit send = 0;
- user feedback/value.

## 19. Stop-the-line

Pause rollout on:

```text
credential leakage
cross-user external data leak
unverified external success
implicit send
scope escalation bug
invalid provider event accepted
missed events without truthful stale state/reconciliation
personal source auto-shared/promoted
provider-specific planner drift
unsafe egress
architecture/pattern drift
Chat runtime dependency
```

## 20. Final rollout criterion

External capabilities are mature only when read/write/event/knowledge lifecycles remain provider-neutral, auditable, privacy-scoped, resilient to revoke/expiry/provider failure and independently disableable without destabilizing the rest of the Copilot.
