import type { ChatPresentation } from "../../data/api/chatTypes";
import type { ChatCanvasOpenPayload } from "../../data/api/chatTypes";

type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;
type DashboardPresentation = Extract<ChatPresentation, { type: "dashboard" }>;

function escapeCell(value: unknown): string {
  const text = String(value ?? "").replace(/\|/g, "\\|").replace(/\n/g, " ");

  return text || "—";
}

function markdownTable(
  rows: Record<string, unknown>[],
  columns: string[],
): string {
  if (!rows.length || !columns.length) {
    return "_Sem dados tabulares._\n";
  }

  const header = `| ${columns.join(" | ")} |`;
  const divider = `| ${columns.map(() => "---").join(" | ")} |`;
  const body = rows
    .map((row) => `| ${columns.map((key) => escapeCell(row[key])).join(" | ")} |`)
    .join("\n");

  return `${header}\n${divider}\n${body}\n`;
}

export function chartPresentationToCanvasMarkdown(
  presentation: ChartPresentation,
  options?: {
    rows?: Record<string, unknown>[];
    xAxis?: string;
    yAxes?: string[];
    chartType?: string;
    filtersNote?: string;
  },
): string {
  const rows = options?.rows ?? presentation.data;
  const xAxis = options?.xAxis ?? presentation.config?.xAxis ?? guessLabelKey(rows);
  const yAxes =
    options?.yAxes ??
    (Array.isArray(presentation.config?.yAxis)
      ? presentation.config.yAxis
      : presentation.config?.yAxis
        ? [presentation.config.yAxis]
        : guessNumericKeys(rows, xAxis));
  const chartType = options?.chartType ?? presentation.chartType;
  const columns = [xAxis, ...yAxes.filter((key) => key && key !== xAxis)];

  const lines = [
    `# ${presentation.title || "Gráfico"}`,
    "",
    `**Tipo:** ${chartType}`,
    "",
  ];

  if (options?.filtersNote) {
    lines.push(`> ${options.filtersNote}`, "");
  }

  lines.push("## Dados", "", markdownTable(rows, columns));

  return lines.join("\n").trim();
}

export function dashboardPresentationToCanvasMarkdown(
  presentation: DashboardPresentation,
): string {
  const sections: string[] = [`# ${presentation.title || "Dashboard"}`, ""];

  for (const panel of presentation.panels) {
    const panelTitle = panel.title || panel.id;
    sections.push(`## ${panelTitle}`, "");

    const inner = panel.presentation;

    if (inner.type === "kpi") {
      for (const card of inner.cards) {
        sections.push(`- **${card.label}:** ${card.value}${card.unit ? ` ${card.unit}` : ""}`);
      }

      sections.push("");
      continue;
    }

    if (inner.type === "table") {
      const keys = inner.columns.map((column) => column.key);
      sections.push(markdownTable(inner.rows, keys), "");
      continue;
    }

    if (inner.type === "chart") {
      sections.push(
        chartPresentationToCanvasMarkdown(inner, {
          rows: inner.data,
        }),
        "",
      );
    }
  }

  return sections.join("\n").trim();
}

export function presentationToCanvasPayload(
  presentation: ChartPresentation | DashboardPresentation,
  options?: {
    rows?: Record<string, unknown>[];
    xAxis?: string;
    yAxes?: string[];
    chartType?: string;
    filtersNote?: string;
  },
): ChatCanvasOpenPayload {
  const markdown =
    presentation.type === "dashboard"
      ? dashboardPresentationToCanvasMarkdown(presentation)
      : chartPresentationToCanvasMarkdown(presentation, options);

  return {
    title: presentation.title || "Gráfico na lousa",
    markdown,
    messageId: null,
    sourceMessageId: null,
  };
}

function guessLabelKey(rows: Record<string, unknown>[]): string {
  const sample = rows[0] ?? {};

  for (const key of Object.keys(sample)) {
    if (typeof sample[key] === "string") {
      return key;
    }
  }

  return "label";
}

function guessNumericKeys(rows: Record<string, unknown>[], xAxis: string): string[] {
  const sample = rows[0] ?? {};

  return Object.keys(sample).filter((key) => {
    if (key === xAxis) {
      return false;
    }

    const value = sample[key];

    return typeof value === "number" && Number.isFinite(value);
  });
}
