## Conversão de unidades Protheus — análise de desenho DELPI

Use ao explicar quantidades do PDF × SG1010/SB1010. O **checklist técnico** (`drawingAnalysis.items[]`) já aplica as regras no pipeline — esta policy orienta **narrativa e esclarecimentos** ao usuário.

### Fontes canônicas

| Contexto | Protheus | api-delpi |
|----------|----------|-----------|
| Quantidade na BOM | `SG1010.G1_QUANT` | `structure.items[].quantity` |
| UM do componente | `SB1010.B1_UM` | `structure.items[].unit` |
| Fator UM principal ↔ segunda | **`B1_CONV`** + **`B1_TIPCONV`** (`M` multiplica, `D` divide) | `conversion_factor`, `conversion_type`, `secondary_unit` |
| Base «por 1 PA» (PA em MI) | 1 MI = milheiro | `pa_reference` no `/analyser` |
| Só descrição da UM | `SAH010` — **não calcula** | — |

RAG: `produto-conversao-unidades-protheus.txt` (tutorial completo).

### Regras para chicotes (PA `B1_UM = MI`)

1. Quantidades na estrutura vêm **por 1 PA / 1 MI** (milheiro), não por peça avulsa.
2. **Por 1 chicote (peça):** `qtd_estrutura ÷ 1000` (ou `÷ B1_CONV` do PA quando cadastrado).
3. **MT → mm (físico):** `qtd_MT × 1000 = mm`; depois dividir pelo fator milheiro se for normalizar por peça.
4. Exemplo tubo **10120073** com **650 MT** na SG1010: **650 mm de tubo por chicote** (`650 ÷ 1000 × 1000 mm`).
5. Cotas de **cabos** (785/792 mm) vêm dos intermediários **50xx** — não confundir com consumo de tubo isolante em MT.

### O que o LLM **não** faz

- Não recalcula status OK/Pendente/Crítico — só o pipeline.
- Não usa `SAH010` para fator de conversão.
- Não mistura conversão fiscal (`SB5010.B5_CONVDIP`) com BOM produtiva.

### Ordem de autoridade

**Pipeline (`ChatDrawingBomQuantitySemanticsService`) → API `/analyser` → esta policy / RAG.**
