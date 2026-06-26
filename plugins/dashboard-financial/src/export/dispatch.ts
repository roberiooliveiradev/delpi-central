import {
  exportPayloadsToCsv,
  exportPayloadsToPdf,
  exportPayloadsToXlsx,
  exportTableFormat,
} from "./exportUtils";
import type {FinancialExportRequest} from "./types";

const DASHBOARD_SUBTITLE = "Minha DELPI · Dashboard Financeiro";

export function runFinancialExport(request: FinancialExportRequest): void {
  switch (request.kind) {
    case "table":
      exportTableFormat(request.payload, request.format);
      return;
    case "dashboard": {
      const sheets = request.context.sheets.filter(
        (sheet) => sheet.columns.length > 0,
      );
      if (request.format === "xlsx") {
        exportPayloadsToXlsx(request.context.documentTitle, sheets);
        return;
      }
      if (request.format === "pdf") {
        exportPayloadsToPdf(request.context.documentTitle, sheets, {
          subtitle: DASHBOARD_SUBTITLE,
        });
        return;
      }
      exportPayloadsToCsv(request.context.documentTitle, sheets);
      return;
    }
    default: {
      const _exhaustive: never = request;
      return _exhaustive;
    }
  }
}
