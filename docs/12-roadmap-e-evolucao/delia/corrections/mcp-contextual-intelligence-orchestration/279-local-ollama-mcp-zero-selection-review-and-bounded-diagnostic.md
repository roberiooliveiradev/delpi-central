# 279 — DÉLIA · Review local Ollama/MCP: três unbound e ausência de seleção empresarial

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-G7-LOCAL-OLLAMA-MCP-REAL-EVAL-AND-PRODUCTION-RELEASE-GATE-01`  
**BASE_HEAD REPORTED:** `0352099e4bef79b60baf0cc652a7370f3d18cb00`  
**FINAL_SHA:** `c852b386dd74c2a2f5c08785f6d82910d39656ef`  
**MOUNTED_RUNTIME_SHA REPORTED:** `b3da9b640c6735b15ceb1af061ecae06dce320cb`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` bounded local runtime bring-up and honest completion, `INCONCLUSIVE` tool selection/business outcome, `PRODUCTION_DEPLOY=BLOCKED`. Stale baked `DELIA_RUNTIME_SHA=c311e75e` is explicitly reported `EXECUTION_DRIFT`.

## Independent GitHub findings

- Final commit `c852b386...` is **documentation only**: appends 18 lines to doc256. The base-to-final comparison includes unrelated Kaizometro code, prior DÉLIA test work and doc278 from concurrent commits; do not attribute them to the final task.
- Executor reports local mounted runtime `b3da9b640c`, profile fingerprint `5ae38a6b007f9749`, local Qwen model `qwen3:4b-instruct-2507-q4_K_M`, configured MCP surface and auth; these runtime observations were not independently rerun by reviewer.
- The three authenticated READ questions (product 50220013, customer X average receivables, non-existent product 99999999) all resulted in **honest unbound / no compatible capability selected**. Latencies 29.0s, 1.2s, 1.5s. The non-existent entity negative control cannot serve as a positive business oracle. The ambiguous customer X scenario lacks a resolvable identifier and must not be treated as evidence of a broken owner.
- Three responses without false grounding show bounded honest fallback in these cases; they do not prove general `zero false grounding`, or correct semantic selection. `surface=configured` is not proof that the requested capability is in live catalog, visible to Agent, selected, arguments valid and actually invoked.
- Physical requests per turn and provider measured tokens not included as concrete measurements. The evaluator reported only bounded behavior. No tuning experiment was performed. The effective 4096 window is inferred from prior Ollama error, not newly verified from live provider request-level telemetry in this task.
- Positive business owner record not independently confirmed. Prior `/financial/rol*` 5s timeout with dev JWT does not prove owner data absent. Other owners' seed status has not been established by authoritative evidence.
- Production release correctly stopped; local Ollama profile is dev-only and egress guard reported as preventing production use. Do not deploy production until release gates, target topology, correct profile/provider and a positive authorized READ outcome verified, with actual human approval. Local PASS is not business acceptance. RQ24/RQ28 remain PARTIAL.

## Next bounded task: root-cause zero selection, not another architecture loop

**TASK_ID:** `DELIA-C3-G7-OLLAMA-MCP-CATALOG-SELECTION-AND-READ-OUTCOME-DIAGNOSTIC-01`

1. Reanchor current HEAD/status, Project Instructions/.cursor, canonical 16→50→17→49→51→52→21→20→25, technical/product specs, thematic contracts, ledger/docs256/276–279. Review effective mounted runtime SHA, Pydantic AI version/model/profile, catalog and deadlines.
2. **Instrument existing boundary, no new engine:** for product `50220013` query, capture (redacted) live capability catalog snapshot (IDs/semantic descriptions/owner/operation class/availability, no secrets); admission; Agent active tool registration, actual `FunctionToolset` definitions visible to model; request count; model output/status; tool choice and reason; schema/arguments; owner invocation if attempted; outcome and limitation codes. Identify *which* boundary failed: missing advertised capability, malformed catalog projection, inadequate semantic coverage, Agent chooses finalize/clarify, timeout/context, invalid arguments, owner AuthZ or missing data. Do not assume model selection is broken without a matching catalog item and authoritative owner capability. No provider-name branches in planner.
3. Run **positive technical selection control**: select one *existing, advertised and authorized* READ capability whose owner contract is confirmed; ask a plain question that uniquely matches its semantic description. Compare selection/execution against actual catalog and owner contract. If no suitable capability exists, report owner/catalog blocker, not LLM failure. Avoid synthetic provider evidence for business outcome.
4. Compare no more than 2–3 authorized context profiles (current 4096 and one capacity candidate, only if local resource limits allow); measure provider token usage through existing Ollama interfaces if possible, request counts, token estimation, latency, context rejection, tool chosen, grounded outcome, GPU/RAM; label unavailable measurement `NOT_MEASURED`. Avoid arbitrarily expanding window and local profile changes affecting production.
5. Characterize clarification versus unbound on ambiguous customer X prompt, and negative-control nonexistent product. Preserve fail-closed/provenance. Fix only proved bug with RED→GREEN, smallest diff, mandatory same-delivery removal of replaced legacy and consumer repair; otherwise no code churn.
6. Before any production action: local results and security/API authority reviewed, at least one known-present owner READ record and correct DÉLIA answer, release SHA/profile/env validated, rollback and explicit approval. If not, `PRODUCTION_DEPLOY=NOT_PERFORMED / BLOCKED`.
7. Full focused/backend regressions if code/config changed; docs/ledger facts, commit/push, preserve concurrent work. Report per-case disposition `CATALOG_PRESENT|ABSENT|INCONCLUSIVE`, `TOOL_SELECTED|NOT_SELECTED`, `OWNER_INVOKED|NOT_INVOKED`, `OUTCOME_GROUNDED|UNBOUND|CLARIFY`, measured/estimated tokens, effective config, blockers, SHA.

**Review status:** no new runtime code deficiency proven solely by three unbound responses; evaluation is insufficient to close positive business outcomes. Next step should diagnose the precise semantic selection boundary rather than broad refactors, and only then adjust context or model setup.
