# Chat Presentation Hub — Spec → compiler → renderPlan → MFE

**Status:** vigente (Presentation Composer universal)  
**Escopo:** pipeline de apresentação da `minha-delpi-ai-api` + renderização no `plugins/minha-delpi-chat`

Complementa [`presentation-intelligence.md`](./presentation-intelligence.md) (miolo PI) e o hub MFE [`plugins/minha-delpi-chat/docs/chat-presentation-hub.md`](../../../plugins/minha-delpi-chat/docs/chat-presentation-hub.md) (orquestração `chatPresentation.ts`).

## Fluxo canônico

```text
tool payload + responseSchema
→ slots schema-driven (table | chart | kpi | tree | dashboard | text)
→ Presentation Intelligence (intent → PresentationSpec)
→ PresentationSpecCompiler + compilers por view
   ├── PresentationTableCompilerService   (columns vs exportColumns, sort, hiddenFields)
   ├── PresentationChartCompilerService   (mark, axes, paletteFamily)
   ├── PresentationKpiCompilerService
   └── PresentationDashboardCompilerService
→ ChatPresentationRenderPipelineService.finalize
   → renderPlan v1 (segmentos mecânicos)
→ metadata entregue ao MFE
→ MFE render-only (ChatRich*, Expand, export)
```

O MFE **não redecide** formato quando `renderPlan.version === 1`. Executa segmentos, slots e `presentationDecision` para toolbar/próximo turno.

## PresentationSpec (contrato semântico)

| Campo | Papel |
|-------|--------|
| `view` | `table` \| `chart` \| `kpi` \| `dashboard` \| `tree` \| `canvas` |
| `fields` | Ordem/filtro de colunas ou métricas visíveis |
| `sortField` / `sortDirection` | Ordenação tabular compilada nas rows |
| `table.hiddenFields` | Ocultos na grade — **não** removem dados das rows |
| `chart.mark` / `encoding` | Tipo visual (bar, line, heatmap, …) |
| `paletteFamily` | Família semântica de cores (allowlist) |

Validators e binders determinísticos produzem o `PresentationSpec` antes dos compilers.

## Compilers — visual vs exportação

### Tabela

`PresentationTableCompilerService` emite:

| Campo | Conteúdo |
|-------|----------|
| `columns` | Grade visual (exclui `hiddenFields`) |
| `exportColumns` | Colunas completas para CSV/XLSX/PDF |
| `config.hiddenFields` | Metadado de ocultação visual |
| `config.exportSourceUnchanged` | Rows intactas — export usa `exportColumns` |

O MFE (`exportUtils.resolveTableExportColumns`) prefere `exportColumns` quando presente.

### Gráfico / heatmap

`PresentationChartCompilerService` emite `config.paletteFamily` (preferencial) e `colors[]` legado opcional.

Resolução física de tokens: **`plugins/plugin-ui/src/theme/colorFamilyCatalog.ts`** — espelhado no chat via `mdcCssVars.ts` / `resolveColorFamily`.

Famílias canônicas: `brand`, `sequential-blue`, `cool`, `warm`, `diverging-status`, `status`, `categorical`.

## renderPlan v1

Fonte primária dos segmentos no MFE:

```json
{
  "renderPlan": {
    "version": 1,
    "segments": [
      { "kind": "markdown", "source": "assistantMessage" },
      { "kind": "table", "source": "tablePresentation" }
    ]
  }
}
```

Modos explícitos (`sessionResponseFormat`: tabela, gráfico, painel, canvas) sincronizam decisão + plano antes do stream.

## MFE — consumo

| Camada | Responsabilidade |
|--------|------------------|
| `presentation/presentationMetadataReaders.ts` | Leitura de slots/metadata |
| `presentation/segmentBuilders/` | Monta UI a partir do `renderPlan` |
| `presentation/ChatRich*.tsx` | Render por tipo (table, chart, kpi, dashboard, tree) |
| `presentation/export/exportUtils.ts` | Export CSV/XLSX/PDF — `exportColumns` > `columns` |
| `canvas/ChatExpandModal.tsx` | Expand + toolbar de export |

## Color Family Catalog

| Camada | Caminho |
|--------|---------|
| API (emissão semântica) | `PresentationChartCompilerService`, `PresentationSpec.paletteFamily` |
| Catálogo físico (tokens CSS) | `plugins/plugin-ui/src/theme/colorFamilyCatalog.ts` |
| Resolução no chat MFE | `plugins/minha-delpi-chat/src/ui/theme/mdcCssVars.ts` |

Regra: API emite **ID semântico**; MFE/plugin-ui resolve para `var(--mdc-chart-series-*)` ou heatmap — nunca hex solto no payload operacional.

## Referências

- [`presentation-intelligence.md`](./presentation-intelligence.md) — orchestrator, composer LLM, evals
- [`../changelog/2026-06-p6-renderplan-modos-apresentacao.md`](../changelog/2026-06-p6-renderplan-modos-apresentacao.md) — modos e renderPlan
- [`../../../plugins/minha-delpi-chat/docs/export.md`](../../../plugins/minha-delpi-chat/docs/export.md) — formatos de exportação
- [`../../../plugins/plugin-ui/README.md`](../../../plugins/plugin-ui/README.md) — `colorFamilyCatalog` export
