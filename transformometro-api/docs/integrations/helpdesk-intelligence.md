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

R4 introduces governed writes through the canonical PREPARE/ACT engine:
`prepare_helpdesk_change` seals an exact change and `commit_proposal` is
the sole ACT — see §20. No generic write surface exists.

## 10. Attachment boundary

Attachment inventory is always metadata first: `attachments[]`
(`document_id`, `filename`, `mime`) plus `attachment_refs` — the
deduplicated document universe including inline `<img>` refs in
description/timeline HTML (R4.2). Binary content is delivered on demand
via `helpdesk_read(action=attachment)` as MCP `ImageContent` /
`EmbeddedResource` blocks, and user files upload via governed
`upload_attachment` — see §22. (HISTORICAL: classified
`PLATFORM_BLOCKED` until R4.2 proved canonical transports.)

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
(`teo_agent_intelligence.json`) with `HELPDESK_DEMAND_GATE` and four
intents: `HELPDESK_DISCOVERY` (helpdesk_read only), `DEMAND_ANALYSIS`
(helpdesk_read → evidence reasoning → extra sources only if needed),
`DEMAND_TO_PROCESS` (helpdesk_read → record_read → get_process_context
→ methodology only if analytical work requires it → solution_read when
digital solution is considered), and `HELPDESK_WRITE` (helpdesk_read
current state → catalogs → `prepare_helpdesk_change` → policy gate →
`commit_proposal` → authoritative read-back → verify).

## 13. Roadmap

| Stage | Content | Status |
|---|---|---|
| R1 Integration Contract V1 | this document | ACCEPT |
| R2 Read Intelligence V1 | `helpdesk_read` + orchestration | ACCEPT / CLOSED — see §19 |
| R3 Demand Intelligence V1 | recurrence/discovery composition — zero new tools | ACCEPT / CLOSED — see §19 |
| R4 Governed Writes V1 | `prepare_helpdesk_change` + `commit_proposal`, idempotency bound to proposal, BFF revalidation, read-back | ACCEPT / CLOSED — see §20 |
| R4.1 Full Capability Coverage | 100% route ledger (37 routes, 0 unclassified) + governed ticket delete (GLPI trash) + governed session unlink | ACCEPT / CLOSED — see §21 |
| R4.2 Full Ticket Context & Binary Attachments | `action=attachment` (ImageContent/EmbeddedResource) + governed `upload_attachment` via `openai/fileParams` + `attachment_refs` dedup | ACCEPT / CLOSED — see §22–23 (live upload/vision proven; C1+C2 host corrective closed) |
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
| `tickets`/`ticket` with linked session | HISTORICAL — was `PENDING_MANUAL_GLPI_LINK` on the local env at `8686552a1e` (0 oauth_sessions locally, `GLPI_OAUTH_CLIENT_*` unset). **Superseded by §19**: linked session + real ticket list/detail accepted live |
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

## 18. R3 — Demand Intelligence V1

Objective: TÉO uses real tickets as demand evidence — recurrence, themes,
candidate processes, solution reuse, governed recommendation — with zero new
tools, zero persistence, zero ticket mirror.

Contract (orchestration only — `teo_agent_intelligence.json`
`2026.10.09.4 → .5`):

- `sources.helpdesk_demand.analysis`: explicit analysis window; bounded
  pagination (never "no recurrence" after one page); summaries-first
  minimization (detail/timeline only for validated subset; attachments out);
  status scope follows intent (pending vs recurring, active vs historical);
  aggregate privacy (counts/themes over names).
- `sources.helpdesk_demand.epistemic`: frequency/distribution = CALCULATED;
  candidate process/solution = INFERRED; improvement idea = PROPOSED.
- `routing.DEMAND_ANALYSIS.analysis`: 12-field conversational output model
  (theme → evidence → frequency → window → actors → symptoms → reported
  causes → candidate process → existing solution → gaps → recommendation →
  confidence); grouping signals enumerated, cluster stays INFERRED; counts
  must be calculated; root cause never promoted from ticket text (method only
  on explicit request); explicit stop after answering.
- `routing.DEMAND_TO_PROCESS.confidence`: ticket→process association marked
  INFERRED with alta|média|baixa; record_read(search) before
  get_process_context; never infer process IDs.
- `DIGITAL_SOLUTION_NEED.fit`: added `NO_DIGITAL_SOLUTION_NEEDED`, `UNKNOWN`.
- `sufficiency`: added demand stop line.

`analyze` decision (Abstraction Gate): the capability is the Transformômetro
dashboard/snapshot engine — its contract does not cover ticket-text grouping.
Conversational reasoning over `helpdesk_read` summaries/details is the
smallest sufficient path; no call required, no contract change.

