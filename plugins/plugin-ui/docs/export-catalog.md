# Catálogo de exportação — plugins MFE

> Baseline: jul/2026 · Objetivo: **um motor shared** para formatos transversais; builders/UI de domínio ficam nos plugins.

## Formatos e fonte canônica

| Formato | Onde nasceu (mais completo) | Destino shared | Status |
|--------|------------------------------|----------------|--------|
| **CSV** (UTF-8 BOM, `;`) | `dashboard-*/src/export/exportUtils` (= chat núcleo) | `@delpi/plugin-ui` → `export/` | ✅ Fase E1 |
| **Excel / XLSX** (multi-sheet) | idem + multi-sheet | `@delpi/plugin-ui` | ✅ Fase E1 |
| **PDF DELPI** (HTML + print) | `*/src/export/pdf/delpiDocument*` (9 cópias) | `@delpi/plugin-ui` → `export/pdf/` | ✅ Fase E1 |
| **PDF jsPDF** (seções campo+tabela) | `dashboard-production` / `eficiencia-fabril` `exportDocument.ts` | avaliar facade ou 2º motor | ⏳ Fase E3 |
| **PNG gráfico** (SVG Recharts → canvas) | `minha-delpi-chat` `chartPngExport.ts` | `@delpi/plugin-ui` | ⏳ Fase E2 |
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

API:

- `exportTableFormat(payload, "csv" | "xlsx" | "pdf")`
- `exportPayloadsToXlsx` / `ToCsv` / `ToPdf` (multi-tabela)
- `sanitizeFilename` / `sanitizeSheetName` / `csvCell` / `triggerBlobDownload`
- PDF: `buildDelpiDocumentHtml` + `printDelpiDocumentSpec`

## Famílias ainda locais (não misturar no motor)

| Família | Plugins | Ação |
|---------|---------|------|
| Builders de domínio (`*DashboardSheets`, `commercialExportBuilders`) | cada dashboard | **permanecem** no plugin |
| `*ExportButtons` / dispatch | cada dashboard + chat | UI local → futuro `TabularExportButtons` genérico (E2) |
| `exportDocument` / `ExportTable` (headers+rows matrix) | production, eficiencia, CR | adapter → `TableExportPayload` (E3) |
| Export Outliers rudimentares | PVA `exportPedidosExcel`, utils/csv legado | migrar para `exportTableFormat` (E2) |
| Server PDF/XLSX (PAC, transformometro, propostas) | API blob | só `triggerBlobDownload` |

## Fases

| Fase | Escopo | Meta |
|------|--------|------|
| **E1** | Motor tabular + PDF DELPI em `plugin-ui`; piloto `dashboard-commercial` | ✅ |
| **E2** | Migrar outros 7 `dashboard-*` + chat reexport; PNG chart; botões genéricos | próximo |
| **E3** | Bridge `ExportTable` ↔ payload; reduzir `ExportActions` duplicados; limpar `utils/csv.ts` | |
| **E4** | Outliers (PVA, CR) e doc commercial PNG (se implementar) | |

## Piloto E1

`dashboard-commercial/src/export/{exportUtils,primitives,exportAlert,pdf,types}` reexportam `@delpi/plugin-ui` (subtítulo PDF Comercial preservado). Builders e `CommercialExportButtons` / `dispatch` ficam locais.

## Dependências

- `xlsx` — peer **opcional** de `@delpi/plugin-ui` (dynamic import). O plugin que chama Excel deve declarar `xlsx` no `package.json`.
- Sem `jspdf` no motor E1 (PDF = print HTML certificado).

## Como consumir

```ts
import {
  exportTableFormat,
  exportPayloadsToXlsx,
  type TableExportPayload,
} from "@delpi/plugin-ui";

exportTableFormat(payload, "xlsx");
```

## Referências

- Inventário pré-centralização: conversa jul/2026 (agent transcript)
- Doc comercial legada (PNG prometido): `dashboard-commercial/docs/export.md` — PNG ainda só no chat
- Playbook UI: [refactoring-roadmap.md](./refactoring-roadmap.md)
