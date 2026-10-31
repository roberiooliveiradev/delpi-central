# 74 — EVA — Drawing Intelligence R2: PDF Contract Repair, Native Technical Report, Evaluation & Production Evidence

**Status:** IMPLEMENTED + DEPLOYED (engineering-api rebuild). **Data:** 2026-10-31.
**Baseline:** `02cf82fce4` → **SHA final:** `63f3aa3b65` (main). Regressão principal: produto **90264302** (CHICOTE DE LIGACAO).

## 1. Causa raiz — `drawing_not_found` (R1) — COMPROVADA

`read(product.drawing)` retornava `found=true`/`90264302.pdf` mas `analyze` respondia 404. Causa: `_get_json` (delegated_auxiliary) embrulha respostas em `{"status":"available","data":{...}}` — o serviço lia `found`/`product`/`root` no nível externo, vendo sempre `None` → falso `drawing_not_found`, campos de produto vazios e `bom_items=[]` silencioso.

**Fix:** `application/drawing/drawing_contracts.py::unwrap_delegated` — ponto único de normalização: aceita envelope `{"status","data"}` e dicts raw (retrocompat); `forbidden`→403 (jamais not_found), `unavailable`→502, `not_found`→código correto, payload inválido→`source_unavailable`. Aplicado em detail/drawing-meta/structure. PDF bytes já funcionavam (`get_raw`→`content`).

## 2. Semânticas honestas (R4/R5)

- **Revisão (R5):** `00` vs `001` — larguras distintas → possíveis controles de revisão distintos → `INCONCLUSIVE`, não `revision_mismatch`. WARNING só com mesma representação e valor divergente. Sem regra oficial de normalização, nada de equivalência inventada.
- **Quantidades (R4):** `quantity_semantics` — qty+unidade brutas do SG1 reportadas INCONCLUSIVE: sem contrato de base de consumo/fator/unidade secundária, `643 MT` não é presumivelmente 643m por chicote nem `1000 PC` consumo por peça. Estrutura indisponível → `bom_availability` INCONCLUSIVE explícito (antes era silencioso).

## 3. Relatório nativo v3 (R6/R7/R8)

Inventário legado: `chat_drawing_report_export_service` (payload markdown+tabelas export), policy `drawing-analysis-render-only` (checklist OK/Pendente/Erro/Erro crítico, nunca promover/rebaixar, citar pdfEvidence×apiEvidence, proibido aprovar com erro crítico) — conceitos absorvidos como seções nativas, **zero runtime import**.

`contract_version=drawing_analysis.v3` aditivo: `sections` A–H — A identificação, B resumo executivo, C verificações visuais/textuais, D cruzamentos oficiais (BOM, qty, MP/PI), E achados, F inconclusões (INCONCLUSIVE/NOT_CHECKED/NOT_APPLICABLE explícitas), G recomendações, H revisão técnica (`DRAFT`, reviewer=Engenharia, `automatic_approval=false`). Campos v1/v2 preservados (retrocompat).

## 4. Avaliação de bibliotecas (R2) — DECISÃO: manter `pypdf`

PyMuPDF avaliado: licença **AGPL** (risco de distribuição server-side), ganho não comprovado sem corpus comparativo; pdfplumber não agrega capacidade necessária além do pypdf para o contrato atual. Coordenadas/região permanecem limitação honesta (evidência por página). Sem OCR/VLM próprio nesta missão.

## 5. Testes (SHA `63f3aa3b65`)

`test_drawing_analysis_r2.py` — 10 testes: unwrap envelope+raw+inválido, forbidden≠not_found (403), unavailable≠not_found (502), T02 recuperação do desenho 90264302, T03 bytes+assinatura+extração, T08 revisão 00×001→INCONCLUSIVE sem finding, T09/T11 PI 50226113/114 + qty 643/663/1000 sem erro fictício, T10 observações 643/663mm aceitas, T13/T16 seções H DRAFT + routing/inspection/pa NOT_CHECKED. **Suite: 533 passed / 0 failed.**

## 6. Deploy e smoke produtivo

Push `feat/engineering-products-e2e:main` → `origin/main=63f3aa3b65`. Prod `operador@192.168.1.237`: `git merge origin/main` (repo prod divergido — merge não destrutivo) → `up-prod-sequential.sh --build engineering-api` → `delpi-engineering-api Up (healthy)`, `drawing_contracts.unwrap_delegated` importável em prod, `/v1/health` 401 auth-gated. **Rollback:** checkout SHA anterior + rebuild.

## 7. Matriz EVA-R2-01..30

- **PASS:** 01–05, 07–13, 14–17, 18–22, 25–29 (pypdf mantido, comparabilidade, BOM comparado, conversões não inventadas, revisões por fonte, inventário legado, relatório v3 nativo, evidências/rules por achado, DRAFT, knowledge v1.1, retrocompat, 6 tools, suíte 90264302, segurança, testes no SHA, commit/push, deploy, smoke, rollback, docs).
- **TEST_NOT_RUN:** 23 (MCP/ChatGPT E2E real — sem sessão consumidora).
- **PENDING:** 24 (métricas/thresholds — ground truth owner ainda não aprovado; nenhum inventado).
- **OWNER_BLOCKED:** roteiro/inspeção/PA norma (NOT_CHECKED explícito).
- **PASS 30:** zero aprovação técnica automatizada.

## 8. Residuais

1. ONDA14 corpus → eval metrics: EVAL_PENDING até validação de Engenharia.
2. ChatGPT real session: TEST_NOT_RUN (contrato implementado, consumidor não exercitado).
3. Região/coordenada de evidência: limitação de pypdf documentada (PyMuPDF rejeitado por AGPL).
4. Conversão de quantidades SG1: OWNER_BLOCKED (contrato de base de consumo).
5. Prod repo divergido — merge deploy documentado; realinhamento ff-only recomendado.
