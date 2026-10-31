# 73 — EVA — ChatGPT Visual Collaboration R1: Implementation, Evaluation & Production Evidence

**Status:** G0–G6 IMPLEMENTED + DEPLOYED (CODE_READY; consumer E2E e ground truth owner-validated pendentes). **Data:** 2026-10-31.
**Baseline:** `c23e3ee25b` → **SHA final:** `00fc7d8d0b` (main). Deploy prod via merge.

## 1. Implementado (G1–G4)

- **Contratos (doc 72):** `DrawingVisualObservation` (untrusted, ≤50 itens, campos fechados), `SourceMatch` (4 estados), entrada v2 backward-compatible, relatório v2, erros tipados.
- **Comparador multifonte** (`application/drawing/drawing_comparator.py`): visual×textual somente em `same_document_verified`; visual×oficial (revisão/código/bom_item) com conflito→finding WARNING e `is_hypothesis` tratado como indício; ausência visual nunca vira divergência comprovada.
- **Orquestração** (`drawing_analysis_service.py`): verificações `visual_observations` + `visual_vs_textual` (NOT_CHECKED sem identidade verificada); findings `visual_vs_official`; payload `source_match`/`visual_observations`/`comparison_results`/`contract_version=drawing_analysis.v2`.
- **EVA (G4):** `analyze` aceita `visual_observations[]`/`scope[]` com validação tipada `invalid_visual_observation`; registry atualizado; seis tools preservadas.
- **Conhecimento (G2):** `knowledge` tópico `product.drawing_criteria` v1.1 — 7 regras tipadas com owner/fonte/aplicabilidade/severidade; norma PA/roteiro/inspeção permanecem `NOT_CHECKED/OWNER_BLOCKED`.

## 2. Testes

`test_drawing_visual_collab.py` — 16 testes: schema (rejeições/normalização/caps), SourceMatch (hash, revisão divergente, código solitário não verifica), comparador (agreement/conflict/possible_divergence), serviço com observações (same_document_verified→agreement; sem identidade→NOT_CHECKED; retrocompatibilidade). **Suite: 523 passed / 0 failed** no SHA `00fc7d8d0b` (inclui E1–E3 + purity + registry).

## 3. Deploy e smoke produtivo

Push `feat/engineering-products-e2e:main` → `origin/main=00fc7d8d0b`. Prod `operador@192.168.1.237`: `git merge origin/main` (repo prod divergido — merge não destrutivo, ff impossível) → `up-prod-sequential.sh --build engineering-api` → `delpi-engineering-api Up (healthy)`; módulos `parse_visual_observations`/`SourceMatch` importáveis no container; `/v1/health` 401 auth-gated. **Rollback:** checkout SHA anterior + rebuild `engineering-api`.

## 4. Matriz EVC-01..26

| Estado | Critérios |
|---|---|
| PASS | 01,02,03,04,05,06,07,08,09,10,11,12,13,16(fixtures contratuais+tests),19(schema+untrusted+injection-immune determinístico),20,21,22,23,24,25,26 |
| TEST_NOT_RUN | 14 (anexo ChatGPT real — sem sessão do consumidor), 15 (DEV MCP E2E OAuth — não executado) |
| PENDING/OWNER | 17 (ground truth owner-validated pendente), 18 (metrics/thresholds aguardam corpus aprovado — nenhum resultado inventado) |

## 5. Residuais

1. ChatGPT real E2E não provado (nenhuma sessão de consumidor) — honestamente TEST_NOT_RUN; capacidade backend PROVEN por testes.
2. ONDA14: corpus existe no legado como scripts; port de fixtures para evals EVA + thresholds = próximo passo com owner Engenharia.
3. SG2/inspeção/PA: OWNER_BLOCKED por contrato.
4. Prod repo divergido — deploy por merge (já documentado); realinhamento recomendado.
5. `attachment` cru via MCP não suportado — observações estruturadas são o contrato vigente; upload via Portal = G7 futuro.

## 6. G7 — Portal futuro (documentado, não implementado)

`Analisar desenho com EVA` na Ficha + página de upload autorizado — exige contrato de upload/retenção/AuthZ/custo antes de implementar. Fora do escopo desta missão.
