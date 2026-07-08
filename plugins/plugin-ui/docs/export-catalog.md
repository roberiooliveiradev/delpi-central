# Catálogo de exportação — plugins MFE

> Baseline: jul/2026 · Objetivo: **um motor shared** para formatos transversais; builders/UI de domínio ficam nos plugins.

## Formatos e fonte canônica

| Formato | Onde nasceu (mais completo) | Destino shared | Status |
|--------|------------------------------|----------------|--------|
| **CSV** (UTF-8 BOM, `;`) | `dashboard-*/src/export/exportUtils` (= chat núcleo) | `@delpi/plugin-ui` → `export/` | ✅ E1 |
| **Excel / XLSX** (multi-sheet) | idem + multi-sheet | `@delpi/plugin-ui` | ✅ E1 |
| **PDF DELPI** (HTML + print) | `*/src/export/pdf/delpiDocument*` | `@delpi/plugin-ui` → `export/pdf/` | ✅ E1 |
| **UI botões** CSV/Excel/PDF · Excel+PDF · Excel só | clones por plugin | `@delpi/plugin-ui` → `ExportButtons` | ✅ E2 |
| **PDF jsPDF** (seções campo+tabela) | `dashboard-production` / `eficiencia-fabril` `exportDocument.ts` | adapter matrix + avaliar 2º motor | ⏳ E3 |
| **PNG gráfico** (SVG Recharts → canvas) | `minha-delpi-chat` `chartPngExport.ts` | `@delpi/plugin-ui` | ⏳ E3 |
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

API do motor:

- `exportTableFormat(payload, "csv" | "xlsx" | "pdf")`
- `exportPayloadsToXlsx` / `ToCsv` / `ToPdf` (multi-tabela)
- `runTabularExport({ kind: "table" | "tables", ... })`
- `tableExportPayloadFromMatrix` — bridge `headers`/`rows` → payload
- `sanitizeFilename` / `sanitizeSheetName` / `csvCell` / `triggerBlobDownload`
- PDF: `buildDelpiDocumentHtml` + `printDelpiDocumentSpec`

## Componentes UI (`@delpi/plugin-ui`)

| Componente | Uso | Classes |
|------------|-----|---------|
| `TabularExportButtons` | CSV · Excel · PDF (dashboards) | `className` / `buttonClassName` BEM do plugin |
| `DocumentExportActions` | Excel + PDF (ícones spreadsheet/file) | production, eficiência-fabril |
| `ExcelExportButton` | só Excel | controle-retrabalhos |
| `createDashboardTabularExportButtons({ prefix })` | factory com prefixo BEM | opcional |

O plugin passa `onExport(format)` ou callbacks; **dispatch/builders de domínio permanecem locais**.

## Famílias ainda locais

| Família | Plugins | Ação |
|---------|---------|------|
| Builders de domínio (`*DashboardSheets`, `commercialExportBuilders`) | cada dashboard | **permanecem** |
| `*ExportButtons` wrappers + `dispatch` | dashboards | thin wrappers sobre `TabularExportButtons` ✅ |
| `exportDocument` / `ExportTable` (jsPDF) | production, eficiencia, CR | E3 — matrix adapter + motor ou facade |
| Chat presentation/drawing export | minha-delpi-chat | domínio; motor tabular pode reexportar depois |
| Outliers PVA / csv legado | pedidos-venda-abertos | migrar para `exportTableFormat` |

## Fases

| Fase | Escopo | Status |
|------|--------|--------|
| **E1** | Motor tabular + PDF DELPI; piloto commercial | ✅ |
| **E2** | Botões shared + 7 dashboards reexportam motor; wrappers UI production/ef/CR | ✅ |
| **E3** | Bridge jsPDF / matrix; PNG chart; limpar `utils/csv.ts` | próximo |
| **E4** | Outliers (PVA) e chat PDF/CSV-aware se 2+ consumidores | |

## Como consumir

```ts
import {
  TabularExportButtons,
  DocumentExportActions,
  ExcelExportButton,
  exportTableFormat,
  runTabularExport,
  tableExportPayloadFromMatrix,
  type TableExportPayload,
} from "@delpi/plugin-ui";

// UI (CSS do plugin)
<TabularExportButtons
  className="dc-export-actions"
  buttonClassName="dc-ghost-btn dc-export-actions__btn"
  onExport={(format) => runMyDomainExport(format)}
/>

// Motor
exportTableFormat(payload, "xlsx");
```

Dashboards: `src/export/exportUtils.ts` e `pdf/index.ts` são **wrappers finos** (subtítulo PDF por produto); builders e `dispatch` ficam no plugin.

## Dependências

- `xlsx` — peer **opcional** de `@delpi/plugin-ui` (dynamic import). O plugin que chama Excel deve declarar `xlsx`.
- Sem `jspdf` no motor tabular (PDF = print HTML certificado). jsPDF continua nos plugins de apontamento até E3.

## Referências

- Playbook UI: [refactoring-roadmap.md](./refactoring-roadmap.md)
- Doc comercial: `dashboard-commercial/docs/export.md`
