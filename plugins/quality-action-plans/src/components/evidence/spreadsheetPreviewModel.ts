import type { CSSProperties } from "react";
import type ExcelJS from "exceljs";

import {
  excelCellStyleToCss,
  excelColumnWidthToPx,
  excelRowHeightToPx,
} from "./spreadsheetPreviewStyles";

const MAX_PREVIEW_ROWS = 500;
const MAX_PREVIEW_COLS = 40;

export type SpreadsheetPreviewRichPart = {
  text: string;
  style?: CSSProperties;
};

export type SpreadsheetPreviewCell = {
  value: string;
  richParts?: SpreadsheetPreviewRichPart[];
  style?: CSSProperties;
  colspan?: number;
  rowspan?: number;
  skip?: boolean;
};

export type SpreadsheetPreviewSheet = {
  name: string;
  rows: SpreadsheetPreviewCell[][];
  columnWidths: Array<number | undefined>;
  rowHeights: Array<number | undefined>;
  hidden: boolean;
};

export type SpreadsheetPreviewData = {
  sheets: SpreadsheetPreviewSheet[];
};

export type SpreadsheetPreviewLimits = {
  rowTruncated: boolean;
  colTruncated: boolean;
};

type MergeRange = {
  top: number;
  left: number;
  bottom: number;
  right: number;
};

export function spreadsheetColumnLabel(index: number): string {
  let label = "";
  let n = index + 1;

  while (n > 0) {
    const rem = (n - 1) % 26;
    label = String.fromCharCode(65 + rem) + label;
    n = Math.floor((n - 1) / 26);
  }

  return label;
}

function decodeAddress(address: string): { row: number; col: number } {
  const match = /^([A-Z]+)(\d+)$/i.exec(address.trim());
  if (!match) return { row: 1, col: 1 };

  const letters = match[1].toUpperCase();
  let col = 0;
  for (let index = 0; index < letters.length; index += 1) {
    col = col * 26 + (letters.charCodeAt(index) - 64);
  }

  return {
    row: Number.parseInt(match[2], 10),
    col,
  };
}

function parseMergeRanges(worksheet: ExcelJS.Worksheet): MergeRange[] {
  const merges = worksheet.model.merges ?? [];
  return merges.map((merge) => {
    const [start, end = start] = merge.split(":");
    const from = decodeAddress(start);
    const to = decodeAddress(end);
    return {
      top: Math.min(from.row, to.row),
      left: Math.min(from.col, to.col),
      bottom: Math.max(from.row, to.row),
      right: Math.max(from.col, to.col),
    };
  });
}

function mergeAt(
  row: number,
  col: number,
  merges: MergeRange[],
): { skip: boolean; colspan?: number; rowspan?: number } | null {
  for (const merge of merges) {
    if (row < merge.top || row > merge.bottom || col < merge.left || col > merge.right) {
      continue;
    }

    if (row === merge.top && col === merge.left) {
      return {
        skip: false,
        colspan: merge.right - merge.left + 1,
        rowspan: merge.bottom - merge.top + 1,
      };
    }

    return { skip: true };
  }

  return null;
}

function formatCellValue(cell: ExcelJS.Cell): { value: string; richParts?: SpreadsheetPreviewRichPart[] } {
  const raw = cell.value;

  if (raw == null) {
    return { value: cell.text?.trim() ? String(cell.text) : "" };
  }

  if (typeof raw === "object") {
    if ("richText" in raw && Array.isArray(raw.richText)) {
      const richParts = raw.richText
        .map((part) => ({
          text: part.text ?? "",
          style: part.font ? excelCellStyleToCss({ font: part.font } as ExcelJS.Cell) : undefined,
        }))
        .filter((part) => part.text.length > 0);

      return {
        value: richParts.map((part) => part.text).join(""),
        richParts: richParts.length > 0 ? richParts : undefined,
      };
    }

    if ("formula" in raw) {
      const result = raw.result;
      if (result instanceof Date) {
        return { value: cell.text ?? result.toLocaleDateString("pt-BR") };
      }
      return { value: cell.text ?? (result == null ? "" : String(result)) };
    }

    if ("text" in raw && raw.text) {
      return { value: String(raw.text) };
    }

    if (raw instanceof Date) {
      return { value: cell.text ?? raw.toLocaleDateString("pt-BR") };
    }

    if ("hyperlink" in raw) {
      return { value: raw.text ? String(raw.text) : String(raw.hyperlink ?? "") };
    }
  }

  return { value: cell.text ?? String(raw) };
}

function trimTrailingEmptyColumns(rows: SpreadsheetPreviewCell[][]): SpreadsheetPreviewCell[][] {
  let lastNonEmpty = -1;

  for (const row of rows) {
    for (let col = row.length - 1; col > lastNonEmpty; col -= 1) {
      const cell = row[col];
      if (cell && !cell.skip && cell.value.trim()) {
        lastNonEmpty = Math.max(lastNonEmpty, col);
        break;
      }
    }
  }

  const width = Math.max(lastNonEmpty + 1, 1);
  return rows.map((row) => row.slice(0, width));
}

