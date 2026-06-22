# Exportação — módulo centralizado (Minha DELPI Chat)

> Atualizado em **22/06/2026** — `src/export/` (dispatch + PDF certificado DELPI).

## Princípio

Toda exportação do chat (CSV, Excel, PDF, PNG, Markdown de desenho) passa por **`src/export/`**.  
**Não** duplicar `triggerDownload`, `sanitizeFilename` ou layout PDF em componentes.

| Formato | Apresentação rica | Relatório de desenho |
|---------|-------------------|----------------------|
| CSV | `exportPresentation(..., "csv")` | `runChatExport({ kind: "drawing", format: "csv" })` |
| Excel | `"xlsx"` | `"xlsx"` |
| PDF | `"pdf"` — layout certificado DELPI | `"pdf"` — mesmo layout |
| PNG | `exportChartElementToPng` (gráficos) | — |
| Markdown | — | `"markdown"` |

## Estrutura

```text
src/export/
├── index.ts                 # Barrel público — importar daqui
├── types.ts                 # TabularExportFormat, ChatExportRequest, TableExportPayload
├── primitives.ts            # csvCell, sanitizeFilename, triggerFileDownload
├── dispatch.ts              # runChatExport(), resolveDrawingExportActions()
├── ChatExportButtons.tsx    # UI unificada (apresentação + desenho)
└── pdf/                     # PDF certificado DELPI (HTML + window.print)
    ├── delpiDocumentStyles.ts
    ├── delpiDocumentHtml.ts   # buildDelpiDocumentHtml()
    ├── delpiDocumentPrint.ts  # printDelpiDocumentHtml()
    ├── tablePdfExport.ts      # exportTablePayloadToPdf, exportChartPayloadToPdf
    └── types.ts               # DelpiDocumentSpec

src/ui/components/presentation/export/   # Payloads CSV/XLSX + PNG + lousa
    exportUtils.ts             # build*ExportPayload, exportPresentation (CSV/XLSX/PDF delega ao pdf/)
    chartPngExport.ts
    chartCanvasMarkdown.ts
    dashboardExportCsv.ts

src/ui/utils/
    drawingAnalysisExport.ts   # CSV/XLSX/MD do metadata da API
    drawingAnalysisPrint.ts    # Wrapper desenho → buildDelpiDocumentHtml()
```

## API recomendada

```typescript
import {
  runChatExport,
  exportPresentation,
  ChatPresentationExportButtons,
  ChatDrawingExportButtons,
  exportTablePayloadToPdf,
  buildDelpiDocumentHtml,
} from "../export";

// Apresentação rica (toolbar ChatRich*)
runChatExport({
  kind: "presentation",
  presentation,
  format: "pdf",
  options: { tableRows, chartRoot },
});

// Relatório de análise de desenho
runChatExport({
  kind: "drawing",
  payload: metadata.drawingAnalysisExport,
  format: "pdf",
  drawingAnalysis: metadata.drawingAnalysis,
});
```

Consumo legado ainda válido: `import { exportPresentation } from "./presentation/export"`.

## PDF — layout certificado DELPI

**Todos** os PDFs do chat (tabela, gráfico, dashboard, desenho) usam o **mesmo** pipeline:

1. Montar `DelpiDocumentSpec` (título, subtítulo, tabelas, imagem opcional, selo opcional).
2. `buildDelpiDocumentHtml(spec, logoUrl)` — HTML A4 com logo, faixa de cores, cabeçalho repetível, rodapé `www.delpi.com.br`.
3. `printDelpiDocumentHtml(html)` — janela ou iframe + diálogo de impressão do navegador («Salvar como PDF»).

Logo: `{origin}/logoDelpi.svg` (servido pelo gateway/portal).

**Não usar** jsPDF/autotable para apresentação rica — removido em jun/2026 (`f3fd1113`).

| Caso | Módulo |
|------|--------|
| Tabela / KPI / árvore | `exportTablePayloadToPdf` |
| Gráfico | Raster SVG → PNG + tabela de dados em `exportChartPayloadToPdf` |
| Dashboard multi-painel | `exportTablePayloadsToPdf` |
| Desenho técnico | `drawingAnalysisPrint.ts` → spec com selo de status + tabelas checklist |

## UI

| Componente | Uso |
|------------|-----|
| `ChatPresentationExportButtons` | Toolbar `ChatRichTable`, `ChatRichChart`, KPI, árvore, dashboard |
| `ChatDrawingExportButtons` | Rodapé da mensagem com `metadata.drawingAnalysisExport` |

## Testes

```bash
cd plugins/minha-delpi-chat
npm run typecheck
npm test -- src/export src/ui/utils/drawingAnalysisExport.test.ts \
  src/ui/components/presentation/export/exportUtils.test.ts
```

## O que NÃO fazer

- Novo `if (format === "pdf")` com jsPDF em componente ou hook.
- Copiar CSS/HTML do certificado fora de `src/export/pdf/`.
- `triggerDownload` local — usar `triggerFileDownload` de `src/export/primitives.ts`.
- Bypass de `runChatExport` para novo botão de exportação na timeline.

## Referências

- Estrutura MFE: [`component-structure.md`](./component-structure.md)
- Hub apresentação: [`chat-presentation-hub.md`](./chat-presentation-hub.md)
- Desenho (API): [`chat-intelligence-base.md`](../../../minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md) § validação desenho
- Conversão MI→UN (api-delpi): [`playbook-conversao-unidades-protheus.md`](../../../api-delpi/docs/roadmaps/playbook-conversao-unidades-protheus.md) § 3.4
