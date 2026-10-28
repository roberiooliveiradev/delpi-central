# 191 — DÉLIA · Market Framework Reuse Fit Assessment

**Date:** 2026-10-28. **Task:** `DELIA-C3-MARKET-REUSE-FRAMEWORK-FIT-ASSESSMENT-01`. **Evaluated SHA:** `c0788d25ff` (main, post-H6). **Status:** RESEARCH_DONE; read-only; no code/dependency/production changes. Cross-reference: doc 189 (reuse-before-build register), doc 188 (WP0/WP1 baseline), doc 190 (H6 fix — CONFIRMED merged `c0788d25ff`).

## 1. Executive summary

DÉLIA's orchestrator is **not a generic agent loop** — it is a deterministic governed control plane that invokes the LLM at bounded, typed stages and keeps selection/validation/AuthZ/fail-closed in code. Every primary agent framework (Pydantic AI, LangGraph, mcp-agent, OpenAI Agents SDK) instead puts the model inside an autonomous tool-calling loop. Adopting any of them wholesale would create a second planner and parallel authority — the exact pattern the frozen decisions prohibit. **No agent framework earns an orchestrator-replacement POC.**

What the market can legitimately supply is **narrow infrastructure inside existing adapters**: the official MCP Python SDK under the `specialist_interop` transport boundary, and a structured-output validation/repair library (Instructor or Pydantic) inside the `model_invocation` adapter. Those two are the only POC-worthy reuse candidates; both are component swaps, not architecture changes.

## 2. Reanchor and environment inventory (verified at HEAD)

- HEAD = origin/main = `c0788d25ff`; phase C3 unchanged; H6 goal-projection **MERGED** (doc 190).
- **Python:** 3.12.16 (container). **Dep manager:** `requirements.txt` pins (no lockfile, no Poetry/uv).
- **delia-api deps (complete):** Flask 3.1.0, gunicorn 23.0.0, requests 2.34.2, urllib3 2.8.0, python-jose, cryptography, pytest 8.3.4.
- **Absent (verified `pip list`):** no pydantic, no openai SDK, no MCP SDK, no httpx, no tenacity, no langchain/langgraph, no async framework, no OTel.
- **Existing mechanisms:** custom streamable-HTTP MCP transport (`app/infrastructure/interoperability/mcp/transport.py` + `shared/delpi_mcp`), custom JSON-schema validation (`_validate_instance`), custom OpenAI-compatible adapter (`openai_compatible_adapter.py` over `requests`), `ModelCallLedger`, `TurnBudget`/`TurnDeadline`, `_TurnGoal`, `EvidenceFacts`, `GoalEvidenceJudgment`, `_fit_json_block` bounded projections, governed instruction resource v25.
- **Implication:** any framework adoption introduces a full dependency tree into a deliberately minimal, supply-chain-lean service — the cost side of every reuse decision is higher than typical.

## 3. Capability matrix

Legend: NATIVE / EXT (extension required) / NO / TV (to verify) / NA.

