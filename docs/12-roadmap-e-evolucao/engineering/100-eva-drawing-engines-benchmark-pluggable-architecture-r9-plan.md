# 100 — EVA Drawing Intelligence R9: benchmark competitivo e arquitetura plugável de motores

**Estado:** PLANNED / ARCHITECTURE_DECISION_REQUIRED para introduzir contratos/owner/serviços ou egress novos. **Data:** 2026-11-02. **Owner proposto:** Engineering API / Portal Engenharia; Engenharia aprova anotação técnica; API DELPI mantém bytes e BOM oficiais, Core controla AuthZ, Keycloak AuthN, EVA interpreta DRAFT/CANDIDATE. **Referências:** docs 93–99, AGENTS.md, ENG-REV-001. **Esta publicação é um plano, não teste executado nem aprovação de uso cloud.**

## 1. Decisão de investigação

Interromper proliferação de heurísticas R8 para layout e executar benchmark imparcial usando **o mesmo corpus, páginas, hardware e métricas**. Avaliar plug-ins sem importar dependências de fornecedores em Domain/Application. Baseline `engineering_heuristics_r823` também concorre. Não alterar `drawing_understanding.v1` nem criar sétima tool MCP; qualquer runtime novo fica opt-in/read-only/feature-gated, com rollback.

**Famílias e pré-requisitos:**
- **A — Local/offline (executáveis após inventário de licença e aprovação de infra):** PP-StructureV3 (layout, OCR/tabela), Docling (layout + TableFormer), baseline R8.2.3 OpenCV/PaddleOCR, e combinação seletiva.
- **B — SaaS/externos (somente prospectivos):** Werk24 (API especializada em desenho mecânico), Azure AI Document Intelligence (Layout), Google Document AI Layout Parser. **NÃO transmitir nenhum PDF DELPI, nem exemplos internos, sem aprovação documentada de owner de dados + InfoSec/DPO + contrato de processamento, região/residência/retenção + credenciais/vault + orçamento + egress allowlist.** Testar primeiro em fixtures públicas/sintéticas, ou marcar OWNER_BLOCKED/TEST_NOT_RUN. A cloud usa outro denominador de privacidade/custo, não confundir com benchmark de PDFs DELPI autorizado.
- **C — Treináveis para etapas futuras:** detector de símbolos/objetos como RF-DETR ou equivalente com licença de uso comercial revisada. **Não** assumir que modelos genéricos já reconhecem balões/cotas/chicotes; sem ground truth anotado, apenas SPIKE/prova de viabilidade.

Verificar versão, pesos, licença, OCR model assets, Python/Paddle/Torch dependencies, CPU/GPU, download e egress de **cada** motor. Download controlado só na etapa de provisionamento, execução sem egress. Não instalar dependências conflitantes no processo principal da Engineering API.

Documentação técnica pública de referência:
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline_usage/PP-StructureV3.en.md
- Docling models: https://github.com/docling-project/docling/blob/main/docs/usage/model_catalog.md
- Docling: https://docling.ai/
- Werk24: https://www.werk24.io/documentation
- Azure: https://learn.microsoft.com/azure/ai-services/document-intelligence/prebuilt/layout
- Google: https://docs.cloud.google.com/document-ai/docs/layout-parse-chunk
- Roboflow licensing: https://roboflow.com/licensing

## 2. Arquitetura: Ports & Adapters, NÃO um framework novo prematuro

```text
Core delegated identity → Engineering API (policy + orchestration)
                       → authorized PDF gateway (API DELPI) → bounded render/page manifest
                       → DocumentPerceptionPort [candidate contract owner: Engineering API]
                         ↳ Existing OpenCV/PaddleOCR baseline adapter
                         ↳ PP-StructureV3 isolated adapter (local)
                         ↳ Docling isolated adapter (local)
                         ↳ Werk24 external adapter (OFF / approval required)
                         ↳ Azure external adapter (OFF / approval required)
                         ↳ Google external adapter (OFF / approval required)
                       → evidence normalization and coordinate validation
                       → comparison / optional independent fusion
                       → Engineering interpretation / BOM gated via official API DELPI
                       → DRAFT/CANDIDATE with provenance and per-page coverage
                       → existing analyze(product.drawing_understanding) (gated consumer)
```

