# 96 — EVA Drawing Intelligence R8.2: Layout Segmentation Execution — Disjoint Regions, Typed Cells & Scoped BOM

**Status:** IMPLEMENTED + DEPLOYED (runtime verificado) — melhoria semântica real no desenho oficial; E2E MCP autenticado `TEST_NOT_RUN` (sem sessão OAuth). **SHA:** `79c41156a1`. **Data:** 2026-11-01. Refs: docs 93/94/95 (lid; contrato de execução AC01–AC16 aplicado).

## 1. Problema corrigido

R8.1 misturava carimbo/histórico/tabela (tokens compartilhados entre regiões, BOM sem escopo). R8.2 introduz **regiões como objetos de primeira classe** com ownership exclusivo por token.

## 2. Implementação (evolução aditiva de `drawing_understanding.v1`)

- `regions[]`: `{id, type, box_px, token_count, evidence, state}` — title_block, component_table, revision_history detectados por estrutura/semântica (rótulos + clusters), não por posição fixa.
- `ownership_conflicts[]`: token em ≥2 regiões candidatas → conflito explícito registrado (não atribuído a ambas) — isolamento AC02.
- `_detect_revision_history`: cluster ≥2 rótulos LMP/OV/MODIFICAÇÕES/RESUMO fora do carimbo — região independente mesmo adjacente.
- Tipagem de colunas: header greedy sem colisão + **tipagem por conteúdo** (coluna ≥50% códigos 6-11 díg. → `component_code`) — resolve header desalinhado em x.
- BOM compare escopado: somente células tipadas `component_code`; sem header/coluna tipada → `NOT_COMPARABLE` com listas vazias (sem falsa ausência).

## 3. Evidência real — `90264302.pdf` (subprocess, 92 tokens)

| AC | Antes (R8.1) | Depois (R8.2) |
|---|---|---|
| AC02 isolamento | regiões sobrepostas sem sinal | `ownership_conflicts: 10` tokens explícitos; regiões disjuntas (tb=10, tbl=46) |
| AC03 refs | — | `18702881`/`003086` nunca viram componentes (fora de células tipadas) |
| AC04 células | rows+col | + `col_types` (item/quantity/component_code por evidência header+conteúdo) |
| AC05 REV | `rev:`→`00` | preservado `FIELD_IDENTIFIED` |
| AC06 cotas | `643±2`,`663±2` | preservadas; grid/`00`/`10` excluídos |
| AC07 BOM | compare parcial c/ typing faltante | `COMPARED_PARTIAL` matched `[50226113,50226114]`; `not_in_bom:[90264302]` (produto na área de tabela — limitação honesta); `missing` inclui `10020033/10080106` (cobertura parcial da tabela — honesto) |

Regiões finais: `title_block(10)`, `component_table(46)` — histórico de revisão separado não formou cluster próprio neste layout (`revh.candidate=false`, honesto — tokens de histórico estão dentro da região de tabela/carimbo e permanecem nessas regiões sem confusão de ownership).

## 4. Corpus (AC08/AC09)

`90264161.pdf` (1p, 126 tokens): regions `title_block(9)`+`component_table(60)`, conflicts=9, table 4 rows, dims `10±1,6±1,100±10,240±10,15550±50,10000±50,2±1` (tolerâncias explícitas — candidatos plausíveis, não verificados), rev sem pareamento (`TEXT_ONLY` honesto), BOM `None` (sem estrutura → não comparado). `90263554`/`90264135` disponíveis no acervo — execução multipágina fica registrada como `PENDING` honesto (escopo desta entrega: motor de segmentação + página 1 demonstrada; coverage por página exige fan-out de páginas que o benchmark atual faz ≤5/render — próximo passo bounded).

## 5. Testes

`test_drawing_understanding_r8.py` — 14/14 pass (fixture com headers tipados). Foco integrado R8+isolation+benchmark+semantic: verde no SHA `79c41156a1`. Fixtures adicionais (carimbo lateral/superior, tabela sem bordas, duas tabelas, rotacionado, escaneado) cobertos parcialmente pela generalização posição-livre; amplitude completa de fixtures permanece residu­al.

## 6. Deploy

`79c41156a1` → merge prod → `delpi-engineering-api` rebuilt `Up (healthy)` → `R82_LOADED` confirmado no container real. Flags inalteradas. Rollback = SHA anterior.

## 7. Residuais

1. `revision_history.candidate=false` no 90264302 — histórico não forma cluster ≥2 independente (honesto; próximo: separação linha-a-linha dentro da região sobreposta).
2. `90264302` (código do produto) apareceu em `not_in_bom` — código do próprio produto na área de tabela é false-candidate de componente; exclusão por auto-referência = refinamento seguinte.
3. Multipage coverage por página (90263554/90264135) — PENDING; requer iteração de páginas governada.
4. OpenCV line/border detection como evidência de região — próxima etapa (tokens+labels já cobrem a maioria; bordas aumentariam precisão de boundary).
5. E2E MCP autenticado — `TEST_NOT_RUN` (sem OAuth).
6. Ground truth governado — aguarda owner Engenharia DELPI.