Boundaries kept: no new MCP tool (22), no new GPT Action (20), no OpenAPI
change, no ticket cache/mirror/table, no embeddings/vector/ML clustering, no
ticket→process link, no writes (R4/R5/R6 untouched). OAuth user ACL remains
the Helpdesk universe boundary; legacy search remains ids-only discovery.

Tests: `test_teo_knowledge_orchestration.py` +6 (bounded analysis contract,
output model + epistemic non-promotion, process-discovery ordering,
fit classes, sufficiency stop, zero new tools) — 19/19 suite green.

## 19. Final acceptance & closeout — R2 CLOSED / R3 CLOSED (2026-10-08)

Recorded after both assignee-filter correctives (§16, §17) and the R3
directive contract (§18). Evidence below is point-in-time runtime evidence,
not permanent fixtures.

### R2 — final live evidence (supersedes §14 residual)

| Gate | Result |
|---|---|
| GLPI linked session | PASS |
| Real ticket list (`helpdesk_read` tickets) | PASS |
| Ticket detail | PASS |
| list → detail chaining | PASS |
| timeline | PASS |
| dynamic `can_*` flags | PASS |
| Recursive privacy scan | PASS |
| ChatGPT MCP discovery | PASS (22 tools) |
| Assignee resolution (`catalog users purpose=assignee` → Robério Oliveira, GLPI id 11) | PASS |
| Assignee filter (`assignee_id=<resolved>`, `updated_at:desc`) | PASS — 15 tickets returned after §16+§17 fixes |
| TÉO "quais os últimos chamados do helpdesk direcionados a mim?" | PASS — get_my_context → catalog assignee resolution → filtered `helpdesk_read`; returned tickets carried `assigned_user_id=11` / `assigned_display_name=Robério Oliveira` (e.g. #1204, #1222, #1153, #1156, #1128 — point-in-time ids) |
| **R2 final status** | **ACCEPT / CLOSED** |

### R3 — live acceptance (authenticated TÉO session)

Dataset: the 15 tickets assigned to the authenticated user at acceptance
time (`helpdesk_read tickets assignee_id=<resolved> page_size=50` →
count=15, `has_more=false`). Explicit bounded window.

- **Scenario A — recurrence** "Quais dos meus últimos chamados parecem
  recorrentes ou relacionados?": 15 tickets analyzed; strong
  Painéis/Indicadores theme (TV Dashboard/gráfico/indicador/dashboard),
  e.g. #1204 Correção Painel de TV, #1222 Dados Do Grafico TV no GR.
  Grouping stayed INFERRED, counts CALCULATED, no causal claim, no
  process/solution call → **PASS**
- **Scenario B — process candidate** "relacionados a algum processo do
  Transformômetro?": `record_read` search found no direct process for
  "TV Dashboard"/"Painel de TV"; candidate found for "Gerenciamento de
  Rotina" → PROC-0067 (collecting/consolidating/monitoring routine
  indicators via structured information and dashboards). Association
  ticket→process stays INFERRED; process identity/content = authoritative
  Transformômetro truth. NOT claimed: all 15 belong to PROC-0067 → **PASS**
- **Scenario C — digital solution** "já existe solução digital na DELPI?":
  `solution_read` → `tv-dashboard` "Painéis TV" (active). Fit for the
  dashboard subset: REUSE_EXISTING / EXTEND_EXISTING before any new
  capability. Solution metadata = knowledge, not authorization → **PASS**
- **Scenario D — root cause** "esses chamados comprovam a causa raiz?": NO —
  symptoms/reports are INFORMED, similarity INFERRED, frequency CALCULATED,
  root cause UNKNOWN until validated; no automatic method call → **PASS**
- **Scenario E — improvement opportunity**: recurring dashboard/indicator
  demand = valid investigation candidate; no invented impact/redesign;
  candidate improvement != registered improvement → **PASS**
- **Methodology**: no `get_methodology_guide` call needed across A–E —
  smallest-sufficient-truth-set validated.
- **Tool surface**: MCP 22→22, GPT 20→20, zero new operations.
- **Persistence**: none — computed/conversational intelligence only.

**R3 final status: ACCEPT / CLOSED.**

### Boundaries preserved

R3 closeout does NOT authorize Helpdesk writes (follow-up, assignment,
task, solution, approval, validation, satisfaction stay in R4 — PLANNED).
R5 (persistent ticket↔process metadata) stays TO_INVENTORY; R6 (backlog
aggregation) stays TARGET — no implementation performed for either.

