# 294 — INT-1 OpenRouter Qwen 14B instrumented causal evaluation

**REPORT_ORIGIN:** `ORIGINAL_SANITIZED`
**PERSISTENCE_TASK:** `DELIA-C3-T2-INT1-OPENROUTER-CAUSAL-REPORT-PERSISTENCE-01`
**SOURCE_EVAL_TASK:** `DELIA-C3-T2-INT1-LOCAL-QWEN14B-SETUP-AND-INSTRUMENTED-ROOT-CAUSE-EVAL-01`
**LOCAL_ORIGINAL (gitignored, not committed):** `delia-api/.battery/int1-openrouter-qwen14b-eval/CAUSAL-REPORT-or-qwen14b-35aaf1a4174b.md`
**LOCAL_TRACES (gitignored, not committed):** `delia-api/.battery/int1-secure-decision-trace/or-qwen14b-35aaf1a4174b/`

This document publishes a **sanitized, self-contained** causal report for independent review. Conclusions below are supported by projections extracted from the host JSONL traces of evaluation `or-qwen14b-35aaf1a4174b`. Raw `.battery` artifacts remain untracked.

**INT1_STAGE_ACCEPTANCE=BLOCKED** · **INT1_CLOSED=NO** · **INT2/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED** · **No functional rework in this publication.**

---

## 1. Execution identity

| Field | Value | Evidence class |
|---|---|---|
| `TASK_ID` (eval) | `DELIA-C3-T2-INT1-LOCAL-QWEN14B-SETUP-AND-INSTRUMENTED-ROOT-CAUSE-EVAL-01` | CONFIRMADO_NO_TRACE (`session.jsonl`) |
| `EVALUATION_ID` | `or-qwen14b-35aaf1a4174b` | CONFIRMADO_NO_TRACE |
| `EVALUATED_SHA` | `NOT_OBSERVED` in session meta; host git at publication prep = `807b4e02a3a6d57ea01ea6daf8b375d06402e352`; INT-1 impl ancestor historically `3bb2be887b` | MIXED |
| `RUNTIME_SHA` | `NOT_OBSERVED` in traces | MISSING_EVIDENCE |
| `MODEL_ID` | `qwen/qwen3-14b` | CONFIRMADO_NO_TRACE |
| `MODEL_PROFILE` | `openrouter_qwen` | CONFIRMADO_NO_TRACE |
| `MODEL_CONFIG_FINGERPRINT` | `b42a0da3f3be8154` | CONFIRMADO_NO_TRACE |
| `INSTRUCTION_FINGERPRINT` | `7dbc94c5035b0f19` (ledger/prior INT-1 stamps; **not** in this session meta) | HERDADO_POR_DOC |
| `TOOLSET_FINGERPRINT` | `3ae0125669b68521` (sha256 prefix of ordered capability_id list) | CONFIRMADO_NO_TRACE |
| `PYDANTIC_AI` | `2.50.0` | CONFIRMADO_NO_TRACE |
| `LLM_BASE_HOST` | `openrouter.ai` | CONFIRMADO_NO_TRACE |
| `EVALUATION_TIMESTAMP` | session meta `timestamp_unix_ms=1794404036161` ≈ 2026-11-11 UTC | CONFIRMADO_NO_TRACE |
| `ENVIRONMENT` | `development` | CONFIRMADO_NO_TRACE |
| `SECURE_EVAL_GATE` | `READY_FOR_ISOLATED_EVAL` | CONFIRMADO_NO_TRACE |

Scenarios executed (same evaluation): `P3_visualization_formats`, `G1_semantic_reword_structure`, `P1_product_structure_control`.

---

## 2. Security

| Field | Status |
|---|---|
| `EGRESS_PATH` | `https://openrouter.ai/api/v1` (real host; **no** localhost proxy) |
| `EGRESS_AUTHORIZATION_STATUS` | `PROVEN_ALLOWLIST_OPENROUTER` under `DELIA_EVAL_EGRESS_AUTHORIZED=1` |
| `CREDENTIAL_ISOLATION_STATUS` | `NONE_PROVEN_SEPARATE_FROM_PROD` — selective keys from `infra/.env` + portal from `infra/.env.local`; **no** prod `printenv` dump |
| `MCP_READ_AUTHORIZATION_STATUS` | `PROVEN_FOR_THIS_EVAL` — live MCP list/read succeeded after host-header + issuer alignment (probe + scenario wire calls) |
| `PRODUCTION_UNTOUCHED` | `YES` — eval container distinct; prod `StartedAt` unchanged in harness log |
| `SECURITY_RESIDUALS` | Shared infra LLM API key scope; eval flag is not a permanent production policy |

