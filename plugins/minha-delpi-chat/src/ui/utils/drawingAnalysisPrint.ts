import type { DrawingAnalysisExportPayload } from "./drawingAnalysisExport";
import {
  buildDelpiDocumentHtml,
  resolveDelpiLogoUrl,
} from "../../export/pdf/delpiDocumentHtml";
import { printDelpiDocumentHtml } from "../../export/pdf/delpiDocumentPrint";
import type { DelpiDocumentBadgeTone, DelpiDocumentSpec } from "../../export/pdf/types";

export type DrawingExportTable = NonNullable<
  DrawingAnalysisExportPayload["tables"]
>[number];

function resolveSealTone(drawingAnalysis?: Record<string, unknown>): DelpiDocumentBadgeTone {
  const status = String(drawingAnalysis?.status || "").toLowerCase();

  if (status === "approved" || status === "ok") {
    return "approved";
  }

  if (status === "rejected") {
    return "rejected";
  }

  const label = String(drawingAnalysis?.overallLabel || "").toLowerCase();

  if (label.includes("reprov")) {
    return "rejected";
  }

  if (label.includes("aprov")) {
    return "approved";
  }

  return "neutral";
}

function buildDrawingDocumentSpec(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): DelpiDocumentSpec {
  const exportLabels = exportPayload.exportLabels ?? {};
  const productCode = String(drawingAnalysis?.productCode || "—");
  const overall = String(drawingAnalysis?.overallLabel ?? "—");
  const critical = drawingAnalysis?.criticalErrors;
  const documentTitle = String(
    exportLabels.pdfTitle || "Relatório de Análise de Desenho DELPI",
  );
  const subtitle = String(
    exportLabels.pdfSubtitle || "Validação técnica PDF × API DELPI",
  );

  const summaryLines = [
    {
      label: String(exportLabels.pdfSummaryProduct || "Produto"),
      value: productCode,
    },
    {
      label: String(exportLabels.pdfSummaryStatus || "Status geral"),
      value: overall,
    },
  ];

  if (critical != null) {
    summaryLines.push({
      label: String(exportLabels.pdfSummaryCritical || "Erros críticos"),
      value: String(critical),
    });
  }

  const criticalSuffix =
    critical != null
      ? ` · ${String(exportLabels.pdfSummaryCritical || "Erros críticos")}: ${String(critical)}`
      : "";

  return {
    documentTitle,
    subtitle,
    badge: overall,
    badgeTone: resolveSealTone(drawingAnalysis),
    runningMeta: `${String(exportLabels.pdfSummaryProduct || "Produto")}: ${productCode} · ${String(
      exportLabels.pdfSummaryStatus || "Status",
    )}: ${overall}${criticalSuffix}`,
    summaryLines,
    tables: (exportPayload.tables ?? []).map((table) => ({
      title: table.title,
      columns: table.columns,
      rows: table.rows,
      highlightStatusColumn: true,
    })),
    footerNote: String(
      exportLabels.pdfFooterNote || "Relatório gerado eletronicamente pelo Minha DELPI.",
    ),
    footerContext: productCode,
  };
}

export function buildDrawingAnalysisReportHtml(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
  logoUrl?: string,
): string {
  return buildDelpiDocumentHtml(
    buildDrawingDocumentSpec(exportPayload, drawingAnalysis),
    logoUrl ?? resolveDelpiLogoUrl(),
  );
}

export function printDrawingAnalysisReport(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): boolean {
  const html = buildDrawingAnalysisReportHtml(exportPayload, drawingAnalysis);
  return printDelpiDocumentHtml(html, {
    iframeTitle: "Relatório de análise de desenho",
  });
}
