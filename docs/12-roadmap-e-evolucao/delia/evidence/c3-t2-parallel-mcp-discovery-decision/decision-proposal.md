# C3-T2 · Parallel MCP Discovery — Architectural Decision Proposal

**Status:** PROPOSED — awaiting coordination decision. NOT implemented.
**Task:** `DELIA-C3-T2-R5-INT3-SUFFICIENCY-AND-PARALLEL-MCP-DISCOVERY-01`, Front B.
**SHA analyzed:** `d1fb95865c`.

```yaml
DECISION_ID: C3_T2_PARALLEL_MCP_DISCOVERY

RESPONSIBILITY: governed capability discovery (provider groups → live catalog)
OWNER: OperationalCapabilityOrchestrator._groups
       (app/application/capability_provision/governed_capability_orchestrator.py:1572)
CONSUMERS:
  - PydanticAiInvestigationOrchestrator.investigate (1×/turn catalog projection)
EXISTING_EQUIVALENT: YES — _groups() is the single canonical discovery path;
  no cache, no pool, no scheduler exists elsewhere
REUSE_DECISION: EXTEND_EXISTING (same function, same provider seam,
  asyncio fan-out inside one bounded stage)

CURRENT_PATH: |
  for provider in self._providers:            # sequential
      deadline.check("surface_list")
      surface = provider.list_groups(...)     # credential exchange + tools/list
      [1 bounded transient retry when deadline permits]
      groups[provider_id:group_id] = group    # deterministic key order

  Measured: ~15.2s fixed per turn (3 specialists × ~5s each:
  delegated-token exchange + MCP tools/list, serialized).

PROPOSED_PATH: |
  results = await asyncio.gather(              # or equivalent bounded fan-out
      provider.list_groups(correlation, timeout=deadline.remaining_seconds())
      for provider in self._providers
  )   # each provider keeps its OWN exchange/credentials/timeout
  merge results keyed by provider_id:group_id — identical output shape
  identical failure collection, identical transient-retry policy per provider

CONTRACT_IMPACT: |
  None on the return contract: (groups dict, failures list) unchanged.
  Provider interface unchanged (same list_groups signature).
  Consumers see identical catalog projection timing — only latency shifts.
SECURITY_IMPACT: |
  Each provider performs its own delegated exchange with its own
  credentials — no credential sharing introduced. Discovery ≠ approval
  invariant untouched (authorization still evaluated per-call at invoke).
AUTHZ_IMPACT: ZERO — catalog remains advisory; AuthZ is per-invocation.
DEADLINE_MODEL: |
  SAME shared TurnDeadline passed to every concurrent call (a clock, not
  a per-provider budget). Each call receives remaining_seconds() at
  dispatch; the deadline check after gather still applies. Parallelism
  does not grant extra wall-clock budget — worst case is bounded by the
  slowest provider, never the sum.
CANCELLATION_MODEL: |
  _cancel_observed() checked before dispatch and after gather; cancelled
  turn abandons all in-flight discovery (asyncio cancellation propagates).
PARTIAL_FAILURE_MODEL: |
  Identical to today: per-provider exception → failures.append(exc.code)
  and that owner contributes nothing — never reclassified as
  capability-absent; catalog_failure markers preserved for the model.
ORDERING_MODEL: |
  groups keyed by f"{provider_id}:{group_id}" — provider iteration order
  no longer matters; deterministic merge keeps identical dict keys.
RESOURCE_LIMITS: |
  Fan-out width = len(self._providers) (3 today) — bounded by registry,
  not by a new pool. tools/list is read-only metadata; provider-side
  rate limits apply per-owner as today.
OBSERVABILITY: |
  Existing stage logs (surface_list, catalog_failure) preserved; add
  per-provider discovery elapsed to the existing trace fields (no new
  observability service).
ROLLBACK: |
  Single-flag or code revert — sequential path is the strict subset;
  no contract migration needed.

EXPECTED_LATENCY_BENEFIT: |
  ~15.2s → ~max(provider latencies) ≈ 5–6s per turn (~65% of the fixed
  cost), for every turn in both agent variants (A and B).
EVIDENCE_REQUIRED: |
  - per-provider list_groups elapsed timings (already in mcp_invoke/
    catalog logs)
  - thread-safety verification of each provider's token-exchange path
    — DONE: token cache is lock-guarded (delegation.py:120); BLOCKER
    FOUND AND SOLVED ON PAPER: subject bearer is ContextVar/flask.g —
    workers need the existing bind_subject_bearer seam
  - Keycloak exchange concurrency limits — none documented; N small
RISKS: |
  - Worker threads see no subject bearer (ContextVar) — resolved by
    the existing binding seam; a bug there fails all-parallel auth
  - Concurrent tools/list bursts could trip owner-side rate limits
  - Deadline starvation: a slow provider still blocks the join to its
    own timeout (same as sequential tail, not worse)
RESIDUALS: |
  - Does not address model-loop latency (dominant cost)
  - Comprehension pass latency untouched

DECISION: READY_FOR_COORDINATION_AUTHORIZATION (revised after
  DELIA-C3-T2-COMPREHENSION-VOCABULARY-RELIABILITY-AND-PARALLEL-
  DISCOVERY-GATE-01 concurrency inventory — see gate section below)
```

