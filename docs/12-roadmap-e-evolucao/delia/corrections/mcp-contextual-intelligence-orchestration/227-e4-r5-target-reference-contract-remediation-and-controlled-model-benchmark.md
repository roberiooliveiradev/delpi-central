# 227 — DÉLIA · E4 R5 — target-reference contract remediation before model-size decision

**Date:** 2026-11-03. **REVIEW_OF:** `DELIA-C3-E4-R4-TYPED-GOAL-EXECUTION-AND-MODEL-AB-CLOSURE-01`. **EVALUATED_CODE_SHA:** `c42d95e4f0` (GitHub HEAD had advanced in unrelated production-control files at review). **REVIEW_VERDICT:** `REWORK / EXECUTION_DRIFT` (specific R4 target-binding design); not accepted as end-to-end. **NO PRODUCTION DEPLOY**.

## 1. Critical verified code finding

At reviewed SHA, `orchestration.py::_read_obligations_from_goal`:
- Uses `re.findall(r"\b\d{5,}\b", business_subject)` and falls back to the same regex on `input_text` to invent candidate targets; sorts and truncates to four.
- Creates each `SubObjective.goal` by hardcoding `"Consulte a estrutura completa do produto {target}"`.
- Runs only when `goal.comparison_requested=True`; otherwise returns None.
- Does **not** carry typed authorized `EntityRef/EvidenceRef` source owner, origin, provenance, occurrence or scope. `business_subject` is model-authored text; regex tokens from this field are not proof of domain target.
- Cannot resolve implicit cross-turn `as duas` by itself because it does not use revalidatable typed references.
- Can misinterpret numeric quantities/dates/IDs and silently discard 5th+ requested target, and is hardwired to product structures rather than general authorized multi-evidence comparisons.

**This is substantive conflict with ADR58's semantic-proposer/typed-provenance boundary, doc 221 R1, 222, 225 and 226; it is not just a small-model limitation.** `EXISTING_EQUIVALENT=PARTIAL` for current typed target representation (needs exact existing consumer/contract inventory); `REUSE_DECISION=EXTEND` legitimate reference representation / REMOVE ungrounded regex string builder, rather than invent new planner. If source authorities lack an admissible ref contract, STOP `ARCHITECTURE_DECISION_REQUIRED` on that specific change; no fabricated refs.

## 2. Other observed evidence

- R4 commit includes runtime change to `orchestration.py` (+55/-7 vs plan baseline), plus ledger; executor reports full mechanism and prior E2E, but **no repeated final-SHA reliable two-tree client comparison acceptance**.
- `goal_understanding comparison=True/False` varies; `decompose` sometimes empty, sometimes extra `so_compare`; many E2E tests are inherited from prior SHAs. These are observed effects, not controlled proof that 4B cannot succeed after correct target contract.
- A valid source count `sources=3` cannot prove requested two target identities; source cardinality and source matching are separate invariants.
- `SEC01=PASS` is executor-reported with documented bearer revocation limitation; concurrency and gateway delivery remain release gates.

## 3. Coordination decision — approved bounded implementation, finite independent benchmark

**A — Fix target-reference contract now (priority 1).** Use existing scoped conversation/investigation refs, model goal proposal, authoritative owner results and live Core/Domain validation. Keep distinct layers: (i) **user-supplied literal** is a request candidate, (ii) **model-proposed referent** is HYPOTHESIS, (iii) **authorized owner-backed resolved target** is admissible for actual READ/evidence. Context text is never factual evidence. Persist only refs/hashes appropriate to existing owner and retention policy; no new DB/memory.

Once goal semantically requests comparison, use **the existing typed goal** and *validated target refs* to derive minimal source-read obligations. If goal class is disputed, test the same model invocation under exact frozen stage prompt/schema/history before changing it; do not force compare from keyword or numeric regex. If refs are missing, use existing discovery/resolver and targeted clarification; do not invent or silently transform an unknown target into a confirmed product. Typed representations must generalize to other admissible source types, not only BOM/product.

