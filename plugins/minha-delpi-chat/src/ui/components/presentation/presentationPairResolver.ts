import type { ChatPresentation, ChatToolCall } from "../../../data/api/chatTypes";

import { normalizeChartPresentation } from "./pipeline/chartPresentationNormalize";

export type PresentationPair = {
  primary: ChatPresentation | null;
  table: ChatPresentation | null;
  tree: ChatPresentation | null;
};

export function isTablePresentation(
  value: unknown,
): value is Extract<ChatPresentation, { type: "table" }> {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { type?: string }).type === "table"
  );
}

function isTreePresentation(
  value: unknown,
): value is Extract<ChatPresentation, { type: "tree" }> {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { type?: string }).type === "tree"
  );
}

function tableColumnsMatch(
  left: Extract<ChatPresentation, { type: "table" }>["columns"],
  right: Extract<ChatPresentation, { type: "table" }>["columns"],
): boolean {
  if (left.length !== right.length) {
    return false;
  }

  return left.every((column, index) => column.key === right[index]?.key);
}

function inferProductCodeFromTable(
  table: Extract<ChatPresentation, { type: "table" }>,
): string {
  const firstRow = table.rows[0];

  if (!firstRow) {
    return "";
  }

  for (const key of ["product_code", "code", "productCode", "produto"]) {
    const value = firstRow[key];

    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value).trim();
    }
  }

  return "";
}

function mergeTablePresentations(
  tables: Extract<ChatPresentation, { type: "table" }>[],
): Extract<ChatPresentation, { type: "table" }> | null {
  if (tables.length === 0) {
    return null;
  }

  if (tables.length === 1) {
    return tables[0];
  }

  const [first, ...rest] = tables;

  if (!rest.every((table) => tableColumnsMatch(first.columns, table.columns))) {
    return first;
  }

  const productCodes = tables
    .map((table) => inferProductCodeFromTable(table))
    .filter(Boolean);

  const title =
    productCodes.length > 1
      ? "Estoque por filial/armazém"
      : first.title;

  return {
    ...first,
    title,
    rows: tables.flatMap((table) => table.rows),
  };
}

function prefixChartSeriesName(
  entry: Record<string, unknown>,
  productCode: string,
): Record<string, unknown> {
  if (!productCode) {
    return entry;
  }

  const name = String(entry.name ?? "").trim();

  if (!name) {
    return entry;
  }

  if (name.startsWith(`${productCode} ·`) || name.startsWith(`${productCode} `)) {
    return entry;
  }

  return {
    ...entry,
    name: `${productCode} · ${name}`,
  };
}

function mergeChartPresentations(
  charts: Extract<ChatPresentation, { type: "chart" }>[],
  tables: Extract<ChatPresentation, { type: "table" }>[],
): Extract<ChatPresentation, { type: "chart" }> | null {
  if (charts.length === 0) {
    return null;
  }

  if (charts.length === 1) {
    return charts[0];
  }

  const [first, ...rest] = charts;

  if (
    rest.some(
      (chart) =>
        chart.chartType !== first.chartType ||
        JSON.stringify(chart.config ?? {}) !== JSON.stringify(first.config ?? {}),
    )
  ) {
    return first;
  }

  const mergedData = charts.flatMap((chart, index) => {
    const productCode = inferProductCodeFromTable(tables[index] ?? { type: "table", title: "", columns: [], rows: [] });

    return (chart.data ?? []).map((entry) =>
      prefixChartSeriesName(entry as Record<string, unknown>, productCode),
    );
  });

  const productCodes = tables
    .map((table) => inferProductCodeFromTable(table))
    .filter(Boolean);

  return {
    ...first,
    title:
      productCodes.length > 1
        ? "Estoque por filial/armazém"
        : first.title,
    data: mergedData,
  };
}

