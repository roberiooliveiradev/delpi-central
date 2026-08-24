import { copy } from "../content/copy";
import type { DeliveryMapPayload, DeliveryMapRow, DeliveryMapSection } from "../types";
import { formatIsoDate } from "./formatIsoDate";

export type DeliveryMapExcelSheetRow =
  | { kind: "header" }
  | { kind: "blank" }
  | { kind: "data"; row: DeliveryMapRow; sectionKey: string };

const QTY_NUM_FMT = "#.##0,000";
const HEADER_BLUE = "FF0070C0";
const BORDER_BLACK = "FF000000";
const STRIKE_GRAY = "FF808080";

const THIN_BORDER = {
  style: "thin" as const,
  color: { argb: BORDER_BLACK },
};

const ALL_BORDERS = {
  top: THIN_BORDER,
  left: THIN_BORDER,
  bottom: THIN_BORDER,
  right: THIN_BORDER,
};

/** Achata seções do mapa em linhas de planilha (cabeçalho + dados + linha em branco). */
export function flattenDeliveryMapExcelRows(
  sections: readonly DeliveryMapSection[],
): DeliveryMapExcelSheetRow[] {
  const nonEmpty = sections.filter((section) => section.rows.length > 0);
  const rows: DeliveryMapExcelSheetRow[] = [];

  nonEmpty.forEach((section, index) => {
    rows.push({ kind: "header" });
    for (const row of section.rows) {
      rows.push({ kind: "data", row, sectionKey: section.section_key });
    }
    if (index < nonEmpty.length - 1) {
      rows.push({ kind: "blank" });
    }
  });

  return rows;
}

export function deliveryMapExcelCellValues(row: DeliveryMapRow): (string | number)[] {
  return [
    row.production_order,
    row.product_code,
    row.due_date ? formatIsoDate(row.due_date) : "",
    row.planned_qty,
    row.pending_qty,
    row.observation ?? "",
  ];
}

function sanitizeFileBase(name: string): string {
  return name.replace(/\.xlsx$/i, "").replace(/[\\/:*?"<>|]+/g, "_").trim() || "mapa-entrega";
}

function triggerXlsxDownload(buffer: ArrayBuffer, fileName: string): void {
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${sanitizeFileBase(fileName)}.xlsx`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function downloadDeliveryMapExcel(
  payload: DeliveryMapPayload,
  fileName: string,
): Promise<void> {
  if (typeof document === "undefined") return;

  const flatRows = flattenDeliveryMapExcelRows(payload.sections);
  if (!flatRows.some((entry) => entry.kind === "data")) {
    window.alert(copy.deliveryMap.exportEmpty);
    return;
  }

  const ExcelJSImport = await import("exceljs");
  const ExcelJS = ExcelJSImport.default ?? ExcelJSImport;

  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet(copy.deliveryMap.exportSheetTitle.slice(0, 31));
  const headers = copy.deliveryMap.excelColumns.map((column) => column.label);

  sheet.columns = [
    { width: 14 },
    { width: 12 },
    { width: 12 },
    { width: 14 },
    { width: 16 },
    { width: 28 },
  ];

  let rowIndex = 1;

  for (const entry of flatRows) {
    if (entry.kind === "blank") {
      rowIndex += 1;
      continue;
    }

    const worksheetRow = sheet.getRow(rowIndex);

    if (entry.kind === "header") {
      headers.forEach((label, columnIndex) => {
        const cell = worksheetRow.getCell(columnIndex + 1);
        cell.value = label;
        cell.font = { bold: true, color: { argb: HEADER_BLUE }, size: 10 };
        cell.alignment = { horizontal: "center", vertical: "middle", wrapText: true };
        cell.border = { bottom: THIN_BORDER };
      });
      rowIndex += 1;
      continue;
    }

    const values = deliveryMapExcelCellValues(entry.row);
    values.forEach((value, columnIndex) => {
      const cell = worksheetRow.getCell(columnIndex + 1);
      cell.value = value;
      cell.border = ALL_BORDERS;
      cell.alignment = { vertical: "middle", wrapText: columnIndex === 5 };

      if (columnIndex === 3 || columnIndex === 4) {
        cell.numFmt = QTY_NUM_FMT;
        cell.alignment = { ...cell.alignment, horizontal: "right" };
      }

      if (entry.row.is_reported) {
        cell.font = { strike: true, color: { argb: STRIKE_GRAY }, size: 10 };
      }
    });

    rowIndex += 1;
  }

  const buffer = await workbook.xlsx.writeBuffer();
  triggerXlsxDownload(buffer, fileName);
}