## 20. R4 — Governed Helpdesk Writes V1

Status: **ACCEPT / CLOSED** — live governed writes proven in §22.2
(`set_assignee` on #1299, `upload_attachment` + `delete_ticket` on #1300:
PREPARE → policy → commit_proposal → BFF → GLPI → authoritative
read-back → verify).

### Architecture

```text
TÉO
→ prepare_helpdesk_change   (closed action enum; PREPARE never writes)
→ GovernedWriteOrchestrator (canonical proposal engine — unchanged)
→ commit_proposal           (sole ACT choke point — unchanged)
→ HelpdeskWritePort         (application contract)
→ HelpdeskBffGateway        (same-user Bearer forward; BFF owns OAuth,
                             idempotency and the GLPI side effect)
→ GET /tickets/{id}         (authoritative read-back)
→ verify expected postcondition
```

`PREPARE != ACT` · `request != authorization` · `confirmation !=
authorization` · `2xx != business outcome`.

### Write capability matrix

| Operation | BFF route | can_* | Idempotent | Read-back | Policy | R4 V1 |
|---|---|---|---|---|---|---|
| create_ticket | `POST /tickets` | — (can_assign if assignee) | `Idempotency-Key` | `GET /tickets/{id}` | AUTO_ACT | IMPLEMENT |
| set_assignee | `PUT /tickets/{id}/assignee` | can_assign | yes | `assigned_user_id` | CONFIRM_BEFORE_ACT | IMPLEMENT |
| add_followup | `POST /tickets/{id}/followups` | can_followup | yes | timeline id+kind | AUTO_ACT | IMPLEMENT |
| create_task | `POST /tickets/{id}/tasks` | can_create_task | yes | timeline id+kind | AUTO_ACT | IMPLEMENT |
| add_solution | `POST /tickets/{id}/solutions` | can_create_solution | yes | timeline id+kind | CONFIRM_BEFORE_ACT | IMPLEMENT |
| request_validation | `POST /tickets/{id}/validations` | can_request_approval | yes | validations[].id | CONFIRM_BEFORE_ACT | IMPLEMENT |
| accept_solution | `POST /tickets/{id}/solution/accept` | can_accept_solution | yes | status_id | CONFIRM_BEFORE_ACT | IMPLEMENT |
| reject_solution | `POST /tickets/{id}/solution/reject` | can_reject_solution | yes | status_id | CONFIRM_BEFORE_ACT | IMPLEMENT |
| submit_satisfaction | `PUT /tickets/{id}/satisfaction` | can_submit_satisfaction | yes | satisfaction | CONFIRM_BEFORE_ACT | IMPLEMENT |
| accept_validation | `POST /tickets/{id}/validations/{vid}/accept` | can_decide_validation + mine_to_decide | yes | validations[].status | CONFIRM_BEFORE_ACT | IMPLEMENT |
| reject_validation | `POST /tickets/{id}/validations/{vid}/reject` | can_decide_validation + mine_to_decide | yes | validations[].status | CONFIRM_BEFORE_ACT | IMPLEMENT |
| attachments | `POST /tickets/{id}/attachments` | — | multipart | — | — | OUT_OF_SCOPE_V1 (binary transport not exposed to TÉO) |

All ticket-scoped operations require `ticket_id`; PREPARE reads the
current ticket through the BFF first (`current_state_read`) and seals a
relevant-field fingerprint (`ticket_id`, `status_id`,
`assigned_user_id`, `updated_at`, + target validation state when
deciding). `can_*` flags are early UX/validation guidance only — the BFF
revalidates on commit; `can_*` false makes the proposal `ready=false`,
never widens authority.

### Idempotency

ACT sends `Idempotency-Key: teo-<proposal_id>` — proposal-bound,
deterministic. Same proposal + retry reaches the BFF under the same key;
the BFF's canonical idempotency store dedupes the business effect. The
key never appears in the public proposal payload or logs. BFF caveat:
its store dedupes by (subject, operation, key) without payload-hash
conflict detection — recorded as owner-side behavior, not widened here.

### Read-back / postconditions

- `create_ticket`: `GET /tickets/{returned_id}` must exist — 2xx without
  read-back is not success.
- `set_assignee`: `ticket.assigned_user_id == target`.
- `add_followup`/`create_task`/`add_solution`: returned entry id present
  in authoritative `timeline[]` with matching `kind`.
- `request_validation`: returned id present in `validations[]`.
- `accept/reject_solution`: `ticket.status_id` equals the BFF-returned
  post-decision status.
