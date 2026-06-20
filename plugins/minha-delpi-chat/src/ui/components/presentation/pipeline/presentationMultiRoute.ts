import type { ChatPresentation, ChatToolCall } from "../../../../data/api/chatTypes";

import { orderVisualSegments, resolveVisualOrderFromToolCalls } from "../../message/assistantContentLayout";
import { normalizeChartPresentation } from "../pipeline/chartPresentationNormalize";
import type { AssistantContentSegment } from "../../message/assistantContentTypes";
import { parseMarkdownAndCodeSegments } from "../../message/assistantContentSegments";
import type { StackSectionChrome } from "./presentationStackSections";
import type { StackPresentationPlan } from "./presentationStackPlan";
import {
  isProductRouteKey,
  routeFraming,
  routeTitle,
  type ProductRouteKey,
} from "../../../../content/operationalPresentationContent";
import { dedupeTableSegments } from "./presentationTableDedup";
import {
  resolveRenderableHumanizedDetailLines,
  resolveRenderableHumanizedLines,
  resolveRenderableTemplateMarkdown,
} from "../presentationProseDeliveryReaders";

export type { ProductRouteKey };

export type ProductRouteBlock = {
  path: string;
  routeKey: ProductRouteKey;
  toolCall: ChatToolCall;
};

const ROUTE_SHOW_IN: Record<ProductRouteKey, StackSectionChrome["showIn"]> = {
  profile: ["complete", "text", "table"],
  guide: ["complete", "text", "table"],
  inspection: ["complete", "text", "table"],
  structure: ["complete", "table", "tree"],
  stock: ["complete", "text", "table", "chart"],
  parents: ["complete", "text", "table", "tree"],
  analyser: ["complete", "text", "table", "tree"],
  other: ["complete", "text", "table", "tree", "chart"],
};

function isSuccessfulExternalAction(toolCall: ChatToolCall): boolean {
  if (toolCall.name && toolCall.name !== "execute_external_action") {
    return false;
  }

  const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;

  return metadata.ok === true;
}

export function productCodeFromPath(path: string): string | null {
  const match = /\/products\/([^/]+)/i.exec(String(path || "").trim());

  return match?.[1]?.trim() || null;
}

export function routeKeyFromPath(path: string): ProductRouteKey {
  const lowered = String(path || "").trim().toLowerCase();

  if (lowered.includes("/analyser")) {
    return "analyser";
  }

  if (lowered.includes("/stock")) {
    return "stock";
  }

  if (lowered.includes("/structure")) {
    return "structure";
  }

  if (lowered.includes("/guide")) {
    return "guide";
  }

  if (lowered.includes("/inspection")) {
    return "inspection";
  }

  if (lowered.includes("/parents")) {
    return "parents";
  }

  if (/\/products\/[^/]+\/?$/.test(lowered)) {
    return "profile";
  }

  return "other";
}

