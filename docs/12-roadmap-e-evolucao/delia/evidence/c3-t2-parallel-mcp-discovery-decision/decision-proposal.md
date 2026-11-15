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
    (shared token cache/locks — NOT yet verified; the exchange internals
    may assume serialized access)
  - Keycloak exchange concurrency limits
RISKS: |
  - Provider exchange/token-cache internals may not be concurrency-safe
    (each provider object holds own session state — must verify no
    shared mutable cache between providers)
  - Concurrent tools/list bursts could trip owner-side rate limits
  - Deadline starvation: a slow provider still blocks gather to its own
    timeout (same as sequential tail, not worse)
RESIDUALS: |
  - Does not address model-loop latency (dominant cost)
  - Comprehension pass latency untouched

DECISION: ARCHITECTURE_DECISION_REQUIRED
  Justification: the change is small in code (EXTEND_EXISTING on
  _groups) but alters the execution model of a governed stage — thread
  safety of provider credential exchange is unproven, and the DÉLIA
  governance protocol requires explicit authorization before structural
  parallelism. Proposal ready for coordination review.
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
