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
| R4 Governed Writes V1 | `prepare_helpdesk_change` + `commit_proposal`, idempotency bound to proposal, BFF revalidation, read-back | IMPLEMENTED — see §20 (live GLPI-write acceptance pending user OAuth link) |
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

Status: **IMPLEMENTED** (contract + unit/integration evidence below; live
GLPI-write acceptance pending — see Live acceptance gate).

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

### Live acceptance gate

Pending: the dev Helpdesk BFF points at the production GLPI via OAuth
(`helpdesk.centraldelpi.com.br`) and the authenticated user currently has
no linked GLPI session (`linked: false` —
`glpi_link_required` + `authorize_url` propagated typed end-to-end, which
itself verified the live Bearer/error path). `GLPI_OAUTH_CLIENT_ID`/
`SECRET` are empty in the dev env, so the link must be completed
interactively once credentials are configured. The acceptance script
(`tmp-teo-write/r4_accept.py` flow: create → follow-up+retry → task →
confirm-before-act set_assignee) is ready to run the moment a session
exists.
