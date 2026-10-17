# 10 — I02-R2 Independent Architecture and Deploy Review

**DATE:** 2026-10-17. **REVIEWED_HEAD:** `552ff2e5cc7e9b26633a723ac02ce7b05d5d584b`. **CODE_SHA:** `4a8e4d1881957833ecce36d10344d4900f7087ed`. **VERDICT:** `ACCEPT_WITH_RESIDUAL` for **bounded index_probe remediation**, `I02_ACCEPTED=NO` (I02 as a whole remains `REWORK`).

## Scope and evidence
Independent GitHub code diff review (commit `4a8e4d1`), [executor report 09](./09-i02r2-index-probe-headroom-fix-and-deploy.md), including reported backend regression and production live evidence at deployed code SHA `4a8e4d1`, model `moonshotai/kimi-k3`, config `dd51e9912270e46b`. Independent production deployment, tests, logs and authenticated live scenario were **not rerun** by reviewer. Health HTTP 200 + SHA markers indicate technical deployment, not business outcome.

## Accepted bounded correction
- Existing application pipeline reused: `_contract_declares_omit_returns_index` now recognizes Portuguese omit/index language; declared omit→index runs owner INDEX READ without extra model probe. Schema validation and owner-returned identifier binding preserved.
- `_budget_allows_optional_index_probe` checks shared deadline before an optional model call; when skipped for budget, the path rejects unproven optional free-string IDs and requests missing inputs. Exhausted global deadline remains terminal. `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`, no planner/memory/public-contract changes.
- Executor live VISTA K3: owner index (11 IDs) → model index selection `display_formats` → owner guidance READ → nested guide projection, `GROUNDED`, 28,532ms, `PASS_WITH_LIMITATION`. Relevance of `display_formats` for full legibility/visualization question only PARTIAL.
- Executor-reported tests and full backend PASS; material unauthorized ACT 0; deploy SHA `4a8e4d1` and health 200 reported.

## Material residuals / cautions
1. **Budget floor effectively disables optional model index probes under observed runtime config:** required = `2 * _model_stage_timeout_seconds + MIN_VIABLE_MODEL_STAGE_SECONDS * 3`. When stage timeout is 30s and the global budget is 30s, the optional probe cannot meet even its first two timeout terms. Contract-declared index still works, but non-declared providers may regress to clarification. Do not call this proof of generalized provider-neutral completion; test alternative configuration and provider contracts.
2. **Portuguese contract declaration is inferred from untrusted free-text description** (broad `sem ` combined with `índice`/`lista de` anywhere). This may produce false positives where negation/semantics differ. Retain schema and READ-class gates, but evaluate adversarial descriptions and refine with approved structured owner contract if available; discovery metadata never authority/permission.
3. **K1 FAIL, K2 FAIL:** reported TÉO K1 `model_timeout` 30,014ms, K2 no usable prior evidence/timeout 30,013ms. No basis to accept full I02 or claim general knowledge continuity.
4. Selection quality for VISTA: owner-selected `display_formats` was semantically partial; evaluate index selection against original user request, not merely valid owner ID.
5. Outcome evidence for live is executor-reported; independent reexecution `TEST_NOT_RUN`. No autonomous phase advancement.

## Next bounded step / architecture decision
Keep R2 code and deployment as a bounded improvement; **do not close I02**. Priority is diagnosis of four-plus pre-owner model stages and intermittent TÉO K1/K2 timeout (latency evidence per stage, necessity and reuse of stages), then minimal approved correction. In parallel/afterward, evaluate false-positive descriptions and optional-probe floor across synthetic providers and configs. Do not silently replace stage model timeout policy or authorize a new planner. K3 topic relevance remains a distinct semantic-selection residual.

```text
I02_R2_INDEPENDENT_REVIEW=ACCEPT_WITH_RESIDUAL
I02_R2_INDEX_PROBE_FIX=ACCEPTED_WITH_RESIDUAL
I02_ACCEPTED=NO
I02_OVERALL=REWORK
K1_LIVE=FAIL
K2_LIVE=FAIL
K3_LIVE=PASS_WITH_LIMITATION
DEPLOYED_SHA_REPORTED=4a8e4d1881957833ecce36d10344d4900f7087ed
OPTIONAL_PROBE_CONFIG_REGRESSION_RISK=OPEN
PT_CONTRACT_FALSE_POSITIVE_RISK=OPEN
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
NEXT=I02_R3_TEO_PRE_OWNER_LATENCY_ARCHITECTURE_DIAGNOSIS
```
