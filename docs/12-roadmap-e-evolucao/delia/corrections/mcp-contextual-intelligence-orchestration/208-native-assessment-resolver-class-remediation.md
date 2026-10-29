# 208 — Native Assessment Resolver-Class Remediation (Task 17, local rework)

Task: `DELIA-C3-LOCAL-ORCHESTRATION-NATIVE-ASSESSMENT-REWORK-01`
Base: `f2da73f121` (Task 16 consolidation) — HEAD at execution `2e1783f73e` (concurrent workstreams ahead, unrelated).
Environment: local WSL/Docker/Ollama `qwen3:4b-instruct-2507-q4_K_M`, LangGraph B1, authenticated MCP.
No production deploy. No production model calls.

## 1. Task 16 consolidation (Gate A)

Task 16 ended uncommitted. Its task-owned changes were inspected, verified against
owners, and committed as `f2da73f121` (already ancestor of main):

- orchestration instruction resource v26 to v27 (decision-rule-first restructuring),
- DAVI `discover_delpi_information` owner-description enrichment (api-delpi),
- TÉO `get_process_timeline` owner-description enrichment (transformometro-api),
- bearer-TTL refresh + scorecard scenarios in `local_orchestration_reliability_eval.py`,
- instruction snapshot/version pins (`test_r1`, `test_c3`, `test_projection_omission`),
- diagnostic scripts `local_stage_replay_eval.py`, `nat_probe.py`.

Controllership-finance/CLARA and other workstream files were left untouched
(several are staged by their own workstream — not part of this task).

## 2. Infrastructure integrity (Gate A)

- **Keycloak realm lost** on WSL crash, rebuilt via canonical bootstrap; the
  bootstrap realm-existence check is a latent defect (`admin_api` ignores the
  extra arg and compares the JSON body to `"404"`, so on a fresh volume the realm
  is never created). Realm created manually, then bootstrap re-ran. Dev user
  `rober` required email/firstName attributes under KC26 user profile.
- **Token exchange**: post-rebuild, exchanged tokens lacked `delpi-central` in
  `aud` (validator default `KEYCLOAK_AUDIENCE`). Fixed by adding a
  `delpi-central` audience mapper to the shared `audience-delpi` client scope
  attached to resource clients (DAVI/TÉO/VISTA exchanges validate again).
- **tv-dashboard-api crash-loop**: `ModuleNotFoundError: delpi_character_profiles`.
  The HEAD commit added `shared/delpi_character_profiles`, but the image's
  editable-install finder (generated at build time) did not map it, and
  `PYTHONPATH=/app` excludes `/shared`. Canonical fix = image rebuild +
  regenerated `delpi_auth.egg-info` manifests (tracked files, now truthful).
- **api-delpi V014 checksum**: verified stable this session — DB holds the new
  V014 checksum and file matches HEAD. No action; the earlier lesson stands
  (editing applied migrations breaks environments that applied the prior
  checksum — new logic belongs in a new migration).
- **WSL instability**: 4 crashes during this task (7GB RAM, ~32 containers).
  Mitigated by pruning to the essential eval stack (gateway, keycloak(+db),
  ollama, delia-api, api-delpi, transformometro-api, tv-dashboard-api, postgres
  x2) — classified as environmental, never model-semantic.
- **delpi-gateway is on the token path**: `_mint_bearer` goes through
  `delpi-gateway/auth/...` — it is essential, not prunable.

## 3. Native assessment causal diagnosis (Gate B)

Faithful probe (`nat_diag_probe*.py`) calling `_assess_native_path` with the real
`_TurnGoal`, real group surfaces, real instruction, warm model, x4 reps.

Fingerprint of the model input (v27): `b5cab3f017b4624b` blocks of 1.1 to 5.9KB —
payload verified complete (no truncation-driven loss; TÉO descriptions compress
to ~30 chars under the 6000-char budget but names/roles/required-args intact).

