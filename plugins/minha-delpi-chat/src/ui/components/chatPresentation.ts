import type { ChatMessage, ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";

export type PresentationPair = {
  primary: ChatPresentation | null;
  table: ChatPresentation | null;
};

export type ViewFormat = "text" | "chart" | "table";

function getPresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
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

  for (const toolCall of toolCalls) {
    const tablePresentation = (toolCall.metadata as Record<string, unknown>)?.tablePresentation;

    if (
      tablePresentation &&
      typeof tablePresentation === "object" &&
      "type" in (tablePresentation as Record<string, unknown>)
    ) {
      return tablePresentation as ChatPresentation;
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
