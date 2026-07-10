import type { DelpiDocumentColumn } from "./types";

export type DelpiDocumentColumnLayout = {
  width?: string;
  className?: string;
};

const COLUMN_PROFILES: Record<string, Record<string, DelpiDocumentColumnLayout>> = {
  structure: {
    code: { width: "11%", className: "cert-cell--nowrap" },
    description: { width: "40%", className: "cert-cell--wrap" },
    quantity: { width: "8%", className: "cert-cell--numeric cert-cell--nowrap" },
    unit: { width: "7%", className: "cert-cell--numeric cert-cell--nowrap" },
    type: { width: "7%", className: "cert-cell--numeric cert-cell--nowrap" },
    level: { width: "6%", className: "cert-cell--numeric cert-cell--nowrap" },
  },
  guide: {
    product: { width: "12%", className: "cert-cell--nowrap" },
    level: { width: "6%", className: "cert-cell--numeric cert-cell--nowrap" },
    operation: { width: "7%", className: "cert-cell--numeric cert-cell--nowrap" },
    center: { width: "10%", className: "cert-cell--nowrap" },
    description: { width: "65%", className: "cert-cell--wrap" },
  },
  inspection: {
    product: { width: "9%", className: "cert-cell--nowrap" },
    level: { width: "4%", className: "cert-cell--numeric cert-cell--nowrap" },
    section: { width: "9%", className: "cert-cell--nowrap" },
    operation: { width: "5%", className: "cert-cell--numeric cert-cell--nowrap" },
    test: { width: "7%", className: "cert-cell--nowrap" },
    lab: { width: "6%", className: "cert-cell--nowrap" },
    nominal: { width: "7%", className: "cert-cell--numeric cert-cell--nowrap" },
    lower: { width: "7%", className: "cert-cell--numeric cert-cell--nowrap" },
    upper: { width: "7%", className: "cert-cell--numeric cert-cell--nowrap" },
    unit: { width: "5%", className: "cert-cell--numeric cert-cell--nowrap" },
    detail: { width: "34%", className: "cert-cell--wrap" },
  },
  checklist: {
    section: { width: "14%", className: "cert-cell--nowrap" },
    item: { width: "30%", className: "cert-cell--wrap" },
    status: { width: "8%", className: "cert-cell--numeric cert-cell--nowrap" },
    observation: { width: "48%", className: "cert-cell--wrap" },
  },
  nonconformities: {
    section: { width: "12%", className: "cert-cell--nowrap" },
    item: { width: "22%", className: "cert-cell--wrap" },
    status: { width: "10%", className: "cert-cell--numeric cert-cell--nowrap" },
    pdfEvidence: { width: "18%", className: "cert-cell--wrap" },
    apiEvidence: { width: "18%", className: "cert-cell--wrap" },
    recommendation: { width: "20%", className: "cert-cell--wrap" },
  },
  pdfData: {
    field: { width: "34%", className: "cert-cell--nowrap" },
    value: { width: "66%", className: "cert-cell--wrap" },
  },
  apiData: {
    field: { width: "34%", className: "cert-cell--nowrap" },
    value: { width: "66%", className: "cert-cell--wrap" },
  },
};

const NARROW_COLUMN_KEYS = new Set([
  "level",
  "nivel",
  "bom_level",
  "operation",
  "operation_code",
  "op",
  "unit",
  "unid",
  "type",
  "status",
  "lab",
  "labor",
  "quantity",
  "qty",
  "center",
  "work_center",
  "nominal",
  "lower",
  "upper",
  "test",
  "product",
  "code",
]);

const WIDE_COLUMN_KEYS = new Set([
  "description",
  "item",
  "detail",
  "observation",
  "recommendation",
  "pdfEvidence",
  "apiEvidence",
  "value",
  "field",
  "section",
]);

function normalizeLayoutKey(layoutKey?: string): string {
  return String(layoutKey || "").trim().toLowerCase();
}

function fallbackLayout(columnKey: string): DelpiDocumentColumnLayout {
  const key = columnKey.trim().toLowerCase();

  if (NARROW_COLUMN_KEYS.has(key)) {
    return { className: "cert-cell--numeric cert-cell--nowrap" };
  }

  if (WIDE_COLUMN_KEYS.has(key)) {
    return { className: "cert-cell--wrap" };
  }

  return { className: "cert-cell--wrap" };
}

export function resolveDelpiDocumentColumnLayouts(
  columns: DelpiDocumentColumn[],
  layoutKey?: string,
): DelpiDocumentColumnLayout[] {
  const profile = COLUMN_PROFILES[normalizeLayoutKey(layoutKey)] ?? {};

  return columns.map((column) => {
    const key = String(column.key || "").trim();
    return profile[key] ?? fallbackLayout(key);
  });
}

export function buildDelpiDocumentColgroup(
  columns: DelpiDocumentColumn[],
  layoutKey?: string,
): string {
  const layouts = resolveDelpiDocumentColumnLayouts(columns, layoutKey);
  const cols = layouts
    .map((layout) =>
      layout.width ? `<col style="width:${layout.width}" />` : "<col />",
    )
    .join("");

  return cols ? `<colgroup>${cols}</colgroup>` : "";
}

export function resolveDelpiDocumentTableClassName(layoutKey?: string): string {
  const normalized = normalizeLayoutKey(layoutKey);

  if (!normalized || normalized === "generic") {
    return "cert-table cert-table--dense";
  }

  return `cert-table cert-table--dense cert-table--${normalized}`;
}
