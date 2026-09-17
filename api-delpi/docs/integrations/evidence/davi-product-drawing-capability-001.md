# DAVI-PRODUCT-DRAWING-CAPABILITY-001 — Evidence

**Artifact class:** `EVIDENCE_NOT_RUNTIME_AUTHORITY`  
**Outcome:** B (JSON catalog + metadata promoted; document transport / analysis PENDING)  
**Verdict (source):** `PASS_WITH_RESIDUAL`

## Freeze decisions

| Capability | Class | Status | Action |
|---|---|---|---|
| `product.drawing.catalog` | READ | PROVEN | Promoted `list_product_drawings` (allowlist v9; `requireArguments=[code]`) |
| `product.drawing.metadata` | READ | PROVEN | Promoted `get_product_drawing` |
| `product.drawing.document` | READ_DOCUMENT | PENDING | HTTP PDF route proven; generic DAVI document transport unproven |
| `product.drawing.analysis` | DERIVED_ANALYSIS | PENDING | AI API workflow PROVEN; blocked on document transport |
| `product.drawing.compare` | DERIVED_ANALYSIS | TARGET | Needs analysis + dual document inputs |
| `product.drawing.batch_analysis` | ORCHESTRATION | TARGET | Needs analysis + document budgets |
| `product.quality.inspection` | READ | DEFER | `DRAWING_ANALYSIS_INSPECTION_CROSSCHECK=DEFERRED` |

## Authority model

- API DELPI drawing use cases = authorized file resolution/access
- File server = document storage (`DRAWING_PDF_LIBRARY_DIR`)
- Protheus / Product use cases = operational facts
- AI API `drawing-analysis-delpi` skill = derived analysis procedure (reuse, do not copy into Agent Instructions)
- Uploaded PDF = `UNTRUSTED_INPUT`
- Automated analysis ≠ engineering approval

## Drawing resolution

Resolver algorithm PROVEN (`DrawingPdfLibraryStorage.find_drawing`): exact `CODE.pdf` → numeric-prefix candidates → rank (prefer exact, then highest `_RNN`, variants).

`CURRENT_DRAWING_RESOLUTION` official/approved semantics = **TO_INVENTORY**. DAVI must say **server-resolved drawing**, never “official/approved revision”, until business owner is proven.

## Document transport gate

- Forbidden: `pdf_base64` / PDF bytes inside `execute_delpi_information` JSON
- MCP tools remain exactly 3
- New binary MCP tool/resource = `ARCHITECTURE_ESCALATION_REQUIRED`
- `get_product_drawing_pdf` = `explicitlyNotApproved` / `NEEDS_GENERIC_DOCUMENT_BOUNDARY`
- `PRODUCT_ANALYSER_DIRECT_PROMOTION = NOT_REQUIRED`

## Model-safe projection

Catalog drops: `summary.library_dir`, `drawing_metadata_path`, `drawing_pdf_path`, absolute paths.  
Metadata drops: filesystem `path` / absolute paths / messages outside allowlist.

## AI API workflow (PROVEN)

- Skill: `minha-delpi-ai-api/app/domain/prompt_policies/drawing-analysis-delpi-skill.md`
- Validation: `drawing_validation.json` / `drawing_validation_rules.json`
- Statuses observed: OK / Pendente / Erro / Erro crítico
- ChatGPT Skill packaging in this repo: **TO_INVENTORY** (no invented `SKILL.md` packaging)

## Counts

| Metric | Before | After |
|---|---|---|
| Allowlist version | 8 | 9 |
| Eligible READ | 15 | 17 |
| MCP tools | 3 | 3 |

## Runtime

SOURCE = PASS_WITH_RESIDUAL (JSON foundation)  
LOCAL TESTS = see test run  
DEPLOY / LIVE / AGENT PREVIEW = `TEST_NOT_RUN`
