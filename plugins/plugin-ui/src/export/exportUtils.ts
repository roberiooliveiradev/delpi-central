import { exportAlert } from "./exportAlert";
import {
  buildUtf8CsvBlob,
  csvCell,
  sanitizeFilename,
  sanitizeSheetName,
  triggerFileDownload,
} from "./primitives";
import {
  exportTablePayloadToPdf,
  exportTablePayloadsToPdf,
} from "./pdf/tablePdfExport";
import type { TableExportPayload, TabularExportFormat } from "./types";

export type ExportXlsxOptions = {
  /** Mensagem quando não há colunas/linhas. */
  emptyMessage?: string;
  /** Basename do arquivo (sem extensão); padrão = título do payload. */
  filename?: string;
};

export type ExportPdfOptions = {
  subtitle?: string;
};

export function exportPayloadToCsv(payload: TableExportPayload): void {
  if (!payload.columns.length) {
    exportAlert("Não há dados para exportar em CSV.");
    return;
  }

  const header = payload.columns.map((column) => column.label).join(";");
  const body = payload.rows
    .map((row) =>
      payload.columns.map((column) => csvCell(row[column.key])).join(";"),
    )
    .join("\n");

  triggerFileDownload(
    buildUtf8CsvBlob(`${header}\n${body}`),
    `${sanitizeFilename(payload.title)}.csv`,
  );
}

export function exportPayloadToXlsx(
  payload: TableExportPayload,
  options?: ExportXlsxOptions,
): void {
  if (!payload.columns.length) {
    exportAlert(options?.emptyMessage ?? "Não há dados para exportar em Excel.");
    return;
  }

  void import("xlsx")
    .then((XLSX) => {
      const headers = payload.columns.map((column) => column.label);
      const data = payload.rows.map((row) =>
        payload.columns.map((column) => row[column.key] ?? ""),
      );

      const ws = XLSX.utils.aoa_to_sheet([headers, ...data]);
      ws["!cols"] = payload.columns.map((column) => {
        const maxLen = Math.max(
          column.label.length,
          ...payload.rows.map((row) => String(row[column.key] ?? "").length),
        );

        return { wch: Math.min(maxLen + 2, 50) };
      });

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(
        wb,
        ws,
        sanitizeSheetName(payload.title || "Dados"),
      );
      const fileBase = options?.filename?.trim()
        ? sanitizeFilename(options.filename)
        : sanitizeFilename(payload.title || "dados");
      XLSX.writeFile(wb, `${fileBase}.xlsx`);
    })
    .catch((error) => {
      console.error("[exportPayloadToXlsx]", error);
      exportAlert("Não foi possível exportar Excel. Tente novamente.");
    });
}

export function exportPayloadToPdf(
  payload: TableExportPayload,
  options?: ExportPdfOptions,
): void {
  exportTablePayloadToPdf(payload, options);
}

export function exportPayloadsToXlsx(
  title: string,
  payloads: TableExportPayload[],
): void {
  const sheets = payloads.filter(
    (payload) => payload.columns.length && payload.rows.length,
  );

  if (!sheets.length) {
    exportAlert("Não há dados para exportar em Excel.");
    return;
  }

  void import("xlsx")
    .then((XLSX) => {
      const wb = XLSX.utils.book_new();
      const usedNames = new Set<string>();

      for (const payload of sheets) {
        let sheetName = sanitizeSheetName(payload.title || "Dados");
        let suffix = 2;

        while (usedNames.has(sheetName)) {
          const base = sanitizeSheetName(payload.title || "Dados").slice(0, 28);
          sheetName = `${base}_${suffix}`;
          suffix += 1;
        }

        usedNames.add(sheetName);

        const headers = payload.columns.map((column) => column.label);
        const data = payload.rows.map((row) =>
          payload.columns.map((column) => row[column.key] ?? ""),
        );

        const ws = XLSX.utils.aoa_to_sheet([headers, ...data]);
        XLSX.utils.book_append_sheet(wb, ws, sheetName);
      }

      XLSX.writeFile(wb, `${sanitizeFilename(title)}.xlsx`);
    })
    .catch((error) => {
      console.error("[exportPayloadsToXlsx]", error);
      exportAlert("Não foi possível exportar Excel. Tente novamente.");
    });
}

export function exportPayloadsToCsv(
  title: string,
  payloads: TableExportPayload[],
): void {
  const sheets = payloads.filter(
    (payload) => payload.columns.length && payload.rows.length,
  );

  if (!sheets.length) {
    exportAlert("Não há dados para exportar em CSV.");
    return;
  }

  const content = sheets
    .map((payload) => {
      const header = payload.columns.map((column) => column.label).join(";");
      const body = payload.rows
        .map((row) =>
          payload.columns.map((column) => csvCell(row[column.key])).join(";"),
        )
        .join("\n");

      return [`## ${payload.title}`, header, body].join("\n");
    })
    .join("\n\n");

  triggerFileDownload(
    buildUtf8CsvBlob(content),
    `${sanitizeFilename(title)}.csv`,
  );
}

export function exportPayloadsToPdf(
  title: string,
  payloads: TableExportPayload[],
  options?: ExportPdfOptions,
): void {
  exportTablePayloadsToPdf(title, payloads, options);
}

export function exportTableFormat(
  payload: TableExportPayload,
  format: TabularExportFormat,
  options?: ExportPdfOptions & ExportXlsxOptions,
): void {
  switch (format) {
    case "csv":
      exportPayloadToCsv(payload);
      return;
    case "xlsx":
      exportPayloadToXlsx(payload, options);
      return;
    case "pdf":
      exportPayloadToPdf(payload, options);
      return;
    default: {
      const _exhaustive: never = format;
      return _exhaustive;
    }
  }
}