RED reproduction (v27, x4 each):

| case | selected cap | v27 verdict x4 |
|---|---|---|
| `vista_prepare` | vista.prepare_change | foreign x4 |
| `davi_discover` | davi.discover_delpi_information | foreign x4 |
| `teo_latest` | teo.record_read | foreign x4 |
| `teo_ctx` (explicit PROC-0105) | teo.get_process_context | mixed 3/4 foreign |

**Proven contract defect**: the decision rule's resolver scan enumerated only
"documentation, guide, catalog, context, methodology or knowledge READs". The
owners' actual designation resolvers are **DISCOVERY-class** capabilities
(`role: owner_vocabulary_discovery` — DAVI `discover_delpi_information`,
TÉO/VISTA `get_catalog`). A literal scan finds none of the listed nouns on those
surfaces, condition (3) appears satisfied, and `foreign_evidence_required` fires
systematically. Compounding factor: the rule sat at the *top* of the prompt
while the long exception clause recurred mid-text — this model family follows
recency-placed rules far better (same phenomenon as select_group in Task 16).

**Model-bound residuals** (unfixable at the contract boundary without keyword
routing — prohibited): `vista_prepare` and `teo_latest` anchor
`foreign_evidence_required` x4 under every variant (v28, v29, v30, v31, v32 —
six formulations incl. explicit governed-action and ordinal exclusions).
`teo_ctx` regressed on v32's mid-body rewrite; that variant was rejected.

## 4. Reuse gate

RESPONSIBILITY=native sufficiency adjudication
OWNER=OperationalCapabilityOrchestrator._assess_native_path
CANONICAL_SOURCE=delia.capability_orchestration.native_assessment (CRI resource)
CONSUMERS=LangGraph B1 governed owner path (shared with Engine A seam)
CONTRACT=4-status JSON (sufficient|foreign_evidence_required|corroboration_requested|inconclusive), fail-closed to inconclusive

EXISTING_EQUIVALENT=YES. REUSE_DECISION=REUSE (instruction resource only).
ABSTRACTION_GATE=PASS — no new port, planner, registry, or evidence engine; the
correction is contract text inside the existing governed instruction; the model
still decides the status semantically.

## 5. Minimal correction (v28)

Single-file, single-instruction change: `native_assessment` v27 to v28.

- DECISION RULE moved to the END of the instruction (recency placement).
- Resolver scan now names DISCOVERY-role capabilities
  (`owner_vocabulary_discovery`) alongside documentation/guide/catalog/context/
  methodology/knowledge READs.
- Explicit exclusions: governed create/modify/prepare actions (self-contained;
  missing user inputs resolved via clarification, never foreign evidence); the
  selected capability itself being the owner discovery/catalog read; owner-native
  ordering/listing/filtering (latest/most recent/all/count).
