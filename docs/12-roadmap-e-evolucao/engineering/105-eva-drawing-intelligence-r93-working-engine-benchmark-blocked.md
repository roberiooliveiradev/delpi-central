# 105 — EVA Drawing Intelligence R9.3: Working Engine Real Benchmark — FUNCTIONAL_DELIVERY_BLOCKED

**Status:** `FUNCTIONAL_DELIVERY_BLOCKED` — nenhum motor moderno executou inferência real nos desenhos DELPI; baseline preservada; bloqueios exatos documentados. **Data:** 2026-11-02.

## 1. Tentativas reais (não-importação)

| Motor | Tentativa | Resultado real |
|---|---|---|
| PP-StructureV3 | `PPStructureV3(use_formula_recognition=False,use_chart_recognition=False)` | `SIGTERM` — modelos multi-GB carregam na INIT (RT-DETR/FormulaNet/Chart2Table) mesmo com módulos off; ~4.6GB livres no host → `RESOURCE_BLOCKED` |
| Docling | `docling 2.145 + torch 2.15+cpu`, transformers **4.46.3 / 4.56.2 / 5.22.1** | `RuntimeError: Failed to load image processor from docling-layout-heron` em TODAS as versões — snapshot completo no disco, processor não resolvível → `MODEL_NOT_PROVISIONED`/UNAVAILABLE tipado |

## 2. Causa raiz exata

- **PPS-v3:** peso total dos modelos excede RAM disponível; a flag de módulo não evita o carregamento na inicialização do pipeline.
- **Docling:** `docling-layout-heron` requer pareamento exato docling↔transformers não coberto pelas versões testadas; solução correta = venv dedicado com lockfile oficial docling (não pinning arbitrário).

## 3. Menor ação concreta para desbloqueio

1. **Docling:** criar venv isolado com `uv`/`pip` usando o lockfile oficial docling (docling ships sua matriz de versões testadas) — `uv pip install docling` em ambiente limpo onde o docling controla as deps. Esforço estimado: baixo.
2. **PPS-v3:** worker dedicado ≥12GB RAM isolada (proposta já registrada — `ARCHITECTURE_DECISION_REQUIRED`).

## 4. Estado

- Baseline `eva_baseline_r823` — único motor executável, preservado.
- `R92_LOADED` — 3 adapters no registry (baseline+pps+docling), contrato v1 íntegro, erros tipados isolados.
- `90264302`: baseline 2 regions/4-row/24 cells/2 dims — única evidência real disponível.
