# 299 — INT-1 investigation context, model-visible MCP tool surface, semantic selection and recovery audit

**TASK_ID:** `DELIA-C3-T2-INT1-INVESTIGATION-CONTEXT-TOOL-SURFACE-AND-RECOVERY-REMEDIATION-01`  
**AUTHORIZATION:** PO — investigate existing investigation mechanism; minimal proven fixes; retest. No new Agent/router/INT-2/INT-3/prod.  
**BASELINE:** `generalist-semantic-v2` / `7dbc94c5035b0f19`  
**INT1_STAGE_ACCEPTANCE:** BLOCKED  

## 1. Execution identity

| Field | Value |
|---|---|
| REFERENCE / BASE_HEAD | `0cde0f674bd31e494f6af3f9f688d908f24f5542` |
| LIVE_EVAL_MOUNT | host `delia-api` → `/app` (remediation loaded before commit) |
| EVALUATION_ID | `ctx-rec-1bc5578991` |
| BASELINE_REF (doc 298) | `stab-v2-5b0e914eb9` |
| MODEL | `qwen/qwen3-14b` / `openrouter_qwen` |
| RUBRIC_SHA16 | `268db33af5f24770` |
| PROD_UNTOUCHED | YES |

Artifacts (gitignored): `delia-api/.battery/int1-context-recovery-rerun/`  
Traces: `delia-api/.battery/int1-secure-decision-trace/ctx-rec-1bc5578991/`

## 2. Pipeline inventory (model-visible vs backend-only)

| Stage | Source → consumer | Model-visible? | Notes |
|---|---|---|---|
| User question | HTTP/`run_scenario` → `input_text` → Agent prompt | YES | Prompt = raw question |
| Actor/session/workspace | `InvestigationDeps` | NO (deps closed) | AuthZ/deadline only |
| Prior turns | `_prior_message_history` (limit 4) | YES if present | Eval scenarios used `prior=[]` |
| Instructions | `investigation_instructions.delpi.json` v2 | YES | Fingerprint frozen |
| Live catalog metadata | `_project_semantic_tool_catalog` | Indirect | Descriptions capped `[:320]` for catalog DTO / budget estimate — **not** the MCPToolset schema path |
| MCP tools/list | native `MCPToolset` | YES | Full owner descriptions historically truncated by EnvelopeHint |
| RenamedToolset | capability_id rename | YES | Name only |
| EnvelopeHint | schema-derived append | YES | **PROVEN defect:** `(desc+hint)[:500]` destroyed owner text |
| Tool observation | `_attempt_projection` → `_bounded_json` | YES | Progress/coverage notes; **pagination missing before fix** |
| Progress classes | `classify_investigation_progress` | YES (in projection) | NEW/RELATED/DISCOVERY/NONE |
| Finalize / Outcome | Application acceptor | NO to model | Grounding ≠ objective |

**MCP providers inventaried for INT-1 live surface:** DAVI, TÉO, VISTA (12 model-visible tools). Other platform MCPs (e.g. supplies) not in this eligible catalog for the eval subject.

## 3. Proven defects (before correction)

| ID | Responsibility | Root cause | Evidence |
|---|---|---|---|
| F1 | Tool description parity | `_EnvelopeHintedToolset` truncated MCP descriptions to 500 chars when appending hints | Code `description=(desc+hint)[:500]`; MCP `teo.read` ~1784 chars → loses 1284; unit RED |
| F2 | Pagination / continuity | `_attempt_projection` omitted `extract_pagination_envelope` fields; model only saw `result_truncated` | Doc 298 P2 never advanced `page`; projection lacked `pagination`/`continuation_note`; unit RED |
| F3 | G1 selection attractor | TEO `read` contract lists `decomposition_tree` — semantically attracts “árvore de componentes” vs DAVI BOM | Doc 298 + ctx-rec args `entity=decomposition_tree` / `process` first; DAVI available |
| F4 | P3 specialist ambiguity | Dashboard analyze vs visualization formats — partially description/schema clarity | Doc 298 first tools vista/teo/vista mixed |

F1/F2 classified **PROVEN** and corrected. F3 remains **OPEN** after F1 (see results). F4 improved after F1 (no `teo:analyze` first-tool in corrected core).

## 4. Reuse decision

| Item | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Agent / orchestrator | YES | REUSE |
| EnvelopeHint wrapper | YES | EXTEND (preserve owner description) |
| `extract_pagination_envelope` | YES | REUSE inside `_attempt_projection` |
| Instructions v2 | YES | REUSE (unchanged) |
| New Agent / specialist router | — | **NOT created** |