**Abstraction Gate:** use one narrow `DocumentPerceptionPort` only if 2 working local consumers prove need. Until then, implement isolated research harness with explicit JSON exchange and no new runtime service. Never let Domain/Application import provider SDKs, network or OpenCV. No direct filesystem/file-server runtime authority. External adapters cannot receive signed URLs/JWT, secrets in prompts/logs or unrestricted PDFs.

**Proposed minimal common schema, versioned `drawing_perception_candidate.v1` (not a new source of truth):**

```json
{
  "schema": "drawing_perception_candidate.v1",
  "document": {"sha256": "...", "product_code": "...", "source_revision": null},
  "run": {"provider_id": "ppstructurev3", "provider_version": "...", "model_digest": "...", "config_digest": "...", "runtime_sha": "...", "execution_mode": "local"},
  "coverage": {"total_pages": 18, "requested_pages": [1], "processed_pages": [1], "failed_pages": [], "sampled": true},
  "pages": [{
    "page_number": 1, "width_px": 2339, "height_px": 1653, "dpi": 150, "rotation_deg": 0,
    "regions": [{"id":"r1","type":"component_table_candidate","bbox_px":[1,2,3,4],"source_label":"table","confidence":null,"evidence_ids":[]}],
    "tables":[{"region_id":"r1","columns":[],"rows":[],"cells":[{"row":0,"col":0,"text":"...","bbox_px":[1,2,3,4],"evidence_ids":[]}]}],
    "texts":[], "figures":[], "unclassified":[], "limitations":[]
  }],
  "quality": {"status":"EVAL_PENDING","limitations":[]},
  "authority": {"candidate_only":true,"bom_writes":false,"approved":false}
}
```

Mandatory semantics: **1-based page numbers**, coordinate reference and transforms, token/region/cell IDs, source document hash, provider and model versions, exact config, confidence type (do not conflate model probability with engineering correctness), page failures, null/UNKNOWN when not supported. Provider native payload held only in access-controlled temporary benchmark evidence. Normalize nomenclature: generic `table` IS NOT automatically a BOM table; `header` IS NOT automatically a drawing title block. No fabricated `revision`, `dimension`, `quantity`, `balloon`, `component_code`.

## 3. Adapter contract and execution modes

Interface proposal:
- `capabilities()`: supports_pdf, raster, multipage, selected_pages, tables, cells, symbols, coordinates, offline, needs_gpu, max_pages, model/license policy
- `analyze_page(page_image_or_authorized_input, page_context, requested_capabilities, budget)`: returns normalized page perception candidate + errors; **do not pass raw credential**, path/URL supplied by client, or external page bytes unless explicitly approved.
- Optional `analyze_document` only if required for multi-page semantic models, with bounded page policy.
- standard errors: `UNSUPPORTED_INPUT`, `UNAVAILABLE`, `TIMEOUT`, `RESOURCE_LIMIT`, `MODEL_NOT_PROVISIONED`, `POLICY_DENIED`, `INCOMPLETE_COVERAGE`, `INVALID_PROVIDER_OUTPUT`.
- timeout, memory/CPU, concurrency, cancellation, circuit-breaker, engine allowlist and idempotent read-only job key: SHA + pages + provider/model/config versions (subject to permission check each request).
- Authorization before PDF access and before serving cached result; cache keyed by document SHA/revision/access policy, never a substitute for AuthZ.
- benchmarking and normal workflow separate; **shadow runs** do not affect BOM or user-facing conclusions.

## 4. Controlled corpus, gold labels and splits

