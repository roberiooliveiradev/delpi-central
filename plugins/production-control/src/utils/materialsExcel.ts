import { copy } from "../content/copy";
import type { MaterialsIssueId, MaterialsLine, MaterialsShortageLine } from "../types";
import { formatIsoDate } from "./formatIsoDate";

export type MaterialsExcelColumn = { key: string; label: string };

export type MaterialsExcelPayload = {
  title: string;
  columns: MaterialsExcelColumn[];
  rows: Record<string, string | number>[];
};

function isShortage(
  line: MaterialsLine | MaterialsShortageLine,
): line is MaterialsShortageLine {
  return line.kind === "shortage" || !("request_number" in line);
}

export function buildMaterialsExcelPayload(
  lines: readonly (MaterialsLine | MaterialsShortageLine)[],
  view: MaterialsIssueId = "excess",
): MaterialsExcelPayload {
  const columns = copy.materials.columns;
  if (view === "shortage") {
    return {
      title: copy.materials.shortageTableTitle,
      columns: [
        { key: "product", label: columns.product },
        { key: "safety", label: columns.safety },
        { key: "stock", label: columns.stock },
        { key: "orders", label: columns.orders },
        { key: "commitments", label: columns.commitments },
        { key: "projected", label: columns.projected },
        { key: "openSc1", label: columns.openSc1 },
        { key: "shortage", label: columns.shortage },
      ],
      rows: lines.filter(isShortage).map((line) => ({
        product: line.product_code || "",
        safety: line.safety_stock,
        stock: line.available_stock,
        orders: line.open_purchase_order_quantity,
        commitments: line.open_commitment_quantity,
        projected: line.projected_balance,
        openSc1: line.open_sc1_quantity,
        shortage: line.shortage_quantity,
      })),
    };
  }

  return {
    title: copy.materials.exportSheetTitle,
    columns: [
      { key: "request", label: columns.request },
      { key: "product", label: columns.product },
      { key: "open", label: columns.open },
      { key: "stock", label: columns.stock },
      { key: "safety", label: columns.safety },
      { key: "orders", label: columns.orders },
      { key: "commitments", label: columns.commitments },
      { key: "projected", label: columns.projected },
      { key: "required", label: columns.required },
    ],
    rows: lines
      .filter((line): line is MaterialsLine => !isShortage(line))
      .map((line) => ({
        request: `${line.request_number}/${line.request_item}`,
        product: line.product_code || "",
        open: line.open_quantity,
        stock: line.available_stock,
        safety: line.safety_stock,
        orders: line.open_purchase_order_quantity,
        commitments: line.open_commitment_quantity,
        projected: line.projected_balance,
        required: line.required_date ? formatIsoDate(line.required_date) : "",
      })),
  };
}

function sanitizeFileBase(name: string): string {
  return name.replace(/\.xlsx$/i, "").replace(/[\\/:*?"<>|]+/g, "_").trim() || "materiais";
}

export async function downloadMaterialsExcel(
  lines: readonly (MaterialsLine | MaterialsShortageLine)[],
  view: MaterialsIssueId,
  fileName: string,
): Promise<void> {
  if (typeof document === "undefined") return;
  const payload = buildMaterialsExcelPayload(lines, view);
  if (!payload.columns.length || payload.rows.length === 0) {
    window.alert(copy.materials.exportEmpty);
    return;
  }

  const XLSX = await import("xlsx");
  const headers = payload.columns.map((column) => column.label);
  const data = payload.rows.map((row) =>
    payload.columns.map((column) => row[column.key] ?? ""),
  );
  const worksheet = XLSX.utils.aoa_to_sheet([headers, ...data]);
  worksheet["!cols"] = payload.columns.map((column) => {
    const maxLen = Math.max(
      column.label.length,
      ...payload.rows.map((row) => String(row[column.key] ?? "").length),
    );
    return { wch: Math.min(maxLen + 2, 50) };
  });
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, payload.title.slice(0, 31));
  XLSX.writeFile(workbook, `${sanitizeFileBase(fileName)}.xlsx`);
}