## Dependency analysis (evidence)

- Per-provider `list_groups` calls are **independent**: no provider's
  output feeds another's input; each resolves its own delegated token
  and its own tools/list (verified in `_groups` loop and FakeProvider
  contract `list_groups(correlation_id, timeout_seconds)`).
- The **shared** pre-stage (subject session mint) already happens once
  before `_groups` — not parallelized, unchanged.
- Ordering is deterministic post-merge (dict keyed by provider:group).
- Partial failure already modeled per provider (`failures` list +
  `catalog_failure` markers surfaced to the model).

## Concurrency gate inventory (WS-B, SHA ecb464c3a9)

All findings verified against source — nothing presumed.

```yaml
SYNC_ASYNC_VERIFICATION: |
  PROVEN — the whole path is synchronous blocking I/O.
  `provider.list_groups` is a plain def; `McpCapabilityProvider.
  list_groups` (mcp_provider.py:66) loops specialists synchronously
  calling `SpecialistInterop.discover_catalog` (specialist_interop.py
  :149) → `port.list_remote_tools` (adapter.py:103) →
  `DelpiMcpTransport` over `requests`/urllib3 with a custom
  deadline_transport (per-recv inactivity bounds). `asyncio.gather`
  is NOT applicable — the only compatible fan-out is a bounded
  thread executor (concurrent.futures).

REAL_COST_SEAM: |
  PROVEN — `_groups` iterates providers, but in practice there is ONE
  mcp provider; the ~15.2s lives INSIDE `McpCapabilityProvider.
  list_groups` looping N specialists (each: delegated exchange +
  MCP initialize + tools/list, ~5s). Provider-level fan-out alone
  gains ~0. The parallel seam is per-specialist inside the provider.

TOKEN_EXCHANGE_SAFETY: |
  PROVEN-SAFE-MECHANISM — `InMemoryDelegatedTokenCache`
  (delegation.py:120) guards get/put/invalidate with
  `threading.Lock`; keys are (subject_fingerprint, resource_audience)
  so per-specialist exchanges never collide. Benign race only: two
  threads could exchange for the SAME audience concurrently → both
  tokens valid, last write wins.

  MATERIAL-BLOCKER-FOUND — `credential_for` resolves the subject
  bearer via `current_subject_bearer()` (root_composer.py:389), which
  reads `contextvars.ContextVar` + `flask.g` (auth/subject_bearer.py).
  Worker threads see NONE — a naive ThreadPoolExecutor.submit would
  make EVERY parallel discovery fail `MCP_AUTHENTICATION_FAILED`.
  Existing precedent seam: `bind_subject_bearer`/`unbind_subject_bearer`
  (created for the NDJSON worker transport) — any parallel design
  MUST capture the bearer on the caller thread and bind/unbind per
  task (or pre-resolve credentials caller-side), never copy_context
  casually (bearer lifetime must stay bounded).

CLIENT_CONCURRENCY_SAFETY: |
  PROVEN-SAFE — `transport_factory` builds a NEW DelpiMcpTransport
  per connect (adapter.py:90-97); no shared Session/pool between
  specialists. `requests`/urllib3 is thread-safe when each task owns
  its transport. `_invalidate_on_auth_failure` → cache invalidate is
  lock-guarded.

SHARED_STATE: |
  None mutable beyond the locked token cache. `list_groups` builds
  fresh `groups`/`failures` per call.

DEADLINE: |
  Shared TurnDeadline is a clock — each worker receives
  `deadline.remaining_seconds()` at dispatch; `remaining_budget`
  already clamps per-leg timeouts inside the provider loop. A hung
  call burns only its own share — but a leaked thread finishing a
  blocked recv is bounded only by its own transport deadline;
  executor shutdown must not wait indefinitely (wait=False or
  bounded join).

CANCELLATION: |
  Threads are not interruptible mid-recv — cancellation stays
  cooperative: check `_cancel_observed()` before dispatch and at
  join; in-flight calls finish on their own recv deadlines.
  `bind_subject_bearer` must be undone in finally per task so a
  cancelled worker never outlives its binding.

RETRY: |
  Existing single bounded transient retry lives in `_groups` — under
  per-specialist fan-out the retry policy belongs per task with the
  same remaining-budget condition (>15s), never widened.

PARTIAL_FAILURE: |
  Per-specialist exception → failures.append(code) — same contract;
  aggregation must preserve deterministic order (submission order,
  not completion order) so traces stay diffable.

ORDERING: |
  groups keyed `provider_id:group_id` — deterministic by key.
  Failures list MUST be emitted in specialist submission order, not
  completion order (new constraint vs sequential).

CLEANUP: |
  Transports are per-call — nothing pooled to close. Bound bearer
  tokens MUST be unbound in finally (leak = credential exposure to
  unrelated work on the pooled thread).

RESOURCE_LIMITS: |
  Fan-out width = len(specialist_ids) (small, settings-bounded);
  optional hard cap (e.g. 4) for future owner growth. Keycloak
  exchange concurrency: N parallel RFC 8693 exchanges — no documented
  limit found; N is small; risk LOW.

ROLLBACK: |
  Sequential path remains the default; parallel mode flag-gated so a
  revert is a config flip, not a code change.
```

