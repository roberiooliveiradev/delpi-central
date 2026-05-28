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

export function tablePresentationToMarkdown(
  presentation: Extract<ChatPresentation, { type: "table" }>,
): string {
  const { title, columns, rows } = presentation;

  if (!columns.length) {
    return title ? `### ${title}` : "";
  }

  const header = columns.map((column) => column.label).join(" | ");
  const separator = columns.map(() => "---").join(" | ");
  const body = rows.map((row) =>
    columns.map((column) => escapeMarkdownCell(row[column.key])).join(" | "),
  );

  return [
    title ? `### ${title}` : "",
    "",
    `| ${header} |`,
    `| ${separator} |`,
    ...body.map((line) => `| ${line} |`),
  ]
    .filter(Boolean)
    .join("\n");
}

function getTableMarkdownFallback(toolCalls?: ChatToolCall[]): string {
  const pair = getPresentationPairFromToolCalls(toolCalls);
  const table =
    pair.table?.type === "table"
      ? pair.table
      : pair.primary?.type === "table"
        ? pair.primary
        : null;

  if (!table) {
    return "";
  }

  return tablePresentationToMarkdown(table);
}

export function hasDisplayableRichText(text: string | null | undefined): boolean {
  return String(text || "").trim().length > 0;
}

export function resolveRichTextContent(
  messageContent: string | null | undefined,
  toolCalls?: ChatToolCall[],
): string {
  const fromMessage = String(messageContent || "").trim();

  if (fromMessage) {
    return fromMessage;
  }

  const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);

  if (fromMetadata) {
    return fromMetadata;
  }

  return getTableMarkdownFallback(toolCalls);
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

/** Não renderiza markdown duplicado quando o painel rico já exibe o mesmo conteúdo na aba Texto. */
export function shouldSuppressMarkdownForPresentation(
  content: string | null | undefined,
  pair: PresentationPair,
  toolCalls?: ChatToolCall[],
): boolean {
  if (!hasRichPresentation(pair)) {
    return false;
  }

  const panelText = resolveRichTextContent(content, toolCalls);

  if (!hasDisplayableRichText(panelText)) {
    return false;
  }

  const trimmed = String(content || "").trim();

  if (!trimmed) {
    return false;
  }

  const normalizedPanel = panelText.trim();
  const normalizedContent = trimmed;

  if (normalizedContent === normalizedPanel) {
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
