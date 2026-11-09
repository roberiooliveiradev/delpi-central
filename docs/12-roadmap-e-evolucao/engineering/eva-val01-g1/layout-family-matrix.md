# G1_LAYOUT_FAMILY_MATRIX

**Status:** `DRAFT` — famílias propostas a partir de evidência visual/Doc 120; homologação = Engenharia.

| Classe pedida | Evidência disponível (autorizada) | Documento / página | Status |
|---|---|---|---|
| Tabela simples | Linhas/colunas convencionais, 1 página | `90264026` p1 | `REPRESENTED` (dev) |
| Ocorrências repetidas | A9/AA sob grupos distintos | `90264004` p1; também A9/AA em `90264135` | `REPRESENTED` (dev) |
| Documento multipágina | Tabelas em páginas distintas | `90264017` (14p); `90264135` (13p); `90264030` (13p) | `REPRESENTED` |
| Agrupamento hierárquico | Subconjuntos → componentes | `90264135` p12 (`5022570x` → AE/AH/AG) | `REPRESENTED` |
| Mesclagem vertical | Parent cell rowspan | `90264135` p10/p12 (código/descrição de conjunto/cabo) | `REPRESENTED` |
| Texto longo | Descrição longa em célula | `90264135` descrições de terminais/conectores | `REPRESENTED` |
| Código dentro da descrição | Número legítimo ≠ coluna Componente | `90264135` p10/p13 A3/A4 (`CONTRA PC 10090…`) | `REPRESENTED` |
| Tabela densa | Linhas próximas / risco de fusão | `90264135` p10/p12; `90263572` p2 | `REPRESENTED` / densos adicionais `TO_INVENTORY` |
| Holdout layout inédito | — | — | **`GAP` — `TRUE_UNSEEN_HOLDOUT=NOT_AVAILABLE`** |

## Lacunas registradas

| GAP_ID | Classe | Nota |
|---|---|---|
| G1-LF-01 | Holdout cego | Exige novos PDFs autorizados pelo owner |
| G1-LF-02 | Famílias `TO_INVENTORY` do corpus 13 | Atribuir família só após inspeção visual dedicada (não inventar) |
| G1-LF-03 | Title block / carimbo como família estrutural | Fora do foco tabular G1; reservado |