export function collectProductRouteBlocks(toolCalls: ChatToolCall[]): ProductRouteBlock[] {
  const blocks: ProductRouteBlock[] = [];
  const seenPaths = new Set<string>();

  for (const toolCall of toolCalls) {
    if (!isSuccessfulExternalAction(toolCall)) {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const path = String(metadata.path || "").trim();

    if (!path) {
      continue;
    }

    const dedupeKey = path.toLowerCase();

    if (seenPaths.has(dedupeKey)) {
      continue;
    }

    seenPaths.add(dedupeKey);

    blocks.push({
      path,
      routeKey: routeKeyFromPath(path),
      toolCall,
    });
  }

  return blocks;
}

export function isMultiRouteProductPresentation(toolCalls: ChatToolCall[]): boolean {
  const blocks = collectProductRouteBlocks(toolCalls);

  if (blocks.length < 2) {
    return false;
  }

  const analyserOnly = blocks.every((block) => block.routeKey === "analyser");

  return !analyserOnly;
}

export function isStockFocusedPresentation(toolCalls: ChatToolCall[]): boolean {
  const blocks = collectProductRouteBlocks(toolCalls);

  return blocks.length === 1 && blocks[0]?.routeKey === "stock";
}

export function resolveMultiRouteStackPlan(_toolCalls: ChatToolCall[]): StackPresentationPlan {
  return {
    profileFirst: false,
    highlightsAfterProfile: false,
    attentionLast: false,
    humanizedSections: false,
    presentationProfile: undefined,
    narrativeOrder: ["lead"],
    tableRoleOrder: ["profile", "guide", "inspection", "stock", "structure", "list", "other"],
    tailVisualOrder: [],
  };
}

export type RouteSectionGroup = {
  section: StackSectionChrome;
  segments: AssistantContentSegment[];
};

export function routeKeyFromSectionId(sectionId: string): ProductRouteKey | null {
  const match = /^route-([a-z]+)(?:-|$)/.exec(String(sectionId || "").trim());

  if (!match) {
    return null;
  }

  const key = match[1] as ProductRouteKey;

  return isProductRouteKey(key) ? key : null;
}

export function groupSegmentsByRouteSections(segments: AssistantContentSegment[]): {
  lead: AssistantContentSegment[];
  sections: RouteSectionGroup[];
} {
  const lead: AssistantContentSegment[] = [];
  const sections: RouteSectionGroup[] = [];
  let current: RouteSectionGroup | null = null;

  for (const segment of segments) {
    if (
      segment.kind === "stackSection" &&
      routeKeyFromSectionId(segment.section.id) !== null
    ) {
      if (current) {
        sections.push(current);
      }

      current = {
        section: segment.section,
        segments: [segment],
      };
      continue;
    }

    if (current) {
      current.segments.push(segment);
    } else {
      lead.push(segment);
    }
  }

  if (current) {
    sections.push(current);
  }

  return { lead, sections };
}

function buildRouteSectionChrome(
  routeKey: ProductRouteKey,
  index: number,
  path = "",
): StackSectionChrome {
  const code = productCodeFromPath(path);
  const baseTitle = routeTitle(routeKey);
  const titled = code ? `${baseTitle} — ${code}` : baseTitle;

  return {
    id: `route-${routeKey}${code ? `-${code}` : ""}`,
    title: `${index}. ${titled}`,
    showIn: ROUTE_SHOW_IN[routeKey],
  };
}

function normalizeCompositeHeadingKey(heading: string): string {
  return String(heading || "").trim().toLowerCase();
}

export function splitCompositeProseByHeading(content: string): Map<string, string> {
  const map = new Map<string, string>();
  const trimmed = String(content || "").trim();

  if (!trimmed) {
    return map;
  }

  const parts = trimmed.split(/\n(?=###\s+)/);

  for (const part of parts) {
    const match = part.match(/^###\s+(.+?)\n+([\s\S]*)$/);

    if (!match) {
      continue;
    }

    map.set(normalizeCompositeHeadingKey(match[1]), match[2].trim());
  }

  return map;
}

function stripMarkdownHeading(markdown: string, title?: string): string {
  let body = String(markdown || "").trim();

  if (!body) {
    return "";
  }

  body = body.replace(/^###\s+.+?\n+/m, "").trim();

  if (title) {
    const escaped = title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    body = body.replace(new RegExp(`^\\*\\*${escaped}\\*\\*\\s*\\n+`, "m"), "").trim();
  }

  return body;
}

export function resolveRouteTextDetailMarkdown(toolCall: ChatToolCall | undefined): string {
  if (!toolCall) {
    return "";
  }

  const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;

  const markdown = resolveRenderableTemplateMarkdown(metadata);

  if (markdown) {
    const humanized = metadata.humanizedSummary as { titulo?: string } | undefined;
    const textPresentation = metadata.textPresentation as { title?: string } | undefined;
    const title = String(humanized?.titulo || textPresentation?.title || "").trim();

    return stripMarkdownHeading(markdown, title);
  }

  const detailLines = resolveRenderableHumanizedDetailLines(metadata);

  if (!detailLines.length) {
    return "";
  }

  return [
    "**Detalhamento por filial e armazém**",
    "",
    ...detailLines.map((line) => (line.startsWith("-") ? line : `- ${line}`)),
  ].join("\n");
}

function resolveProseForBlock(
  block: ProductRouteBlock,
  compositeSections: Map<string, string>,
): string {
  const titleKey = normalizeCompositeHeadingKey(
    routeTitle(block.routeKey) || block.routeKey,
  );
  const pathKey = normalizeCompositeHeadingKey(block.path);
  const fromTitle = compositeSections.get(titleKey);
  const fromPath = compositeSections.get(pathKey);

  if (fromTitle) {
    return fromTitle;
  }

  if (fromPath) {
    return fromPath;
  }

  const metadata = (block.toolCall.metadata ?? {}) as Record<string, unknown>;

  const lines = resolveRenderableHumanizedLines(metadata);

  if (lines.length) {
    return lines.join("\n\n");
  }

  return resolveRenderableTemplateMarkdown(metadata);
}

function collectVisualsForToolCall(toolCall: ChatToolCall): AssistantContentSegment[] {
  const segments: AssistantContentSegment[] = [];
  const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;

  const queueTable = (presentation: Extract<ChatPresentation, { type: "table" }>) => {
    segments.push({ kind: "table", presentation });
  };

  const presentation = metadata.presentation;

  if (
    presentation &&
    typeof presentation === "object" &&
    (presentation as ChatPresentation).type === "table"
  ) {
    queueTable(presentation as Extract<ChatPresentation, { type: "table" }>);
  } else if (
    presentation &&
    typeof presentation === "object" &&
    (presentation as ChatPresentation).type === "tree"
  ) {
    segments.push({
      kind: "tree",
      presentation: presentation as Extract<ChatPresentation, { type: "tree" }>,
    });
  } else if (
    presentation &&
    typeof presentation === "object" &&
    (presentation as ChatPresentation).type === "chart"
  ) {
    segments.push({
      kind: "chart",
      presentation: presentation as Extract<ChatPresentation, { type: "chart" }>,
    });
  }

  const bundled = metadata.tablePresentations;

  if (Array.isArray(bundled)) {
    for (const candidate of bundled) {
      if (candidate && typeof candidate === "object" && (candidate as ChatPresentation).type === "table") {
        queueTable(candidate as Extract<ChatPresentation, { type: "table" }>);
      }
    }
  } else {
    for (const key of ["tablePresentation", "profileTablePresentation", "inspectionTablePresentation"]) {
      const slot = metadata[key];

      if (slot && typeof slot === "object" && (slot as ChatPresentation).type === "table") {
        queueTable(slot as Extract<ChatPresentation, { type: "table" }>);
      }
    }
  }

  const chartPresentation = normalizeChartPresentation(metadata.chartPresentation);

  if (chartPresentation) {
    segments.push({
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
    segments.push({
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
    segments.push({
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
    segments.push({
      kind: "dashboard",
      presentation: dashboardPresentation as Extract<ChatPresentation, { type: "dashboard" }>,
    });
  }

  return segments;
}

export function buildMultiRouteStackSegments(
  commentary: string,
  toolCalls: ChatToolCall[],
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): AssistantContentSegment[] | null {
  const blocks = collectProductRouteBlocks(toolCalls);

  if (blocks.length < 2) {
    return null;
  }

  const segments: AssistantContentSegment[] = [];
  const compositeSections = splitCompositeProseByHeading(commentary);
  let sectionIndex = 0;

  const lead = commentary
    .split(/\n(?=###\s+)/)[0]
    ?.replace(/^#\s+.+$/m, "")
    .trim();

  if (lead && !lead.startsWith("###")) {
    for (const segment of parseMarkdownAndCodeSegments(lead)) {
      appendUnique(segments, segment);
    }
  }

  for (const block of blocks) {
    sectionIndex += 1;
    appendUnique(segments, {
      kind: "stackSection",
      section: buildRouteSectionChrome(block.routeKey, sectionIndex, block.path),
    });

    const framing = routeFraming(block.routeKey);

    if (framing) {
      for (const segment of parseMarkdownAndCodeSegments(framing)) {
        appendUnique(segments, segment);
      }
    }

    const prose = resolveProseForBlock(block, compositeSections);

    if (prose) {
      for (const segment of parseMarkdownAndCodeSegments(prose)) {
        appendUnique(segments, segment);
      }
    }

    const routeVisuals = collectVisualsForToolCall(block.toolCall);
    const visualOrder = resolveVisualOrderFromToolCalls([block.toolCall]);
    const ordered = orderVisualSegments(routeVisuals, visualOrder);

    for (const segment of ordered) {
      appendUnique(segments, segment);
    }
  }

  return dedupeTableSegments(segments);
}