function collectExternalActionPresentations(toolCalls: ChatToolCall[]): {
  charts: Extract<ChatPresentation, { type: "chart" }>[];
  tables: Extract<ChatPresentation, { type: "table" }>[];
  trees: Extract<ChatPresentation, { type: "tree" }>[];
} {
  const charts: Extract<ChatPresentation, { type: "chart" }>[] = [];
  const tables: Extract<ChatPresentation, { type: "table" }>[] = [];
  const trees: Extract<ChatPresentation, { type: "tree" }>[] = [];

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const presentation = metadata.presentation;
    const tablePresentation = metadata.tablePresentation;
    const treePresentation = metadata.treePresentation;
    const chartPresentation = metadata.chartPresentation;

    const normalizedChart =
      normalizeChartPresentation(presentation) ?? normalizeChartPresentation(chartPresentation);

    if (normalizedChart) {
      charts.push(normalizedChart);
    }

    if (isTreePresentation(presentation)) {
      trees.push(presentation);
    } else if (isTreePresentation(treePresentation)) {
      trees.push(treePresentation);
    }

    if (isTablePresentation(tablePresentation)) {
      tables.push(tablePresentation);
    } else if (isTablePresentation(presentation)) {
      tables.push(presentation);
    }
  }

  return { charts, tables, trees };
}

function getPresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  const { charts, tables, trees } = collectExternalActionPresentations(toolCalls);

  if (trees.length > 0) {
    return trees[0];
  }

  const mergedChart = mergeChartPresentations(charts, tables);

  if (mergedChart) {
    return mergedChart;
  }

  if (trees.length === 1) {
    return trees[0];
  }

  if (trees.length > 1) {
    return trees[0];
  }

  for (const toolCall of toolCalls) {
    const presentation = toolCall.metadata?.presentation;

    if (
      presentation &&
      typeof presentation === "object" &&
      "type" in presentation
    ) {
      const presentationType = (presentation as ChatPresentation).type;

      if (presentationType !== "markdown") {
        return presentation as ChatPresentation;
      }
    }
  }

  return null;
}

function getTablePresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  const { tables } = collectExternalActionPresentations(toolCalls);
  const mergedTable = mergeTablePresentations(tables);

  if (mergedTable) {
    return mergedTable;
  }

  for (const toolCall of toolCalls) {
    const tablePresentation = (toolCall.metadata as Record<string, unknown>)?.tablePresentation;

    if (isTablePresentation(tablePresentation)) {
      return tablePresentation;
    }
  }

  return null;
}

function getTreePresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  const { trees } = collectExternalActionPresentations(toolCalls);

  if (trees.length === 1) {
    return trees[0];
  }

  if (trees.length > 1) {
    return trees[0];
  }

  for (const toolCall of toolCalls) {
    const treePresentation = (toolCall.metadata as Record<string, unknown>)?.treePresentation;

    if (isTreePresentation(treePresentation)) {
      return treePresentation;
    }
  }

  return null;
}



export function getTablePresentationFromPair(
  pair: PresentationPair,
): Extract<ChatPresentation, { type: "table" }> | null {
  if (pair.table?.type === "table") {
    return pair.table;
  }

  if (pair.primary?.type === "table") {
    return pair.primary;
  }

  return null;
}

export function getTreePresentationFromPair(
  pair: PresentationPair,
): Extract<ChatPresentation, { type: "tree" }> | null {
  if (pair.tree?.type === "tree") {
    return pair.tree;
  }

  if (pair.primary?.type === "tree") {
    return pair.primary;
  }

  return null;
}

export function getChartPresentationFromPair(
  pair: PresentationPair,
  toolCalls?: ChatToolCall[],
): Extract<ChatPresentation, { type: "chart" }> | null {
  if (pair.primary?.type === "chart") {
    return pair.primary;
  }

  if (!Array.isArray(toolCalls)) {
    return null;
  }

  const { charts, tables } = collectExternalActionPresentations(toolCalls);

  return mergeChartPresentations(charts, tables);
}
export function getPresentationPairFromToolCalls(
  toolCalls?: ChatToolCall[],
): PresentationPair {
  return {
    primary: getPresentationFromToolCalls(toolCalls),
    table: getTablePresentationFromToolCalls(toolCalls),
    tree: getTreePresentationFromToolCalls(toolCalls),
  };
}

const RICH_PRESENTATION_TYPES = new Set([
  "table",
  "chart",
  "kpi",
  "tree",
  "dashboard",
]);

export function hasRichPresentation(pair: PresentationPair): boolean {
  const primaryType = pair.primary?.type;

  if (primaryType && RICH_PRESENTATION_TYPES.has(primaryType)) {
    return true;
  }

  const tableType = pair.table?.type;
  const treeType = pair.tree?.type;

  return Boolean(
    (tableType && RICH_PRESENTATION_TYPES.has(tableType)) ||
      (treeType && RICH_PRESENTATION_TYPES.has(treeType)),
  );
}
