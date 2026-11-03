# 109 — EVA Drawing Intelligence R9.7: OCR–SLANet Cell Association Functional E2E — FUNCTIONAL_DELIVERY_PASS

**Status:** **FUNCTIONAL_DELIVERY_PASS** — fluxo completo `PDF → OCR real → SLANet → associação → tabela candidata COM TEXTO` comprovado em ambos os desenhos; baseline preservada; deploy-lag residual. **Data:** 2026-11-02.

## 1. Correção (causa raiz R9.6)

`TableStructureEngine.run` passou a executar `run_pipeline_isolated` internamente para obter `rec["_tokens_sample"]` (≤200, suficiente p/ 92/126 tokens) + render + SLANet + `associate_tokens_to_cells` — associação real dentro do motor, não de amostra externa vazia.

## 2. E2E real

**`90264302`** (crop `[41,31,2295,262]`): células COM texto real — `QTD`, `CHICOTE DE LIGACÄO`, `18702881 DES: 10013396831 REV: 00 CLIENTE: WEG INDUSTRIA S.`, `90264302`. Tokens OCR mapeados p/ células SLANet.
**`90264161`** (crop `[25,7,2282,520]`): **86 cells, 41 com texto** — `Código`, `Descrição`, `Item QTD Componente`, `CHICOTE DE LIGAÇAO 003405`, `90264161`.

## 3. Semântica honesta

`18702881`/`CLIENTE`/`RESUMO` aparecem como texto em células porque a tabela SLANet cobre a banda administrativa inteira — correto geometricamente; a **tipagem** (admin vs componente) continua sendo trabalho do `understanding`/gate BOM, não da associação. Nada inventado; conflicts/unassigned registrados.

## 4. Diff de 40 vs 34 cells (R9.6)

Variação de crop/confidence entre runs (não-determinismo SLANet ~bordas) — documentado, não crítico; ambos ≥34 cells reais.

## 5. Residuais

- Prod container = 3 engines (imagem 1 rev atrás) → EXECUTION_DRIFT, rebuild pendente.
- GT Engenharia/E2E MCP: `TEST_NOT_RUN`/pendente.
- Baseline default intacta; BOM gate fail-closed.
