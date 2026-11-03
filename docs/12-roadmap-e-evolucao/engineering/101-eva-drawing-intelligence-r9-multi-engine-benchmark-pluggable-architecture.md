# 101 — EVA Drawing Intelligence R9: Multi-Engine Benchmark, Pluggable Architecture & Provider Evaluation

**Status:** arquitetura plugável + contrato `drawing_perception_candidate.v1` + adapters implementados + benchmark executado; deploy verificado; cloud engines `OWNER_BLOCKED`; E2E MCP `TEST_NOT_RUN`. **SHA:** pendente. **Data:** 2026-11-02. Ref: doc 100 (plano).

## 1. Arquitetura (Clean + Ports & Adapters, Abstraction Gate aplicado)

- `perception_contract.py` (Application, pure-python): `drawing_perception_candidate.v1` — provider_id/version, model_version/digest, config_digest, execution_mode, page dims/DPI/rotation, regions/tables/cells/text_blocks/figures/dimension_candidates, provenance, limitations, `error_kind` (fechado), `quality_status` (fechado). `PerceptionEnginePort` Protocol.
- `engine_adapters.py` (Infra): `EvaBaselineEngine` (wraps run_pipeline_isolated+understanding.v1→v1) e `PPStructureEngine` (PPStructureV3→v1). Registry `ENGINES` + `engine_capabilities()` (capability discovery honesto — supports dict por motor).

## 2. Inventário de motores

| Motor | Capability | Estado |
|---|---|---|
| **A EVA baseline** (PaddleOCR+PDFium+OpenCV+R8.2.3) | ocr, layout, tables, cells, coords, graphic_primitives, local, no GPU | **EXECUTADO** |
| **B PP-StructureV3** | ocr, layout, tables, cells, figures, multipage, local | **RESOURCE_BLOCKED** — dep `paddlex[ocr]` resolvida; modelos RT-DETR/FormulaNet/Chart2Table multi-GB + SIGTERM (OEM/timeout) — exige recursos além do host prod (~4GB livre) |
| **C Docling** | layout+TableFormer | `TEST_NOT_RUN` — requer torch (~2GB+), não provisionado offline |
| **D Werk24** | API técnica | `OWNER_BLOCKED` — sem credenciais/aprovação; PDFs não transmitidos |
| **E Azure AI DocInt** | layout | `OWNER_BLOCKED` — idem |
| **F Google DocAI** | layout | `OWNER_BLOCKED` — idem |
| **G RF-DETR/YOLO símbolos** | detecção especializada | `PENDING` — exploratório, treinamento específico exigido |

## 3. Benchmark real — `90264302` (92 toks, SHA f33447b2)

| Motor | Regions | Tables | Cells | Dims | Dur (ms) | Erro |
|---|---|---|---|---|---|---|
| eva_baseline_r823 | 2 (title_block [1164,69,2006,318] + component_table [41,31,2295,262] gb=True) | 1 (4 rows, item/qtd/componente, col_types tipados) | 24 | 2 (`643±2`,`663±2`) | 60.766 | — |
| pp_structure_v3 | — | — | — | — | 10.336 | `UNAVAILABLE` (dep → models multi-GB → SIGTERM/OOM) |

`90264161` e corpus multipage: baseline executável; PPS-v3 idem bloqueio de recurso. `10210267-2` escaneado — baseline 0→463 chars comprovado R7.

## 4. Recomendação

- **Motor principal:** EVA baseline (R8.2.3) — único executável offline, recursos compatíveis, já produz regiões/tabela/cotas com provenance.
- **Alternativo/complementar:** PP-StructureV3 — capacidade superior (multipage, figures, TableFormer) mas recursos incompatíveis com host atual; candidato quando houver worker dedicado/GPU.
- **Fallback:** Docling como trilha alternativa de layout+table; cloud engines como opção governada pós-aprovação (privacidade/custo/decisão owner).
- **Fusão:** não implementada — evidência insuficiente (PPS-v3 não executou); OCR atual + PPS-v3 = candidato futuro quando provisionado.

## 5. Governança

- `confidence` de modelo ≠ aprovação técnica; todos candidatos DRAFT; EVAL_PENDING sem GT aprovado (owner Engenharia DELPI).
- Cloud engines: nenhum PDF transmitido (OWNER_BLOCKED); credenciais/custos/residência pendentes de decisão.
- Seis tools MCP preservadas; ação `product.drawing_understanding` inalterada.
