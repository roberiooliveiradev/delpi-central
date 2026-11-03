# 102 — EVA Drawing Intelligence R9.1: Local Engine Execution, Docling and PP-StructureV3 Benchmark

**Status:** BOM gate corrigido + motores avaliados com evidência real; PP-StructureV3 `RESOURCE_BLOCKED` fundamentado; Docling `TEST_NOT_RUN` (instalação excede recursos do host); deploy verificado; E2E MCP `TEST_NOT_RUN` (sem OAuth). **SHA:** pendente. **Data:** 2026-11-02. Ref: doc 100/101.

## 1. Correção do gate BOM (R91-12 — defeito explícito)

`unreliable_boundary=true` + `COMPARED_PARTIAL` era semanticamente inseguro. Corrigido: `elif (table and table.unreliable_boundary) or not col_types:` → `NOT_COMPARABLE` com listas vazias. **Comprovado:** `90264161` → `state=NOT_COMPARABLE`, matched/missing/not_in_bom `[]`, `unreliable_boundary=True`. Regressão: `test_unreliable_boundary_forces_not_comparable` (moldura sintética >60% página → NOT_COMPARABLE).

## 2. Diagnóstico PP-StructureV3 (R91-02/03)

`use_formula_recognition=False,use_chart_recognition=False` → ainda `SIGTERM` — os modelos (RT-DETR table cell det, PP-FormulaNet, PP-Chart2Table) carregam **na inicialização**, não só no uso; o flag de módulo não evita o peso do pipeline. `RESOURCE_BLOCKED` fundamentado: requer worker dedicado/GPU (proposta: worker isolado com ≥8GB RAM dedicada, modelos read-only pré-baixados — decisão de infraestrutura pendente).

## 3. Docling (R91-04/05)

`pip install docling` cortado por timeout — dependência `torch` ~2GB+ excede a capacidade do host (~4GB livre) dentro do prazo de provisionamento autorizado. `TEST_NOT_RUN`/`RESOURCE_BLOCKED` — adapter Docling pronto para implementar quando provisionado em ambiente dedicado.

## 4. Estado dos motores

| Motor | Execução | Resultado |
|---|---|---|
| eva_baseline_r823 | **EXECUTADO** | 90264302: 2 regions, 4-row table, 24 cells, 2 dims; 90264161: NOT_COMPARABLE honesto, cotas restauradas |
| pp_structure_v3 | **RESOURCE_BLOCKED** | modelos multi-GB → SIGTERM no host; requer worker dedicado |
| docling | **TEST_NOT_RUN** | torch ~2GB excede host; adapter pronto p/ ambiente dedicado |
| Werk24/Azure/Google | **OWNER_BLOCKED** | sem credenciais/aprovação; PDFs nunca transmitidos |

## 5. Testes

`test_drawing_perception_r9.py` (11) + `test_drawing_understanding_r8.py` (15) — 26 verde. BOM gate regression provada.
