import type { ChatMessage, ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";

export type PresentationPair = {
  primary: ChatPresentation | null;
  table: ChatPresentation | null;
};

export type ViewFormat = "text" | "chart" | "table";

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
} {
  const charts: Extract<ChatPresentation, { type: "chart" }>[] = [];
  const tables: Extract<ChatPresentation, { type: "table" }>[] = [];

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const presentation = metadata.presentation;
    const tablePresentation = metadata.tablePresentation;

    if (isChartPresentation(presentation)) {
      charts.push(presentation);
    }

    if (isTablePresentation(tablePresentation)) {
      tables.push(tablePresentation);
    } else if (isTablePresentation(presentation)) {
      tables.push(presentation);
    }
  }

  return { charts, tables };
}

function getPresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  const { charts, tables } = collectExternalActionPresentations(toolCalls);
  const mergedChart = mergeChartPresentations(charts, tables);

  if (mergedChart) {
    return mergedChart;
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

    if (preferred === "text" || preferred === "chart" || preferred === "table") {
      return preferred;
    }
  }

  return null;
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

export function getPresentationTitle(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const pair = getPresentationPairFromToolCalls(toolCalls);

  if (pair.primary?.type === "chart" && pair.primary.title) {
    return pair.primary.title;
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

/** Corpo markdown da aba Texto (tabela em GFM), sem repetir o título do cabeçalho. */
export function resolveRichTextBody(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const fromMessage = String(messageContent || "").trim();
  const tableBody = getTableMarkdownBody(toolCalls);
  const presentationTitle = getPresentationTitle(fromMessage, toolCalls);

  if (tableBody && (isShortPresentationCaption(fromMessage, toolCalls) || !fromMessage)) {
    return tableBody;
  }

  const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);

  if (fromMetadata) {
    return stripLeadingMarkdownTitle(fromMetadata, presentationTitle);
  }

  if (fromMessage) {
    return stripLeadingMarkdownTitle(fromMessage, presentationTitle);
  }

  return tableBody;
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
  };
}

export function getPresentationFromMessages(
  messages: ChatMessage[],
): ChatPresentation | null {
  for (const message of [...messages].reverse()) {
    const toolCalls = message.metadata?.toolCalls;

    const presentation = getPresentationFromToolCalls(toolCalls);

    if (presentation) {
      return presentation;
    }
  }

  return null;
}

export function getPresentationFromStreamingToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  return getPresentationFromToolCalls(toolCalls);
}

const RICH_PRESENTATION_TYPES = new Set(["table", "chart", "kpi"]);

export function hasRichPresentation(pair: PresentationPair): boolean {
  const primaryType = pair.primary?.type;

  if (primaryType && RICH_PRESENTATION_TYPES.has(primaryType)) {
    return true;
  }

  const tableType = pair.table?.type;

  return Boolean(tableType && RICH_PRESENTATION_TYPES.has(tableType));
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

/** Não renderiza markdown duplicado quando o painel rico já exibe o mesmo conteúdo na aba Texto. */
export function shouldSuppressMarkdownForPresentation(
  content: string | null | undefined,
  pair: PresentationPair,
  toolCalls?: ChatToolCall[],
): boolean {
  if (!hasRichPresentation(pair)) {
    return false;
  }

  const panelBody = resolveRichTextBody(content, toolCalls);
  const panelTitle = getPresentationTitle(content, toolCalls);

  if (!hasDisplayableRichText(panelBody) && !panelTitle) {
    return false;
  }

  const trimmed = String(content || "").trim();

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
