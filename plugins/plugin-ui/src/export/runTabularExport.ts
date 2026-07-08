import {
  exportPayloadsToCsv,
  exportPayloadsToPdf,
  exportPayloadsToXlsx,
  exportTableFormat,
  type ExportPdfOptions,
} from "./exportUtils";
import type { TableExportPayload, TabularExportFormat } from "./types";

export type TabularExportRequest =
  | {
      kind: "table";
      payload: TableExportPayload;
      format: TabularExportFormat;
      pdf?: ExportPdfOptions;
    }
  | {
      kind: "tables";
      title: string;
      payloads: TableExportPayload[];
      format: TabularExportFormat;
      pdf?: ExportPdfOptions;
    };

/**
 * Dispatch genérico table / multi-tabela → motor shared.
 * Builders de domínio montam os payloads; este helper só escolhe o formato.
 */
export function runTabularExport(request: TabularExportRequest): void {
  if (request.kind === "table") {
    exportTableFormat(request.payload, request.format, request.pdf);
    return;
  }

  if (request.format === "xlsx") {
    exportPayloadsToXlsx(request.title, request.payloads);
    return;
  }

  if (request.format === "pdf") {
    exportPayloadsToPdf(request.title, request.payloads, request.pdf);
    return;
  }

  exportPayloadsToCsv(request.title, request.payloads);
}