- `submit_satisfaction`: `ticket.satisfaction == submitted score`.
- `accept/reject_validation`: `validations[].status == 3|4` as returned.

Any read-back mismatch raises `OUTCOME_VERIFICATION_FAILED` — the
outcome is never reported as done on 2xx alone.

### Security / AuthZ

Same-user Bearer is forwarded unchanged end-to-end (MCP rebuilds the
request with `context.authorization`; GPT Actions pass the HTTP header).
No service account, no technical GLPI credentials from the
Transformômetro side, no direct GLPI client, no ticket mirror/cache, no
duplicate RBAC. The BFF-internal legacy GLPI paths (solution decision,
satisfaction) remain BFF-owned exceptions — TÉO only ever sees the BFF
contract.

### Tool surface

MCP 22 → 23 (`prepare_helpdesk_change`); GPT 20 → 21
(`gpt_prepare_helpdesk_change`); `commit_proposal` stays the single ACT.
Registry-derived parity; `HELPDESK_WRITE` added to
`teo_agent_intelligence.json` (`2026.10.09.6`).

### Evidence

- `tests/test_teo_helpdesk_write.py` — 30 tests: PREPARE never writes,
  closed action enum, can_* guidance, policy classification
  (AUTO_ACT/CONFIRM_BEFORE_ACT), confirmation gate, proposal-bound
  idempotency key, consumed-proposal rejection, stale-state blocking,
  per-operation read-back verification, `OUTCOME_VERIFICATION_FAILED`
  on 2xx/read-back mismatch, typed `glpi_link_required` propagation,
  multi-action chain on authoritative returned id.
- Surface/parity/orchestration pins updated: MCP 23, GPT 21.

### Live acceptance gate — SUPERSEDED by §22.2

HISTORICAL: at R4 time the dev env had no linked GLPI session and no
`GLPI_OAUTH_CLIENT_*`, so live write acceptance was pending. The linked
session now exists and live governed writes passed (§22.2:
assignment/upload/delete with read-back and consumed-proposal
idempotency).

## 21. R4.1 — Full Helpdesk Capability Coverage

Complete route inventory + governed ticket deletion + governed session
unlink. Route coverage != route proxy: every BFF route is classified,
agent-facing business routes map to the bounded semantic surface
(`helpdesk_read` / `prepare_helpdesk_change` → `commit_proposal`), and
nothing else is exposed. **UNCLASSIFIED ROUTES = 0** — enforced by
`tests/test_helpdesk_route_coverage.py` (AST scan of the BFF route
decorators vs the ledger; drift fails CI).

### 21.1 Delete contract (GLPI-verified)

- **GLPI endpoint**: `DELETE /api.php/v2.2/Assistance/Ticket/{id}` —
  HLAPI v2.2 (`HttpxGlpiClient.delete_ticket`).
- **Semantics**: soft delete — the ticket is moved to the GLPI trash
  (`is_deleted=1`). `?force=true` (permanent purge) exists in GLPI as a
  distinct operation and is **never sent** — purge stays out of scope.
- **Restore**: possible inside GLPI (trash bin), outside TÉO scope.
- **Authorization**: same-user OAuth Bearer end-to-end; GLPI enforces
  `Ticket::canDelete()` on the user profile — 403 fails closed. No
  `can_delete` flag is projected because GLPI does not expose a reliable
  per-item flag on this contract; authorization is validated on the
  write path itself.
- **BFF route**: `DELETE /tickets/{ticket_id}` +
  `Idempotency-Key` header → `{"id","title","deleted","delete_semantics":"trash"}`.
- **BFF idempotency**: `delete_ticket:{ticket_id}` keyed on
  (subject, operation, key) — same-proposal retry replays the stored
  response, no second GLPI effect. An initial `not_found` is never
  masked as a successful retry.
- **Read-back (two layers)**: the BFF re-reads the ticket after the
  write and fails with `glpi_unavailable` if it is still readable; TÉO
  then re-reads through `helpdesk_read(action=ticket)` — canonical
  `not_found` (GLPI 404 or `is_deleted` payload) is the verified
  postcondition. A 2xx with the ticket still active →
  `OUTCOME_VERIFICATION_FAILED`.
- **PREPARE display**: the proposal carries `confirmation_requirement.
  display` = `{ticket_id, title, status, assigned_display_name,
  delete_semantics:"trash"}` — exact ticket shown, never a vague ask.
- **Stale state**: the standard fingerprint re-read blocks ACT when the
  ticket drifted or was deleted between PREPARE and commit.

### 21.2 Session unlink contract

