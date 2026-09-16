# DAVI READ Governance Ratification — DAVI-GOV-READ-001

> **Artifact status:** `SUPERSEDED_IN_PART` by [`DAVI-READ-AUTHZ-REBASELINE-001`](./davi-read-authz-policy-rebaseline-001.md)
> **Task:** `DAVI-GOV-READ-001` (historical ledger — preserved)
> **Does not prove runtime.**

```text
This ledger ≠ runtime allowlist
Historical PENDING_RATIFICATION packs whose sole premise was
branch AuthZ / per-family external approval / taxonomy absence
are SUPERSEDED by DAVI-READ-AUTHZ-REBASELINE-001.
```

Companion machine-readable summary: [`davi-read-governance-ratification-001.json`](./davi-read-governance-ratification-001.json)

---

## SUPERSESSION (DAVI-READ-AUTHZ-REBASELINE-001)

| Decision ID | Status |
|---|---|
| `DAVI-GOV-STOCK-001` | **SUPERSEDED** — branch is query filter; DAVI must not invent filial AuthZ |
| `DAVI-GOV-EXT-001` … `DAVI-GOV-EXT-010` | **SUPERSEDED** when sole blocker was missing per-family DAVI approval |
| `DAVI-GOV-CLASS-001` … `DAVI-GOV-CLASS-003` | **SUPERSEDED** when sole blocker was taxonomy absence |
| `DAVI-GOV-TAX-001` | Remains optional future taxonomy work — **not** a universal READ gate |

Canonical AuthZ policy: [`davi-read-authz-policy-rebaseline-001.md`](./davi-read-authz-policy-rebaseline-001.md)

Runtime eligibility after rebaseline is defined by allowlist v5 + regenerated inventory — not by this historical pack.

---

## 0. Baseline (historical at GOV-001)

| Item | Value | State |
|---|---|---|
| HEAD at analysis | `9ff48fc44cf6f5d95bb3d73b96836b0c6de9721c` | PROVEN |
| `DAVI_ELIGIBLE_READ` | 1 (`search_products`) | PROVEN |
| MCP tools | 3 | PROVEN |
| Coverage decision | `DAVI-DYNAMIC-READ-005` = `PROMOTE_ZERO_NEW_OPERATIONS` | ACCEPTED |
| Inventory | 703 ops / 506 GET | PROVEN |

Blocker distribution (unchanged; from `davi-governed-read-coverage-005.json`):

```text
NEEDS_EXTERNAL_PROCESSING_APPROVAL = 316
NEEDS_NESTED_PROJECTION_SUPPORT    = 70
NEEDS_DATA_CLASSIFICATION          = 60
NEEDS_BRANCH_AUTHZ_EVIDENCE        = 1
(+ out-of-scope buckets not addressed here)
```

---

## 1. Governance model found

### What exists (PROVEN / PARTIAL)

| Concept | Status | Evidence |
|---|---|---|
| Product Master V1 **data slice** for external MCP/GPT | PROVEN | `API-DELPI-GPT-004A.2` → fields `product_code`, `description`, `group_category`; `APPROVED_WITH_RESTRICTIONS`; refs in `custom-gpt-actions.md`, `external_capabilities/constants.py`, allowlist |
| Allowlist as **execution gate** for dynamic READ | PROVEN | `davi_external_read_allowlist.json` v4 |
| GPT Actions V1 freeze (catalog + search only) | PROVEN | `custom-gpt-actions.md` Scope V1; stock/BOM/production/pricing/finance/sales **out of scope** |
| Inventory gate statuses | PROVEN | `dynamic_information/constants.py` + generated inventory |
| Privacy/LGPD for **on-prem chat LLM** | PARTIAL | ROPA/Ollama on-prem; **no** OpenAI/MCP/DAVI cloud data policy |
| Formal taxonomy PUBLIC/CONFIDENTIAL/RESTRICTED/MODEL_* | NOT_FOUND | Only `INTERNAL` appears on approved slice |
| Named human/org **governance owner** per family | NOT_FOUND | README cites Architecture/Coordination for baseline; no per-family owner registry |
| Legacy GPT Action exposure of detail/stock/BOM | PROVEN absent | Only `gpt_get_catalog` + `gpt_search_products` |

