# TÉO × Helpdesk — Integration Contract V1

## 1. Purpose

Governed foundation for TÉO to read Helpdesk/GLPI information through
the existing Helpdesk BFF — knowledge only, never a second authority.

```text
User → ChatGPT / TÉO MCP → Transformômetro API
     → Helpdesk read port → Helpdesk BFF → GLPI
```

## 2. Owners

| Layer | Owns |
|---|---|
| GLPI | ticket truth, lifecycle, timeline, GLPI user-level access |
| Helpdesk BFF | GLPI OAuth sessions, validation, idempotency, error map, safe projections, can_* flags |
| Core | Keycloak identity, `helpdesk.access`, app registry, transversal RBAC |
| Transformômetro | process/improvement truth only — never stores ticket truth |
| TÉO | conversational orchestration — owns no Helpdesk permission, no GLPI credential |

## 3. Source of truth

`GET` on the BFF = current Helpdesk/GLPI truth as projected by the
owner. Missing ticket state is never supplemented from model memory.

## 4. Identity flow

```text
authenticated user Bearer
→ Transformômetro Helpdesk gateway (forward, unchanged)
→ Helpdesk BFF → require_actor() → helpdesk.access → subject
→ OAuthSession(subject) → GLPI
```

No service account simulates the user. TÉO never sees GLPI access_token,
refresh_token, client secret, App-Token, User-Token, profile-sync
credentials or encryption keys.

## 5. OAuth semantics

GLPI OAuth lives entirely inside the BFF (`/auth/glpi/start`,
`/auth/glpi/callback`, session keyed by user subject). Transformômetro
does not create a second OAuth flow.

## 6. Authorization flow

BFF `require_actor` enforces `helpdesk.access` per request; GLPI scope
is applied by the BFF per subject session. TÉO adds no local RBAC and
cannot widen what the user may see.

## 7. Safe read projection

The BFF already projects minimal fields (list: id, title, status,
category, urgency, timestamps, display names, SLA fields; detail adds
description, timeline, attachments metadata, `can_*` flags,
validations). The TÉO service passes the owner projection through with
an envelope (`schema`, `authority=helpdesk_bff_glpi`, epistemic note) —
no extra fields are synthesized.

## 8. Errors

BFF domain errors map into the canonical TÉO envelope — never 500:

| BFF status / code | TÉO `error_kind` |
|---|---|
| 401 | `authn` |
| 403 `forbidden` | `forbidden` |
| 404 `not_found` | `not_found` |
| 409 `glpi_link_required` (+`authorize_url`) | `conflict` — actionable link surfaced |
| 422 `validation_error` | `validation` |
| 502 `glpi_unavailable` | `upstream_unavailable` |
| 503 `glpi_feature_disabled` | `feature_disabled` |

Python exception types are never exposed.

## 9. Read/write boundary

V1 is read-only. Writes stay PREPARE/ACT candidates for R4 — no
`prepare_helpdesk_change` exists yet.

## 10. Attachment boundary

Attachments are metadata only (`document_id`, `filename`, `mime`).
Binary transport: `PLATFORM_BLOCKED` / out of scope.

## 11. Epistemic rules

- ticket existence/status/date → OBSERVED
- requester/technician text → INFORMED
- timeline → OBSERVED record of what was registered
- reported cause → INFORMED, never proven causal truth
- similarity/clustering → INFERRED/CALCULATED, never FACT
- ticket ≠ process truth ≠ validated root cause ≠ formal improvement
- tickets may initiate process discovery; they never silently become
  canonical AS-IS

## 12. Knowledge Orchestration role

`helpdesk_demand` is a live source in `knowledge_orchestration`
(`teo_agent_intelligence.json`) with `HELPDESK_DEMAND_GATE` and three
intents: `HELPDESK_DISCOVERY` (helpdesk_read only), `DEMAND_ANALYSIS`
(helpdesk_read → evidence reasoning → extra sources only if needed),
`DEMAND_TO_PROCESS` (helpdesk_read → record_read → get_process_context
→ methodology only if analytical work requires it → solution_read when
digital solution is considered).