- `prepare_helpdesk_change(action=unlink_glpi_session)` →
  `DELETE /auth/glpi/session` (naturally idempotent at the BFF) →
  read-back `helpdesk_read(action=session)` must show `linked=false`,
  else `OUTCOME_VERIFICATION_FAILED`. Relink remains `BROWSER_FLOW`
  (OAuth start/callback never agent-facing).

### 21.3 Route coverage ledger (37 routes)

| HTTP | Route | Classification | TÉO mapping |
|---|---|---|---|
| GET | `/auth/glpi/start` | BROWSER_FLOW | authorize_url guidance only |
| GET | `/auth/glpi/callback` | BROWSER_FLOW | never agent ACT |
| GET | `/auth/glpi/session` | EXPOSED_READ | `helpdesk_read(action=session)` |
| DELETE | `/auth/glpi/session` | EXPOSED_WRITE | `unlink_glpi_session` |
| GET | `/ticket-categories` | EXPOSED_READ | `catalog=categories` |
| GET | `/request-types` | EXPOSED_READ | `catalog=request_types` |
| GET | `/followup-templates` | EXPOSED_READ | `catalog=followup_templates` |
| GET | `/solution-types` | EXPOSED_READ | `catalog=solution_types` |
| GET | `/solution-templates` | EXPOSED_READ | `catalog=solution_templates` |
| GET | `/task-categories` | EXPOSED_READ | `catalog=task_categories` |
| GET | `/task-templates` | EXPOSED_READ | `catalog=task_templates` |
| GET | `/task-statuses` | EXPOSED_READ | `catalog=task_statuses` |
| GET | `/groups` | EXPOSED_READ | `catalog=groups` |
| GET | `/validation-templates` | EXPOSED_READ | `catalog=validation_templates` |
| GET | `/approval-steps` | EXPOSED_READ | `catalog=approval_steps` |
| GET | `/urgencies` | EXPOSED_READ | `catalog=urgencies` |
| GET | `/users` | EXPOSED_READ | `catalog=users` |
| GET | `/session/capabilities` | EXPOSED_READ | `helpdesk_read(action=capabilities)` |
| GET | `/tickets` | EXPOSED_READ | `helpdesk_read(action=tickets)` |
| GET | `/tickets/{ticket_id}` | EXPOSED_READ | `helpdesk_read(action=ticket)` |
| GET | `/tickets/{id}/attachments/{doc}` | EXPOSED_READ_BINARY | `helpdesk_read(action=attachment)` — MCP `ImageContent`/`EmbeddedResource` (R4.2) |
| POST | `/tickets/{id}/attachments` | EXPOSED_WRITE | `upload_attachment` via `prepare_helpdesk_change` → `commit_proposal` (R4.2) |
| POST | `/tickets` | EXPOSED_WRITE | `create_ticket` |
| PUT | `/tickets/{id}/assignee` | EXPOSED_WRITE | `set_assignee` |
| POST | `/tickets/{id}/followups` | EXPOSED_WRITE | `add_followup` |
| POST | `/tickets/{id}/solutions` | EXPOSED_WRITE | `add_solution` |
| POST | `/tickets/{id}/tasks` | EXPOSED_WRITE | `create_task` |
| POST | `/tickets/{id}/validations` | EXPOSED_WRITE | `request_validation` |
| POST | `/tickets/{id}/solution/accept` | EXPOSED_WRITE | `accept_solution` |
| POST | `/tickets/{id}/solution/reject` | EXPOSED_WRITE | `reject_solution` |
| GET | `/tickets/{id}/satisfaction` | COVERED_BY_EXISTING_PROJECTION | `satisfaction`+`can_submit_satisfaction` on `action=ticket` |
| PUT | `/tickets/{id}/satisfaction` | EXPOSED_WRITE | `submit_satisfaction` |
| POST | `/tickets/{id}/validations/{vid}/accept` | EXPOSED_WRITE | `accept_validation` |
| POST | `/tickets/{id}/validations/{vid}/reject` | EXPOSED_WRITE | `reject_validation` |
| DELETE | `/tickets/{ticket_id}` | EXPOSED_WRITE | `delete_ticket` — GLPI trash |
| GET | `/person-profiles/{user_id}/photo` | UI_ONLY | avatar binary — Portal UI |
| GET | `/health` | INFRA_ONLY | observability probe |

Counts: EXPOSED_READ 16 · EXPOSED_WRITE 14 ·
COVERED_BY_EXISTING_PROJECTION 1 · BROWSER_FLOW 2 · UI_ONLY 1 ·
INFRA_ONLY 1 · EXPOSED_READ_BINARY 1 · **UNCLASSIFIED 0**. (R4.1 classified the two attachment rows PLATFORM_BLOCKED_BINARY; R4.2 reclassified them once canonical MCP/OpenAI transports were proven — see §22.)