### Independent axes (mandatory)

```text
DATA CLASSIFICATION
≠
EXTERNAL PROCESSING APPROVAL
≠
BACKEND AUTHZ
≠
MCP TOOL EXISTENCE
≠
HTTP GET EXISTENCE
```

`search_products` approval **does not transfer** to other operationIds (allowlist + coverage-005).

---

## 2. Owners

| Role | Finding | State |
|---|---|---|
| Technical execution owner (Product routes / use cases) | `api-delpi` Product bounded paths (`product_routes.py`, application use cases, TOTVS repos) | PROVEN |
| Technical AuthZ owner (HTTP) | `API_DELPI_ACCESS` (`api-delpi.access`) for most product GETs; `ENGINEERING_LMP_ACCESS` for search | PROVEN |
| Identity | Keycloak | PROVEN |
| Business governance owner (external processing / classification / exposure) | **Not named** in authorities reviewed | PENDING_OWNER_DECISION |
| Architecture/Coordination | Product baseline authority for DAVI architecture docs | PARTIAL (process owner, not data-family approver) |

---

## 3. Family matrix (high-value)

Legend for EXTERNAL / CLASSIFICATION:

- `PROVEN_*` = authority exists for that exact family/slice
- `PENDING_OWNER_DECISION` = no authority to approve or forbid
- `NOT_APPROVED` only when an authority **explicitly** forbids (GPT V1 “out of scope” is **LEGACY_EVIDENCE** for GPT Actions surface, not automatic DAVI forever-forbid without owner confirmation for MCP dynamic path)

### PRODUCT MASTER (search)

| Field | Value |
|---|---|
| BUSINESS NEED | Locate product by code/description/group |
| DOMAIN / TECH OWNER | api-delpi Product |
| AUTHORITATIVE SOURCE | TOTVS product master via search use case |
| DATA CLASSIFICATION | `INTERNAL` (allowlist) | PROVEN for this slice |
| EXTERNAL PROCESSING | `APPROVED_WITH_RESTRICTIONS` (`API-DELPI-GPT-004A.2`) | PROVEN |
| BACKEND AUTHZ | `ENGINEERING_LMP_ACCESS` | PROVEN |
| BRANCH SCOPE | none | PROVEN |
| MODEL-SAFE PROJECTION | flat 3 fields | PROVEN |
| PRIMARY BLOCKER | none (already eligible) | — |
| STATE | CURRENT PROVEN V1 |

### PRODUCT DETAIL (`get_product_detail`)

| Field | Value |
|---|---|
| HTTP AuthZ | `API_DELPI_ACCESS` | PROVEN |
| Shape | `product_snapshot` (nested) | PROVEN |
| Classification of **same 3 master fields** | may align with INTERNAL slice | PARTIAL — not independently ratified for this operation |
| External processing | not independently ratified; 004A.2 covers **search** data slice — **extension to detail op unclear** | PENDING_OWNER_DECISION `DAVI-GOV-EXT-001` |
| Nested projection | needed if exposing nested tree; **not** needed if only flat same-slice fields extracted | CONDITIONAL |
| BLOCKER STACK | 1) `DAVI-GOV-EXT-001` external slice scope · 2) projection mechanism (flat same-slice vs nested) · 3) exclude non-approved fields |
| NEXT AFTER CURRENT | If EXT-001 = APPROVE same slice flat → implement allowlist entry **without** nested abstraction |
| Inventory primary today | `NEEDS_NESTED_PROJECTION_SUPPORT` (overstates nested as sole blocker) | drift noted |

### STRUCTURE / BOM (`get_product_structure`, `get_product_structure_exclusivity`)

