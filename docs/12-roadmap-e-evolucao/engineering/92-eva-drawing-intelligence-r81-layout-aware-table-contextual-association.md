# 92 — EVA Drawing Intelligence R8.1: Layout-Aware Region Detection, Table Reconstruction & Contextual Technical Association

**Status:** D1–D5 corrigidos e comprovados no PDF oficial real; D6 avanço honesto-limitado; deploy prod verificado; E2E MCP autenticado `TEST_NOT_RUN` (sem sessão OAuth). **SHA:** `be207c4984`. **Data:** 2026-11-01.

## 1. Root causes e correções (D1–D5)

| Defeito | Root cause | Correção |
|---|---|---|
| D1 região só por posição | `classify_region` usava frações fixas da página | Detecção por estrutura/semântica: carimbo = cluster de ≥2 rótulos conhecidos (`_TITLEBLOCK_LABELS`), tabela = coluna de códigos alinhados em X |
| D2 `component_table.candidate=false` | tabela só dentro da região posicional | `_detect_component_table`: códigos 6-11 dígitos → coluna X cluster → linhas por y-proximidade + headers acima |
| D3 `REV:` sem valor | nenhum pareamento label→valor | `_match_revisions`: `label_right_same_row` / `label_below_same_col` com bounds |
| D4 `00`/`10` como cotas | regex de número solto | `_is_dimension_candidate`: exclui valores pareados, códigos longos, regiões estruturadas; exige tolerância/unidade explícita OU drawing_area≥3 dígitos |
| D5 falsa ausência em BOM | compare rodava com tabela vazia | fail-closed: sem linhas → `NOT_COMPARABLE` com listas vazias; com linhas → multiplicity-aware por células de código |

## 2. Comprovação real — `90264302.pdf` (subprocess isolado, 92 tokens)

| Capacidade | R8 (antes) | R8.1 (depois) |
|---|---|---|
| Carimbo | posição errada | **`candidate=True`** — labels `rev`,`data` detectadas |
| Tabela | `row_count=0` | **`candidate=True`, 4 linhas**, headers `item/qtd/componente`, 4 códigos |
| Revisão | `[]` | **`rev:`→`00`** `FIELD_IDENTIFIED` via `label_right_same_row` (boxes preservados) |
| Cotas | `643±2`,`663±2`,`00`,`10` | **somente `643±2`/`663±2`** (`explicit_tolerance_or_unit`); 00/10/grid excluídos com razão registrada |
| BOM | `NOT_COMPARABLE` + falsas ausências | **`COMPARED_PARTIAL`**: matched `10020033,50226114,10080106,50226113`; `occurrence_mismatches` honestos (`10020033`/`10080106` bom=1 vs tabela=2); `99999999` missing real |
| Regiões | revision_history=37 | component_table=46, drawing_area=35, notes=11 — estrutural |

## 3. Contrato preservado

`drawing_understanding.v1` — evolução aditiva: `title_block{}` (box/labels/detection), `component_table.headers/code_count`, `dimension_excluded[]` (razão por exclusão), `bom_comparison` fail-closed. Semântica v2 documentada; consumidores não quebram.

## 4. Testes

`test_drawing_understanding_r8.py` atualizado p/ semântica v2 (fixture com carimbo por rótulos + tabela por coluna de códigos + tolerância explícita): **14/14 pass**. Focus suite R8+isolation+benchmark+semantic: 82+ verde.

## 5. Deploy / runtime

`be207c4984` → merge prod → `delpi-engineering-api` rebuilt → `Up (healthy)` → `R81_LOADED drawing_understanding.v1` confirmado no container real. Flags inalteradas (master+OCR ativas, understanding exige ambas). Rollback = SHA anterior / flag.

## 6. Residuais honestos

- **D6**: associação cota↔geometria real (linhas de cota/setas via OpenCV) não implementada — `DIMENSION_GEOMETRY_ASSOCIATION_CANDIDATE` existe no contrato mas não emitido ainda.
- `occurrence_mismatches` (bom=1 vs tabela=2 em 10020033/10080106) é divergência documental real candidata — requer revisão Engenharia, não prova erro.
- E2E MCP autenticado: `TEST_NOT_RUN` — sem JWT usuário produtivo; cadeia pronta.
- Detecção estrutural assume ≥2 rótulos/coluna de códigos; desenhos sem carimbo/tabela ou OCR incompleto degradam para honesto `candidate=false`.
- Ground truth governado: corpus proposto aguarda owner Engenharia DELPI.