## 13. Roadmap

| Stage | Content | Status |
|---|---|---|
| R1 Integration Contract V1 | this document | IMPLEMENTED |
| R2 Read Intelligence V1 | `helpdesk_read` + orchestration | IMPLEMENTED |
| R3 Demand Intelligence V1 | recurrence/discovery composition — zero new tools unless proven | PLANNED |
| R4 Governed Writes V1 | `prepare_helpdesk_change` + `commit_proposal`, idempotency bound to proposal, BFF revalidation, read-back | PLANNED |
| R5 Helpdesk ↔ TM Link | relationship metadata only (source_system=glpi), never ticket copy — Abstraction Gate first | TO_INVENTORY |
| R6 Backlog Intelligence | only if paginated reads prove inadequate; projection lives in the BFF, never a TÉO cache | TARGET |

Dependencies: R1→R2→R3; R2→R4; R2/R3→R5; R2+usage evidence→R6.

## 14. Acceptance model

Unit: port/gateway/service (Bearer forward, params, error map,
fail-closed validation, recursive forbidden-key scan). Behavioral:
orchestration routes Helpdesk intents to `helpdesk_read` only.
Runtime: session/capabilities/tickets/ticket/catalogs through the live
MCP + GPT surfaces; `glpi_link_required` and 403 handled typed.

### Final acceptance evidence — `8686552a1e` (2026-10-08)

| Gate | Result |
|---|---|
| MCP `tools/list` (live server) | **22** tools, `helpdesk_read` present, zero fragmented/per-route tools — PASS |
| GPT Actions OpenAPI (live served) | **20** ops, `gpt_helpdesk_read` present, `action` enum closed — PASS |
| Capability bindings | `helpdesk.{session,capabilities,ticket.search,ticket.read,catalog}.read` → one `helpdesk_read`/`gpt_helpdesk_read` — PASS |
| Same-user Bearer forward | `session` → 200 `linked:false` through BFF `require_actor` — PASS |
| `catalog(urgencies)` | 200, real GLPI projection — PASS |
| `glpi_link_required` | typed 409 + canonical `authorize_url` on MCP **and** GPT — PASS |
| Fail-closed validation | `TICKET_ID_REQUIRED`, `INVALID_CATALOG_KIND`, closed action enum (400/422) on both — PASS |
| Recursive secret scan | all live payloads clean (no token/secret/verifier keys) — PASS |
| Gateway logging | URL + error only; no Authorization/payload/ticket text — PASS |
| 403 `helpdesk.access` | TESTED_AUTOMATICALLY (unit suite) — no real user's permission mutated |
| `tickets`/`ticket` with linked session | **PENDING_MANUAL_GLPI_LINK** — `helpdesk.oauth_sessions` has 0 rows; `GLPI_OAUTH_CLIENT_*` unset locally; `/auth/glpi/start` returns 302 (canonical flow works) but completion needs human browser + configured GLPI OAuth client |
| Local edge route `/apps/helpdesk-api/*` | INFRA RESIDUAL — `gateway/nginx.dev.conf` lacks a location block (edge serves SPA); TÉO path is container-internal and proven |
| MCP auth contract suite | 13/13 PASS via project `.venv` (pytest-asyncio declared dep; container lacks it — environmental, not code) |
| `test_create_shared_resource_validation` | PRE_EXISTING — fails identically on clean pushed HEAD |

## 15. Security invariants

- `TÉO capability <= authenticated user capability`
- Bearer forward only — no service account, no impersonation
- bounded timeout, no token logging, no raw payload logging
- knowledge visibility ≠ access authorization
- no direct GLPI access, no Helpdesk DB access, no ticket cache

## 16. Assignee Filter Corrective V1 — evidence

