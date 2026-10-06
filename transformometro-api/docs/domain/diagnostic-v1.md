# Diagnostic V1 — domain capability & governance record

**Status (per surface — runtime facts only):**
- Domain + Persistence + Application + TÉO MCP: PROVEN IN PRODUCTION
  (deployed SHA `230fbb9b6a`).
- Portal HTTP backend (`/transformometro/...`): PROVEN — runtime acceptance
  (Prompt 3/3) on the local dev stack at evaluated HEAD `63656e5741e321ad7b8abb21fe37c9992f45d1ff`;
  authenticated gateway/JWT smoke PASSED; governed PREPARE→COMMIT→read-back,
  realtime payload/fan-out, stale proposal and error contract all verified live.
  Production deployment of the Portal routes NOT PERFORMED.
- Final architecture verdict: **ACCEPT** (historical:
  ACCEPT_WITH_RESIDUAL — governance/infra/fixture residuals closed in the
  Master Residual Closure pass).
**Date:** 2026-09-29 (acceptance record atualizado no fechamento de resíduos)
**Owner:** Transformômetro (domain + persistence + use cases)
**Surfaces:** TÉO MCP (`/apps/transformometro-api/mcp`) and Portal HTTP
(`/transformometro/...`) — no GPT Actions operations.

## Capability inventory

| Tool | Class | Canonical path |
|---|---|---|
| `diagnostic_read` | READ | `action=get` → `GetDiagnostic` use case → aggregate read projection + revision context + resolved evidence links + data-quality signals; `action=by_revision` → `ListDiagnosticsByRevision` → canonical ordering, compact summaries, no evidence fan-out |
| `prepare_diagnostic_change` | PREPARE | `action=create` → `create_diagnostic` governed capability (server-generated `diagnostic_id`); manage actions → `manage_diagnostic` governed capability (closed enum of 13 actions) |
| `commit_proposal` | ACT (shared, single) | opaque `proposal_handle` + explicit `confirmation` |

> Tool Surface Rationalization V1: the pre-family tools (`get_diagnostic`,
> `list_diagnostics_by_revision`, `prepare_create_diagnostic`,
> `prepare_manage_diagnostic`) were consolidated into the two family tools
> above — same use cases, same closed action enum, tombstoned from
> `tools/list`.

Manage actions (closed enum): `add_finding`, `add_hypothesis`, `add_causal_link`,
`add_evidence_link`, `add_conclusion`, `validate_hypothesis`, `reject_hypothesis`,
`supersede_hypothesis`, `mark_hypothesis_stale_evidence`,
`mark_hypothesis_revalidation_required`, `validate_conclusion`, `reject_conclusion`,
`supersede_conclusion`.

## Portal HTTP surface (PROVEN — local runtime acceptance)

| Route | Kind | Canonical path |
|---|---|---|
| `GET /transformometro/revisions/{revision_id}/diagnostics` | READ | `ListDiagnosticsByRevision` use case → canonical ordering + revision context |
| `GET /transformometro/diagnostics/{diagnostic_id}` | READ | `GetDiagnostic` use case → aggregate read projection + resolved evidence links + data-quality signals |
| `POST /transformometro/revisions/{revision_id}/diagnostics/prepare` | PREPARE | `create_diagnostic` capability; server-generated `diagnostic_id`; provenance forced `USER` |
| `POST /transformometro/diagnostics/{diagnostic_id}/prepare` | PREPARE | `manage_diagnostic` capability; closed 13-action enum; server-generated entity ids (`finding_id`, `hypothesis_id`, `link_id`, `conclusion_id`); provenance forced `USER` |
| `POST /transformometro/governed-proposals/commit` | ACT (shared, single) | `GovernedActionsFacade.commit_proposal` — same proposal store, fingerprint, actor binding, stale detection, read-back verification as GPT/MCP |

- All routes require authenticated end-user (`principal_type == "user"`) +
  `transformometro.access` — `require_prepare_authz` runs at the route
  boundary; service principals are denied at PREPARE and again at fresh ACT
  AuthZ. Confirmation ≠ AuthZ.
- Realtime: exactly one `entity.updated` (`entityType=diagnostic`,
  `sectionKey=diagnostico`, payload `{"revision_id"}` only) emitted after
  WRITE + read-back + postcondition verification; fan-out `diagnostic:{id}` +
  `revisao:{revision_id}`. Never on PREPARE or failed/unverified ACT.
- Error contract: 401 unauthenticated · 403 denied/actor-mismatch/service
  principal · 404 not found · 409 stale/concurrency/outcome-verification ·
  422 validation/unsupported action/server-owned field/confirmation missing ·
  503 Core AuthZ unavailable.
- Shared transport projections live in
  `tm_app/interface/diagnostic_projection.py` (single source for HTTP and MCP).

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

**PROVEN (local dev stack — Prompt 3/3 runtime acceptance)** — Portal HTTP
Diagnostic surface end-to-end through gateway + real Keycloak JWT: 5 canonical
operations (2 reads, 2 governed prepares, shared commit), Portal-forced `USER`
provenance, server-generated ids (`server_owned_field` 422 verified live),
authoritative read-back, realtime invalidation post-verify (`entityType=diagnostic`,
`sectionKey=diagnostico`, payload `{"revision_id"}` only, fan-out
`diagnostic:{id}` + `revisao:{revision_id}`), stale proposal `409`, error
contract 401/403/404/409/422/503, MFE Portal UX (zero/one/multiple, deep links,
local-draft preservation, no auto-merge). Evaluated HEAD `63656e5741e321ad7b8abb21fe37c9992f45d1ff`.
No GPT Actions operations added; MCP unchanged (24 tools, Diagnostic MCP-native).

**NOT PERFORMED** — Portal HTTP **production** deployment: local runtime
acceptance only; no claim of production availability.

**TEST_NOT_RUN** — TÉO conversational confirmation UX (no real ChatGPT driver in this
environment); runtime authz negatives (missing-permission user, service principal,
revocation between PREPARE and ACT — covered by code/integration tests plus
live unauthenticated 401 probe).

**ACCEPTED RESIDUAL** — proposal store is in-process; acceptable under the current
single-container, single-uvicorn-process topology. Multi-replica deployment requires
a shared proposal store or sticky/owned execution design — PLANNED, not implemented.
Proposals do not survive container restart (known characteristic, not a defect).

**TARGET / PLANNED** — DÉLIA adapter with user delegation; multi-replica proposal
store; GPT Actions Diagnostic surface (requires separate surface gate decision).
