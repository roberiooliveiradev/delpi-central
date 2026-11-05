# 287 — DÉLIA · Review: resposta real ao produto 50220013 entregue; proveniência e regressões residuais

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-P0-GPU-ENABLED-STRUCTURED-OUTPUT-AND-REAL-READ-CLOSURE-01`  
**BASE_HEAD REPORTED:** `9395d34e3c81e881b47f0a2936894d9e20d225fa`  
**REVIEWED_SHA:** `08aae365682b870f4e0fa8490d55f68cf125d7a7`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` for the **reported** successful real client/owner READ; provenance contract and new dynamic-tool/generalization/security regressions `PENDING`. Production deploy `NOT_AUTHORIZED`.

## Verified GitHub change set

Actual commit modifies four files: `delia-api/app/application/capability_provision/contracts.py`, `delia-api/app/application/capability_provision/orchestration.py`, `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py`, `infra/scripts/get-dev-token.sh`. No test files were added/edited in the commit. Full suite PASS is executor-reported, not independent reviewer execution.

- `InvestigationAnswer.schema_version` moved `str` to `Literal["1"]`, promoting a stronger schema constraint; consumer compatibility and schema serialization must be kept under contract.
- Adapter explicitly instructs native output JSON or output-tool mode, exposes candidate `required_arguments`/`argument_schema` in bounded projection, and synthesizes per-capability native tool signatures/annotations from owner `input_schema`, continuing to delegate authorization and validation to Application.
- Application extracts bounded nonempty `candidate_token` only for candidate-bound descriptors, validates other arguments against descriptor schema, then relays token to `_invoke_selected`. The token remains **untrusted owner-issued opaque input** and cannot create permission, authorize/forge business facts or override stage gates. Assert binding to authorized discovery session/actor/owner if supported by actual owner contract. Do not claim token validation inside DÉLIA; owner authority is final.
- Dev token helper requests `scope=openid profile email`. Verify client permitted scopes and existing browser parity, no token logging, no auth bypass. Any effect on production auth flow is excluded.
- Typed diagnostic logs include argument *key names* and native retry error type/location; even keys may be untrusted/sensitive metadata, so keep log allowlisted/bounded and ensure no values or secrets.

## Positive runtime evidence: reported, not independently rerun

Executor reports real Keycloak-authenticated `POST /apps/delia-api/interaction/turns` HTTP200, ~30–35s, `grounding=GROUNDED`, `epistemic=OBSERVATION`, `finalized status=SUCCESS`; response with code `50220013`, description `CB18BRAN-00368/06/15-3100-0000`, group `5022`, independently compared by executor to authoritative `GET /apps/api-delpi/products/50220013`. Real 10-cap catalog, DAVI discover→execute candidate-bound READ, Pydantic AI valid InvestigationAnswer and client delivery reported. This is **first reported P0 positive customer-facing READ**. Do not classify it as independently reviewer-verified or full-scope generalization.

**Material residual:** final serialized `source_refs=[]` despite GROUNDED/OBSERVATION; executor reports owner execute projection omits them. Grounded label may be derived from evidence/outcome despite no user-facing refs. Need inspect canonical evidence/projection contract and ensure READ outcome authoritative refs propagated, not fabricated or model-created; if a mandatory contract requires refs for GROUNDED, classify contract failure and adjust acceptance accordingly. Do not set GROUNDED solely on textual content matching owner. RQ24/RQ28 stay PARTIAL pending verified provenance and coverage.

## Specific source review risks / bounded regression tests

1. Dynamic `inspect.Signature(params)` is assembled in owner schema property iteration order with some defaulted optionals and nondefault required params. **If optional property appears before required property**, Python signature rejects `non-default argument follows default argument`; need tests using realistic varied schemas and compliant ordering, without inventing owner contracts. Also test illegal/reserved parameter names, duplicate names, schemas lacking properties, nested argument objects, booleans/enums/arrays, collision of `arguments` escape hatch and untrusted metadata. The synthetic function has `**kwargs` runtime but `__signature__` advertises typed params; verify actual native Pydantic AI validation matches authorization boundary.
2. `candidate_token` temporarily bypasses `_validate_instance` for ORCHESTRATED_FIELDS then is re-inserted. For real owner schemas requiring `candidate_token`, verify actual validation consistency, one-candidate/actor/session binding at authoritative owner, no replay/cross-owner token, no other orchestrated key passes. Fail closed on invalid/oversized tokens. Need precise contract tests, not blanket rejection that breaks the positive path.
3. `schema_version=Literal["1"]` should be tested on native JSON/output mode and mismatch `"1.0"` behavior; avoid compatibility breaks without contract evidence.
4. Development OAuth scope addition should be checked against declared Keycloak client allowlist; no auth bypass; no log secret.
5. SourceRefs need actual owner output provenance, not synthetic link derived from product code or arbitrary model response. Reproduce same positive test with expected nonempty authoritative source refs if contract requires them; test negative/unauthorized/no-data and one second-capability control to establish generalization. A lone successful 50220013 question does not prove all MCP tools function.

## Next bounded task: provenance + targeted regression, not a new inference/GPU investigation

**TASK_ID:** `DELIA-C3-P0-SOURCE-REFS-AND-DYNAMIC-TOOL-CONTRACT-HARDENING-01`.

- Reanchor current HEAD/status, Project Instructions/.cursor, authorities 16→50→17→49→51→52→21→20→25, architecture/product/thematic spec/ledger/docs 256,283–287. Identify exact CP/RQ owner contracts and existing adapters/projections; `EXISTING_EQUIVALENT` and `REUSE_DECISION`.
- Capture authorized owner READ outcome for 50220013 with authoritative source IDs, track source_refs through provider adapter→governed attempt→Pydantic AI evidence→finalize→HTTP response; locate first loss. If owner contract genuinely has no source references, label `SOURCE_REFS_NOT_AVAILABLE`, do not invent or mark complete. Preserve fail-closed grounding semantics per authority.
- Add RED tests for provenance loss and for dynamic schema optional-before-required and boundary security. Fix proven bug with smallest diff, physically remove any replaced legacy in same delivery, repair consumers; full regression/residual search.
- Re-execute real owner-positive 50220013 through authenticated client with exact answer, valid InvestigationAnswer, authoritative source refs and timestamp/latency; negative/no-data control and at least one additional owner/capability READ. Never claim all features operational from one query.
- Freeze GPU and context configuration unless a new measured defect arises. No production deployment without release gate, security, authorization and rollback.

## Classification

- `P0_USER_ANSWER_DELIVERED=PASS_REPORTED`.
- `P0_OWNER_CONTENT_MATCH=PASS_REPORTED`.
- `P0_STRUCTURED_OUTPUT=PASS_REPORTED`.
- `P0_SOURCE_REFS=PARTIAL`.
- `P0_GENERALIZATION=INCONCLUSIVE`.
- `FULL_REGRESSION=PASS_REPORTED`.
- `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

**Conclusion:** celebrate the first working real question, but do not silently accept missing authoritative provenance or untested generic input schema and token boundaries.
