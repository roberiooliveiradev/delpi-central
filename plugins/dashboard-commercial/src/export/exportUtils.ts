/**
 * Reexporta o motor tabular canônico (`@delpi/plugin-ui`).
 * Mantém subtítulo do PDF Comercial e API estável para builders/dispatch locais.
 */

import {
  triggerFileDownload,
  triggerBlobDownload,
  csvCell,
  buildUtf8CsvBlob,
  sanitizeFilename,
  sanitizeSheetName,
  exportAlert,
  configureExportAlert,
  exportPayloadToCsv,
  exportPayloadToXlsx,
  exportPayloadsToCsv,
  exportPayloadsToXlsx,
  TABULAR_EXPORT_ACTIONS,
  exportPayloadToPdf as sharedExportPayloadToPdf,
  exportPayloadsToPdf as sharedExportPayloadsToPdf,
  exportTableFormat as sharedExportTableFormat,
  type TabularExportFormat,
  type ExportAction,
  type ExportColumn,
  type TableExportPayload,
  type ExportAlertFn,
  type ExportPdfOptions,
} from "@delpi/plugin-ui/index";

export {
  triggerFileDownload,
  triggerBlobDownload,
  csvCell,
  buildUtf8CsvBlob,
  sanitizeFilename,
  sanitizeSheetName,
  exportAlert,
  configureExportAlert,
  exportPayloadToCsv,
  exportPayloadToXlsx,
  exportPayloadsToCsv,
  exportPayloadsToXlsx,
  TABULAR_EXPORT_ACTIONS,
};

export type {
  TabularExportFormat,
  ExportAction,
  ExportColumn,
  TableExportPayload,
  ExportAlertFn,
  ExportPdfOptions,
};

const COMMERCIAL_PDF_SUBTITLE = "Minha DELPI · Dashboard Comercial";

export function exportPayloadToPdf(
  payload: TableExportPayload,
  options?: ExportPdfOptions,
): void {
  sharedExportPayloadToPdf(payload, {
    subtitle: options?.subtitle ?? COMMERCIAL_PDF_SUBTITLE,
  });
}

export function exportPayloadsToPdf(
  title: string,
  payloads: TableExportPayload[],
  options?: ExportPdfOptions,
): void {
  sharedExportPayloadsToPdf(title, payloads, {
    subtitle: options?.subtitle ?? COMMERCIAL_PDF_SUBTITLE,
  });
}

export function exportTableFormat(
  payload: TableExportPayload,
  format: TabularExportFormat,
  options?: ExportPdfOptions,
): void {
  sharedExportTableFormat(payload, format, {
    subtitle: options?.subtitle ?? COMMERCIAL_PDF_SUBTITLE,
  });
}