## Gate decision matrix

| Aspect | Verdict | Evidence |
|---|---|---|
| list_groups sync/async | SYNC (blocking requests) | mcp_provider.py:66, adapter.py:103, transport.py:25 |
| Shared mutable state | Token cache only, lock-guarded | delegation.py:120-172 |
| HTTP client thread-safe | YES — per-call transport, no shared session | adapter.py:90-97 |
| Subject credential in worker | **NO — ContextVar/flask.g** | subject_bearer.py, delegation.py:215 |
| Existing binding seam for workers | YES — bind_subject_bearer (NDJSON precedent) | subject_bearer.py:35-50 |
| Timeout aborts in-flight call | Cooperative recv deadlines; per-call bound | deadline_transport.py |
| Failure of one affects others | No — isolated per specialist | mcp_provider.py:94-96 |
| Deterministic ordering | By dict key; failures need submission order | orchestrator.py:1626 |
| Cleanup on cancel | Bearer unbind in finally; transport per-call | subject_bearer.py:46-50 |

```yaml
RECOMMENDED_PATH: |
  Bounded ThreadPoolExecutor INSIDE `McpCapabilityProvider.list_groups`
  (per-specialist discover_catalog fan-out) — NOT asyncio (sync path),
  NOT provider-level (one mcp provider → no gain). Caller thread
  captures subject bearer once; each task binds/unbinds via the
  existing seam in try/finally. Submission-order aggregation;
  shared TurnDeadline; per-task transient retry under the same
  remaining-budget condition; flag-gated with sequential default.

  Alternative considered and weaker: pre-resolve all delegated
  credentials on the caller thread then fan out only tools/list —
  simpler (no binding seam needed in workers) but serializes the
  exchange portion (~40% of per-specialist cost) — still a valid
  first increment if coordination prefers minimal binding risk.

EXPECTED_LATENCY: |
  ~15.2s → ~max(specialist latencies) + merge ≈ 5–6s (TARGET, not
  PROVEN — real measurement required post-implementation).
RISKS: |
  - Credential binding bug → all-parallel auth failure (mitigation:
    seam exists + negative test)
  - Thread leak on hang (bounded by per-call recv deadline +
    wait=False join)
  - N concurrent Keycloak exchanges (small N, monitor)
  - Determinism drift in failures ordering (submission-order emit)

DECISION: READY_FOR_COORDINATION_AUTHORIZATION
  All blockers inventoried with code references; the design is
  bounded and preserves every governed invariant (deadline, cancel,
  partial failure, deterministic order, per-owner credentials,
  discovery≠approval). Implementation NOT authorized/executed —
  awaiting explicit coordination authorization.
```
