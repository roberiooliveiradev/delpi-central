# 98 — EVA Drawing Intelligence R8.2.2: Real Graphic-Line Region Segmentation & BOM Membership Gate

**Status:** IMPLEMENTED + DEPLOYED — detecção gráfica real de linhas/retângulos alimenta a fronteira da tabela; defeitos semânticos principais corrigidos nos dois desenhos de regressão; E2E MCP autenticado `TEST_NOT_RUN` (sem OAuth). **SHA:** `78677f9205`. Refs: docs 93–97.

## 1. Correção estrutural (AC03/AC04 — primeira vez com evidência gráfica real)

`detect_graphic_primitives` (`opencv_adapter.py`): `adaptiveThreshold` + morphological open horizontal/vertical + `findContours(RETR_LIST)` — produz `{h_lines, v_lines, rects}` em pixels, com `count` de provenance. `RETR_LIST` captura células aninhadas; moldura da página (área >90%) é excluída. Worker: `stage.graphic_primitives` por página → `record._graphic_primitives` + `page_size_px`; falha de detecção degrada para `None` (nunca derruba OCR).

Fronteira da tabela (`understanding.py`): união dos **menores retângulos que contêm cada token da coluna de códigos** (células reais), não a moldura externa — `boundary_source=graphic_rects` vs `tokens_inferred` registrado.

## 2. Correções semânticas

| Defeito R8.2.1 | Correção R8.2.2 |
|---|---|
| Tabela continha `COD:`/`CLIENTE:`/`REV:`/`RESUMO` | `_is_label` `rstrip(".:")` — labels removidos das células (admin labels=0) |
| Produto pai em `matched` | `product_code` excluído de células `component_code` + BOM (nib=[]) |
| Fronteira = faixa toda | fronteira por células gráficas — `[41,31,2295,262]` no 90264302 |
| `10020033`/`10080106` ambíguos | `extracted_but_unclassified` preservado — nunca falsa ausência |

## 3. Evidência real — regressão

**`90264302` (92 toks, rects=103):** `title_block [1167.7,184.9,2006.2,318.2]` + `component_table [41,31,2295,262]` (gb=True), 4 rows, BOM `COMPARED_PARTIAL` matched `[50226113,50226114]` + `uncl[10080106,10020033]`, `rev:`→`00`, dims `643±2`/`663±2`. Residual honesto: `18702881`/`003086` permanecem como **células não-tipadas** dentro da banda graficamente delimitada (são parte da mesma região de borda real) — nunca viram componentes (não estão em matched/unclassified).

**`90264161` (126 toks, rects=123):** `title_block` válido + `component_table [25,7,2282,1638]` (gb=True — o desenho tem borda ampla legítima que engloba a coluna de códigos), 4 rows, admin cells=0, BOM `NOT_COMPARABLE` fail-closed, produto pai excluído. Residual: cotas excluídas (região estruturada ampla) — documentado.

## 4. Residuais

1. `18702881`/`003086` permanecem como células na banda de tabela (são parte do retângulo real) — tipadas não-componente, nunca na BOM; refinamento = separar células por tipagem em sub-regiões.
2. `90264161`: cotas excluídas por região estruturada ampla — detecção gráfica correta, mas filtro de cota precisa de `dimension` region como exceção.
3. OpenCV cost ~+10-30% no pipeline; multipage coverage por página PENDING.
4. E2E autenticado `TEST_NOT_RUN`; GT owner Engenharia pendente.