### 21.4 Surface after R4.1

- `helpdesk_read` actions: `session | capabilities | tickets | ticket |
  catalog` — unchanged (all reads already covered).
- `prepare_helpdesk_change` actions: 11 → **13**
  (`+delete_ticket`, `+unlink_glpi_session`).
- `commit_proposal`: unchanged — sole ACT choke point.
- MCP tools: 23 (unchanged) · GPT operations: 21 (unchanged; the
  `GptHelpdeskChangeBody.action` enum expanded → **Builder reimport
  required**).
- Policy: `helpdesk.ticket.delete` +
  `helpdesk.glpi_session.unlink` = CONFIRM_BEFORE_ACT (canonical
  `confirmation_policy.py` only).

### 21.5 Evidence

- BFF: `tests/test_helpdesk_api.py` — delete success+read-back,
  idempotent replay, missing key, no-permission, not-found never masked,
  forbidden fail-closed, unlinked-session typed error, 2xx-without-
  read-back → `glpi_unavailable`.
- TM: `tests/test_teo_helpdesk_write.py` — 19 new tests covering
  PREPARE-never-writes, exact-ticket confirmation display, policy
  classes, confirmation gate, proposal-bound key, consumed-proposal,
  stale state, already-gone-at-commit, 2xx/still-active →
  `OUTCOME_VERIFICATION_FAILED`, typed `glpi_link_required`, unlink
  prepare/commit/verify/retry.
- `tests/test_helpdesk_route_coverage.py` — inventory parity (37),
  0 unclassified, no stale entries, no orphan business read/write.

### 21.6 Live acceptance gate — SUPERSEDED by §22.2

HISTORICAL blocker: same as §20 (no linked session in dev env). Governed
`delete_ticket` was subsequently executed live on the disposable
acceptance ticket #1300 — confirm_before_act → commit → GLPI trash →
authoritative read-back 404 `not_found` (§22.2). Live unlink acceptance
is intentionally not
run against the real session (user friction/re-auth, per spec §34).

## 22. R4.2 — Full Ticket Context & Binary Attachments V1

### Binary transport selected

- **Read (BFF → TÉO)**: canonical MCP 2.2.0 rich content blocks.
  `image/png|jpeg|webp|gif` → `ImageContent`; any other supported file →
  `EmbeddedResource` + `BlobResourceContents` (`helpdesk://tickets/{id}/
  attachments/{doc}` URI). Text + structured metadata always accompany the
  binary block — the client that cannot render binary still receives the
  full document contract. Inline cap: 8 MiB per attachment; larger files
  return `content_delivery=too_large` (metadata only). BFF hard limit for
  upload/download remains 20 MiB.
- **Write (ChatGPT → TÉO)**: canonical `_meta["openai/fileParams"]` —
  the host binds the user-uploaded file to the `file` tool argument as
  `{download_url, file_id, mime_type?, file_name?}`. The backend resolves
  the platform-authorized `download_url` through `OpenAIFileGateway`
  (HTTPS only, host allowlist `OPENAI_FILE_DOWNLOAD_HOSTS` default
  `files.oaiusercontent.com`, no redirects, ≤20 MiB streamed cap,
  no filesystem paths, no model-supplied URLs).
- **No base64-in-JSON**, no generic URL fetcher, no local path, no
  ticket/attachment mirror, no service account.

### Architecture

```text
READ:  TÉO helpdesk_read(action=attachment, ticket_id, document_id)
       → same-user Bearer → HelpdeskBffGateway.download_ticket_attachment
       → BFF GET /tickets/{t}/attachments/{d} (belongs-to-ticket + AuthZ)
       → bytes → ImageContent|EmbeddedResource + structured metadata
WRITE: user file → openai/fileParams {file_id, download_url}
       → prepare_helpdesk_change(action=upload_attachment) [AUTO_ACT]
       → commit_proposal → OpenAIFileGateway.fetch(guarded)
       → HelpdeskBffGateway.upload_ticket_document (multipart +
         proposal-bound Idempotency-Key)
       → BFF POST /tickets/{t}/attachments → GLPI
       → authoritative read-back: document_id ∈ attachment_refs/attachments
```

### Full-ticket contract

`GET /tickets/{id}` now also projects **`attachment_refs`**: the
deduplicated document universe = `attachments[]` ∪ inline `<img>` refs
extracted from `description_html` and every `timeline[].content_html`
(`extract_bff_attachment_refs`, same-ticket only). TÉO never misses an
inline screenshot and never double-fetches the same `document_id`.