| Field | Value |
|---|---|
| HTTP AuthZ | `API_DELPI_ACCESS` | PROVEN |
| Shape | hierarchy / playbook_report | PROVEN |
| GPT V1 | BOM **out of scope** | LEGACY_EVIDENCE (not automatic forever veto) |
| Classification | NOT_FOUND independent | PENDING_OWNER_DECISION (bundle with EXT) |
| External processing | NOT_FOUND | PENDING_OWNER_DECISION `DAVI-GOV-EXT-002` |
| Nested | required for meaningful BOM | NEEDS_TECHNICAL_CAPABILITY **after** EXT-002 |
| BLOCKER STACK | PRIMARY=`DAVI-GOV-EXT-002` · SECONDARY=nested projection · TERTIARY=classification if owner separates |
| If nested shipped tomorrow without EXT-002? | **Still blocked** | |

### STOCK (`get_product_stock`)

| Field | Value |
|---|---|
| Canonical source | `ProductStockRepository` / SB2; formula `available = QATU - QEMP - RESERVA` | PROVEN |
| HTTP AuthZ today | `API_DELPI_ACCESS` only; `branch` optional filter | PROVEN gap |
| Branch AuthZ | **not** applied on this route | PROVEN gap |
| Sibling pattern | `BranchAccessGate` + `estoque-seguranca.view.filial-*` for **safety stock** | PROVEN (different capability — do not invent reuse without owner) |
| Product-stock business permission family | NOT_FOUND (no `product.stock` / stock-read permission for this route) | PENDING_OWNER_DECISION `DAVI-GOV-STOCK-001` |
| External processing | NOT_FOUND; GPT V1 stock out of scope | PENDING_OWNER_DECISION `DAVI-GOV-EXT-007` |
| Classification | NOT_FOUND independent; response includes quantities + `cost_center` | PENDING / may need CLASS if cost_center exposed |
| Proposed minimum projection (needs ratification) | `product_code`, `branch`, `warehouse`, `available_quantity` (optional: `current_quantity`) — **exclude** `cost_center` by default | NEEDS_RATIFICATION |
| BLOCKER STACK | 1) STOCK-001 AuthZ policy · 2) EXT-007 · 3) projection ratification · 4) wire BranchAccessGate |
| STOCK_AUTHZ_IMPLEMENTATION_GATE | **NOT_READY** | missing proven stock-read + branch permission **policy for this capability** |

### PRODUCTION (`get_product_production_status`)

| Field | Value |
|---|---|
| HTTP AuthZ | `API_DELPI_ACCESS`; optional branch filter | PROVEN |
| Shape | playbook_report nested | PROVEN |
| External / classification | NOT_FOUND | PENDING `DAVI-GOV-EXT-006` |
| Nested | required | secondary |
| BRANCH | optional filter; no proven requested-branch AuthZ | PARTIAL gap |

### FACTORY STATUS (`get_product_factory_status`)

| Field | Value |
|---|---|
| Composite | structure + raw_material_stock + production + shipping | PROVEN |
| Rule | eligibility ≤ most restrictive section | PROVEN (platform rule) |
| Primary | blocked by stock + production + structure sections | depends on EXT-002, EXT-006, EXT-007, STOCK-001 |
| Cannot approve factory alone | PROVEN |

### SUPPLIERS / CUSTOMERS / PURCHASES

| Op | Ext-proc | Classification | AuthZ | Projection | Decision |
|---|---|---|---|---|---|
| `get_product_suppliers` | PENDING | NOT_FOUND | `API_DELPI_ACCESS` | paged_list — minimize IDs/names only if approved | `DAVI-GOV-EXT-003` |
| `get_product_customers` | PENDING | NOT_FOUND (higher privacy risk) | `API_DELPI_ACCESS` | same | `DAVI-GOV-EXT-004` |
| `get_product_purchases` | PENDING | NOT_FOUND | `API_DELPI_ACCESS` | exclude price fields unless CLASS+EXT | `DAVI-GOV-EXT-005` |

Status if asked today without owner: **PENDING_OWNER_DECISION** (not NOT_APPROVED — no explicit forbid authority for MCP dynamic; GPT V1 out-of-scope is LEGACY_EVIDENCE).

### PRICING / COST

