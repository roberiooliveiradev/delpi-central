# 202 — native_assessment status fail-closed remediation (deployed)

**Task**: `DELIA-C3-NATIVE-ASSESSMENT-STATUS-FAIL-CLOSED-REMEDIATION-01`
**Deployed SHA**: `45118d6425` — production `srv-api`, image
`sha256:def538a02e11…`, engine `langgraph`, model `moonshotai/kimi-k3`.

---

## 1. Defect (proven, not assumed)

Task 08 (doc 201) identified the coercion; this task proved it with a
failing test before fixing:

`_assess_native_path` (orchestration.py):

```python
if status not in ("sufficient","foreign_evidence_required",
                  "corroboration_requested","inconclusive"):
    status = "sufficient"      # ← fail-open coercion
```

Absent, null, wrong-typed or unrecognized `status` values were recorded
and consumed as affirmative evidence sufficiency. RED evidence:
`assert 'sufficient' == 'inconclusive'` on `{"status": "unknown_status"}`.

## 2. Contract owner / reuse gate

```text
RESPONSIBILITY=native-assessment status extraction + vocabulary gate
OWNER=delia-api application layer
CANONICAL_SOURCE=orchestration.py::_assess_native_path (+ instruction
  vocabulary: orchestration_instructions.delpi.json
  delia.capability_orchestration.native_assessment)
CONSUMERS=_governed_owner_path path selection (call sites ~4917 and
  ~10080); _record_native_assessment ledger; Engine A and LangGraph B1
  share this exact implementation (B1 → gates._governed_owner_path)
CONTRACT=returns decision str; valid vocabulary = sufficient,
  foreign_evidence_required, corroboration_requested, inconclusive

EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND (same validation site; no new port/schema/framework)
ABSTRACTION_GATE=PASS
```

## 3. Fix (minimal diff)

Invalid values now resolve to `"inconclusive"` — the canonical
"cannot determine sufficiency" decision — with a distinguishing
`decision=invalid_status_rejected` log line. The native default is
preserved (foreign fan-out is never the fallback); no new retries, no
graph/budget/deadline/authorization changes. ~18 lines + docstring.

## 4. RED → GREEN

`tests/test_native_assessment_status_contract.py` — 34 tests:

- R1–R3: all 4 valid statuses preserved.
- R4–R8: 16 invalid values (unknown, near-miss strings, `""`, `"  "`,
  `123`, `0`, `True`, `False`, `1.5`, `[]`, `[x]`, `{}`, `{status:…}`),
  missing, null, non-Mapping → all `inconclusive`, never `sufficient`.
- R9/R10: turn-level governed outcome — invalid status does not
  authorize or fabricate; native path runs target owner only.
- R11/R12: invalid input consumes zero extra model calls.
- R13/R14: identical contract across `delia`, `langgraph_b0`,
  `langgraph` engines (shared `_assess_native_path` proven by
  parametrized turn tests + B1 wiring inspection).
- R15–R17: no silent positive fallback; observability intact;
  PREPARE/ACT untouched.
- R18: valid-status turn parity.

Ordering-sensitivity fix inside the suite: `app` logger state left by
earlier suites is rebound via the established `capture_*_logs`
fixture pattern.

## 5. Regression / audits

- New suite: 34/34 GREEN.
- Focused engine + recovery + relevance suites: GREEN.
- Full `delia-api` suite: 2 failures — BOTH verified pre-existing
  (`test_cri_instruction_variant_carries_requirements_clause` fails on
  stash of the fix; `test_infra_and_env_carry_no_direct_delpi_wiring`
  is a comment-substring audit in an untouched file). Zero regressions
  attributable to the diff.
- Phase-3 architecture audit: OK. Backend-boundary audit: 0 findings.
- Residual: fix confined to one function; no new imports/deps.

## 6. Production deployment

- Host: `srv-api` (`operador@192.168.1.237`, canonical per AGENTS.md).
- Pre-state: checkout `7644500a58`, running image `8931066e` (built at
  the Task 07-R1 deploy); `.env` already carried
  `DELIA_ORCHESTRATION_ENGINE=langgraph`.
- `git pull --ff-only` → `45118d6425` (ancestry verified);
  `./infra/scripts/up-prod-sequential.sh --build delia-api` — only
  delia-api rebuilt; ~92 containers untouched.
- Deploy start ~02:58 UTC, container recreated ~02:59 UTC, healthy.
- Startup log: `delia_orchestration_engine selected=langgraph
  surface=configured`. `DELIA_ENV=production`,
  `moonshotai/kimi-k3` + OpenRouter preserved.
- Rollback: prior image `8931066e` retained; Engine A remains
  `DELIA_ORCHESTRATION_ENGINE=delia` + restart (config-only,
  no business replay). Note: Engine A image also contains this fix —
  the engines share the corrected contract path.

## 7. Authenticated READ smoke (2 turns, identity `user`)

Credential note: the smoke identity is the PO-provided `user`. The
first attempt used a token minted without an explicit scope and
Keycloak issued `scope=email profile` (no `openid`); api-delpi's MCP
authz correctly denied the delegated exchange product
(`MISSING_REQUIRED_SCOPE missing=openid`) — an *identity-minting*
issue on the smoke side, not a runtime defect. Re-minting with
`scope=openid profile email` produced a conformant credential; no
passwords were reset, no admin/impersonation APIs used.

| # | Query | HTTP | Grounding | Outcome | Calls | Tokens in/out | Latency |
|---|-------|------|-----------|---------|-------|---------------|---------|
| S1 | product description for code 10080092 | 200 | GROUNDED / OBSERVATION | real record `TERM. BALA 0,50-2,27MM2 ESTANHADO CARRETEL S/ISOLACAO` via DAVI (discover+execute_delpi_information), full provenance | 7 | 10432 / 1858 | ~27.6s |
| S2 | "Me dê dois exemplos de terminal bala" | 200 | GROUNDED / OBSERVATION | honest typed outcome — owner records returned but did not match the request; refused to present (`insufficient_evidence`), no fabrication | 16 | 27174 / 10274 | ~111.6s |

Recovery observability fired for real on S2:
`relevance_recovery_entered=1, reuse_candidates=1, reassessments=1,
native_assessment_calls=2` — reuse correctly NOT eligible/performed
(`reuse_eligible=0`). Production logs show valid assessment decisions
(`sufficient`, `foreign_evidence_required`) through the corrected
contract; zero `invalid_status_rejected`, zero tracebacks/criticals.

## 8. Verdict

`PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED` — the fail-open coercion is
closed on the real host under LangGraph B1 with Engine A available as
rollback (config-only). Production LLM unchanged; no migrations; no
other services touched; `insufficient_evidence` semantics confirm the
bounded recovery path behaves truthfully under the corrected contract.

Residual: `inconclusive` on invalid status remains semantically
indistinguishable from a model-declared inconclusive in the response
projection — the `invalid_status_rejected` log decision preserves the
audit distinction at the orchestration layer.