**Real PDFs (via API DELPI and live delegated authorization, no indiscriminate scan):**
- `90264302` 1p, SHA `f33447b271a3518643559582d79cf54527b85778537cfb1e20a5ccf5d989f0ef`: carimbo/tabela/histórico, client/OV contamination, 643±2/663±2.
- `90264161` 1p, SHA `8d9fe28a19cae334abd6eaa3b0fb13059aecad715672b0dfd6aaf10462b85195`: false full-page table, 15550±50/10000±50, headerless and partial BOM.
- `90263554` 18p PDF benchmark confirmed: sample page 1, a middle page, final page only **after owner authorizes which pages / selection criteria**, then stratify.
- `90264135` 13p confirmed, same approach.
- `90264094` 1p alternative `9026`.
- `10210267-2` scanned non-9026 secondary adversarial, not primary PA benchmark.

**No invented ground truth:** Engenharia labels regions/title block/revision history/table cells/notes/drawing_area and per-page completeness. Provide annotation instruction and blinded holdout; label `UNKNOWN` for ambiguous. Splits by *document/family/customer/template*, not page only (avoid leakage); samples of same drawing must not contaminate train and test. Record source file hash+revision+page, annotation approver/date. Benchmark without signed GT can report exploratory manual error counts only, not accuracy/recall.

**Synthetic/public fixtures:** independent of DELPI, use for SaaS smoke prior to privacy approval, rotated/scan/wire harness/no table/multiple tables/layout distribution.

## 5. Fair benchmark matrix and scoring

Each provider/combination must return per-page structured outputs, diagnostic overlays (restricted internal QA), latency, peak RSS, CPU/GPU, licensing/privacy/cost, completeness and failures. No provider-specific relaxed rules. Fix resolution, DPI, preprocessing, time/resource budget, batch, hardware and concurrency or report stratified comparison (different quotas cloud must not be ranked as equal).

**Primary metrics (with GT):**
- Region detection IoU ≥0.5 and ≥0.75: precision/recall/F1 by `title_block,component_table,revision_history,notes,drawing_area,unknown`.
- Table structural correctness: table bbox IoU, header assignment, TEDS/GriTS when appropriate, row/col/cell matching, type accuracy (component_code, quantity, item, description), OCR cell text CER.
- Semantic safety hard gates: **0 accepted client/OV/revision tokens as component codes in test set; 0 parent-product false membership; 0 BOM false `missing`**; if absence cannot be proved => NOT_COMPARABLE.
- Dimension text coverage, false positives, revision pair extraction, page coverage per selected page.
- Throughput p50/p95, RSS peak, failure rate, offline/egress, license, total cost per page, observability, rollback.

Suggested decision (targets to calibrate with Engenharia, NOT claims): hard safety gates mandatory; among passing, weighted score: region 25%, table/cell 30%, engineering extraction 20%, reliability/resources 15%, operational/licensing 10%. Publish raw metrics, confidence intervals/denominators and failure taxonomy; ranking separately for 1-page, multipage-selected, scanned, vector. Never hide non-comparable cloud runs.

**Comparison arms:**
1. R8.2.3 baseline alone.
2. PP-StructureV3 alone (native OCR allowed).
3. Docling/TableFormer alone.
4. R8 native OCR + PP-Structure layout/cells.
5. R8 native OCR + Docling layout/cells.
6. Optional gated pairwise fusion `ppstructurev3+docling`: union/intersection only with explicit conflict policy; disagreement ⇒ abstain/UNKNOWN, NOT majority-vote technical authority.
7. Werk24, Azure, Google **only synthetic/public data until approvals**, then same authorized corpus if explicitly approved.
8. Trainable object detection for balões/símbolos **future R8.4**, do not penalize generic document models for capability absent by design.

## 6. Execution gates, acceptance and reporting