| Ops | Status |
|---|---|
| `get_product_pricing`, `get_product_purchase_price_history`, `get_product_raw_material_price_intelligence`, `get_product_cost_impact_simulation` | CLASSIFICATION = **PENDING_OWNER_DECISION** `DAVI-GOV-CLASS-001` (do **not** infer CONFIDENTIAL) |
| External processing | PENDING (after or bundled with CLASS) `DAVI-GOV-EXT-010` |
| AuthZ | `API_DELPI_ACCESS` | PROVEN HTTP |
| Default | KEEP quarantined until CLASS + EXT ratified |

### PRODUCT SUMMARY (`get_product_summary`)

Composite product + stock sample + prices → limited by pricing CLASS + stock AuthZ + EXT. Decision: `DAVI-GOV-CLASS-002` (or derive from CLASS-001 + STOCK + EXT). **No composite bypass.**

### SALES

| Ops | Status |
|---|---|
| `get_product_sales_*`, commercial OTD family | `NEEDS_EXTERNAL_PROCESSING_APPROVAL` | PENDING `DAVI-GOV-EXT-008` |
| GPT V1 | sales out of scope | LEGACY_EVIDENCE |

### OTHER (dashboards / KPIs / quality / finance indicators)

| Family | Dominant blocker | Note |
|---|---|---|
| Strategic indicators / dashboards | EXT or CLASS (cost/% financial) | No clearer approval than Product Detail; **do not prioritize** without owner |
| Quality labels / action plans | EXT (+ PII/audit risk) | PENDING; not READY |
| Engineering LMP dashboards | EXT | PENDING |
| Financial indicators | CLASS | `DAVI-GOV-CLASS-003` |

No non-product family found with **PROVEN** external-processing authority besides Product Master search slice.

---

## 4. Queues (objective)

### READY_FOR_IMPLEMENTATION

```text
(empty for DAVI eligibility expansion)
```

No operation other than `search_products` has all governance gates PROVEN.
Do **not** implement allowlist growth until DECISION_IDs below are `RATIFIED`.

### PENDING_OWNER_DECISION

See §5 Decision Pack (`DAVI-GOV-*`).

### NEEDS_TECHNICAL_CAPABILITY (only after related GOV RATIFIED)

| Capability | Prerequisite GOV | Technical work |
|---|---|---|
| Nested projection abstraction | ≥2 ops with EXT+CLASS+AuthZ PROVEN and nested as sole remaining blocker | Generic path allowlist projector |
| Stock branch AuthZ wiring | `DAVI-GOV-STOCK-001` RATIFIED with exact permission codes | Apply `BranchAccessGate` (or equivalent) on `get_product_stock` |
| Flat same-slice detail | `DAVI-GOV-EXT-001` Option C/A | Allowlist + approvedResponseFields only |

### OUT_OF_SCOPE (this governance task / permanent architecture)

```text
STREAM_BINARY / GENERIC_SQL / WRITE / ADMIN / DESTRUCTIVE
MCP tool proliferation
route-by-route MCP tools
```

---

## 5. Gates

### NESTED_PROJECTION_ABSTRACTION_GATE = **FAIL**

```text
real consumers with EXT+CLASS+AuthZ PROVEN and ONLY nested remaining = 0
```

Therefore: do **not** recommend implementing generic nested projection now.
Contract sketch deferred until gate becomes `PASS_CANDIDATE` (≥2 real consumers).

Conceptual target (not approved for build):

```text
approvedProjection paths
→ recursive fail-closed drop of unknown fields/objects
→ bounded arrays/depth
→ no model-supplied JSONPath
```

### STOCK_AUTHZ_IMPLEMENTATION_GATE = **NOT_READY**

```text
reason =
  no proven product-stock business permission family for get_product_stock
  + no proven requested-branch AuthZ policy bound to this route
  + sibling safety-stock permissions must not be invented as substitute
```

### CLASSIFICATION_GATE (pricing/cost) = **PENDING_OWNER_DECISION**

### EXTERNAL_PROCESSING_GATE (non-search families) = **PENDING_OWNER_DECISION** / PARTIAL authority only for Product Master search slice

---

## 6. Decision Pack