No tokens, passwords, API keys, Authorization headers, or `.env` values are reproduced in this document.

---

## 3. Shared model-visible toolset (P1 / P3 / G1)

All three scenarios observed the **same** projected tool surface (`tool_count=12`, fingerprint `3ae0125669b68521`):

| capability_id | remote_name | description_head (sanitized) |
|---|---|---|
| `davi.get_context` | `get_context` | DAVI entry point; catalog/context |
| `davi.knowledge` | `knowledge` | Governed DELPI knowledge |
| `davi.read` | `read` | Business read via catalog capability (incl. `get_product_structure` in description) |
| `davi.analyze` | `analyze` | Governed analytic capability |
| `teo.analyze` | `analyze` | Analysis views including live `dashboard_*` |
| `teo.get_context` | `get_context` | TEO semantic discovery |
| `teo.read` | `read` | TEO semantic read (process/domain entities) |
| `teo.knowledge` | `knowledge` | TEO product guides (guidance, not domain truth) |
| `vista.get_context` | `get_context` | VISTA context/catalog |
| `vista.read` | `read` | Closed entity+action vocabulary |
| `vista.analyze` | `analyze` | VISTA closed analyses |
| `vista.knowledge` | `knowledge` | VISTA product guides |

`specialists` field in projection recorded as `["mcp"]` (adapter grouping) while targets on the wire are specialist-qualified (`davi` / `teo` / `vista`).

---

## 4. P3 — Formatos de visualização

### QUESTION
`Quais formatos de visualização de dados estão disponíveis?`

### ADMISSION
Not separately traced as an admission gate event. Scenario started with full 12-tool surface. `ADMISSION_EVENT=NOT_OBSERVED` as distinct record; tools were available.

### MODEL_VISIBLE_TOOLS
See §3 (`teo.analyze` and `vista.knowledge` / `vista.read` present).

### FIRST_TOOL_CALL
- Target: `vista` / `read`
- Argument keys (types only in native capture): `entity` (string), `action` (string)
- Concrete argument **values:** `NOT_OBSERVED` as structured fields (adapter stored type shapes); recoverable only via owner error message below

### FIRST_TOOL_ARGUMENTS_SANITIZED
```text
keys: entity, action
types: string, string
values: MISSING_EVIDENCE (type-shape capture only)
```

### VISTA_READ_422_DETAILS (first call)

| Aspect | Evidence |
|---|---|
| HTTP | `422` |
| `error_kind` | `validation` |
| `code` | `INVALID_CHANGE` |
| Message (sanitized) | `playlistId, slideId e modelId são obrigatórios.` |
| `recoverable` | `true` (per owner JSON) |
| Inferred operation class | VISTA `read` requiring presentation target ids — **not** a display-format catalog read |
| Boundary | Owner validation (tv-dashboard / VISTA) — wrong action/shape for the user question |
| Responsible class | **Model tool selection / argument binding** (Agent chose VISTA read needing playlist context) |

### SUBSEQUENT_TOOL_CALLS (wire order)

| # | Specialist | Tool | Result (sanitized) |
|---|---|---|---|
| 1 | vista | read | 422 `INVALID_CHANGE` (playlist/slide/model required) |
| 2 | vista | get_context | success; catalogVersion present; discovery |
| 3 | vista | read | 422 `UNKNOWN_ACTION` — `read.product_guide: 'get'` |
| 4 | teo | knowledge | fail — unknown topic `data_visualization`; available topics include `dashboard`, `data_transfer`, … |
| 5 | teo | knowledge | success — product guide topic effectively `dashboard` (guidance) |

**Never observed:** `teo.analyze` with any `dashboard_*` view.

### OWNER_RESULTS / PROGRESS_DECISIONS (projections)