export function prepareSpreadsheetSheet(
  sheet: SpreadsheetPreviewSheet,
): { sheet: SpreadsheetPreviewSheet; limits: SpreadsheetPreviewLimits } {
  const trimmedRows = trimTrailingEmptyColumns(sheet.rows);
  const rowTruncated = trimmedRows.length > MAX_PREVIEW_ROWS;
  const visibleRows = rowTruncated ? trimmedRows.slice(0, MAX_PREVIEW_ROWS) : trimmedRows;

  const width = Math.max(...visibleRows.map((row) => row.length), 1);
  const colTruncated = width > MAX_PREVIEW_COLS;
  const visibleWidth = colTruncated ? MAX_PREVIEW_COLS : width;

  const rows = visibleRows.map((row) => row.slice(0, visibleWidth));
  const columnWidths = sheet.columnWidths.slice(0, visibleWidth);
  const rowHeights = sheet.rowHeights.slice(0, rows.length);

  if (rows.length === 0) {
    return {
      sheet: {
        ...sheet,
        rows: [[{ value: "" }]],
        columnWidths: [undefined],
        rowHeights: [undefined],
      },
      limits: { rowTruncated: false, colTruncated: false },
    };
  }

  return {
    sheet: {
      ...sheet,
      rows,
      columnWidths,
      rowHeights,
    },
    limits: { rowTruncated, colTruncated },
  };
}

function sheetFromWorksheet(worksheet: ExcelJS.Worksheet): SpreadsheetPreviewSheet {
  const dimensions = worksheet.dimensions;
  const merges = parseMergeRanges(worksheet);

  if (!dimensions) {
    return {
      name: worksheet.name,
      rows: [[{ value: "" }]],
      columnWidths: [undefined],
      rowHeights: [undefined],
      hidden: worksheet.state === "hidden" || worksheet.state === "veryHidden",
    };
  }

  const rows: SpreadsheetPreviewCell[][] = [];
  const rowHeights: Array<number | undefined> = [];

  for (let rowIndex = dimensions.top; rowIndex <= dimensions.bottom; rowIndex += 1) {
    const rowCells: SpreadsheetPreviewCell[] = [];
    const row = worksheet.getRow(rowIndex);
    rowHeights.push(excelRowHeightToPx(row.height));

    for (let colIndex = dimensions.left; colIndex <= dimensions.right; colIndex += 1) {
      const merge = mergeAt(rowIndex, colIndex, merges);
      if (merge?.skip) {
        rowCells.push({ value: "", skip: true });
        continue;
      }

      const cell = worksheet.getCell(rowIndex, colIndex);
      const formatted = formatCellValue(cell);
      rowCells.push({
        value: formatted.value,
        richParts: formatted.richParts,
        style: excelCellStyleToCss(cell),
        colspan: merge?.colspan,
        rowspan: merge?.rowspan,
      });
    }

    rows.push(rowCells);
  }

  const columnWidths: Array<number | undefined> = [];
  for (let colIndex = dimensions.left; colIndex <= dimensions.right; colIndex += 1) {
    columnWidths.push(excelColumnWidthToPx(worksheet.getColumn(colIndex).width));
  }

  return {
    name: worksheet.name,
    rows: rows.length > 0 ? rows : [[{ value: "" }]],
    columnWidths: columnWidths.length > 0 ? columnWidths : [undefined],
    rowHeights: rowHeights.length > 0 ? rowHeights : [undefined],
    hidden: worksheet.state === "hidden" || worksheet.state === "veryHidden",
  };
}

function isLegacyXls(fileName?: string): boolean {
  const name = (fileName ?? "").toLowerCase();
  return name.endsWith(".xls") && !name.endsWith(".xlsx");
}

async function parseLegacyXlsPreview(blob: Blob): Promise<SpreadsheetPreviewData> {
  const XLSX = await import("xlsx");
  const workbook = XLSX.read(await blob.arrayBuffer(), {
    type: "array",
    cellDates: true,
    raw: false,
    bookSheets: true,
  });

  const sheets = workbook.SheetNames.map((name) => {
    const worksheet = workbook.Sheets[name];
    const ref = worksheet?.["!ref"];
    if (!ref) {
      return {
        name,
        rows: [[{ value: "" }]],
        columnWidths: [undefined],
        rowHeights: [undefined],
        hidden: false,
      };
    }

    const range = XLSX.utils.decode_range(ref);
    const rows: SpreadsheetPreviewCell[][] = [];

    for (let rowIndex = range.s.r; rowIndex <= range.e.r; rowIndex += 1) {
      const row: SpreadsheetPreviewCell[] = [];
      for (let colIndex = range.s.c; colIndex <= range.e.c; colIndex += 1) {
        const address = XLSX.utils.encode_cell({ r: rowIndex, c: colIndex });
        const cell = worksheet[address];
        row.push({ value: cell ? XLSX.utils.format_cell(cell) : "" });
      }
      rows.push(row);
    }

    return {
      name,
      rows: rows.length > 0 ? rows : [[{ value: "" }]],
      columnWidths: rows[0]?.map(() => undefined) ?? [undefined],
      rowHeights: rows.map(() => undefined),
      hidden: false,
    };
  });

  return { sheets: sheets.length > 0 ? sheets : [{ name: "Planilha1", rows: [[{ value: "" }]], columnWidths: [undefined], rowHeights: [undefined], hidden: false }] };
}

export async function parseSpreadsheetPreview(
  blob: Blob,
  options?: { fileName?: string },
): Promise<SpreadsheetPreviewData> {
  if (isLegacyXls(options?.fileName)) {
    return parseLegacyXlsPreview(blob);
  }

  const ExcelJSImport = await import("exceljs");
  const ExcelJS = ExcelJSImport.default ?? ExcelJSImport;
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(await blob.arrayBuffer());

  const sheets = workbook.worksheets.map((worksheet) => sheetFromWorksheet(worksheet));

  if (sheets.length === 0) {
    return {
      sheets: [{
        name: "Planilha1",
        rows: [[{ value: "" }]],
        columnWidths: [undefined],
        rowHeights: [undefined],
        hidden: false,
      }],
    };
  }

  return { sheets };
}
