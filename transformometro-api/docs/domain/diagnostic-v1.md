# Diagnostic V1 — domain capability & governance record

**Status:** PROVEN IN PRODUCTION (deployed SHA `721db1d469`)
**Date:** 2026-09-29
**Owner:** Transformômetro (domain + persistence + use cases)
**Surface:** TÉO MCP (`/apps/transformometro-api/mcp`) — MCP-only; no GPT Actions operations.

## Capability inventory

| Tool | Class | Canonical path |
|---|---|---|
| `get_diagnostic` | READ | `GetDiagnostic` use case → aggregate read projection + revision context + resolved evidence links + data-quality signals |
| `list_diagnostics_by_revision` | READ | `ListDiagnosticsByRevision` → canonical ordering, compact summaries, no evidence fan-out |
| `prepare_create_diagnostic` | PREPARE | `create_diagnostic` governed capability; server-generated `diagnostic_id` |
| `prepare_manage_diagnostic` | PREPARE | `manage_diagnostic` governed capability; closed enum of 13 actions |
| `commit_proposal` | ACT (shared, single) | opaque `proposal_handle` + explicit `confirmation` |

Manage actions (closed enum): `add_finding`, `add_hypothesis`, `add_causal_link`,
`add_evidence_link`, `add_conclusion`, `validate_hypothesis`, `reject_hypothesis`,
`supersede_hypothesis`, `mark_hypothesis_stale_evidence`,
`mark_hypothesis_revalidation_required`, `validate_conclusion`, `reject_conclusion`,
`supersede_conclusion`.

## Authority model

```text
Keycloak      = identity (OIDC)
Core /me      = effective permission authority (fresh load_user_rbac(force_refresh=True) on ACT)
Transformômetro = Diagnostic domain authority (DiagnosticWriteUseCase = only write path)
TÉO           = conversational consumer (capability <= authenticated user capability)
```

Never: TÉO owns Diagnostic state; TÉO has own RBAC; GPT confirmation grants permission.
End-user writes require `principal_type == "user"`; service principals are denied.
Canonical permission: `transformometro.access`. No local MCP RBAC.

## Write contract (governed flow)

```text
UNDERSTAND → READ CURRENT STATE → PREPARE EXACT CHANGE → VALIDATE
→ SHOW USER → EXPLICIT CONFIRMATION → COMMIT → FRESH AUTHZ
→ DOMAIN → SAVE → AUTHORITATIVE READ-BACK → VERIFY → REPORT
```

- PREPARE seals `exact_change`; ACT consumes only the sealed proposal handle.
- `commit_proposal` requires `confirmation` (schema-required, no default) — omitted
  confirmation never means confirmed; `confirmation=false` → `CONFIRMATION_REQUIRED`.
- Confirmation ≠ AuthZ: fresh Core authorization revalidates on every ACT.
- Read-back failure → `OUTCOME_VERIFICATION_FAILED`; never report success without it.
- Proposal handles are single-use and bound to actor + fingerprint.
- New entity ids (`diagnostic_id`, `finding_id`, `hypothesis_id`, `link_id`,
  `conclusion_id`) are server-generated at PREPARE; caller-supplied ids are rejected.
  Referenced ids (`revision_id`, `evidence_id`, lifecycle targets) are preserved
  byte-for-byte, never fabricated.

## Epistemic contract

| Element | epistemic_state | Note |
|---|---|---|
| Finding | OBSERVED / CALCULATED | direct observation or computed result |
| Hypothesis | INFERRED | stays INFERRED even when lifecycle=VALIDATED |
| Conclusion | INFERRED | never a fact |
| Root cause | designation | over a valid/current hypothesis, not a fact claim |
| Evidence | supports / contradicts | never converts inference into fact |

VALIDATED ≠ FACT. Do not let conversational summaries promote inference to truth.

## Fact classification (final SHA)

**PROVEN** — domain aggregate + invariants, PostgreSQL persistence (V050/V051),
canonical read use cases, governed writes via shared orchestrator, fresh Core AuthZ
on ACT, MCP 4-tool surface discovered at runtime (24 total), server-generated ids,
explicit confirmation backend (omitted → validation error; false →
CONFIRMATION_REQUIRED; true → persisted + verified read-back), single-use handles,
authoritative read-back in production.

**TEST_NOT_RUN** — TÉO conversational confirmation UX (no real ChatGPT driver in this
environment); runtime authz negatives (missing-permission user, service principal,
revocation between PREPARE and ACT — covered by code/integration tests only).

**ACCEPTED RESIDUAL** — proposal store is in-process; acceptable under the current
single-container, single-uvicorn-process topology. Multi-replica deployment requires
a shared proposal store or sticky/owned execution design — PLANNED, not implemented.
Proposals do not survive container restart (known characteristic, not a defect).

**TARGET / PLANNED** — DÉLIA adapter with user delegation; multi-replica proposal
store; GPT Actions Diagnostic surface (requires separate surface gate decision).
