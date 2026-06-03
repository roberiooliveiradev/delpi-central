import type { ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";

import {
  getPresentationPairFromToolCalls,
  getTextMarkdownFromToolCalls,
  resolveCommentaryTextBody,
  resolvePresentationLayoutMode,
  stripLeadingMarkdownTitle,
  getPresentationTitle,
} from "./chatPresentation";

export type AssistantContentSegment =
  | { kind: "markdown"; markdown: string }
  | { kind: "code"; language: string; code: string }
  | { kind: "table"; presentation: Extract<ChatPresentation, { type: "table" }> }
  | { kind: "chart"; presentation: Extract<ChatPresentation, { type: "chart" }> }
  | { kind: "tree"; presentation: Extract<ChatPresentation, { type: "tree" }> }
  | { kind: "kpi"; presentation: Extract<ChatPresentation, { type: "kpi" }> }
  | { kind: "dashboard"; presentation: Extract<ChatPresentation, { type: "dashboard" }> };

const PRESENTATION_MARKER_RE =
  /\[\[(tabela|table|grafico|chart|arvore|tree|kpi|dashboard)(?::(\d+))?]]/gi;

const SQL_FENCE_RE = /```sql\s*([\s\S]*?)```/gi;

function isSuppressedToolCall(toolCall: ChatToolCall): boolean {
  const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;

  if (metadata.sqlSchemaPrefetch === true || metadata.suppressClientPresentation === true) {
    return true;
  }

  const path = String(metadata.path || "").toLowerCase();

  return (
    path.includes("/system/tables") &&
    (path.includes("/columns") || path.includes("/schema") || path.includes("/relations"))
  );
}

function collectVisualSegments(toolCalls: ChatToolCall[]): AssistantContentSegment[] {
  const segments: AssistantContentSegment[] = [];

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    if (isSuppressedToolCall(toolCall)) {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const presentation = metadata.presentation;

    if (presentation && typeof presentation === "object" && "type" in presentation) {
      const typed = presentation as ChatPresentation;

      if (typed.type === "table") {
        segments.push({ kind: "table", presentation: typed });
        continue;
      }

      if (typed.type === "chart") {
        segments.push({ kind: "chart", presentation: typed });
        continue;
      }

      if (typed.type === "tree") {
        segments.push({ kind: "tree", presentation: typed });
        continue;
      }

      if (typed.type === "kpi") {
        segments.push({ kind: "kpi", presentation: typed });
        continue;
      }

      if (typed.type === "dashboard") {
        segments.push({ kind: "dashboard", presentation: typed });
      }
    }

    const tablePresentation = metadata.tablePresentation;

    if (
      tablePresentation &&
      typeof tablePresentation === "object" &&
      (tablePresentation as ChatPresentation).type === "table"
    ) {
      segments.push({
        kind: "table",
        presentation: tablePresentation as Extract<ChatPresentation, { type: "table" }>,
      });
    }

    const chartPresentation = metadata.chartPresentation;

    if (
      chartPresentation &&
      typeof chartPresentation === "object" &&
      (chartPresentation as ChatPresentation).type === "chart"
    ) {
      segments.push({
        kind: "chart",
        presentation: chartPresentation as Extract<ChatPresentation, { type: "chart" }>,
      });
    }

    const treePresentation = metadata.treePresentation;

    if (
      treePresentation &&
      typeof treePresentation === "object" &&
      (treePresentation as ChatPresentation).type === "tree"
    ) {
      segments.push({
        kind: "tree",
        presentation: treePresentation as Extract<ChatPresentation, { type: "tree" }>,
      });
    }
  }

  return segments;
}

export function dedupeSqlFencesInMarkdown(content: string): string {
  const matches = [...content.matchAll(SQL_FENCE_RE)];

  if (matches.length <= 1) {
    return content.trim();
  }

  const first = matches[0][0];
  const withoutRest = content.replace(SQL_FENCE_RE, "").trim();

  return `${first}\n\n${withoutRest}`.trim();
}

export function parseMarkdownAndCodeSegments(content: string): AssistantContentSegment[] {
  const normalized = dedupeSqlFencesInMarkdown(content);
  const segments: AssistantContentSegment[] = [];
  let lastIndex = 0;

  for (const match of normalized.matchAll(SQL_FENCE_RE)) {
    const index = match.index ?? 0;
    const prose = normalized.slice(lastIndex, index).trim();

    if (prose) {
      segments.push({ kind: "markdown", markdown: prose });
    }

    const code = String(match[1] || "").trim();

    if (code) {
      segments.push({ kind: "code", language: "sql", code });
    }

    lastIndex = index + match[0].length;
  }

  const tail = normalized.slice(lastIndex).trim();

  if (tail) {
    segments.push({ kind: "markdown", markdown: tail });
  }

  if (!segments.length && normalized) {
    segments.push({ kind: "markdown", markdown: normalized });
  }

  return segments;
}

function resolveMarkerPresentation(
  marker: string,
  index: number | undefined,
  visuals: AssistantContentSegment[],
): AssistantContentSegment | null {
  const kind =
    marker === "tabela" || marker === "table"
      ? "table"
      : marker === "grafico" || marker === "chart"
        ? "chart"
        : marker === "arvore" || marker === "tree"
          ? "tree"
          : marker === "kpi"
            ? "kpi"
            : "dashboard";

  const pool = visuals.filter((item) => item.kind === kind);

  if (!pool.length) {
    return null;
  }

  const position = index ?? 1;

  return pool[Math.max(0, Math.min(pool.length, position) - 1)] ?? null;
}

function splitMarkdownWithPresentationMarkers(
  markdown: string,
  visuals: AssistantContentSegment[],
): AssistantContentSegment[] {
  const segments: AssistantContentSegment[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  const pattern = new RegExp(PRESENTATION_MARKER_RE);

  while ((match = pattern.exec(markdown)) !== null) {
    const index = match.index ?? 0;
    const prose = markdown.slice(lastIndex, index).trim();

    if (prose) {
      segments.push(...parseMarkdownAndCodeSegments(prose));
    }

    const marker = String(match[1] || "").toLowerCase();
    const markerIndex = match[2] ? Number.parseInt(match[2], 10) : undefined;
    const visual = resolveMarkerPresentation(marker, markerIndex, visuals);

    if (visual) {
      segments.push(visual);
    }

    lastIndex = index + match[0].length;
  }

  const tail = markdown.slice(lastIndex).trim();

  if (tail) {
    segments.push(...parseMarkdownAndCodeSegments(tail));
  }

  return segments;
}

function resolvePrimaryMarkdown(
  content: string,
  toolCalls: ChatToolCall[],
): string {
  const fromMetadata = getTextMarkdownFromToolCalls(toolCalls);
  const presentationTitle = getPresentationTitle(content, toolCalls);
  const raw = String(content || "").trim();

  if (fromMetadata) {
    return stripLeadingMarkdownTitle(fromMetadata, presentationTitle);
  }

  return stripLeadingMarkdownTitle(raw, presentationTitle);
}

export function buildAssistantContentSegments(
  content: string,
  toolCalls: ChatToolCall[] = [],
): AssistantContentSegment[] {
  const pair = getPresentationPairFromToolCalls(toolCalls);
  const layoutMode = resolvePresentationLayoutMode(toolCalls, pair);
  const visuals = collectVisualSegments(toolCalls);
  const rawMarkdown = resolvePrimaryMarkdown(content, toolCalls);

  if (layoutMode === "commentary-visual") {
    const commentary = resolveCommentaryTextBody(content, toolCalls, pair);
    const segments: AssistantContentSegment[] = [];

    if (commentary.trim()) {
      segments.push(...splitMarkdownWithPresentationMarkers(commentary, visuals));
    }

    for (const visual of visuals) {
      if (!segments.some((item) => item === visual)) {
        segments.push(visual);
      }
    }

    return segments;
  }

  if (/\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)/i.test(rawMarkdown)) {
    return splitMarkdownWithPresentationMarkers(rawMarkdown, visuals);
  }

  const textSegments = parseMarkdownAndCodeSegments(rawMarkdown);
  const usedVisuals = new Set<AssistantContentSegment>();

  if (!visuals.length) {
    return textSegments;
  }

  const proseOnly = textSegments.every((item) => item.kind === "markdown" || item.kind === "code");
  const hasSqlCode = textSegments.some((item) => item.kind === "code");

  if (proseOnly && hasSqlCode) {
    return textSegments;
  }

  const combined = [...textSegments];

  for (const visual of visuals) {
    combined.push(visual);
    usedVisuals.add(visual);
  }

  return combined;
}

export function hasAssistantContentSegments(
  content: string,
  toolCalls: ChatToolCall[] = [],
): boolean {
  return buildAssistantContentSegments(content, toolCalls).length > 0;
}
