import { chatAlert } from "../../ui/utils/chatNativeDialogs";
import type { TableExportPayload } from "../types";
import {
  buildDefaultExportSummaryLines,
  buildDelpiDocumentHtml,
  buildDelpiDocumentTableSection,
  resolveDelpiLogoUrl,
} from "./delpiDocumentHtml";
import { printDelpiDocumentHtml } from "./delpiDocumentPrint";
import type { DelpiDocumentSpec, DelpiDocumentTable } from "./types";

const DEFAULT_SUBTITLE = "Minha DELPI · Exportação de dados";

function toDocumentTable(payload: TableExportPayload): DelpiDocumentTable {
  return {
    title: payload.title,
    columns: payload.columns,
    rows: payload.rows,
  };
}

function buildTableExportSpec(
  title: string,
  tables: DelpiDocumentTable[],
  options?: {
    subtitle?: string;
    imageSections?: DelpiDocumentSpec["imageSections"];
    summaryLines?: DelpiDocumentSpec["summaryLines"];
  },
): DelpiDocumentSpec {
  const recordCount = tables.reduce((total, table) => total + table.rows.length, 0);

  return {
    documentTitle: title,
    subtitle: options?.subtitle || DEFAULT_SUBTITLE,
    runningMeta: `${recordCount} registro${recordCount === 1 ? "" : "s"}`,
    summaryLines: options?.summaryLines || buildDefaultExportSummaryLines(recordCount),
    tables,
    imageSections: options?.imageSections,
    footerContext: title,
  };
}

export function printDelpiDocumentSpec(spec: DelpiDocumentSpec): boolean {
  const html = buildDelpiDocumentHtml(spec, resolveDelpiLogoUrl());
  return printDelpiDocumentHtml(html, { iframeTitle: spec.documentTitle });
}

export function exportTablePayloadToPdf(payload: TableExportPayload): void {
  if (!payload.columns.length) {
    chatAlert("Não há dados para exportar em PDF.");
    return;
  }

  const opened = printDelpiDocumentSpec(
    buildTableExportSpec(payload.title, [toDocumentTable(payload)]),
  );

  if (!opened) {
    chatAlert("Não foi possível abrir a janela de impressão. Verifique o bloqueador de pop-ups.");
  }
}

export function exportTablePayloadsToPdf(title: string, payloads: TableExportPayload[]): void {
  const tables = payloads
    .filter((payload) => payload.columns.length)
    .map(toDocumentTable);

  if (!tables.length) {
    chatAlert("Não há dados para exportar em PDF.");
    return;
  }

  const opened = printDelpiDocumentSpec(buildTableExportSpec(title, tables));

  if (!opened) {
    chatAlert("Não foi possível abrir a janela de impressão. Verifique o bloqueador de pop-ups.");
  }
}

export function exportChartPayloadToPdf(
  title: string,
  payload: TableExportPayload,
  chartDataUrl: string | null,
): void {
  const tables = payload.columns.length ? [toDocumentTable(payload)] : [];
  const imageSections = chartDataUrl
    ? [{ title: "Visualização", dataUrl: chartDataUrl, alt: title }]
    : undefined;

  if (!tables.length && !imageSections?.length) {
    chatAlert("Não há dados para exportar em PDF.");
    return;
  }

  const opened = printDelpiDocumentSpec(
    buildTableExportSpec(title, tables, {
      imageSections,
      summaryLines: buildDefaultExportSummaryLines(payload.rows.length),
    }),
  );

  if (!opened) {
    chatAlert("Não foi possível abrir a janela de impressão. Verifique o bloqueador de pop-ups.");
  }
}

export { buildDelpiDocumentTableSection };