| seq | status | progress | provenance | note |
|---|---|---|---|---|
| 1 | SOURCE_UNAVAILABLE | NO_PROGRESS | — | aligns with first failed vista.read |
| 2 | SUCCESS | DISCOVERY_ONLY | vista/get_context | not business evidence |
| 3–4 | SOURCE_UNAVAILABLE | NO_PROGRESS | — | failed reads / wrong topic |
| 5 | SUCCESS | NEW_INFORMATION | teo/knowledge | citable guidance text about dashboards |

### FINALIZATION / COVERAGE

- Grounding: `GROUNDED`
- Declared status: `partial`
- Declared answer head: dashboards as analytic projections; points to product-guide topics `dashboard` / `data_transfer`
- Limitations include: `coverage_unknown`, unmet “especificação de formatos além de dashboards”, `declared_status_overridden`

### FIRST_MATERIAL_DIVERGENCE
**PROVEN:** first wire call = `vista.read` (422), **not** `teo.analyze` and **not** a successful format-catalog / product-guide path.

### ROOT_CAUSE_STATUS
**PROVEN (selection/binding class):** multi-specialist mis-selection under ambiguous “formatos de visualização”; recovery via TEO knowledge guide; objective coverage remains `coverage_unknown`. Exact concrete first-call entity/action strings = `INCONCLUSIVE` (values not in structured args).

---

## 5. G1 — Estrutura de produto (reword)

### QUESTION
`Mostre a árvore de componentes e relações do item 90260921.`
Prior turns: empty (independent reword, not conversation continuity).

### MODEL_VISIBLE_TOOLS
Identical to §3 — includes `davi.read` (description mentions `get_product_structure`).

### FIRST_TOOL_CALL
- Target: `teo` / `read`
- Argument keys: `entity`, `action`, `params` (object)
- Values: `MISSING_EVIDENCE` (type shapes only)

### TEO_READ_RESULT (first call)
Owner JSON: `success=false`, message `Erro interno do servidor.`, `error_kind=internal`, `error_type=PluginsRepositoryError`, `error_code=internal`, `status_code=500`.

### SUBSEQUENT_TOOL_CALLS

| # | Specialist | Tool | Result (sanitized) |
|---|---|---|---|
| 1 | teo | read | 500 PluginsRepositoryError |
| 2 | teo | get_context | success; entity catalog includes `decomposition_tree` |
| 3 | teo | analyze | 404 — matrix scope not found |
| 4 | teo | read | 404 — process not found |
| 5 | teo | analyze | 500 PluginsRepositoryError |
| 6 | vista | read | 422 `UNKNOWN_ACTION` product_guide/`get` |
| 7 | vista | read | 422 `UNKNOWN_ACTION` product_guide/`search` |

### DAVI_STRUCTURE_CAPABILITY_AVAILABLE
**YES** on model-visible surface (`davi.read` description lists `get_product_structure`). Confirmed by P1 control in same evaluation.

### GET_PRODUCT_STRUCTURE_INVOKED
**NO** on G1 — no `davi.read` / `get_product_structure` wire call observed.

### PROGRESS_DECISIONS
Observed projections: predominantly `SOURCE_UNAVAILABLE` / `NO_PROGRESS`; one `DISCOVERY_ONLY` on teo/get_context; one `NOT_APPLICABLE`. No citable BOM progress.

### FINALIZATION / UNCOVERED_IDENTIFIERS

- Grounding: `NON_GROUNDED`
- Declared status: `insufficient`
- Limitations include: `insufficient_evidence`, `identifier_coverage_incomplete`, **`uncovered_identifier:90260921`**
- Final prose: authorized queries did not yield sufficient evidence

### FIRST_MATERIAL_DIVERGENCE
**PROVEN vs P1:** G1 first call = `teo.read`; P1 first call = `davi.get_context`.

### ROOT_CAUSE_STATUS
**PROVEN (capability/specialist selection class):** single-turn misrouting of product-structure reword toward TEO hierarchy language; DAVI structure path never taken. Concrete TEO entity/action strings = `INCONCLUSIVE` (type-only args). Continuity failure = **NOT applicable** (no prior turns).

---

## 6. P1 — Controle positivo

### QUESTION
`Qual é a estrutura do produto 90260921?`

### MODEL_VISIBLE_TOOLS
Identical to §3.

