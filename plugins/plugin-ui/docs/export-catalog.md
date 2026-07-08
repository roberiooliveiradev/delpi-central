# Catálogo de exportação — plugins MFE

> Baseline: jul/2026 · Objetivo: **um motor shared** para formatos transversais; builders/UI de domínio ficam nos plugins.

## Formatos e fonte canônica

| Formato | Onde nasceu (mais completo) | Destino shared | Status |
|--------|------------------------------|----------------|--------|
| **CSV** (UTF-8 BOM, `;`) | `dashboard-*/src/export/exportUtils` | `@delpi/plugin-ui` → `export/` | ✅ E1 |
| **Excel / XLSX** (multi-sheet) | idem + multi-sheet | `@delpi/plugin-ui` | ✅ E1 |
| **PDF DELPI** (HTML + print) | `*/src/export/pdf/delpiDocument*` | `@delpi/plugin-ui` → `export/pdf/` | ✅ E1 |
| **UI botões** CSV/Excel/PDF · Excel+PDF · Excel só | clones por plugin | `@delpi/plugin-ui` → `ExportButtons` | ✅ E2 |
| **Matrix → tabular** | `exportDocument` ExportTable | `tableExportPayloadFromMatrix` / `exportMatrix*` | ✅ E3 |
| **PDF jsPDF** (seções campo+tabela) | production / eficiencia `exportDocument.ts` | `@delpi/plugin-ui` → `export/jspdf/` | ✅ E3 |
| **PNG gráfico** (SVG Recharts → canvas) | `minha-delpi-chat` `chartPngExport.ts` | `@delpi/plugin-ui` → `chartPngExport` | ✅ E3 |
| **PVA Excel** | `pedidos-venda-abertos` | `exportTableFormat` + `ExcelExportButton` | ✅ E3 (adiantado do E4) |
| **Markdown** | `drawingAnalysisExport` (chat) | manter no chat (domínio desenho) | — domínio |
| **CSV Excel-aware** (UTF-16 LE + `sep=;`) | `drawingAnalysisCsvEncoding` (chat) | opcional em plugin-ui | ⏳ se 2+ consumidores |
| **Download server-side** (blob API) | transformometro, PAC, propostas | helper `triggerBlobDownload` já shared; fetch fica no plugin | parcial |

## Contrato canônico (`TableExportPayload`)

```ts
type TableExportPayload = {
  title: string;
  columns: { key: string; label: string }[];
  rows: Record<string, unknown>[];
};
```

API do motor tabular:

- `exportTableFormat(payload, "csv" | "xlsx" | "pdf")`
- `exportPayloadsToXlsx` / `ToCsv` / `ToPdf` (multi-tabela)
- `runTabularExport({ kind: "table" | "tables", ... })`
- `tableExportPayloadFromMatrix` / `exportMatrixToXlsx` / `exportMatrixTableFormat`
- PDF DELPI: `buildDelpiDocumentHtml` + `printDelpiDocumentSpec`

API jsPDF (peer opcional `jspdf` + `jspdf-autotable`):

- `exportTableExcel` / `exportTablePdf` / `exportDocumentExcel` / `exportDocumentPdf`
- `sanitizePdfText`

API PNG:

- `prepareSvgCloneForRasterExport` / `rasterizeSvgElement` / `exportSvgElementToPng`

## Componentes UI (`@delpi/plugin-ui`)

| Componente | Uso | Classes |
|------------|-----|---------|
| `TabularExportButtons` | CSV · Excel · PDF (dashboards) | `className` / `buttonClassName` BEM do plugin |
| `DocumentExportActions` | Excel + PDF (ícones spreadsheet/file) | production, eficiência-fabril |
| `ExcelExportButton` | só Excel | controle-retrabalhos, PVA |
| `createDashboardTabularExportButtons({ prefix })` | factory com prefixo BEM | opcional |

## Famílias ainda locais

| Família | Plugins | Ação |
|---------|---------|------|
| Builders de domínio | dashboards, OEE/OTD, CR, CX | **permanecem** |
| Chat presentation/drawing (markdown, CSV UTF-16) | minha-delpi-chat | domínio; PNG núcleo shared |
| Transformometro `html-to-image` | diagramas | domínio distinto |

## Fases

| Fase | Escopo | Status |
|------|--------|--------|
| **E1** | Motor tabular + PDF DELPI; piloto commercial | ✅ |
| **E2** | Botões shared + 7 dashboards reexportam motor | ✅ |
| **E3** | Matrix bridge + jsPDF shared + PNG chart + PVA + CX tabular | ✅ |
| **E4** | CSV Excel-aware drawing (chat) | ⏳ backlog — só se ≥2 consumidores; ver residual no [refactoring-roadmap.md](./refactoring-roadmap.md) § 7 |

## Como consumir

```ts
import {
  exportTableFormat,
  exportMatrixToXlsx,
  exportTablePdf,
  exportSvgElementToPng,
  type TableExportPayload,
  type ExportTable,
} from "@delpi/plugin-ui";

exportMatrixToXlsx({ title: "OEE", headers: ["A"], rows: [["1"]] }, "oee-apontamentos");
await exportTablePdf(table, "apontamentos");
exportSvgElementToPng(svg, { width: 640, height: 280, filename: "grafico" });
```

Dashboards: `src/export/exportUtils.ts` e `pdf/index.ts` são **wrappers finos** (subtítulo PDF por produto).

## Dependências

- `xlsx` — peer opcional (Excel tabular e jsPDF Excel).
- `jspdf` + `jspdf-autotable` — peers opcionais (só quem chama `export/jspdf`).
- PDF DELPI = print HTML; **não** depende de jsPDF.

## Referências

- Playbook UI: [refactoring-roadmap.md](./refactoring-roadmap.md)
- Doc comercial: `dashboard-commercial/docs/export.md`
