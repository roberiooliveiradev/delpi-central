# G2 — Mapa de perdas por fronteira (90264135)

**Fonte PDF:** SHA `af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3` (`MATCH`)  
**Pipeline medido (read-only, container `delpi-engineering-api`):**  
`PDF → PDFium/render → PaddleOCR tokens → Understanding regions → SLANet(+OCR assoc) → rows_from_native_cells`  
**Render observado:** 2339×1653 px (páginas 10/12/13).  
**GT:** G1 DRAFT (OWNER_BLOCKED) — contraste, não verdade absoluta.

Legenda de classes: `PROVEN` | `HIPOTESE_A_VALIDAR` | `INCONCLUSIVE`.

---

## Caso P10 — A2=`10080192` ≠ A3=`10090316`

| Fronteira | Achado | Classe | Owner da perda |
|---|---|---|---|
| PDF visual / G1 DRAFT | Linhas distintas; códigos em células distintas | `PROVEN` (visual+G1) | — |
| PDFium render | Página 10 renderizada; size OK | `PROVEN` | — |
| OCR tokens | Tokens separados: `A2@(y≈117)`, `10080192@(y≈117)`, `A3@(y≈147)`, `10090316@(y≈147)`; conf≥0.997 | `PROVEN` | — (OCR OK) |
| Understanding region | `component_table` crop `[460,51,1913,1625]` | `PROVEN` | — |
| SLANet cell | **Uma** célula `row=1,col=6` texto `10080192 10090316`, bbox Y 89–140 cobrindo ambas as bandas; `line_texts=['10080192','10090316']`, `line_centers=[117,147.5]` | `PROVEN` | **SLANet / table structure** (fusão geométrica de duas linhas de código) |
| Adapter OCR↔célula | Preserva `line_texts` / `token_centers` (sinal de recuperação) | `PROVEN` | Adapter **não** é a primeira perda |
| `rows_from_native_cells` | `component_code='10080192 10090316'`; item rotulado `A3`; A2 como ocorrência distinta **ausente** | `PROVEN` | **Understanding** (não promove `line_texts` da coluna de código a linhas lógicas distintas) |

**FIRST_LOSS_GEOMETRY:** SLANet (célula única cobrindo duas bandas Y).  
**FIRST_LOSS_OF_DISTINCT_OCCURRENCE_FIELD:** Understanding/`rows_from_native_cells` (campo fundido apesar de `line_texts`).  
Não atribuir a falha ao OCR.

Evidência: `.local/eva-val01-g2/page_10.json` SHA `eaf470c9…`.

---

## Caso P12 — parent `50225702` → AE / AH / AG

| Fronteira | Achado | Classe | Owner |
|---|---|---|---|
| PDF / G1 DRAFT | `50225702` é subset_code com rowspan; filhos AE/AH/AG com códigos `10010028`/`10080897`/`10110676` | `PROVEN` (G1 DRAFT) | — |
| OCR tokens | Tokens distintos e legíveis para `50225701/02/03/04/40`, `AE`/`AH`/`AG` e códigos de componente (conf≈1.0) | `PROVEN` | — (OCR OK) |
| Region crop | `component_table` quase página inteira `[2,62,2325,1322]` | `PROVEN` | Regioner amplo |
| SLANet | Célula `row=0,col=0` **`rowspan=11`** agregando dezenas de linhas (set + todos os subconjuntos) num único texto multilinha; inclui `50225702 … AH …` na mesma célula | `PROVEN` | **SLANet** (rowspan/célula gigante) |
| `rows_from_native_cells` | `50225702` aparece como `component_code` de linha; **sem** `parent_group_candidate` ligando AE/AH/AG a esse pai; filhos sem código/qtd estáveis | `PROVEN` | **Understanding** (hierarquia visual perdida / papel errado) |

**FIRST_LOSS_PARENT_CHILD:** SLANet (estrutura de grade não isola coluna de subset vs linhas filhas).  
**SECONDARY_LOSS:** Understanding trata código de subconjunto como `component_code` de ocorrência e não materializa `parent→children`.

Evidência: `.local/eva-val01-g2/page_12.json` SHA `e022898a…`.

---

## Caso P13 — tabela vs desenho; `component_code='4 5'`

| Fronteira | Achado | Classe | Owner |
|---|---|---|---|
| PDF / G1 DRAFT | `drawing_area` ≠ `component_table`; `4 5` **não** é código esperado | `PROVEN` (G1) | — |
| OCR | Tokens `4` e `5` **existem** como dígitos isolados no rodapé da página (`token_index` 166@x≈1019 y≈1619; 167@x≈1290 y≈1618), na sequência `1…8` de índices de folha/quadro — **não** são códigos de componente | `PROVEN` | — (OCR lê o que está impresso) |
| Region | Crop de tabela `[15,979,1745,1625]` **inclui** a faixa inferior dos índices 1–8 | `PROVEN` | Regioner / crop |
| SLANet | Célula `row=20,col=4` `colspan=2` texto `4 5`, `token_refs=[166,167]` | `PROVEN` | **SLANet+assoc** (promove rodapé a célula de tabela) |
| `rows_from_native_cells` | `component_code='4 5'` | `PROVEN` | **Understanding** (tipa texto da célula como código) |

**FIRST_LOSS_FALSE_COMPONENT_CODE:** fronteira **SLANet cell construction / token→cell** sobre tokens de rodapé já presentes no OCR; Understanding apenas tipa o texto agregado.  
Origem geométrica do defeito histórico EVA: **não inventada** — rastreada a tokens 166/167 no crop tabular.

Desenho vs tabela: token `A3` em `(2124,256)` está fora do crop tabular (y=979+) — separação espacial existe no raster; Understanding listou só `component_table` nesta página (drawing_area não tipada nesta execução).

Evidência: `.local/eva-val01-g2/page_13.json` SHA `7d7fe73b…` + OCR token dump desta rodada.

---

## Síntese de owners

| Defeito | Primeira fronteira PROVEN | Camada para G4 (proposta, não implementar) |
|---|---|---|
| Fusão A2/A3 códigos | SLANet cell merge | Framework config/crop **e/ou** Understanding split via `line_texts` |
| Hierarquia 50225702 | SLANet rowspan monolítico | Framework grade **e/ou** papéis parent≠component no Understanding |
| `4 5` falso código | SLANet inclui tokens de rodapé na grade | Exclusão de faixa administrativa / tipagem conservadora no Understanding |