All previously projected fields unchanged (identity, lifecycle,
classification, people, SLA, description(+html), can_* flags,
validations, satisfaction, full timeline).

### Policy

`upload_attachment` → **AUTO_ACT** (`confirmation_policy.py`), same
class as `add_followup`/`create_task`: user-supplied file, append-only,
per-ticket. Still requires PREPARE → `commit_proposal` (sole ACT choke
point) and read-back. 2xx without the returned `document_id` present in
the authoritative inventory → `OUTCOME_VERIFICATION_FAILED`. GLPI
timeline lag is tolerated via `attachment_refs`/`Document_Item`
ownership, never by skipping the check.

`delete_attachment`: **NOT_AVAILABLE** — the BFF exposes no attachment
delete route; not invented at GLPI (ledger stays accurate).

### GPT Actions vs MCP parity

- **MCP**: full parity — image/resource blocks deliver real bytes;
  `fileParams` `_meta` binds user uploads to `prepare_helpdesk_change`.
- **GPT Actions** (JSON-only): `action=attachment` returns
  `content_delivery=metadata_only` (never raw bytes in JSON);
  `upload_attachment` accepts the same `file` object contract — usable
  where the client supplies the authorized reference. OpenAPI enum/schema
  changed → **Builder reimport required**.

### Evidence

- BFF (`helpdesk-api/tests/test_helpdesk_api.py`): attachment download
  success/sibling/foreign-404/no-leak, timeline-lag download via
  `Document_Item`, `attachment_refs` dedup incl. inline `<img>` refs.
- TM read (`tests/test_teo_helpdesk_read.py`): attachment action
  validation, image → `ImageContent`, PDF → `EmbeddedResource`,
  too-large → metadata_only, cross-field rejection, wire serialization
  (`image`/`resource` blocks, `mimeType` wire alias).
- TM write (`tests/test_teo_helpdesk_write.py`): PREPARE-never-fetches,
  exact file in proposal display, AUTO_ACT commit + verify, proposal-
  bound idempotency key, consumed/stale proposal, fetch failure →
  typed error before any write, `file` field rejected on non-upload
  actions, read-back via `attachment_refs` on timeline lag.
- File gateway (`tests/test_openai_file_gateway.py`): non-HTTPS denied,
  non-allowlisted host denied (SSRF), redirect denied, oversized stream
  denied, filename sanitization, `file_id` echoed back.
- Route ledger (`tests/test_helpdesk_route_coverage.py`): 37 routes,
  0 unclassified, attachment rows reclassified.

### Live acceptance gate — SUPERSEDED by §22.2

HISTORICAL: at implementation time the dev env had no linked GLPI OAuth
session and ChatGPT `ImageContent` delivery was
PENDING_RUNTIME_ACCEPTANCE. All gates subsequently passed live —
see §22.2 (image read on #1299, real fileParams upload on #1300,
binary read-back, vision, idempotency, governed cleanup).

### 22.1 R4.2-C1 — fileParams download-host corrective

- **Failure**: live upload ACT failed `FILE_URL_NOT_ALLOWED` — ChatGPT
  delivered the signed file URL on
  `oaisdmntprbrazilsouth.blob.core.windows.net` while the gateway
  allowlist defaulted to `files.oaiusercontent.com` only.
- **Corrective (config-only)**: `OPENAI_FILE_DOWNLOAD_HOSTS` (pre-existing
  env, comma-separated exact/suffix hosts) now set to
  `files.oaiusercontent.com,oaisdmntprbrazilsouth.blob.core.windows.net`
  in `infra/.env` and documented in `.env.dev.example`/`.env.prod.example`.
  No code change — the allowlist mechanism was already correct.
- **Security preserved**: no `*.blob.core.windows.net` wildcard, no
  generic Azure trust. `evilcorp.blob.core.windows.net`, bare
  `blob.core.windows.net`, `example.com`, suffix-confusion
  (`attacker-oaisd…`) and subdomain tricks (`.attacker.example`) all
  remain denied (proven in `test_openai_file_gateway.py`, 14 tests).
  `file_id` is context, never networking AuthZ. Gateway logs hostname
  only — no signed URL/SAS query.
- **Deploy**: `delpi-transformometro-api` recreated only (env change);
  no BFF/Keycloak/Postgres restart.
- **Status**: ACCEPT / CLOSED — the retry passed live (§22.2).
- **Remaining**: GPT Builder OpenAPI reimport = PENDING_MANUAL
  (admin residual, does not invalidate MCP/runtime acceptance).