Baseline defect (runtime, env with legacy search enabled): identity resolved
(Robério Oliveira, `inovacao@delpi.com.br`, GLPI assignable id 11); filtered
`tickets?assignee_id=11&sort=updated_at:desc` → `items=[]`; unfiltered listing
from the same GLPI returned tickets with `assigned_user_id=11` (e.g. #1204,
#1222, #1153, #1156, #1128). UNFILTERED TRUTH CONTAINS ASSIGNEE ∧ FILTERED
QUERY DOES NOT → defect proven, owner = Helpdesk BFF.

Root cause (PROVEN against GLPI 11 canonical source
`CommonITILObject::getSearchOptionsMain()` / `getSearchOptionsActors()`):
legacy Ticket search option `12` is `glpi_tickets.status` (Status); option `5`
is the assigned technician (`glpi_tickets_users` join, `type=ASSIGN`). The BFF
had the two ids swapped (`_FIELD_STATUS=5`, `_FIELD_ASSIGN=12`), so
`assignee_id=11` produced `criteria[field=12][equals][11]` = "status equals 11"
→ always empty.

Fix (smallest diff, owner-side only):
`helpdesk-api/helpdesk_app/infrastructure/glpi/legacy_ticket_search.py` —
`_FIELD_STATUS` default `5→12`, `_FIELD_ASSIGN` default `12→5`; env overrides
`GLPI_LEGACY_TICKET_SEARCH_{STATUS,ASSIGN}_FIELD` kept. Zero Transformômetro
code change; `assignee_id` public contract unchanged.

Security invariants preserved: legacy search only discovers ids; OAuth HLAPI
hydration remains the ACL gate (candidate id not readable by the subject is
dropped); fail-closed — legacy unavailable → typed `glpi_feature_disabled`,
never false empty; no service-account impersonation; no TÉO-side filtering.

Tests (venv, 146/146 BFF suite): canonical field ids (assign=5, status=12),
`equals` searchtype, `updated_at:desc` → sort 19 DESC, page/page_size+1
`has_more`, combined `assignee+status+q`, order preservation after hydration,
ACL drop of unreadable ids, `GlpiFeatureDisabled` when legacy off, empty
candidates → empty page without hydration. Transformômetro `test_teo_helpdesk_read`: 35/35.

Runtime after fix: deployed BFF emits
`criteria[0][field]=5[value=<id>] … sort=19 order=DESC`.
Live filtered-data re-verification runs in the env where
`GLPI_LEGACY_UPLOAD_ENABLED=true` (local dev keeps legacy off → typed
`glpi_feature_disabled`, correct). MCP 22→22; GPT Actions 20→20; no OpenAPI
change.

## 17. Assignee Filter — Runtime Convergence V1 (second defect)

Post-deploy live re-check (prod `srv-api`, 2026-10-08): with the canonical
field fix already running (`ASSIGN=5 STATUS=12` imported in-container),
`assignee_id=11` still returned `items=[]`.

Second root cause (PROVEN, live probe): GLPI `apirest.php/search/Ticket`
answers **HTTP 206 Partial Content** when the result set is paginated. The
BFF `_legacy_get_json` only accepted `200` and silently fell through to
`return []` — so real search rows were discarded. Raw probe (no BFF code):
`criteria[0][field]=5[equals][11]` → `206`, `totalcount=15`. Through
`_legacy_get_json` → `[]` (the `[]` responses observed earlier were 404/206
falls, not true empties; an actually-empty GLPI search returns 200 +
`totalcount:0`, no `data` key).

Fix: `_legacy_get_json` accepts `{200, 206}` — same owner, one-line scope,
covers every legacy paginated GET (search/Ticket, search/User, Profile_User
fallbacks). Test: `test_legacy_search_accepts_206_partial_content`.

Deploy: prod compose `infra` (`docker-compose.yml` +
`docker-compose.prod.cpu.yml`), repo `/home/operador/projetos/delpi-central`,
targeted `build` + `up -d --no-deps --force-recreate helpdesk-api` only.
Transformômetro targets internal `http://helpdesk-api:8000` (env unset →
default; `getent hosts helpdesk-api` resolves in-container).

Live after fix (prod container, `assignee_id=11`, `sort=updated_at:desc`,
page 1 size 10): `totalcount=15`, ids
`[1204, 1222, 1153, 1156, 1128, 969, 1042, 1046, 635, 660, 977]` — matches
the historical control set plus newer assignments; OAuth HLAPI hydration +
ACL unchanged downstream.