### DAVI_GET_CONTEXT
- Wire #1: `davi` / `get_context`, key `action`
- Snippet: Context resolved; structured `action=catalog`, `eligible_action_count=97`, `catalog_version=30`
- Progress: `DISCOVERY_ONLY` (not business evidence)

### DAVI_READ / STRUCTURE_RESULT
- Wire #2: `davi` / `read`, keys `capability`, `arguments`
- Structured capability: **`get_product_structure`**, status `ok`, shape `hierarchy`
- Progress: `NEW_INFORMATION`, `evidence_citable=true`, `authoritative_root_code=90260921`
- Owner head (sanitized): product `90260921` / description present / component `10020003` with quantity — BOM returned

### OWNER_RESULT_INCOMPLETE / EVIDENCE_REFS / FINALIZATION

- Grounding: `GROUNDED`
- Declared status: `partial`
- Limitations: `owner_result_incomplete`, `coverage_unknown`, declared unmet for additional composition detail, `declared_status_overridden`
- Evidence refs in declared answer: `[1]`

P1 proves the DAVI structure path works under the same model/config/toolset as G1.

---

## 7. Comparison matrix

| Elemento | P1 | P3 | G1 |
|---|---|---|---|
| Objetivo | Estrutura/BOM produto 90260921 | Formatos de visualização disponíveis | Árvore de componentes/relações 90260921 (reword) |
| Primeira ferramenta | `davi.get_context` | `vista.read` | `teo.read` |
| Capability / remote | get_context → read/`get_product_structure` | read (VISTA) then knowledge (TEO) | read/analyze/get_context (TEO) then VISTA read |
| Argumentos | keys observed; capability value proven in result | keys `entity`,`action`; values MISSING; 422 proves wrong shape | keys observed; values MISSING; TEO domain inferred from errors |
| Resultado do owner | BOM hierarchy ok | guidance dashboard (not format catalog) | failures 500/404/422; no BOM |
| Progresso | DISCOVERY_ONLY → NEW_INFORMATION | NO_PROGRESS… → NEW_INFORMATION (knowledge) | mostly NO_PROGRESS |
| Outcome | GROUNDED partial + coverage_unknown | GROUNDED partial + coverage_unknown | NON_GROUNDED + uncovered 90260921 |
| Primeira divergência | (controle) | vs esperado analyze/catalog: **vista.read 422** | vs P1: **teo.read** first |

---

## 8. Evidence vs hypothesis

| Claim | Status |
|---|---|
| Tool surface included `teo.analyze` and `davi.read` during P3/G1 | **PROVEN** |
| P3 never called `teo.analyze` | **PROVEN** |
| P3 first call was `vista.read` ending in HTTP 422 validation | **PROVEN** |
| Exact P3 first-call entity/action string values | **INCONCLUSIVE** / `MISSING_EVIDENCE` |
| G1 never invoked `get_product_structure` | **PROVEN** |
| G1 failed because capability absent from toolset | **FALSE** (capability present; P1 used it) |
| G1 is a conversation-continuity failure | **FALSE** (empty prior) |
| `coverage_unknown` on GROUNDED partial is F4/finalize boundary | **PROVEN_BY_PRIOR_CONTRACT** + observed limitations |
| EVALUATED_SHA recorded in session meta | **MISSING_EVIDENCE** |

---

## 9. Sanitization review

- No secrets, tokens, passwords, or env dumps included.
- No full raw JSONL committed.
- Owner business snippets limited to heads needed for causal proof.
- Argument values not fabricated where missing.
- `RAW_TRACES_COMMITTED=NO`

---

## 10. Stage status after publication

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT1_REWORK_BUDGET_EXHAUSTED=YES
INT2_AUTHORIZED=NO
T3_AUTHORIZED=NO
PRODUCTION_DEPLOY=NOT_AUTHORIZED
FUNCTIONAL_CODE_CHANGED=NO (this persistence task)
MODEL_CALLS=0
NEXT=COORDINATION_INT1_PUBLISHED_CAUSAL_REPORT_REVIEW
```

Publishing this report does **not** accept INT-1. Independent coordination review follows.

## Related

Doc **295** records the subsequent instruction-isolation A/B; this doc 294 remains the historical causal eval of `or-qwen14b-35aaf1a4174b` and must not be overwritten.