### 22.2 R4.2 — live acceptance evidence (point-in-time)

**Session/surface**: TÉO MCP 23 tools; Helpdesk session linked;
`helpdesk_read` includes `attachment`; `prepare_helpdesk_change`
includes `upload_attachment`.

**Image read (real ticket)** — #1299 `[Minha DELPI] Erro 500 ao carregar
Minhas Solicitações`, attachment `document_id=1344`
`image_paste5958027.png` (image/png):

- attachment metadata read: PASS
- binary/image content delivered to the model: PASS
- visual understanding: PASS — model described pixel-only evidence
  (Minha DELPI → Minhas solicitações screen, browser DevTools Network
  showing a request returning HTTP 500, "Internal server error" in the
  response detail).
- epistemic: HTTP 500 visible in screenshot = OBSERVED; root cause =
  UNKNOWN (not claimed).

**User file upload (disposable ticket)** — #1300 `[TÉO R4.2 ATTACHMENT
ACCEPTANCE] Teste de mídia binária`, initial `attachments=[]`,
`attachment_refs=[]`. User image bound via canonical `openai/fileParams`
(`image(20261008-215054).png`, image/png):

- PREPARE `upload_attachment`: PASS
- `commit_proposal` → `OpenAIFileGateway` (allowlisted signed URL) →
  BFF multipart → GLPI: PASS
- authoritative read-back: `document_id=1345` present on ticket,
  `postcondition.verified=true`: PASS
- USER FILE BINDING / GOVERNED UPLOAD / GLPI READ-BACK: PASS

**Binary read-back + vision**: `helpdesk_read(action=attachment,
ticket_id=1300, document_id=1345)` → `helpdesk_attachment_v1`,
`content_delivery=inline`, content blocks = text + image (image_count
1). Model received pixels and described pixel-only evidence ("Chamado
#1299 atribuído a Michael Marotto!", row "Imagem anexada — Pendente").

**Idempotency**: second `commit_proposal` on the same proposal →
`proposal_not_found` (consumed); ticket read-back showed exactly one
attachment `document_id=1345`. NO DUPLICATE BUSINESS EFFECT: PASS.

**Cleanup**: #1300 removed via governed `delete_ticket`
(confirm_before_act, explicit confirmation) → GLPI trash semantics,
read-back 404 `not_found`. Moved to GLPI trash / absent from active
view — not claimed as permanently purged. ACCEPTANCE CLEANUP: PASS.

**Fail-closed**: the pre-C1 attempt failed `FILE_URL_NOT_ALLOWED` and
left zero side effects (`attachments=[]` on read-back): PASS.

### 22.3 R4.2-C2 — production configuration evidence

WSL → SSH `operador@srv-api` → prod repo
`/home/operador/projetos/delpi-central`, runtime SHA `a91a053b96`.
Env source `infra/.env`; BEFORE: `OPENAI_FILE_DOWNLOAD_HOSTS` unset;
AFTER: `files.oaiusercontent.com,oaisdmntprbrazilsouth.blob.core.windows.net`.
Backup `.env.backup-20261009-102555`. Targeted recreate of
`delpi-transformometro-api` only (helpdesk-api/core/Keycloak/Postgres
untouched); container env verified; `_host_allowed()` policy verified
live; MCP surface 23 tools with `attachment`/`upload_attachment`.
Subsequent ChatGPT live upload succeeded (§22.2). Runtime evidence,
not source-code evidence. Status: ACCEPT / CLOSED.

## 23. R4.2 — final closeout

| Gate | Verdict |
|---|---|
| Full ticket context (description/timeline/validations/satisfaction/attachments+attachment_refs) | PASS |
| Attachment metadata | PASS |
| Attachment download (BFF → bytes → MCP blocks) | PASS |
| Image content delivery | PASS |
| Model vision (pixel-only evidence, #1299 + #1300) | PASS |
| User file binding (`openai/fileParams`) | PASS |
| Upload attachment (PREPARE → ACT → BFF → GLPI) | PASS |
| Authoritative read-back / no false success | PASS |
| Idempotency / no duplication | PASS |
| Fail-closed (`FILE_URL_NOT_ALLOWED` left no side effect) | PASS |
| Production fileParams host config (C1+C2) | PASS |
| Cleanup (governed delete → GLPI trash) | PASS |

**R4.2 = ACCEPT / CLOSED** (backend + MCP runtime).

**Builder parity residual**: the R4.2 OpenAPI change (`GptFileParam`,
`upload_attachment` enum) requires GPT Builder reimport —
**PENDING_MANUAL** (admin step; does not invalidate MCP acceptance).
