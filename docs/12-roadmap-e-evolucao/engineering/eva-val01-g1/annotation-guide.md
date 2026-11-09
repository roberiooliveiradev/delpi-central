# G1_ANNOTATION_GUIDE — Anotação visual estrutural de tabelas

**Versão:** `g1.0-draft`  
**Owner de homologação:** Engenharia  
**Aplicável a:** corpus Doc 120 + diagnósticos autorizados  
**Proibição:** não usar OCR/SLANet/Understanding como fonte do expected; modelos só como contraste diagnóstico rotulado `EVA_OUTPUT_HISTORICAL`.

## 1. Princípios

1. O PDF oficial (SHA conferido) é a evidência visual.
2. Campos ilegíveis → `UNKNOWN` / `ILLEGIBLE`, nunca inventar.
3. Multiplicidade: não deduplicar por código; cada ocorrência é uma linha/relação.
4. Código citado em descrição ≠ código da coluna Componente.
5. Anotação de papel funcional é referência humana, não inferência da EVA.
6. Discordância entre revisores → adjudicação; sem adjudicação → `AMBIGUOUS`.

## 2. Coordenadas

| Campo | Regra |
|---|---|
| `page` | 1-based, página física do PDF |
| `coordinate_system` | `pixels_top_left` do raster de referência |
| `render_dpi` | DPI do overlay (ex.: 200); independente do DPI de produção (G0=200) |
| `bounding_box_px` | `[x1,y1,x2,y2]` eixo-alinhado; polígono opcional |
| `pdf_sha256` | obrigatório em todo documento |

## 3. Regiões (`region_type`)

| Tipo | Definição |
|---|---|
| `component_table` | Tabela de componentes/itens |
| `title_block` | Carimbo / bloco de título |
| `revision_history` | Histórico de alterações |
| `drawing_area` | Vista/montagem (não tabular) |
| `notes` | Notas textuais |
| `other` / `unknown` | Quando classificação não é evidente |

Para cada região: `page`, `box_px`, `header_box` (opcional), `body_box`, `footer_box` (se existir), `non_table_adjacent`.

## 4. Estrutura tabular

Para cada célula:

```text
cell_id          # estável: {doc}:{page}:r{row}:c{col}
row_index        # 0-based na grade visual da região
col_index
rowspan, colspan # 1 se sem mesclagem
box_px
is_empty
is_merged
text_lines[]     # linhas literais visíveis dentro da célula
text_literal     # junção com \n preservando quebras
text_status      # CLEAR | DOUBTFUL | ILLEGIBLE
```

**Quebra real entre linhas:** nova linha da grade (nova `row_index`).  
**Continuação na mesma célula:** múltiplos `text_lines` com mesmo `cell_id`.

## 5. Papéis funcionais (`role`) — anotação de referência

| Role | Uso |
|---|---|
| `set_code` / `set_description` | Identidade do conjunto na coluna Código/Descrição esquerdas |
| `subset_code` / `subset_description` | Subconjunto / cabo (ex.: `50225702`) |
| `item` | Identificador de item (A1, AE, …) |
| `quantity` | Quantidade |
| `component_code` | Código na coluna Componente |
| `component_description` | Descrição do componente |
| `header` | Cabeçalho |
| `admin` | Informação administrativa |
| `code_in_description` | Número que aparece na descrição mas não é a célula Código |
| `unknown` | Papel não evidente |

## 6. Relações

```text
TABLE → ROW → CELL → TEXT
PARENT_GROUP (set/subset cell) → COMPONENT_OCCURRENCE (item+qty+code+desc)
```

- Preservar `occurrence_id` único por (página, grupo pai, item, código, ordem visual).
- Mesmo código sob pais distintos = ocorrências distintas.

## 7. Contraste com defeitos históricos da EVA

Registrar em `eva_defect_contrast[]`:

| Campo | Regra |
|---|---|
| `eva_value` | Saída histórica (ex.: `10080192 10090316`) |
| `expected_visual` | O que o PDF mostra |
| `never_use_as_gt` | true |

## 8. Consistência entre revisores

Checklist mínimo por página: região; nº linhas/colunas; spans; A2≠A3 quando distintos; códigos em descrição marcados; pai→filhos; drawing_area vs table.

Métrica de acordo (proposta): IoU região ≥0,9; mesma `cell_id` com texto literal idêntico; roles iguais em campos críticos. Threshold final = owner.
