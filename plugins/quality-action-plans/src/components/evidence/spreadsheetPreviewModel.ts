const MAX_PREVIEW_ROWS = 500;
const MAX_PREVIEW_COLS = 40;

export type SpreadsheetPreviewSheet = {
  name: string;
  rows: string[][];
  hidden: boolean;
};

export type SpreadsheetPreviewData = {
  sheets: SpreadsheetPreviewSheet[];
};

export type SpreadsheetPreviewLimits = {
  rowTruncated: boolean;
  colTruncated: boolean;
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

function normalizeCell(value: unknown): string {
  if (value == null) return "";
  return String(value);
}

function trimTrailingEmptyColumns(rows: string[][]): string[][] {
  let lastNonEmpty = -1;

  for (const row of rows) {
    for (let col = row.length - 1; col > lastNonEmpty; col -= 1) {
      if (row[col]?.trim()) {
        lastNonEmpty = Math.max(lastNonEmpty, col);
        break;
      }
    }
  }

  const width = Math.max(lastNonEmpty + 1, 1);
  return rows.map((row) => {
    const next = row.slice(0, width);
    while (next.length < width) next.push("");
    return next;
  });
}

export function prepareSpreadsheetSheet(
  rows: string[][],
): { rows: string[][]; limits: SpreadsheetPreviewLimits } {
  const normalized = trimTrailingEmptyColumns(
    rows.map((row) => row.map((cell) => normalizeCell(cell))),
  );

  const rowTruncated = normalized.length > MAX_PREVIEW_ROWS;
  const visibleRows = rowTruncated ? normalized.slice(0, MAX_PREVIEW_ROWS) : normalized;

  const width = Math.max(...visibleRows.map((row) => row.length), 1);
  const colTruncated = width > MAX_PREVIEW_COLS;
  const visibleWidth = colTruncated ? MAX_PREVIEW_COLS : width;

  const prepared = visibleRows.map((row) => {
    const next = row.slice(0, visibleWidth);
    while (next.length < visibleWidth) next.push("");
    return next;
  });

  if (prepared.length === 0) {
    return {
      rows: [[""]],
      limits: { rowTruncated: false, colTruncated: false },
    };
  }

  return {
    rows: prepared,
    limits: { rowTruncated, colTruncated },
  };
}

function sheetHiddenFlags(workbook: import("xlsx").WorkBook): boolean[] {
  const meta = workbook.Workbook?.Sheets;
  if (!Array.isArray(meta)) {
    return workbook.SheetNames.map(() => false);
  }

  return workbook.SheetNames.map((_name, index) => {
    const entry = meta[index];
    const hiddenValue = entry?.Hidden ?? 0;
    return hiddenValue === 1 || hiddenValue === 2;
  });
}

function sheetToMatrix(
  sheet: import("xlsx").WorkSheet,
  XLSX: typeof import("xlsx"),
): string[][] {
  const ref = sheet["!ref"];
  if (!ref) return [[""]];

  const range = XLSX.utils.decode_range(ref);
  const rows: string[][] = [];

  for (let rowIndex = range.s.r; rowIndex <= range.e.r; rowIndex += 1) {
    const row: string[] = [];
    for (let colIndex = range.s.c; colIndex <= range.e.c; colIndex += 1) {
      const address = XLSX.utils.encode_cell({ r: rowIndex, c: colIndex });
      const cell = sheet[address];
      row.push(cell ? XLSX.utils.format_cell(cell) : "");
    }
    rows.push(row);
  }

  return rows.length > 0 ? rows : [[""]];
}

export async function parseSpreadsheetPreview(blob: Blob): Promise<SpreadsheetPreviewData> {
  const XLSX = await import("xlsx");
  const workbook = XLSX.read(await blob.arrayBuffer(), {
    type: "array",
    cellDates: true,
    raw: false,
    bookSheets: true,
    bookVBA: true,
  });

  const hiddenFlags = sheetHiddenFlags(workbook);

  const sheets = workbook.SheetNames.map((name, index) => {
    const sheet = workbook.Sheets[name];
    const matrix = sheet ? sheetToMatrix(sheet, XLSX) : [[""]];

    return {
      name,
      rows: matrix.map((row) => row.map(normalizeCell)),
      hidden: hiddenFlags[index] ?? false,
    };
  });

  if (sheets.length === 0) {
    return { sheets: [{ name: "Planilha1", rows: [[""]], hidden: false }] };
  }

  return { sheets };
}