- **G00** verify authorities, git HEAD/status, baseline/deploy SHA, 6 MCP tools; detect current docs numbering; concurrent work isolation.
- **G01** owner+Architecture Decision for contract/consumer/host and egress; inventory overlap before new abstractions.
- **G02** dependency/license/SBOM/model weights provenance/runtime security; CPU/GPU sizing; local offline provisioning without runtime downloads.
- **G03** define normalizer schema, provider envelopes, page and coordinate validation, errors, compatibility.
- **G04** implement local benchmark harness in research isolation (no product-visible switch, read-only) with ppstructurev3/docling/baseline; adapters only after evidence.
- **G05** obtain authorized DELPI bytes and approved annotation samples through official gateway; no direct fileserver. When inaccessible, OWNER_BLOCKED.
- **G06** engineer/label GT: document/page/family splits; blind holdout. Without GT, EVAL_PENDING.
- **G07** run all local arms on exactly same pages with normalizer and constrained resources, capture raw outputs and overlays with safe retention.
- **G08** cloud procurement/privacy assessment; first on public fixtures; DELPI artifacts cannot leave until approved, report `OWNER_BLOCKED`.
- **G09** compare metrics/error cases/costs; provider scorecard and ablation (single vs fusion); report what each cannot detect.
- **G10** design recommendation: single provider, hybrid, or continue baseline; proof before integration. If new owner/authority, `ARCHITECTURE_DECISION_REQUIRED`.
- **G11** optional separate governed integration mission: opt-in, shadow, abort/rollback, fail-closed, unchanged 6 MCP tools and read-only product flow.
- **G12** evidence to GitHub next numbered doc, SHA/tested SHA, artifact hashes, exact provider versions/weights, owner signoff gaps, next bounded step.

**Critical acceptance**: at least two local engines benchmarked or honest environment blocker; four 9026 PDFs used only where authorized; no false results from claims without GT; no SaaS egress without approval; normalized output for independent provider substitution; independent provider failure does not fail existing authenticated EVA flows; no new source of truth, DB ownership or 7th MCP tool; per-provider rollback.

**Expected final report**
```text
TASK: EVA.DRAWING.R9.MULTI_ENGINE.BENCHMARK.PORTS_ADAPTERS
BASE_HEAD: / FINAL_HEAD: / TESTED_SHA: / DEPLOYED_SHA:
AUTHORITY_AND_OWNER_DECISION: / ABSTRACTION_GATE:
PROVIDER_MATRIX: baseline, PPStructure, Docling, Werk24, Azure, Google, RF-DETR exploratory
SECURITY_AND_LICENSE: / EGRESS_APPROVAL: / MODEL_PROVISION:
COMMON_SCHEMA: / NORMALIZATION_TESTS: / CAPABILITIES:
CORPUS_AND_PAGES: / PDF_SHAS: / HOLDOUT_GT_STATUS:
PER_PROVIDER_OUTPUTS_AND_OVERLAYS: / ERRORS:
REGION_SCORE: / TABLE_SCORE: / CELL_SCORE: / DIMENSIONS:
BOM_SAFETY: / RUNTIME_CPU_RAM_P95: / COST_AND_LICENSE:
FUSION_ABLATION: / NO_EXTERNAL_EGRESS:
RECOMMENDED_DEFAULT: / FALLBACK: / ROLLBACK:
MCP_E2E: PASS|TEST_NOT_RUN / DOCUMENT_PATH: / UNRESOLVED:
ARCHITECTURE_DECISION_REQUIRED: / NEXT_BOUNDED_STEP:
```

## 7. Governance and stopping rule

No provider/model is source of truth; outputs are DRAFT. No publication, no training on customer material without explicit permission. OpenAI/cloud model not required. **Stop creating provider-specific heuristics in mainline** until objective benchmark proves improvement. Never claim 'all tools tested' if some cloud tools remain blocked. Advance R8.3 only after semantic BOM fail-closed invariant is verified separately; the benchmark is not production acceptance.