Status values for each item: `PROPOSED` → `PENDING_RATIFICATION` → `RATIFIED` (owner only).

### DAVI-GOV-EXT-001

| | |
|---|---|
| SCOPE | Product Master fields via `get_product_detail` |
| EXACT QUESTION | Does `API-DELPI-GPT-004A.2` (or successor) authorize exposing **only** `product_code`, `description`, `group_category` from `get_product_detail` to DAVI/MCP/OpenAI? |
| CURRENT STATE | Detail quarantined; search slice APPROVED_WITH_RESTRICTIONS |
| IF APPROVED | Allowlist entry + flat projection; nested gate not required for this slice |
| REMAINS BLOCKED | Any other detail fields; nested BOM/etc. |
| DATA EXPOSED | Same as search (minimum) |
| IDENTITY | End-user OAuth / user parity |
| BACKEND AUTHZ | `API_DELPI_ACCESS` (route) — confirm if ENGINEERING_LMP parity required |
| MIN PROJECTION | `product_code`, `description`, `group_category` |
| RISK | Low incremental vs search if strictly same slice; existence oracle via detail path |
| EVIDENCE | `constants.py` FIELD_MAP; `custom-gpt-actions.md`; allowlist |
| OWNER | unresolved (PENDING) |
| OPTIONS | A APPROVE_WITH_RESTRICTIONS (same slice) · B KEEP_QUARANTINED · C APPROVE smaller subset |
| STATUS | `PENDING_RATIFICATION` |

### DAVI-GOV-EXT-002

| | |
|---|---|
| SCOPE | Product Structure / BOM (`get_product_structure`, optionally exclusivity) |
| EXACT QUESTION | May BOM hierarchy (codes, quantities, depth-bounded components) be processed by DAVI external model path? |
| CURRENT | Quarantined; GPT V1 BOM out of scope (LEGACY_EVIDENCE) |
| IF APPROVED | Still needs nested projection + classification confirmation |
| REMAINS | exclusivity playbook, factory composite |
| DATA | component codes, quantities, levels (exact field list TBD at ratification) |
| AUTHZ | `API_DELPI_ACCESS` |
| MIN PROJECTION | NEEDS_RATIFICATION — propose only existing structure fields |
| OWNER | unresolved |
| OPTIONS | A APPROVE_WITH_RESTRICTIONS · B KEEP_QUARANTINED · C smaller flat component list only |
| STATUS | `PENDING_RATIFICATION` |

### DAVI-GOV-EXT-003 / 004 / 005

| ID | Scope | Question (summary) |
|---|---|---|
| EXT-003 | suppliers | Approve supplier relational list for external model? |
| EXT-004 | customers | Approve customer relational list for external model? (privacy) |
| EXT-005 | purchases | Approve purchase history **without** unit prices? or with prices (then CLASS)? |
| OPTIONS | A APPROVE_WITH_RESTRICTIONS · B KEEP_QUARANTINED · C smaller projection |
| STATUS | `PENDING_RATIFICATION` |
| OWNER | unresolved |

### DAVI-GOV-EXT-006

Production status family — approve shop-floor OP/appointment summaries for external model? Options A/B/C. Nested secondary. STATUS `PENDING_RATIFICATION`.

### DAVI-GOV-EXT-007

Stock quantities for external model (independent of AuthZ wiring). Options A/B/C. Min projection proposal: `product_code`, `branch`, `warehouse`, `available_quantity`. Exclude `cost_center` unless separately approved. STATUS `PENDING_RATIFICATION`.

### DAVI-GOV-EXT-008

Sales / commercial OTD family for DAVI. STATUS `PENDING_RATIFICATION`.

### DAVI-GOV-EXT-009

Operational KPI / dashboard indicators (non-financial). Batch family decision — same owner/risk only if owner confirms. STATUS `PENDING_RATIFICATION`.

### DAVI-GOV-EXT-010

Pricing/cost **external processing** (after or with CLASS-001). STATUS `PENDING_RATIFICATION`.

### DAVI-GOV-CLASS-001

