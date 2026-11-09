# G2 — Matriz de estrutura visual por ocorrência (candidato)

Referência visual: PDF `90264135` + G1 DRAFT (não homologado).  
Saída EVA medida: `rows_from_native_cells` nesta rodada G2 (não GT).

## Página 10 — set principal (recorte A1–AG)

| Item visual | Qtd visual (G1) | Código visual (G1) | Pai visual | EVA nativa (G2) | Relação preservada? |
|---|---|---|---|---|---|
| A1 | 7 | 10080182 | 90264135 (set) | A1 / 10080182 (DEC-041/G2 vizinhos) | Parcial |
| A2 | 16 | **10080192** | 90264135 | fundido em `10080192 10090316` (item A3) | **NÃO** |
| A3 | 1 | **10090316** | 90264135 | mesmo campo fundido | **NÃO** |
| A4 | 2 | 10090317 | 90264135 | 10090317 (linha seguinte; item A3 A4 fundido em célula) | Parcial/ruído |
| … | … | … | … | … | … |
| AG | 16 | 10110676 | 90264135 | AG presente em outras bandas | Parcial |

**Código em descrição:** descrição de A4 cita `10090316` / conexões cruzadas — deve permanecer description, não `component_code` da linha A3.

## Página 12 — subconjuntos (recorte 50225701–40)

| Pai visual (subset) | Filho item | Qtd | Código componente | Descrição (G1) | EVA nativa |
|---|---|---|---|---|---|
| 50225701 | AE/AH/AG | 1/2/2 | 10010028 / 10080897 / 10110676 | cabo/term./etiqueta | Pai e filhos misturados em célula rowspan=11; `50225702` vira `component_code` solto |
| **50225702** | **AE** | 1 | 10010028 | CABO PVC… | AE sem código estável; pai não linkado |
| **50225702** | **AH** | 2 | 10080897 | TERM. TUBULAR… | idem |
| **50225702** | **AG** | 2 | 10110676 | ETIQUETA… | idem |
| 50225703 | AE/AH/AG | … | … | … | similar |
| 50225704 | AE/AH/AG | … | … | AMB-P12-01 desc | similar |
| 50225740 | AE/AH/AG | … | … | … | similar |
| 50225741 | — | — | — | G1 omitido | não forçar |

**Regra:** rowspan visual do subset ≠ deduplicar filhos; cada item é ocorrência distinta sob o mesmo pai.

## Página 13 — tabela (crop) vs desenho

| Região | Conteúdo | EVA |
|---|---|---|
| drawing_area (superior; A3 em ~y=256) | Balões/desenho | Fora do crop tabular; não tipada como drawing nesta execução |
| component_table | A1–AS + códigos | Grade parcial; fusões multilinha; **falso** `component_code=4 5` (rodapé 4|5) |

| Item | Código célula | Menção em descrição | Nota |
|---|---|---|---|
| A3 | 10090316 | descrição pode citar 10090317 | descrição ≠ código |
| A4 | 10090317 | pode citar 10090316 | idem |
| — | **não** `4 5` | — | índices de folha no rodapé |
