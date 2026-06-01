import type {
  ChatDataCoverageNotice,
  ChatDepthState,
  ChatPaginationState,
  ChatPresentation,
  ChatToolCall,
} from "../../data/api/chatTypes";

export type PresentationPair = {
  primary: ChatPresentation | null;
  table: ChatPresentation | null;
  tree: ChatPresentation | null;
};

export type ViewFormat = "text" | "chart" | "table" | "tree";

function isTablePresentation(
  value: unknown,
): value is Extract<ChatPresentation, { type: "table" }> {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { type?: string }).type === "table"
  );
}

function isChartPresentation(
  value: unknown,
): value is Extract<ChatPresentation, { type: "chart" }> {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { type?: string }).type === "chart"
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

    if (isChartPresentation(presentation)) {
      charts.push(presentation);
    } else if (isChartPresentation(chartPresentation)) {
      charts.push(chartPresentation);
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

export function getDataCoverageNoticeFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatDataCoverageNotice | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const notice = (toolCall.metadata as Record<string, unknown>)?.dataCoverageNotice;

    if (
      notice &&
      typeof notice === "object" &&
      typeof (notice as ChatDataCoverageNotice).message === "string" &&
      (notice as ChatDataCoverageNotice).message.trim()
    ) {
      return notice as ChatDataCoverageNotice;
    }
  }

  return null;
}

export function getAvailableFormatsFromToolCalls(
  toolCalls?: ChatToolCall[],
): string[] {
  if (!Array.isArray(toolCalls)) {
    return [];
  }

  for (const toolCall of toolCalls) {
    const formats = (toolCall.metadata as Record<string, unknown>)?.availableFormats;

    if (Array.isArray(formats)) {
      return formats.map((format) => String(format));
    }
  }

  return [];
}

export function getPreferredFormatFromToolCalls(
  toolCalls?: ChatToolCall[],
): ViewFormat | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const preferred = (toolCall.metadata as Record<string, unknown>)?.preferredFormat;

    if (preferred === "text" || preferred === "chart" || preferred === "table" || preferred === "tree") {
      return preferred;
    }
  }

  return null;
}

export function getTextPresentationTitleFromToolCalls(
  toolCalls?: ChatToolCall[],
): string {
  if (!Array.isArray(toolCalls)) {
    return "";
  }

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      typeof (textPresentation as { title?: string }).title === "string"
    ) {
      const title = (textPresentation as { title?: string }).title?.trim();

      if (title) {
        return title;
      }
    }
  }

  return "";
}

export function getTextMarkdownFromToolCalls(toolCalls?: ChatToolCall[]): string {
  if (!Array.isArray(toolCalls)) {
    return "";
  }

  const sections: string[] = [];

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      (textPresentation as { type?: string }).type === "markdown"
    ) {
      const markdown = (textPresentation as { markdown?: string }).markdown;

      if (typeof markdown === "string" && markdown.trim()) {
        sections.push(markdown.trim());
      }
    }
  }

  if (sections.length > 1) {
    return sections.join("\n\n");
  }

  if (sections.length === 1) {
    return sections[0];
  }

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      (textPresentation as { type?: string }).type === "markdown"
    ) {
      const markdown = (textPresentation as { markdown?: string }).markdown;

      if (typeof markdown === "string" && markdown.trim()) {
        return markdown.trim();
      }
    }

    const presentation = toolCall.metadata?.presentation;

    if (
      presentation &&
      typeof presentation === "object" &&
      (presentation as { type?: string }).type === "markdown"
    ) {
      const markdown = (presentation as { markdown?: string }).markdown;

      if (typeof markdown === "string" && markdown.trim()) {
        return markdown.trim();
      }
    }
  }

  return "";
}