- Mid-body status bullets unchanged (v32's rewrite regressed teo_ctx, rejected).
- Status vocabulary, fail-closed interpretation, relevance_feedback handling,
  and all typed validation untouched. Entry size 3489 to 4122 bytes (within bound).

## 6. Probe verdicts (v28 formulation, x4)

| case | v27 | v28 |
|---|---|---|
| davi_discover | foreign x4 | sufficient x4 |
| teo_ctx | foreign 3/4 | sufficient x4 |
| vista_prepare | foreign x4 | foreign x4 (model-bound) |
| teo_latest | foreign x4 | foreign x4 (model-bound) |
| corroboration (control) | — | corroboration_requested x3 |
| cross-domain (control) | — | foreign x3 (legitimate) |
| teo product-subject (control) | — | sufficient x3 |

Legitimate foreign evidence (cross-owner entities) and corroboration remain
reachable — no regression in the legitimate path.

## 7. 22-scenario incident battery — paired same-session comparison

Real chain: LangGraph B1, authenticated MCP, local Qwen3 4B, repetition=1 each.
Same-session control matters: admission/group-selection stochasticity on this
model is large, so cross-session comparison vs the Task 16 scorecard
(13P/1Pa/8F, different infra state) is not honest evidence.

| Metric | v27 (control) | v28 |
|---|---|---|
| PASS / PARTIAL / FAIL | 8 / 0 / 14 | 10 / 0 / 12 |
| native_assessment fired | 12 | 14 |
| foreign_evidence_required | 7 (58%) | 4 (29%) |
| sufficient | 2 (17%) | 8 (57%) |
| inconclusive | 3 (25%) | 2 (14%) |
| model calls | 120 | 144 |
| input tokens | 188,628 | 231,389 |
| output tokens | 4,401 | 4,842 |
| fabrications | 0 | 0 |

Native-assessment decision quality measurably improved (foreign rate halved,
sufficiency tripled). Business Outcome improved modestly (10 vs 8) within the
same session — the remaining fails are upstream-stage stochasticity
(6x ADMISSION_ERROR, 2x GROUP_SELECTION_ERROR on v28; similar on v27) plus the
model-bound residuals. Token/call count rose because more turns now traverse
the *complete* native path (arguments→invoke→synthesis) instead of dying early
on foreign-selection validation — cost-for-correctness, not waste.

Notable v28-turn win: `d_catalog_exec` PASS (was FAIL). `b_pino` reached the
owner and returned records in both arms; its residual divergence is
evidence-relevance judgment, not assessment.

Remaining model-bound residuals (documented, not hidden): playlist PREPARE
(goal interpretation/false-refusal), latest-process (admission/timeline prior),
TÉO-named group selection, evidence-relevance flips, foreign-selection lures
(vista.get_playlist_history / search_data_routes — fail closed via live-surface
validation).

## 8. RED to GREEN tests

New `tests/test_native_assessment_resolver_contract.py` (6 tests, contract-level
pins — RED on v27, GREEN on v28):
- DISCOVERY-role is a designation resolver class;
- governed actions natively self-contained;
- selected resolver capability never triggers the exception;
- owner-native ordering is not a foreign problem;
- decision rule is the final block (recency);
- canonical 4-status vocabulary unchanged.

Updated pins: `test_r1` snapshot (native_assessment sha/bytes, version 28),
`test_c3` x2, `test_projection_omission` x1; loader `_ORCH_VERSIONS` += "28".

## 9. Regression

- Focused: r1 + native_assessment status-contract + resolver-contract + c3 +
  projection — all GREEN.
- Full `pytest tests/`: GREEN excluding pre-existing env-bound files
  (`test_cri_e2`, `test_g4` fixture, `test_presentation_v2*` — docs/plugins not
  mounted in container; classified in Task 16).
- No new ports, frameworks, dependencies. PREPARE/ACT separation untouched;
  security/token-exchange path unchanged (realm repair only); grounding and
  provenance preserved; zero fabrication observed in both battery arms.

## 10. Verdict

ACCEPTED as a bounded improvement at the proven contract defect:
`foreign_evidence_required` over-fire halved on the same-session paired battery;
the DAVI discovery→execute path (the original "terminal bala" motivation) now
reads `sufficient` x4 where v27 read `foreign` x4. Business Outcome not degraded
(10 vs 8 same-session). The two anchored cases (vista_prepare, teo_latest) are
classified model-bound after six instruction variants; pursuing them requires a
model-tier decision, not more contract text.

NEXT_BOUNDED_STEP: observe the same corpus under a stronger local model tier
(model-bound residual class) and/or promote the battery to >=3 repetitions when
WSL stability permits, to tighten the noise band around Business Outcome.

Evidence files: `docs/12-roadmap-e-evolucao/delia/evidence/local-reliability-v28-incident-208.log.txt`,
`local-reliability-v27-control-208.log.txt`, `local-reliability-v27-runs-208.json`.