| Capability | Existing DÉLIA | Pydantic AI | LangGraph | mcp-agent | OpenAI Agents SDK |
|---|---|---|---|---|---|
| Semantic orchestration (staged, deterministic gates) | NATIVE (custom) | EXT — agent loop inverts control plane | EXT — graph could host stages but adds runtime | EXT — patterns are agent-loop based | EXT — Runner owns loop |
| Dynamic MCP discovery | NATIVE (tools/list, candidate flow) | NATIVE (MCPToolset/FastMCP) | EXT (via tool nodes) | NATIVE (core purpose) | NATIVE (MCP transports) |
| Provider-neutral invocation | NATIVE (openai_compatible port) | NATIVE (multi-provider) | EXT (langchain model layer) | EXT (per-provider LLM classes) | EXT (OpenAI-compatible/LiteLLM) |
| Structured tool calling | NATIVE (typed proposals) | NATIVE (validated outputs) | EXT | EXT | NATIVE |
| Typed output validation | NATIVE (custom `_validate_instance`) | NATIVE (Pydantic) | EXT | EXT | NATIVE (Pydantic) |
| Investigation state (intra-turn) | NATIVE (_TurnGoal/EvidenceFacts) | EXT (deps/run ctx) | NATIVE (StateGraph+checkpoints) | EXT (Temporal workflows) | EXT (sessions) |
| Evidence propagation | NATIVE (bounded projections) | EXT | EXT (state channels) | EXT | EXT |
| Context minimization | NATIVE (fit ladders, omission markers) | EXT (history processors) | EXT | TV | EXT |
| Recovery loops | NATIVE (_recover_relevance, bounded) | EXT | NATIVE (conditional edges) | NATIVE (evaluator-optimizer pattern) | EXT |
| Bounded retries | NATIVE (LLM_CALL_MAX_ATTEMPTS, budgets) | NATIVE (retries) | NATIVE (recursion_limit) | NATIVE | NATIVE |
| Parallel execution | NO (sequential by design) | NATIVE | NATIVE (super-steps) | NATIVE (ParallelLLM) | NATIVE |
| Timeout control | NATIVE (TurnDeadline/stage) | EXT | EXT | EXT | EXT |
| Token accounting | NATIVE (ModelCallLedger) | NATIVE (usage) | EXT (LangSmith) | EXT | NATIVE (tracing) |
| Tracing | NATIVE (ledger+logs) | EXT (Logfire, opt) | EXT (LangSmith, opt) | EXT | NATIVE (built-in) |
| Error handling | NATIVE (typed error vocabulary) | EXT | EXT | EXT | EXT |
| Testing | NATIVE (2415 tests, fakes) | NATIVE (TestModel) | EXT | EXT | EXT |
| Security boundaries (token opacity, fail-closed) | NATIVE (governed) | EXT | EXT | EXT | EXT |
| Operational complexity added | baseline | +async runtime +FastMCP | +langchain core +checkpoints | +app runtime (+Temporal for durable) | +async + sessions/tracing |
| Migration effort | — | HIGH (loop inversion) | HIGH | HIGH | HIGH |
| Maintenance burden | baseline (custom, owned) | MEDIUM | MEDIUM-HIGH | MEDIUM | MEDIUM |

## 4. Replacement/reuse analysis (per custom mechanism)

| Current mechanism | Market equivalent | Benefit | Cost | Risk | Decision |
|---|---|---|---|---|---|
| Governed stage pipeline (`orchestration.py`) | LangGraph StateGraph / agent loops | Explicit state machine; off-the-shelf loops | Rewrite of control plane | **Parallel planner authority**; loses deterministic gates | **KEEP** — the control plane IS the product |
| MCP streamable-HTTP transport | Official `mcp` Python SDK / FastMCP client | Battle-tested protocol lifecycle, spec-tracking | Adapter swap under `specialist_interop` | Auth/session semantics must be re-verified | **MIGRATION_CANDIDATE** — POC #1 |
| Proposal JSON-schema validation | Pydantic / Instructor | Stronger validation + output-repair retries for F4 | Small, adapter-scoped | Repair loop must stay inside existing call budget | **REUSE_LIBRARY** — POC #2 |
| `ModelCallLedger` + usage capture | OTel / Langfuse / Logfire | Provider gen-ID correlation (doc-188 gap) | Instrumentation only | Never persist prompts/CoT/secrets | **EXTEND_EXISTING** — future observability task |
| `_TurnGoal`/EvidenceFacts/recovery context | LangGraph checkpoints / agent sessions | None material (single-turn, in-memory) | Persistence infra unneeded | Over-engineering | **KEEP** |
| `_fit_json_block` fit ladders | Framework context compressors | Marginal | — | Loss of truthful omission markers | **KEEP** |
| Bounded retries/deadlines | tenacity / framework retries | Marginal | — | Budget semantics differ | **KEEP** |

## 5. F1–F6 failure mapping (docs 185/186/188)

| Failure | Root-cause status | Framework capability | Expected benefit | Verdict |
|---|---|---|---|---|
| F1 wrong candidate | FIXED by H6 (goal projection, doc 190) | Agent frameworks offer no better discrimination guarantee | None proven | No framework needed |
| F2 context continuity | Existing mechanisms proven (doc 188) | LangGraph checkpointing — overkill single-turn | None | KEEP existing |
| F3 redundant calls | H5 recovery re-asks (separate task) | No framework removes deliberate gates | None — would likely ADD calls | Custom fix pending |
| F4 invalid structured outputs | 16–36 s/turn retry cost (doc 188) | Instructor/Pydantic validation+repair | MODERATE — bounded output repair | **POC candidate** — causal evidence required on real model |
| F5 latency | Sequential governed stages | Parallel fan-out doesn't apply (stages are dependent) | Negative — frameworks add overhead | Reject |
| F6 business outcome | Goal context (fixed) + owner retrieval adequacy (open, C vs D) | No framework feature addresses owner coverage | None | Owner probe pending |

## 6. Secondary candidates (lightweight)

