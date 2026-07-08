/** PDF DELPI — motor canônico em @delpi/plugin-ui. */
import {
  exportChartPayloadToPdf as sharedExportChartPayloadToPdf,
  exportTablePayloadToPdf as sharedExportTablePayloadToPdf,
  exportTablePayloadsToPdf as sharedExportTablePayloadsToPdf,
  type TableExportPayload,
  type ExportPdfOptions,
} from "@delpi/plugin-ui";

export {
  buildDelpiDocumentStyles,
  buildDelpiBrandBarHtml,
  buildDelpiDocumentHtml,
  buildDelpiDocumentTableSection,
  buildDefaultExportSummaryLines,
  escapeDelpiDocumentHtml,
  resolveDelpiLogoUrl,
  printDelpiDocumentHtml,
  printDelpiDocumentSpec,
} from "@delpi/plugin-ui";

export type {
  DelpiDocumentBadgeTone,
  DelpiDocumentColumn,
  DelpiDocumentImageSection,
  DelpiDocumentSpec,
  DelpiDocumentSummaryLine,
  DelpiDocumentTable,
} from "@delpi/plugin-ui";

const PDF_SUBTITLE = "Minha DELPI · Dashboard Engenharia";

export function exportTablePayloadToPdf(
  payload: TableExportPayload,
  options?: ExportPdfOptions,
): void {
  sharedExportTablePayloadToPdf(payload, {
    subtitle: options?.subtitle ?? PDF_SUBTITLE,
  });
}

export function exportTablePayloadsToPdf(
  title: string,
  payloads: TableExportPayload[],
  options?: ExportPdfOptions,
): void {
  sharedExportTablePayloadsToPdf(title, payloads, {
    subtitle: options?.subtitle ?? PDF_SUBTITLE,
  });
}

export function exportChartPayloadToPdf(
  title: string,
  payload: TableExportPayload,
  chartDataUrl: string | null,
  options?: ExportPdfOptions,
): void {
  sharedExportChartPayloadToPdf(title, payload, chartDataUrl, {
    subtitle: options?.subtitle ?? PDF_SUBTITLE,
  });
}
