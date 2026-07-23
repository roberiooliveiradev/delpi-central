# TextRun Delpi ↔ Google Slides / Canva

Modelo canônico de formatação parcial na caixa visual do TV Dashboard.

## Referência externa

| App | Modelo | Princípio |
|-----|--------|-----------|
| [Google Slides](https://developers.google.com/workspace/slides/api/concepts/text) | `ParagraphMarker` + `TextRun` | Estilo de caractere no run; parágrafo no marker; runs **não cruzam** parágrafo; update por **range** cria/funde runs |
| [Canva Apps SDK](https://www.canva.dev/docs/apps/api/latest/design-create-richtext-range/) | `RichtextRange` / `readTextRegions` | Regiões com formatting; UI só age com seleção; preservar estilo no replace |
| PowerPoint | TextFrame + runs | Caixa = frame; formatação de caractere por run |

## Modelo Delpi

- Tipo: `ComunicadoContentRun` / `ComunicadoContentRunStyle` (`comunicadoTypes.ts`)
- Kit compartilhado (KPI/chart/input): `DeckContentRun` (`plugin-ui` → `deckContentRuns.tsx`)
- Persistência: `content` (plano) + `contentRuns?` (omitido quando equivalente ao plano)

## Pipeline canônico

```
Seleção parcial → ribbon (FormatRibbonTypography)
  → applyContentRunStyleInRange / toggle / list / namedStyle
  → content + contentRuns
  → paint: ComunicadoTextSurface → ComunicadoTextRunsView
```

**Não** pintar `block.content` cru quando houver runs — sempre `ComunicadoTextSurface` (heading / text / shape) ou `DeckContentRunsView` (parts KPI/chart/input).

## Superfícies

| Superfície | Contrato |
|------------|----------|
| heading / text / shape | `ComunicadoTextSurface` |
| KPI title/hint | `part.content` + `part.contentRuns?` |
| Chart title | idem |
| canvas_table cell | `text` + `contentRuns?` (sem runs = run implícito com `cell.style`) |
| input label/badge | `InputPartState.content` + `contentRuns?` |
| valor KPI dinâmico | só `part.style` (sem formatação por dígito) |

## Efeitos tipográficos

Sombra / stroke / reflexo permanecem no **nível caixa** (`block.style` / `part.style`) nesta fase — não entram no patch de trecho até evolução futura alinhada ao Slides.

## Edição

Bridge único: `useVisualBoxTextEditorBridge` (text/heading/shape) e `createPartTextEditorBridge` (KPI/chart). Ribbon: seleção parcial → runs; senão → estilo do alvo (bloco/part).
