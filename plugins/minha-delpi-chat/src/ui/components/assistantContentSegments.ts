import type { ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";
import {
  resolveAssistantRenderableMarkdown,
  shouldRenderPresentationHeading,
} from "./assistantProseRendering";
import type { AssistantContentSegment } from "./assistantContentTypes";

export type { AssistantContentSegment } from "./assistantContentTypes";

import {
  isNativeSingleViewSelection,
  orderVisualSegments,
  resolveAssistantContentLayout,
  resolveStackLayoutOrderFromToolCalls,
  segmentVisualKind,
} from "./assistantContentLayout";
import {
  getPresentationDecisionFromToolCalls,
  getPresentationPairFromToolCalls,
  isExplicitTextSessionMode,
  resolveStackCommentaryBody,
  tablePresentationToMarkdown,
} from "./chatPresentation";
import { buildInterleavedStackSegments } from "./assistantContentInterleave";
import { buildMultiRouteStackSegments } from "./presentationMultiRoute";
import {
  dedupeTablePresentations,
  dedupeTableSegments,
  isSameTablePresentation,
} from "./presentationTableDedup";
import { shouldSkipTableSegment } from "./presentationStructureDedup";
import { normalizeChartPresentation } from "./chartPresentationNormalize";

const SQL_FENCE_RE = /```sql\s*([\s\S]*?)```/gi;

const SQL_AUTHORING_INTRO_RE =
  /Segue a consulta em SQL\s*\(somente leitura[\s\S]*?conforme o ambiente:\s*/gi;

function normalizeProseChunk(value: string): string {
  return value
    .replace(/```[\w]*/gi, "")
    .replace(/`+/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function proseChunksSimilar(left: string, right: string): boolean {
  const leftKey = normalizeProseChunk(left);
  const rightKey = normalizeProseChunk(right);

  if (!leftKey || !rightKey) {
    return false;
  }

  if (leftKey.length < 24 || rightKey.length < 24) {
    return leftKey === rightKey;
  }

  if (leftKey.includes(rightKey) || rightKey.includes(leftKey)) {
    return true;
  }

  const sample = (value: string) => value.slice(0, 500);
  const leftSample = sample(leftKey);
  const rightSample = sample(rightKey);
  let matches = 0;
  const limit = Math.min(leftSample.length, rightSample.length);

  for (let index = 0; index < limit; index += 1) {
    if (leftSample[index] === rightSample[index]) {
      matches += 1;
    }
  }

  return limit > 0 && matches / limit >= 0.82;
}

function stripRedundantSqlTailProse(content: string): string {
  const pattern = /```sql\s*[\s\S]*?```/gi;
  const blocks = [...content.matchAll(pattern)];

  if (!blocks.length) {
    return content;
  }

  const primary = blocks[0];
  const start = primary.index ?? 0;
  const end = start + primary[0].length;
  const before = content.slice(0, start).trim();
  const tail = content.slice(end).replace(pattern, "").trim();

  if (!tail) {
    return content.slice(0, end).trim();
  }

  if (before && proseChunksSimilar(before, tail)) {
    return content.slice(0, end).trim();
  }

  const paragraphs = tail
    .split(/\n\s*\n/)
    .map((part) => part.trim())
    .filter(Boolean);
  const kept: string[] = [];

  for (const paragraph of paragraphs) {
    if (before && proseChunksSimilar(before, paragraph)) {
      continue;
    }

    if (kept.length && proseChunksSimilar(kept[kept.length - 1], paragraph)) {
      continue;
    }

    kept.push(paragraph);
  }

  if (!kept.length) {
    return content.slice(0, end).trim();
  }

  return `${content.slice(0, end).trim()}\n\n${kept.join("\n\n")}`.trim();
}

function stripDuplicateSqlAuthoringIntro(content: string): string {
  const matches = [...content.matchAll(SQL_AUTHORING_INTRO_RE)];

  if (matches.length <= 1) {
    return content.trim();
  }

  let seen = false;

  return content
    .replace(SQL_AUTHORING_INTRO_RE, (match) => {
      if (!seen) {
        seen = true;
        return match;
      }

      return "";
    })
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

const SQL_AUTHORING_INTRO =
  "Segue a consulta em SQL (somente leitura, sem executar no sistema). " +
  "Ajuste sufixo de tabela (ex.: SA1010) conforme o ambiente:";

function extractSqlFromFence(fence: string): string {
  return fence
    .replace(/^```sql\s*/i, "")
    .replace(/\s*```\s*$/i, "")
    .trim();
}

function collectUniqueAuthoringProse(content: string): string[] {
  const fragments: string[] = [];
  let cursor = 0;

  for (const match of content.matchAll(SQL_FENCE_RE)) {
    const index = match.index ?? 0;
    fragments.push(content.slice(cursor, index));
    cursor = index + match[0].length;
  }

  fragments.push(content.slice(cursor));

  const paragraphs = fragments.flatMap((fragment) =>
    fragment
      .replace(SQL_AUTHORING_INTRO_RE, "\n")
      .split(/\n\s*\n/)
      .map((part) => part.trim())
      .filter(Boolean),
  );
  const kept: string[] = [];

  for (const paragraph of paragraphs) {
    if (proseChunksSimilar(SQL_AUTHORING_INTRO, paragraph)) {
      continue;
    }

    if (kept.length && proseChunksSimilar(kept[kept.length - 1], paragraph)) {
      continue;
    }

    kept.push(paragraph);
  }

  return kept;
}

function canonicalizeSqlAuthoringMarkdown(content: string): string {
  const blocks = [...content.matchAll(SQL_FENCE_RE)];

  if (!blocks.length) {
    return content.trim();
  }

  const sqlBody = blocks
    .map((block) => extractSqlFromFence(block[0]))
    .sort((left, right) => {
      const lineDelta = right.split("\n").length - left.split("\n").length;

      return lineDelta || right.length - left.length;
    })[0];

  if (!sqlBody) {
    return content.trim();
  }

  const firstIndex = blocks[0].index ?? 0;
  const beforeFirst = content.slice(0, firstIndex).trim();
  const customBefore = beforeFirst.replace(SQL_AUTHORING_INTRO_RE, "").trim();
  const paragraphs = collectUniqueAuthoringProse(content);
  const parts: string[] = [];

  if (customBefore.length >= 16) {
    parts.push(customBefore);
  } else {
    parts.push(SQL_AUTHORING_INTRO);
  }

  parts.push(`\`\`\`sql\n${sqlBody}\n\`\`\``);

  for (const paragraph of paragraphs) {
    if (parts.length && proseChunksSimilar(parts[0], paragraph)) {
      continue;
    }

    parts.push(paragraph);
  }

  return parts.join("\n\n").trim();
}

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

function sameAssistantSegment(
  left: AssistantContentSegment,
  right: AssistantContentSegment,
): boolean {
  if (left.kind !== right.kind) {
    return false;
  }

  if (left.kind === "markdown") {
    return right.kind === "markdown" && left.markdown === right.markdown;
  }

  if (left.kind === "code") {
    return right.kind === "code" && left.language === right.language && left.code === right.code;
  }

  if (left.kind === "table" && right.kind === "table") {
    return isSameTablePresentation(left.presentation, right.presentation);
  }

  if (left.kind === "stackSection" && right.kind === "stackSection") {
    return left.section.id === right.section.id;
  }

  if (
    left.kind === "chart" ||
    left.kind === "tree" ||
    left.kind === "kpi" ||
    left.kind === "dashboard"
  ) {
    return (
      (right.kind === "chart" ||
        right.kind === "tree" ||
        right.kind === "kpi" ||
        right.kind === "dashboard") &&
      left.presentation === right.presentation
    );
  }

  return false;
}

function appendVisualSegment(
  segments: AssistantContentSegment[],
  segment: AssistantContentSegment,
): void {
  const exists = segments.some((item) => sameAssistantSegment(item, segment));

  if (!exists) {
    segments.push(segment);
  }
}

function collectVisualSegments(toolCalls: ChatToolCall[]): AssistantContentSegment[] {
  const segments: AssistantContentSegment[] = [];
  const tableCandidates: Extract<ChatPresentation, { type: "table" }>[] = [];

  const queueTable = (presentation: Extract<ChatPresentation, { type: "table" }>) => {
    if (shouldSkipTableSegment(presentation, toolCalls)) {
      return;
    }

    tableCandidates.push(presentation);
  };

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
        queueTable(typed);
      } else if (typed.type === "chart") {
        appendVisualSegment(segments, { kind: "chart", presentation: typed });
      } else if (typed.type === "tree") {
        appendVisualSegment(segments, { kind: "tree", presentation: typed });
      } else if (typed.type === "kpi") {
        appendVisualSegment(segments, { kind: "kpi", presentation: typed });
      } else if (typed.type === "dashboard") {
        appendVisualSegment(segments, { kind: "dashboard", presentation: typed });
      }
    }

    const bundledTables = metadata.tablePresentations;

    if (Array.isArray(bundledTables) && bundledTables.length) {
      for (const candidate of bundledTables) {
        if (
          candidate &&
          typeof candidate === "object" &&
          (candidate as ChatPresentation).type === "table"
        ) {
          queueTable(candidate as Extract<ChatPresentation, { type: "table" }>);
        }
      }
    } else {
      for (const key of [
        "tablePresentation",
        "profileTablePresentation",
        "inspectionTablePresentation",
      ]) {
        const slot = metadata[key];

        if (
          slot &&
          typeof slot === "object" &&
          (slot as ChatPresentation).type === "table"
        ) {
          queueTable(slot as Extract<ChatPresentation, { type: "table" }>);
        }
      }
    }

    const chartPresentation = normalizeChartPresentation(metadata.chartPresentation);

    if (chartPresentation) {
      appendVisualSegment(segments, {
        kind: "chart",
        presentation: chartPresentation,
      });
    }

    const treePresentation = metadata.treePresentation;

    if (
      treePresentation &&
      typeof treePresentation === "object" &&
      (treePresentation as ChatPresentation).type === "tree"
    ) {
      appendVisualSegment(segments, {
        kind: "tree",
        presentation: treePresentation as Extract<ChatPresentation, { type: "tree" }>,
      });
    }

    const kpiPresentation = metadata.kpiPresentation;

    if (
      kpiPresentation &&
      typeof kpiPresentation === "object" &&
      (kpiPresentation as ChatPresentation).type === "kpi"
    ) {
      appendVisualSegment(segments, {
        kind: "kpi",
        presentation: kpiPresentation as Extract<ChatPresentation, { type: "kpi" }>,
      });
    }

    const dashboardPresentation = metadata.dashboardPresentation;

    if (
      dashboardPresentation &&
      typeof dashboardPresentation === "object" &&
      (dashboardPresentation as ChatPresentation).type === "dashboard"
    ) {
      appendVisualSegment(segments, {
        kind: "dashboard",
        presentation: dashboardPresentation as Extract<ChatPresentation, { type: "dashboard" }>,
      });
    }
  }

  for (const table of dedupeTablePresentations(tableCandidates)) {
    appendVisualSegment(segments, { kind: "table", presentation: table });
  }

  return dedupeTableSegments(segments);
}

export function dedupeSqlFencesInMarkdown(content: string): string {
  const matches = [...content.matchAll(SQL_FENCE_RE)];

  if (!matches.length) {
    return content.trim();
  }

  const merged =
    matches.length > 1 ? canonicalizeSqlAuthoringMarkdown(content) : content.trim();

  return stripRedundantSqlTailProse(stripDuplicateSqlAuthoringIntro(merged));
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

function splitMarkdownWithPresentationMarkers(
  markdown: string,
  visuals: AssistantContentSegment[],
): AssistantContentSegment[] {
  return buildInterleavedStackSegments(
    markdown,
    visuals,
    parseMarkdownAndCodeSegments,
    appendVisualSegment,
  );
}

function buildStackedSegments(
  content: string,
  toolCalls: ChatToolCall[],
  visuals: AssistantContentSegment[],
): AssistantContentSegment[] {
  const commentary = resolveStackCommentaryBody(content, toolCalls);
  const layoutOrder = resolveStackLayoutOrderFromToolCalls(toolCalls);
  const visualOrder = layoutOrder.filter((slot) => slot !== "text");
  const orderedVisuals = orderVisualSegments(visuals, visualOrder);

  const multiRoute = buildMultiRouteStackSegments(
    commentary,
    toolCalls,
    appendVisualSegment,
  );

  if (multiRoute?.length) {
    return multiRoute;
  }

  return buildInterleavedStackSegments(
    commentary,
    orderedVisuals,
    parseMarkdownAndCodeSegments,
    appendVisualSegment,
    toolCalls,
  );
}

function appendEmbeddedTablesForExplicitText(
  markdown: string,
  toolCalls: ChatToolCall[],
): string {
  const body = String(markdown || "").trim();

  if (!body || body.includes("|")) {
    return body;
  }

  const sections: string[] = [body];
  const seen = new Set<string>();

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const candidates: Extract<ChatPresentation, { type: "table" }>[] = [];

    const pushTable = (value: unknown) => {
      if (
        value &&
        typeof value === "object" &&
        (value as ChatPresentation).type === "table"
      ) {
        candidates.push(value as Extract<ChatPresentation, { type: "table" }>);
      }
    };

    pushTable(metadata.presentation);
    pushTable(metadata.profileTablePresentation);
    pushTable(metadata.tablePresentation);
    pushTable(metadata.inspectionTablePresentation);

    const bundled = metadata.tablePresentations;

    if (Array.isArray(bundled)) {
      for (const item of bundled) {
        pushTable(item);
      }
    }

    for (const table of dedupeTablePresentations(candidates)) {
      const section = tablePresentationToMarkdown(table).trim();

      if (!section || seen.has(section)) {
        continue;
      }

      seen.add(section);
      sections.push(section);
    }
  }

  return sections.join("\n\n").trim();
}

export function buildAssistantContentSegments(
  content: string,
  toolCalls: ChatToolCall[] = [],
): AssistantContentSegment[] {
  if (isExplicitTextSessionMode(toolCalls)) {
    const markdown = appendEmbeddedTablesForExplicitText(
      resolveAssistantRenderableMarkdown(content, toolCalls),
      toolCalls,
    );

    return parseMarkdownAndCodeSegments(markdown);
  }

  const pair = getPresentationPairFromToolCalls(toolCalls);
  const layoutMode = resolveAssistantContentLayout(content, toolCalls, pair);
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const selected = String(decision?.selected ?? "").trim().toLowerCase();
  const visuals = collectVisualSegments(toolCalls);
  const rawMarkdown = resolveAssistantRenderableMarkdown(content, toolCalls);
  const nativeSingle = isNativeSingleViewSelection(toolCalls);

  if (
    layoutMode !== "stack" &&
    selected === "text" &&
    !(nativeSingle.active && nativeSingle.kind && nativeSingle.kind !== "text" && visuals.length)
  ) {
    return parseMarkdownAndCodeSegments(rawMarkdown);
  }

  if (
    nativeSingle.active &&
    nativeSingle.kind &&
    nativeSingle.kind !== "text" &&
    visuals.length
  ) {
    const caption = rawMarkdown.trim();
    const segments: AssistantContentSegment[] = [];

    if (caption) {
      segments.push(...parseMarkdownAndCodeSegments(caption));
    }

    const orderedVisuals = orderVisualSegments(visuals, [nativeSingle.kind]);

    for (const visual of orderedVisuals) {
      if (segmentVisualKind(visual) === nativeSingle.kind) {
        segments.push(visual);
      }
    }

    return segments.length ? segments : orderedVisuals;
  }

  if (layoutMode === "stack") {
    return buildStackedSegments(content, toolCalls, visuals);
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
    const introOnly = (value: string) => {
      const normalized = value.trim();
      const withoutIntro = normalized.replace(SQL_AUTHORING_INTRO_RE, "").trim();

      return (
        /segue a consulta em sql/i.test(normalized) && withoutIntro.length < 8
      );
    };

    const filtered = textSegments.filter((segment, index, list) => {
      if (segment.kind !== "markdown" || !introOnly(segment.markdown)) {
        return true;
      }

      const hasCodeAfter = list.slice(index + 1).some((item) => item.kind === "code");

      if (hasCodeAfter) {
        return false;
      }

      const earlierIntro = list
        .slice(0, index)
        .some((item) => item.kind === "markdown" && introOnly(item.markdown));

      return !earlierIntro;
    });

    const codeIndex = filtered.findIndex((item) => item.kind === "code");

    if (codeIndex >= 0) {
      const beforeMarkdown = filtered
        .slice(0, codeIndex)
        .filter((item) => item.kind === "markdown")
        .map((item) => (item.kind === "markdown" ? item.markdown : ""))
        .join("\n\n");
      const dedupedAroundCode = filtered.filter((segment, index) => {
        if (segment.kind !== "markdown" || index <= codeIndex) {
          return true;
        }

        return !proseChunksSimilar(beforeMarkdown, segment.markdown);
      });

      return dedupedAroundCode.length ? dedupedAroundCode : textSegments;
    }

    return filtered.length ? filtered : textSegments;
  }

  if (textSegments.length && visuals.length) {
    return buildStackedSegments(content, toolCalls, visuals);
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

/** @deprecated Preferir `shouldRenderPresentationHeading` em assistantProseRendering. */
export function isPresentationHeadingTitle(
  title: string | null | undefined,
): boolean {
  return shouldRenderPresentationHeading(title);
}
