/** PDF DELPI — motor canônico em @delpi/plugin-ui. */
import {
  exportChartPayloadToPdf as sharedExportChartPayloadToPdf,
  exportTablePayloadToPdf as sharedExportTablePayloadToPdf,
  exportTablePayloadsToPdf as sharedExportTablePayloadsToPdf,
  buildDelpiDocumentStyles,
  buildDelpiBrandBarHtml,
  buildDelpiDocumentHtml,
  buildDelpiDocumentTableSection,
  buildDefaultExportSummaryLines,
  escapeDelpiDocumentHtml,
  resolveDelpiLogoUrl,
  printDelpiDocumentHtml,
  printDelpiDocumentSpec,
  type TableExportPayload,
  type ExportPdfOptions,
  type DelpiDocumentBadgeTone,
  type DelpiDocumentColumn,
  type DelpiDocumentImageSection,
  type DelpiDocumentSpec,
  type DelpiDocumentSummaryLine,
  type DelpiDocumentTable,
} from "@delpi/plugin-ui/index";

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
};

export type {
  DelpiDocumentBadgeTone,
  DelpiDocumentColumn,
  DelpiDocumentImageSection,
  DelpiDocumentSpec,
  DelpiDocumentSummaryLine,
  DelpiDocumentTable,
};

const PDF_SUBTITLE = "Minha DELPI · Dashboard Comercial";

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
