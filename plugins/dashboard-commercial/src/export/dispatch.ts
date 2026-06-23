import {
  buildDashboardExportSheets,
  buildDetailExportSheets,
} from "./commercialExportBuilders";
import {
  exportPayloadsToCsv,
  exportPayloadsToPdf,
  exportPayloadsToXlsx,
  exportTableFormat,
} from "./exportUtils";
import { exportChartPayloadToPdf } from "./pdf/tablePdfExport";
import { rasterizeChartElement } from "./chartPngExport";
import type { CommercialExportRequest } from "./types";

const DASHBOARD_SUBTITLE = "Minha DELPI · Dashboard Comercial";
const DETAIL_SUBTITLE = "Minha DELPI · Detalhe comercial";

export function runCommercialExport(request: CommercialExportRequest): void {
  switch (request.kind) {
    case "table":
      if (request.format === "pdf" && request.chartRoot) {
        void rasterizeChartElement(request.chartRoot).then((dataUrl) => {
          exportChartPayloadToPdf(request.payload.title, request.payload, dataUrl);
        });
        return;
      }
      exportTableFormat(request.payload, request.format);
      return;
    case "tables":
      if (request.format === "xlsx") {
        exportPayloadsToXlsx(request.title, request.payloads);
        return;
      }
      exportPayloadsToPdf(request.title, request.payloads);
      return;
    case "dashboard": {
      const sheets = buildDashboardExportSheets(request.context);
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
    case "detail": {
      const sheets = buildDetailExportSheets(request.context);
      if (request.format === "xlsx") {
        exportPayloadsToXlsx(request.context.documentTitle, sheets);
        return;
      }
      if (request.format === "pdf") {
        exportPayloadsToPdf(request.context.documentTitle, sheets, {
          subtitle: DETAIL_SUBTITLE,
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