**B — Remove R4 regex and product-specific obligation builder.** Replace the accidental `re.findall(5+ digits)` / `Consulte ... produto` mechanism by owner/capability-neutral typed source obligations under existing stage/subobjective contracts, making real Domain API/owner authoritative for IDs and source values. Provenance/identity/version/scope/occurrence/cardinality must survive. Review consumer use and compat/rollback tests. Never insert provider mechanics into planner.

**C — Benchmark local models without premature upgrade.** Approve isolated A/B on a bigger *already available and authorized* local model, if installed/capable, but do not make benchmark a substitute for correcting target refs. Test identical input/stage/schema/context/provider settings and actual authorized source data after reference contract is corrected. At least 5 repeats each per critical stage and original/sibling E2E where compute allows; record exact failure taxonomy, p50/p95 latency, real tokens/usage, memory and business oracle. If model isn't present, `TEST_NOT_RUN`. Do not change production model automatically. Use a true business outcome, not only JSON syntax validity, for model decision.

**D — Do not blindly add retries/raise gateway limit.** Retry policy doc103 remains authoritative and bounded; streaming only with verified end-to-end HTTP/NDJSON contract. 120s gateway crossing is still unsafe; require client-visible terminal before gateway timeout with meaningful margin and repeated tests.

## 4. Executable task and acceptance

**TASK_ID:** `DELIA-C3-E4-R5-TYPED-TARGET-REFERENCES-AND-MODEL-AB-01`.

1. Reanchor git HEAD/status and authorities 16→50→17→49→51→52→21→20→25, ADR58, 103, 187–226 and ledger.
2. Inventory **only** direct producers/consumers of `_TurnGoal.business_subject`, source refs, `ConversationContextTurn`, `EvidenceFacts`, source resolution and `SubObjective`; prove `EXISTING_EQUIVALENT`/ `REUSE_DECISION` at symbol level.
3. RED: the same `compare as duas` context that previously succeeded in independent READs; also compare with explicit targets, product code fragments, nonnumeric IDs, five targets, numeric distractors, two same-code records from distinct owners, cross-session untrusted text and AuthZ revoked. No heuristic code matching.
4. Implement smallest correct typed reference resolution and source-read obligation derivation using existing capability/model/graph owners. Remove regex and literal product-specific obligation sentence and do not reintroduce equivalent shadow mapping. If a required new typed internal contract is genuinely missing, draft exact owner/consumer/fields/trust/compatibility and raise `ARCHITECTURE_DECISION_REQUIRED` rather than guessing; complete independent tests.
5. Ensure model does semantic interpretation once per meaningful objective; existing authorized discovery/resolver executes needed reads. Additional open-ended decompose only for truly complex unknowns. Deterministic verifier checks exact requested target coverage, records, occurrence, units, hierarchy, no hallucinations.
6. A/B same-stage Qwen3 4B before and after typed-ref fix; conditional bigger available model benchmark if Qwen3 still fails. No model cutover, new provider, generic retry inflation or nginx-only change.
7. E2E actual local Keycloak/Core+DAVI/Domain+Ollama same session A01→A02→A03 and single turn, unrelated sibling, unknown/ambiguous, denied/revoked, cancel and long context; repeated, all outcomes recorded. Correct full-tree oracle (false common 10030012 rejected, 10030015 included), real client-visible PT-BR terminal comfortably within gateway.
8. Complete full relevant regression/security/concurrency/usage and owner contracts on **final SHA**, remove redundant code, update report/ledger, safe commit/push `main`. Do not self-accept phase/production release.

**Gate for `FUNCTIONAL_ACCEPTANCE_CANDIDATE`:** G04/G05/G07/G12 all PASS repeatedly on final SHA, exact typed source coverage, correct oracle, Core/Domain auth, honest refusal on missing/unavailable evidence, bounded delivery, no hardcoded product schema/regex. A local model A/B that helps but does not restore client-visible outcome is not full acceptance.

**If blocker:** `BLOCKED_WITH_EVIDENCE` with precise missing owner contract/authority or unavailable actual model, never claim success from prior SHAs. NO PRODUCTION DEPLOY.
