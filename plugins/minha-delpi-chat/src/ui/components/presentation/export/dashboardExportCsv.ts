import type { ChatPresentation } from "../../../../data/api/chatTypes";

type DashboardPresentation = Extract<ChatPresentation, { type: "dashboard" }>;

function csvCell(value: unknown): string {
  if (value == null) {
    return "";
  }

  const text = String(value);

  if (text.includes(";") || text.includes('"') || text.includes("\n")) {
    return `"${text.replace(/"/g, '""')}"`;
  }

  return text;
}

function csvRow(cells: unknown[]): string {
  return cells.map(csvCell).join(";");
}

function sanitizeFilename(value: string): string {
  return value.replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "_").slice(0, 80) || "dashboard";
}

function chartColumns(
  rows: Record<string, unknown>[],
  config?: { xAxis?: string; yAxis?: string | string[] },
): string[] {
  const xAxis = config?.xAxis ?? Object.keys(rows[0] ?? {}).find((key) => typeof rows[0]?.[key] === "string") ?? "label";
  const yAxisRaw = config?.yAxis;
  const yAxes = Array.isArray(yAxisRaw)
    ? yAxisRaw
    : yAxisRaw
      ? [yAxisRaw]
      : Object.keys(rows[0] ?? {}).filter((key) => key !== xAxis && typeof rows[0]?.[key] === "number");

  return [xAxis, ...yAxes.filter((key) => key && key !== xAxis)];
}

export function buildDashboardCsv(presentation: DashboardPresentation): string {
  const BOM = "\uFEFF";
  const blocks: string[] = [];

  for (const panel of presentation.panels) {
    const panelTitle = panel.title || panel.id;
    blocks.push(csvRow([`Painel: ${panelTitle}`]));

    const inner = panel.presentation;

    if (inner.type === "kpi") {
      blocks.push(csvRow(["Indicador", "Valor", "Unidade"]));
      for (const card of inner.cards) {
        blocks.push(csvRow([card.label, card.value, card.unit ?? ""]));
      }
      blocks.push("");
      continue;
    }

    if (inner.type === "table") {
      const keys = inner.columns.map((column) => column.key);
      blocks.push(csvRow(inner.columns.map((column) => column.label)));
      for (const row of inner.rows) {
        blocks.push(csvRow(keys.map((key) => row[key])));
      }
      blocks.push("");
      continue;
    }

    if (inner.type === "chart") {
      const keys = chartColumns(inner.data, inner.config);
      blocks.push(csvRow(keys));
      for (const row of inner.data) {
        blocks.push(csvRow(keys.map((key) => row[key])));
      }
      blocks.push("");
    }
  }

  return BOM + blocks.join("\n").trim() + "\n";
}

export function downloadDashboardCsv(presentation: DashboardPresentation): void {
  const csv = buildDashboardCsv(presentation);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${sanitizeFilename(presentation.title || "dashboard")}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}