function escapeMarkdownCell(value: unknown): string {
  return String(value ?? "")
    .replace(/\|/g, "\\|")
    .replace(/\n/g, " ");
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

export function getPresentationTitle(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const textTitle = getTextPresentationTitleFromToolCalls(toolCalls);

  if (textTitle) {
    return textTitle;
  }

  const pair = getPresentationPairFromToolCalls(toolCalls);

  if (pair.primary?.type === "chart" && pair.primary.title) {
    return pair.primary.title;
  }

  const tree = getTreePresentationFromPair(pair);

  if (tree?.title) {
    return tree.title;
  }

  const table = getTablePresentationFromPair(pair);

  if (table?.title) {
    return table.title;
  }

  return String(messageContent || "").trim() || "Resultado";
}

export function tablePresentationToMarkdown(
  presentation: Extract<ChatPresentation, { type: "table" }>,
  options?: { includeTitle?: boolean },
): string {
  const { title, columns, rows } = presentation;
  const includeTitle = options?.includeTitle !== false;

  if (!columns.length) {
    return includeTitle && title ? `### ${title}` : "";
  }

  const header = columns.map((column) => column.label).join(" | ");
  const separator = columns.map(() => "---").join(" | ");
  const body = rows.map((row) =>
    columns.map((column) => escapeMarkdownCell(row[column.key])).join(" | "),
  );

  const tableLines = [
    `| ${header} |`,
    `| ${separator} |`,
    ...body.map((line) => `| ${line} |`),
  ];

  if (includeTitle && title) {
    return [`### ${title}`, "", ...tableLines].join("\n");
  }

  return tableLines.join("\n");
}

function getTableMarkdownBody(toolCalls?: ChatToolCall[]): string {
  const pair = getPresentationPairFromToolCalls(toolCalls);
  const table = getTablePresentationFromPair(pair);

  if (!table) {
    return "";
  }

  return tablePresentationToMarkdown(table, { includeTitle: false });
}

function stripLeadingMarkdownTitle(markdown: string, title: string): string {
  const normalizedTitle = title.trim();

  if (!normalizedTitle) {
    return markdown.trim();
  }

  const lines = markdown.split("\n");
  const firstNonEmpty = lines.findIndex((line) => line.trim());

  if (firstNonEmpty === -1) {
    return "";
  }

  const heading = lines[firstNonEmpty].trim();

  if (
    heading === `### ${normalizedTitle}` ||
    heading === `## ${normalizedTitle}` ||
    heading === `# ${normalizedTitle}` ||
    heading === normalizedTitle
  ) {
    return lines
      .slice(firstNonEmpty + 1)
      .join("\n")
      .trim();
  }

  return markdown.trim();
}

export function isShortPresentationCaption(
  content: string | null | undefined,
  toolCalls?: ChatToolCall[],
): boolean {
  const trimmed = String(content || "").trim();

  if (!trimmed) {
    return false;
  }

  if (trimmed.includes("|") && trimmed.includes("-")) {
    return false;
  }

  if (trimmed.length > 220 || trimmed.split("\n").length > 5) {
    return false;
  }

  const title = getPresentationTitle(trimmed, toolCalls);

  return trimmed === title || trimmed === `### ${title}`;
}

export function hasDisplayableRichText(text: string | null | undefined): boolean {
  return String(text || "").trim().length > 0;
}

/** Remove dumps técnicos de inspeção (legado) quando há painel estruturado. */
export function stripRedundantInspectionDumpFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      trimmed.startsWith("- Product=")
      || trimmed.includes("Qp6=[")
      || trimmed.includes("Qp7=[")
      || trimmed.includes("QP6_PRODUT")
    ) {
      continue;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function stripRedundantStructureFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      !skipping &&
      (trimmed.startsWith("**Estrutura do produto") ||
        trimmed === "**Produto pai**" ||
        trimmed === "**Componentes nível 1**" ||
        trimmed === "**Estrutura detalhada**")
    ) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (trimmed.startsWith("**Insights**")) {
        skipping = false;
        result.push(line);
      }

      continue;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function stripRedundantHierarchyListFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      trimmed.startsWith("**") &&
      trimmed.includes("—") &&
      (trimmed.includes("| Qtd:") || trimmed.includes("Qtd:"))
    ) {
      continue;
    }

    if (/^Total encontrado:/i.test(trimmed)) {
      continue;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function stripCoverageNoticeFromMarkdown(markdown: string): string {
  const trimmed = String(markdown || "").trim();

  if (!trimmed) {
    return "";
  }

  const coverageBlockPattern =
    /(?:^|\n\n)> \*\*Cobertura dos dados:\*\*[^\n]*(?:\n> [^\n]*)*/gu;

  return trimmed.replace(coverageBlockPattern, "").replace(/\n{3,}/g, "\n\n").trim();
}

function readPaginationDetail(details: Record<string, unknown>): Record<string, unknown> | null {
  for (const key of ["pagination", "structurePagination", "stockPagination"]) {
    const candidate = details[key];

    if (candidate && typeof candidate === "object") {
      return candidate as Record<string, unknown>;
    }
  }

  return null;
}

export function getPaginationStateFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPaginationState | null {
  const notice = getDataCoverageNoticeFromToolCalls(toolCalls);

  if (!notice) {
    return null;
  }

  const details =
    notice.details && typeof notice.details === "object"
      ? notice.details
      : null;
  const pagination = details ? readPaginationDetail(details) : null;

  const page = Number(pagination?.page ?? notice.page);
  const pageSize = Number(pagination?.pageSize ?? notice.pageSize);
  const totalPages = Number(pagination?.totalPages ?? notice.totalPages);
  const total = Number(pagination?.total ?? notice.total);

  if (!Number.isFinite(page) || page < 1 || !Number.isFinite(pageSize) || pageSize < 1) {
    return null;
  }

  const resolvedTotalPages =
    Number.isFinite(totalPages) && totalPages > 0
      ? totalPages
      : Number.isFinite(total) && total > 0
        ? Math.max(1, Math.ceil(total / pageSize))
        : undefined;

  return {
    page,
    pageSize,
    totalPages: resolvedTotalPages,
    total: Number.isFinite(total) && total >= 0 ? total : undefined,
    hasPrevious: page > 1,
    hasNext: resolvedTotalPages ? page < resolvedTotalPages : true,
  };
}

export function getDepthStateFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatDepthState | null {
  const notice = getDataCoverageNoticeFromToolCalls(toolCalls);

  if (!notice) {
    return null;
  }

  const details =
    notice.details && typeof notice.details === "object"
      ? notice.details
      : null;
  const depth =
    details?.depth && typeof details.depth === "object"
      ? (details.depth as Record<string, unknown>)
      : null;
  const maxDepth = Number(depth?.maxDepth ?? notice.maxDepth);

  if (!Number.isFinite(maxDepth) || maxDepth < 1 || maxDepth >= 99) {
    return null;
  }

  return {
    maxDepth,
    canIncrease: maxDepth < 99,
  };
}

export function getPathFromToolCalls(toolCalls?: ChatToolCall[]): string {
  if (!Array.isArray(toolCalls)) {
    return "";
  }

  for (const toolCall of toolCalls) {
    const path = (toolCall.metadata as Record<string, unknown>)?.path;

    if (typeof path === "string" && path.trim()) {
      return path.trim();
    }
  }

  return "";
}

export type PresentationLayoutMode = "toggle" | "commentary-visual";

export function resolvePresentationLayoutMode(
  toolCalls?: ChatToolCall[],
  pair?: PresentationPair,
): PresentationLayoutMode {
  if (!Array.isArray(toolCalls) || toolCalls.length === 0) {
    return "toggle";
  }

  const resolvedPair = pair ?? getPresentationPairFromToolCalls(toolCalls);
  const path = getPathFromToolCalls(toolCalls).toLowerCase();
  const hasTree = Boolean(getTreePresentationFromPair(resolvedPair));
  const hasTable = Boolean(getTablePresentationFromPair(resolvedPair));
  const hasVisual = hasTree || hasTable || resolvedPair.primary?.type === "chart";
  const commentary = resolveCommentaryTextBody("", toolCalls, resolvedPair);

  if (!hasVisual || !hasDisplayableRichText(commentary)) {
    return "toggle";
  }

  if (
    path.includes("/analyser") ||
    path.includes("/parents") ||
    path.includes("/structure")
  ) {
    return "commentary-visual";
  }

  return "toggle";
}

/** @deprecated Prefer resolvePresentationLayoutMode */
export function shouldStackPresentationBlocks(
  toolCalls?: ChatToolCall[],
  pair?: PresentationPair,
): boolean {
  return resolvePresentationLayoutMode(toolCalls, pair) === "commentary-visual";
}

export function resolveCommentaryTextBody(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
  pair?: PresentationPair,
): string {
  const resolvedPair = pair ?? getPresentationPairFromToolCalls(toolCalls);
  const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);
  const presentationTitle =
    getTextPresentationTitleFromToolCalls(toolCalls) ||
    getPresentationTitle(messageContent, toolCalls);

  let body = fromMetadata;

  if (!body) {
    body = stripLeadingMarkdownTitle(
      String(messageContent || "").trim(),
      presentationTitle,
    );
  } else {
    body = stripLeadingMarkdownTitle(body, presentationTitle);
  }

  if (getTreePresentationFromPair(resolvedPair) || getTablePresentationFromPair(resolvedPair)) {
    body = stripRedundantStructureFromMarkdown(body);
    body = stripRedundantHierarchyListFromMarkdown(body);
    body = stripRedundantInspectionDumpFromMarkdown(body);
  }

  body = stripCoverageNoticeFromMarkdown(body);

  return body.trim();
}

