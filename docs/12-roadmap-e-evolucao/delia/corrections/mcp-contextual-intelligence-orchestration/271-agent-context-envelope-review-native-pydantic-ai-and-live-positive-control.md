# 271 — DÉLIA: revisão do envelope do Agent e próximo passo framework-first

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-G7-AGENT-CONTEXT-ENVELOPE-AND-AUTHORITATIVE-POSITIVE-CONTROL-REWORK-01`  
**REVIEWED_SHA:** `8cab181c7312f67c26cebbd4ea6ded20e042ca90`  
**BASE_SHA:** `cb49f714e529a2a5c127055ee5d869f646719a6d`  
**VERDICT:** `REWORK` for claim of **real Pydantic AI envelope**; `ACCEPT_WITH_RESIDUAL` for broader fail-closed heuristic and regression test; `INCONCLUSIVE` business positive control; `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## Verified GitHub source

- DÉLIA commit updates `pydantic_ai_investigation.py` +33/-4, `test_g1_native_structured_output.py` +32, doc256 +15; comparison from base includes unrelated kaizometro commit; do not attribute its files to DÉLIA.
- Pre-call estimate adds `json.dumps([{id,description,input_schema} for c in live_catalog])`, `json.dumps(InvestigationAnswer.__dict__,default=str)`, `ADAPTER_OVERHEAD_TOKENS=260` and `DEFAULT_GENERATION_RESERVE_TOKENS=512` from existing `context_budget`; rejects typed `investigation_context_overflow` before `Agent.run_sync` if estimate >= declared window.
- **Semantic mismatch:** `InvestigationAnswer.__dict__` is a Python class namespace serialization, not the native JSON schema that Pydantic AI sends to provider as `output_type=InvestigationAnswer`; the native output schema can include enum/literal fields and framing not faithfully represented by class namespace.
- **Tool mismatch:** the actual `FunctionToolset` registers both meta tools (`declare_investigation_goal`, `invoke_read_capability`, `compose_verified_observations`, `request_user_clarification`, etc.) and dynamically constructed owner tools using `toolset.add_function`, with generated names/descriptions/parameter schemas. The estimate of `live_catalog` does not equal serialized tool definitions submitted via Pydantic AI. It may over- or under-estimate.
- Existing `context_budget.py` constants are calibrated for the `InvokeModel` adapter, **not proven to match native Pydantic AI tool/output formatting**; preserve labeled heuristic status, do not claim exact provider tokens. Native SDK usage after calls is provider-specific and not automatically an exact pre-call count.
- New test `test_context_envelope_includes_tool_schemas_and_reserve` uses a tiny input and an artificial window `estimate_text_tokens('oi') + 1200`. It proves new addends affect rejection and zero physical calls, not that an actual 4096-window Ollama invocation avoids `4211 > 4096`, nor growth after one/multiple tools.
- User/executor reports two authenticated live turns including structured clarification and honest unbound; **neither preconfirms an existing owner record nor verifies a matched business answer**. `POSITIVE_CONTROL=INCONCLUSIVE`, RQ24/RQ28 remain PARTIAL. Stale baked runtime SHA reported, must not imply image and mounted code are identical.

## Architecture direction explicitly clarified after prior review

The user requires **framework-first** context/history: prioritize native Pydantic AI history processing, message history, usage metadata, model/request boundaries and registered tool schema; minimize/remove duplicate custom context management when a proven equivalent exists. Do not duplicate Core/domain business authorization or independently pronounce business data true; MCP interoperability is not final authority. Preserve contractual identity/Core permission and domain enforcement by legitimate API owners, while retaining the mechanical binding from actual tool outcome to claims/SourceRefs to avoid invented provenance. Preserve safe PREPARE/ACT and no uncontrolled writes. Before architecture/code modifications complete the canonical authority chain 16→50→17→49→51→52→21→20→25, ledger, docs256/270/271 and `EXISTING_EQUIVALENT`/`REUSE_DECISION`.

## Next task (bounded; avoid another estimator engine)

**TASK_ID:** `DELIA-C3-G7-PYDANTIC-AI-NATIVE-CONTEXT-HISTORY-AND-OWNER-POSITIVE-EVIDENCE-01`.

1. Reanchor current Git HEAD/status + canonical sources and existing docs. Verify installed Pydantic AI version/API and actual runtime/owner contracts. No speculative assumptions about native token counting/tool schema APIs.
2. Inventory only active Agent context construction: `_prior_context_block`, `_INVESTIGATION_INSTRUCTIONS`, runtime `Agent(...)`, `FunctionToolset` registration, `InvestigationAnswer`, prior history from Application, `context_budget.py` users, `UsageLimits`, telemetry path. For each mark native equivalent/ownership/consumer and decide KEEP/REUSE/EXTEND/SHRINK/REMOVE.
3. Replace **false-proxy** output schema class namespace and catalog approximation with framework-exposed **effective request schemas** or actual provider request instrumentation when APIs support it; record limitations if native preflight cannot know exact provider tokenization. Prefer native `message_history`, `history_processors`, usage and bounded result processing; do not create parallel tokenizer, token budget planner or memory runtime. Keep deterministic fail-closed mandatory-context capacity where required, with a typed error and clear estimate labels.
4. RED→GREEN tests against actual FunctionToolset registration and structured output, 4096-window boundary in authorized local model including tool result growth, physical request count, safe history pruning/continuity, mandatory instructions intact. Do not assert provider usage count equals estimates.
5. Separately obtain read-only positive owner control by directly confirming accessible existing record from authorized Domain owner before asking DÉLIA; compare answer to authoritative result and provenance. Without known record, record INCONCLUSIVE and concrete unblock, not a successful evaluation.
6. No production deploy, no ACT, no credentials in logs/docs. Full backend/architecture/security regressions, residual search, docs+ledger factual update, commit/push, report exact evaluated code SHA/model/config fingerprint and business outcome.

**STATUS:** Source review only. No tests independently run by reviewer.