| | |
|---|---|
| SCOPE | Pricing / purchase price / cost intelligence / cost simulation |
| EXACT QUESTION | What formal classification applies to these fields for external AI processing? |
| CURRENT | `NEEDS_DATA_CLASSIFICATION`; no PUBLIC/CONFIDENTIAL taxonomy in repo |
| OPTIONS | A assign classification label + allow with restrictions · B KEEP_QUARANTINED · C approve non-monetary metadata only |
| DO NOT | Infer CONFIDENTIAL from heuristics |
| STATUS | `PENDING_RATIFICATION` |

### DAVI-GOV-CLASS-002

Product summary composite — only after stock+pricing sections decided. STATUS `PENDING_RATIFICATION`.

### DAVI-GOV-CLASS-003

Financial strategic indicators (EBITDA, fixed cost, etc.). STATUS `PENDING_RATIFICATION`.

### DAVI-GOV-STOCK-001

| | |
|---|---|
| SCOPE | Business + branch AuthZ policy for `get_product_stock` |
| EXACT QUESTION | Which permission codes must the authenticated user hold for (a) stock read and (b) each requested branch `01`/`02`? |
| CURRENT | Route uses only `API_DELPI_ACCESS`; branch is filter |
| IF APPROVED | STOCK_AUTHZ_IMPLEMENTATION_GATE → READY; implement BranchAccessGate wiring |
| REMAINS | EXT-007 still required for DAVI eligibility |
| EVIDENCE | `product_routes.py` stock(); `branch_access_gate.py`; safety-stock perms **sibling only** |
| OWNER | unresolved |
| OPTIONS | A define new product-stock filial perms · B reuse an existing named family (must cite codes) · C keep API_DELPI_ACCESS-only (document residual risk) · D KEEP route as-is and keep DAVI quarantine |
| STATUS | `PENDING_RATIFICATION` |

### DAVI-GOV-TAX-001 (optional platform)

Adopt formal data classification taxonomy for DAVI sources? STATUS `PENDING_RATIFICATION`. Enables consistent CLASS decisions.

### Pre-existing

| ID | Note |
|---|---|
| `MCP_RATE_POLICY` | Already `PENDING_OWNER_DECISION` (wider publication) — not READ coverage |

---

## 7. Legacy GPT Actions evidence

```text
LEGACY_EVIDENCE = gpt_get_catalog + gpt_search_products only
NOT exposed historically: detail, summary, stock, BOM, production, pricing, finance, sales
```

Legacy ≠ current MCP dynamic authority. Do not promote from legacy alone. Do not treat “out of scope” text as automatic `NOT_APPROVED` forever for DAVI without owner confirmation — record as LEGACY_EVIDENCE informing risk.

---

## 8. Implementation briefs (post-ratification only)

### Brief A — after EXT-001 Option A/C

1. Add `get_product_detail` to allowlist with `approvedInputFields`/`approvedResponseFields` = same slice (or subset).
2. No new MCP tool.
3. Prefer generic catalog path + flat projection.
4. Tests: discovery aliases, quarantine neighbors, 403, field parity, 3-tool invariant.
5. Do **not** enable nested fields.

### Brief B — after STOCK-001 + EXT-007

1. Wire proven permission map on `get_product_stock`.
2. Enforce requested-branch AuthZ.
3. Allowlist + min projection excluding cost_center unless approved.
4. Tests: branch deny/allow, 403≠empty, top_k.

### Brief C — nested abstraction

Only if Abstraction Gate becomes PASS_CANDIDATE (≥2 consumers). Spec then; implement later.

---

## 9. Explicit non-changes (this task)

```text
DAVI_ELIGIBLE_READ remains 1
MCP tools remain 3
allowlist.operations approvals unchanged
no nested projection code
no stock AuthZ code
no Keycloak changes
no semanticAliases for quarantined ops
```

---

## 10. Next step

```text
Architecture / Product Ratification of exact DECISION_IDs
→ mark RATIFIED with owner + date + chosen OPTION
→ Cursor implementation batch only for RATIFIED + READY items
→ deploy
→ live regression
```