/** Corpo markdown da aba Texto (tabela em GFM), sem repetir o título do cabeçalho. */
export function resolveRichTextBody(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const pair = getPresentationPairFromToolCalls(toolCalls);
  const fromMessage = String(messageContent || "").trim();
  const presentationTitle = getPresentationTitle(fromMessage, toolCalls);
  const hasTree = Boolean(getTreePresentationFromPair(pair));
  const hasHierarchyTable = Boolean(getTablePresentationFromPair(pair));
  const tableBody = getTableMarkdownBody(toolCalls);

  if (
    tableBody &&
    !hasTree &&
    !hasHierarchyTable &&
    (isShortPresentationCaption(fromMessage, toolCalls) || !fromMessage)
  ) {
    return tableBody;
  }

  const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);

  if (fromMetadata) {
    return stripLeadingMarkdownTitle(fromMetadata, presentationTitle);
  }

  if (fromMessage) {
    return stripLeadingMarkdownTitle(fromMessage, presentationTitle);
  }

  if (!hasTree && !hasHierarchyTable) {
    return tableBody;
  }

  return "";
}

/** Texto do rascunho de e-mail (assunto + corpo), sem blocos de apresentação rica. */
export function buildEmailCopyText(messageContent: string | null | undefined): string {
  const raw = String(messageContent || "").trim();
  if (!raw) {
    return "";
  }

  const withoutRich = raw
    .replace(/^###\s+/gm, "")
    .replace(/\*\*Assunto[^*]*\*\*/gi, (match) => match.replace(/\*\*/g, ""))
    .replace(/\*\*/g, "")
    .trim();

  const subjectMatch = withoutRich.match(/^\s*assunto\s*:\s*(.+)$/im);
  if (subjectMatch) {
    return withoutRich;
  }

  const altSubject = withoutRich.match(/^\s*\*\*assunto\s+sugerido:\*\*\s*(.+)$/im);
  if (altSubject) {
    return withoutRich.replace(/^\s*\*\*assunto\s+sugerido:\*\*\s*/i, "Assunto: ");
  }

  return withoutRich;
}

/** Texto completo para copiar/compartilhar respostas com apresentação rica. */
export function buildAssistantCopyText(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const title = getPresentationTitle(messageContent, toolCalls);
  const body = resolveRichTextBody(messageContent, toolCalls);

  if (title && body) {
    return `${title}\n\n${body}`;
  }

  return body || title || String(messageContent || "").trim();
}

/** Compat: título + corpo (legado). Preferir getPresentationTitle + resolveRichTextBody. */
export function resolveRichTextContent(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const title = getPresentationTitle(messageContent, toolCalls);
  const body = resolveRichTextBody(messageContent, toolCalls);

  if (title && body) {
    return `### ${title}\n\n${body}`;
  }

  return body || title;
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

export function hasMultiFormatPresentation(toolCalls?: ChatToolCall[]): boolean {
  const formats = getAvailableFormatsFromToolCalls(toolCalls);
  const unique = new Set(formats);

  if (unique.size >= 2) {
    return true;
  }

  const pair = getPresentationPairFromToolCalls(toolCalls);
  const flags = [
    Boolean(resolveRichTextContent("", toolCalls)),
    pair.primary?.type === "chart" || pair.table?.type === "table",
    pair.primary?.type === "table" || pair.table?.type === "table",
    pair.primary?.type === "tree" || pair.tree?.type === "tree",
  ];

  return flags.filter(Boolean).length >= 2;
}

/** Exibe tabela/gráfico/KPI ou painel multi-formato; evita repetir só markdown na aba Texto. */
export function shouldShowRichPresentation(
  content: string | null | undefined,
  toolCalls?: ChatToolCall[],
): boolean {
  if (!Array.isArray(toolCalls) || toolCalls.length === 0) {
    return false;
  }

  const pair = getPresentationPairFromToolCalls(toolCalls);

  if (hasRichPresentation(pair)) {
    return true;
  }

  if (hasMultiFormatPresentation(toolCalls)) {
    return true;
  }

  return shouldSuppressMarkdownForPresentation(content, pair, toolCalls);
}

export function shouldSuppressMarkdownForPresentation(
  content: string | null | undefined,
  pair: PresentationPair,
  toolCalls?: ChatToolCall[],
): boolean {
  const trimmed = String(content || "").trim();

  if (hasMultiFormatPresentation(toolCalls)) {
    if (!trimmed) {
      return true;
    }

    if (isShortPresentationCaption(trimmed, toolCalls)) {
      return true;
    }
  }

  if (!hasRichPresentation(pair)) {
    return false;
  }

  if (shouldStackPresentationBlocks(toolCalls, pair)) {
    if (!trimmed) {
      return true;
    }

    if (isShortPresentationCaption(trimmed, toolCalls)) {
      return true;
    }

    const stackTitle = getPresentationTitle(content, toolCalls);
    const tableTitle = getTablePresentationFromPair(pair)?.title;
    const commentary = resolveCommentaryTextBody(content, toolCalls, pair);

    if (trimmed === stackTitle || trimmed === `### ${stackTitle}`) {
      return true;
    }

    if (tableTitle && (trimmed === tableTitle || trimmed === `### ${tableTitle}` || trimmed.includes(tableTitle))) {
      return true;
    }

    if (commentary && trimmed === commentary) {
      return true;
    }

    if (stripRedundantHierarchyListFromMarkdown(trimmed) !== trimmed) {
      return true;
    }
  }

  const panelBody = resolveRichTextBody(content, toolCalls);
  const panelTitle = getPresentationTitle(content, toolCalls);

  if (!hasDisplayableRichText(panelBody) && !panelTitle) {
    return false;
  }

  if (!trimmed) {
    return false;
  }

  if (isShortPresentationCaption(trimmed, toolCalls)) {
    return true;
  }

  if (trimmed === panelTitle) {
    return true;
  }

  if (trimmed.includes("|") && trimmed.includes("-")) {
    return true;
  }

  if (pair.primary?.type === "kpi") {
    return trimmed.length > 80;
  }

  return trimmed.length > 100;
}

function hasToolCallTextPresentation(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      typeof (textPresentation as { markdown?: string }).markdown === "string" &&
      (textPresentation as { markdown?: string }).markdown?.trim()
    ) {
      return true;
    }
  }

  return false;
}

/** Oculta JSON bruto da API quando já há apresentação rica ou texto humanizado. */
export function shouldShowActionResults(
  content: string | null | undefined,
  toolCalls?: ChatToolCall[],
): boolean {
  if (!Array.isArray(toolCalls) || toolCalls.length === 0) {
    return false;
  }

  if (shouldShowRichPresentation(content, toolCalls)) {
    return false;
  }

  return !hasToolCallTextPresentation(toolCalls);
}