## 5. Minimal corrections implemented

1. **Preserve published MCP tool descriptions** when appending schema-derived envelope hints (`hint[:280]` only; never shorten owner text).  
2. **Project owner pagination** (`page`, `page_size`, `has_more`, `total_count`, `items_in_page`) + `continuation_note` when truncated/`has_more`.  
3. Harness: capture `pagination`/`continuation_note` in decision traces; generalization scenarios frozen in `int1_context_recovery_generalization.json`.

No instruction v4. No specialist hardcoding. No INT-2/INT-3.

## 6. Tests

| Suite | Result |
|---|---|
| RED→GREEN `test_int1_tool_description_and_pagination_projection.py` | PASS |
| `test_investigation_instructions_decoupling.py` | PASS |
| `test_int1_investigative_progress_rework.py` | PASS |
| `test_pydantic_ai_investigation_runtime.py` + semantic rework + auth lifecycle | PASS |

## 7. Live comparison (Qwen 14B)

Core 8×3=24; env valid 24/24. Generalization +5 (1 rep).  

| Scenario | Doc 298 (A) | Corrected (B) | Selection note |
|---|---|---|---|
| P1 | P2 N1 | P2 N1 | Still mixed; one TEO-first residual |
| P2 | P3 | P2 N1 | **r3 paged 2–4**; r1/r2 still weak |
| P3 | P1 N2 | P2 N1 | **No `teo:analyze` first**; all VISTA |
| G1 | P1 N2 | P1 N2 | Still TEO-first ×3 |
| H1 | S3 | S3 | All DAVI first (more stable) |
| H2 | S3 | S3 | Honest empty preserved |
| H3 | P2 I1 | P3 | No inconclusive |
| H4 | P3 | P3 | `teo:analyze` stable |

Overall objectives (scorer proposal): A SAT6/PART12/NOT5/INC1 → B SAT6/PART13/NOT5/INC0.  
`GROUNDING_WITHOUT_OBJECTIVE`: 2 → 1.

### Generalization (frozen before live)

| ID | First tool | Notes |
|---|---|---|
| N1 stock near-capability | davi:get_context | GROUNDED stock path |
| N2 pagination | teo:read | **pages 1→7** explicit continuation |
| N3 vista vs teo display | vista:read | Correct specialist family |
| N4 missing identifier | (none) | Honest clarification |
| N5 live alerts | teo:analyze | GROUNDED; coverage residual |

## 8. Causal conclusions after fix

| Scenario | Root cause (updated) | Status |
|---|---|---|
| P1 | Mixed owner incompleteness + residual selection | PARTIAL residual |
| P2 | Continuity partially unblocked (projection now present); still not reliable ×3 | IMPROVED_PARTIAL |
| P3 | Description/schema clarity after F1; VISTA-first consistent | IMPROVED selection |
| G1 | Semantic overlap TEO decomposition vs DAVI structure — **not cured by description preservation alone** | OPEN — may need owner contract wording or later INT-2 decision; **no specialist hardcode** |

## 9. Residuals / architecture

```text
CREDENTIAL_SCOPE=NONE_PROVEN_SEPARATE_FROM_PROD
CATALOG_DTO_DESCRIPTION_CAP_320=REMAINS (budget/catalog path; MCPToolset path preserved)
G1_TEO_DECOMPOSITION_ATTRACTOR=OPEN
OBJECTIVE_REPRESENTATION_GAP=NOT_PROVEN_REQUIRED (no INT-2 impl)
INT3=NOT_AUTHORIZED
```

## 10. Recommended next step

```text
RECOMMENDED_NEXT_OWNER=COORDINATION
RECOMMENDED_BOUNDED_NEXT_STEP=INT1_BOUNDED_REWORK_CANDIDATE
  focus: G1 recovery after wrong-owner observation + P2 reliability;
  optionally request owner-side description clarity for decomposition_tree vs product structure
  WITHOUT specialist routers or keyword classifiers
INT2/INT3=NOT_AUTO_AUTHORIZED
```

## 11. Status

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT2_IMPLEMENTATION_AUTHORIZED=NO
INT3_IMPLEMENTATION_AUTHORIZED=NO
T3_AUTHORIZED=NO
PRODUCTION_DEPLOY=NOT_AUTHORIZED
NEXT=COORDINATION_INT1_CONTEXT_AND_RECOVERY_INDEPENDENT_REVIEW
```