- **Microsoft Agent Framework** — reached **1.0 GA (April 2026)**, MIT, multi-provider incl. Ollama, MCP+A2A, middleware. Now production-stable, but still an agent-loop framework — same parallel-authority objection. REJECT for orchestration; note for future middleware reference.
- **Google ADK / CrewAI / Agno / Strands** — same agent-orchestration class; no material advantage over the four primary candidates for a governed control plane. REJECT.
- **LlamaIndex Workflows / Haystack** — retrieval-layer frameworks; DÉLIA's retrieval is owner-side via DAVI, not in-process RAG. NA/REJECT.
- **Instructor** — narrow library: patched OpenAI-compatible client + Pydantic validation + automatic retry on schema failure. Directly targets F4 inside `model_invocation`. **POC candidate.**
- **Guardrails AI** — output validation/repair, similar role; heavier hub model. Alternative to Instructor, TO_VERIFY.

## 7. Scoring (weights: arch compat 25%, complexity ↓ 20%, business outcome 20%, security/contract 15%, perf/tokens 10%, maturity 10%)

| Candidate | Score /5 | Rationale |
|---|---|---|
| Official MCP SDK (adapter-scoped) | **3.6** | Boundary-respecting swap of hand-rolled protocol code; reduces custom transport surface; preserves all gates. Uncertainty: auth/session parity must be proven. |
| Instructor (adapter-scoped) | **3.4** | Targets F4 retry cost at the exact adapter boundary; OpenAI-compatible; minimal blast radius. Uncertainty: repair loops must respect TurnDeadline; real-model gain unproven. |
| Pydantic validation (lib only) | 3.2 | Same boundary as Instructor minus retry policy; could underpin it. |
| Pydantic AI | 2.3 | Excellent pieces (MCPToolset, typed outputs) but adopting its Agent duplicates the control plane; cherry-picking = the two narrow candidates above. |
| OpenAI Agents SDK | 2.0 | Mature tracing/sessions, but loop ownership conflicts; LiteLLM path adds a second provider layer beside the existing port. |
| mcp-agent | 1.9 | MCP-native lifecycle is its strongest card — still agent patterns + optional Temporal infra. |
| LangGraph | 1.8 | State machine expressiveness real, but checkpointing unneeded, langchain dep tree heavy, and the graph would re-own control flow. |

## 8. POC design (not implemented — bounded recommendation)

- **POC-1 (preferred): official `mcp` Python SDK client inside `specialist_interop`** — same fixtures (`MULTI_CANDIDATE_RESULT` family), same FakePort contract, no owner calls, no production. Success = parity on tools/list/tools/call + session/auth semantics + typed error vocabulary preserved + no dependency creep beyond `mcp` + its transitive set. Metrics: code deleted vs added, test parity, handshake/error-path coverage.
- **POC-2 (alternative): Instructor behind `model_invocation`** — drive the `arguments`/`candidate_arguments` stage against local Ollama with the same scenarios; measure invalid-structured-output rate and retry latency vs baseline (doc-188 numbers as reference shape). Success = fewer invalid outputs within existing `LLM_CALL_MAX_ATTEMPTS`/`TurnDeadline` semantics; no new retry loop outside the governed counter.
- Prereqs: dependency vetting (license OK — MIT/Apache), ≥7-day-old pinned versions, architecture decision authorizing a boundary-scoped adapter POC, no domain/application layer imports of framework types (adapter must translate to existing internal contracts — framework output stays untrusted data).

## 9. Security/contract/architecture verdicts

- No framework may own tool selection, AuthZ, provenance, PREPARE/ACT, idempotency or audit — all remain deterministic DÉLIA/Core/Domain code. Agent-loop frameworks rejected on this alone.
- Domain/Application layers must never import framework/HTTP/provider SDKs; allowed surface is `infrastructure` adapters only.
- `DÉLIA → DAVI/MCP → API DELPI` preserved; nothing evaluated restores direct OpenAPI access.

## 10. Classification register

- PROVEN: dependency leanness of delia-api; H6 merged; F4 retry cost; agent-loop vs governed-pipeline mismatch.
- INCONCLUSIVE: semantic gain of Instructor on kimi-k3 (local model can't reach stages — doc 185/188); MCP SDK behavioral parity (not yet POC'd); Guardrails AI details (lightweight pass only).
- TEST_NOT_RUN: all framework executions (none installed, none run — by task restriction).
- NEXT_BOUNDED_STEP: coordination decision on POC-1/POC-2 (or neither); the unresolved retrieval-adequacy probe from doc 186/190 remains independent and higher business priority than any framework work.
