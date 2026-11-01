# 91 — EVA Drawing Intelligence R8: Technical Drawing Understanding, Geometry Association & Governed Ground Truth

**Status:** IMPLEMENTED `drawing_understanding.v1` + ação experimental `analyze(product.drawing_understanding)` — run real sobre 90264302 executado; E2E MCP autenticado `TEST_NOT_RUN` (sem sessão OAuth). **Data:** 2026-11-01.

## 1. Abstraction Gate (R8-02/03)

Nenhuma arquitetura paralela: a camada de interpretação consome **somente** a evidência OCR já governada (`_tokens_sample` com `raw_text/normalized_text/bounding_box_px/bounding_box_pdf_points/confidence/page`). Novo módulo `application/drawing/understanding.py` — Python puro, determinístico, zero visão computacional (gate arquitetural testado). Ação tipada dentro de `analyze` (6 tools preservadas), flags `ENG_DRAWING_BENCHMARK_ENABLED` + `ENG_DRAWING_OCR_BENCHMARK_ENABLED` (mesma cadeia da R7.2).

## 2. Contrato `drawing_understanding.v1`

Estados fechados e honestos — `FIELD_IDENTIFIED | FIELD_AMBIGUOUS | TEXT_ONLY | NOT_FOUND | NOT_COMPARABLE`; `DIMENSION_TEXT_FOUND | DIMENSION_REGION_CANDIDATE | DIMENSION_GEOMETRY_ASSOCIATION_CANDIDATE` (`..._VERIFIED` nunca emitido automaticamente); BOM compare `matched | missing_in_drawing_table | not_in_bom | occurrence_mismatches` (multiplicidade-aware, sem falsas divergências). Provenance: SHA → page → region → token → regra → candidato. `engineering_validated=false` sempre.

## 3. Algoritmos (determinísticos, explicáveis)

Região por posição relativa (carimbo=inferior-direito, tabela=sobre carimbo, histórico=topo, notas=superior-esquerdo); cluster de linhas por centro-Y e de colunas por centro-X; regex de código/revisão/cota (unidade/tolerância só quando explicitamente escritas); BOM compare por multiplicidade. Sem ML, sem confidence técnica inventada.

## 4. Resultado real — `90264302.pdf` (92 tokens, subprocess isolado)

| Capacidade | Resultado real |
|---|---|
| Identificadores | 9 códigos encontrados (90264302 ×2, 18702881, 10020033 ×2, 50226113, 50226114, 10080106 ×2, 003086) — estado `TEXT_ONLY` |
| Cotas | **`643±2` e `663±2` — tolerância ±2 recuperada** (R7 tinha só o número) → `DIMENSION_REGION_CANDIDATE` |
| Regiões | layout do desenho coloca carimbo/tabela na faixa superior → heurística posicional classificou como `revision_history`/`notes` — **limitação real registrada, não mascarada** |
| Revisão | label "REV" não pareado neste layout → `[]` honesto |
| BOM | `NOT_COMPARABLE` — candidatos não atribuídos à região de tabela ⇒ sem comparação falsa |

A saída demonstra exatamente o gate: candidatos com estados e ambiguidade explícita, nunca certeza inventada. Quando a evidência de região falha, o resultado diz `TEXT_ONLY`/`NOT_COMPARABLE` em vez de afirmar associação.

## 5. Testes (SHA final)

`test_drawing_understanding_r8.py` — 14 testes: schema/DRAFT, região determinística, linhas×colunas da tabela, estados de campo, label↔valor de revisão, cotas nunca verificadas, ambiguidade preservada, BOM multiplicidade, NOT_COMPARABLE honesto, provenance, extrator de códigos BOM, registry↔dispatcher da ação nova, ausência de imports de visão na camada application. Foco integrado: **82 passed** (R8 + isolation + benchmark + semantic MCP).

## 6. Residuais

1. E2E autenticado via MCP — `TEST_NOT_RUN` (sem OAuth); cadeia pronta.
2. Classificação de região posicional falha em layouts atípicos/rotacionados — próxima etapa: detecção por estrutura gráfica (linhas/bordas) ou aprendizado supervisionado com ground truth aprovado.
3. Pareamento label↔valor de revisão e associação cota↔geometria — etapas seguintes com validação de Engenharia.
4. `bom_codes` via `fetch_product_structure` — extração best-effort defensiva; formalizar contrato com owner.
5. Ground truth governado: proposta de corpus com owner de validação — pendente Engenharia DELPI.
