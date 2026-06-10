import type { ChatToolCall } from "../../data/api/chatTypes";

import {
  type AssistantVisualKind,
  type ContentFormatKind,
  resolveStackLayoutOrderFromToolCalls,
  segmentVisualKind,
} from "./assistantContentLayout";
import type { AssistantContentSegment } from "./assistantContentTypes";
import {
  isStackSectionVisible,
  renumberStackSectionTitles,
} from "./presentationStackSections";
import { isHierarchyDuplicateTable } from "./presentationStructureDedup";
import { expandTreeSegmentsToBlockTables } from "./treePresentationUtils";
import {
  getPresentationDecisionFromToolCalls,
  getPreferredFormatFromToolCalls,
  hasExplicitPresentationFormatChoice,
  mapPresentationDecisionToViewFormat,
  type ViewFormat,
} from "./chatPresentation";
import {
  getPresentationDecisionFromToolCall,
  mapViewTokenToContentKind,
  mapViewTokenToVisualKind,
  resolveInitialContentKindFromDecision,
  resolveVisualKindsFromDecision,
} from "./presentationMetadataPolicy";
import {
  isMultiRouteProductPresentation,
  ROUTE_VISUAL_ORDER,
  type ProductRouteKey,
} from "./presentationMultiRoute";

export type VisualFormatOption = {
  kind: ContentFormatKind;
  label: string;
};

const FORMAT_LABELS: Record<ContentFormatKind, string> = {
  text: "Texto",
  table: "Tabela",
  tree: "Árvore",
  chart: "Gráfico",
  kpi: "KPI",
  dashboard: "Painel",
};

function mapViewFormatToContentKind(format: ViewFormat | null): ContentFormatKind | null {
  if (!format) {
    return null;
  }

  if (format === "text") {
    return "text";
  }

  return format;
}

function hasTextFormatContent(segments: AssistantContentSegment[]): boolean {
  return segments.some(
    (segment) => segment.kind === "markdown" || segment.kind === "code",
  );
}

function hasFormatContent(
  segments: AssistantContentSegment[],
  kind: ContentFormatKind,
): boolean {
  if (kind === "text") {
    return hasTextFormatContent(segments);
  }

  return collectPresentVisualKinds(segments).has(kind);
}

export function collectPresentVisualKinds(
  segments: AssistantContentSegment[],
): Set<AssistantVisualKind> {
  const kinds = new Set<AssistantVisualKind>();

  for (const segment of segments) {
    const kind = segmentVisualKind(segment);

    if (
      segment.kind === "table" &&
      isHierarchyDuplicateTable(segment.presentation)
    ) {
      continue;
    }

    if (kind) {
      kinds.add(kind);
    }
  }

  return kinds;
}

function resolveRouteVisualOrder(
  routeKey: ProductRouteKey,
  toolCall?: ChatToolCall,
): AssistantVisualKind[] {
  const decision = getPresentationDecisionFromToolCall(toolCall);
  const fromDecision = resolveVisualKindsFromDecision(decision);

  if (fromDecision?.length) {
    return fromDecision;
  }

  return ROUTE_VISUAL_ORDER[routeKey];
}

export function resolveRouteSectionFormatOptions(
  sectionSegments: AssistantContentSegment[],
  routeKey: ProductRouteKey,
  toolCall?: ChatToolCall,
): VisualFormatOption[] {
  const orderedKinds: ContentFormatKind[] = [];

  if (hasTextFormatContent(sectionSegments)) {
    orderedKinds.push("text");
  }

  for (const visualKind of resolveRouteVisualOrder(routeKey, toolCall)) {
    if (hasFormatContent(sectionSegments, visualKind) && !orderedKinds.includes(visualKind)) {
      orderedKinds.push(visualKind);
    }
  }

  for (const kind of collectPresentVisualKinds(sectionSegments)) {
    if (!orderedKinds.includes(kind)) {
      orderedKinds.push(kind);
    }
  }

  return orderedKinds.map((kind) => ({
    kind,
    label: FORMAT_LABELS[kind],
  }));
}

export function resolveInitialToolbarKindForRoute(
  _routeKey: ProductRouteKey,
  options: VisualFormatOption[],
  toolCall?: ChatToolCall,
): ContentFormatKind | null {
  if (options.length < 2) {
    return options[0]?.kind ?? null;
  }

  const available = options.map((item) => item.kind);
  const decision = getPresentationDecisionFromToolCall(toolCall);

  return resolveInitialContentKindFromDecision(decision, available);
}

export function shouldUsePerSectionFormatToolbar(toolCalls: ChatToolCall[]): boolean {
  return isMultiRouteProductPresentation(toolCalls);
}

export function resolveAvailableVisualFormatOptions(
  segments: AssistantContentSegment[],
  toolCalls: ChatToolCall[] = [],
): VisualFormatOption[] {
  if (shouldUsePerSectionFormatToolbar(toolCalls)) {
    return [];
  }

  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const order = resolveStackLayoutOrderFromToolCalls(toolCalls);
  const candidates = new Set<ContentFormatKind>();

  for (const slot of order) {
    if (hasFormatContent(segments, slot)) {
      candidates.add(slot);
    }
  }

  if (decision?.availableViews) {
    for (const view of decision.availableViews) {
      const mapped = mapViewTokenToContentKind(String(view));

      if (mapped && hasFormatContent(segments, mapped)) {
        candidates.add(mapped);
      }
    }
  }

  const orderedKinds: ContentFormatKind[] = [];

  for (const slot of order) {
    if (candidates.has(slot) && !orderedKinds.includes(slot)) {
      orderedKinds.push(slot);
    }
  }

  for (const kind of candidates) {
    if (!orderedKinds.includes(kind)) {
      orderedKinds.push(kind);
    }
  }

  return orderedKinds.map((kind) => ({
    kind,
    label: FORMAT_LABELS[kind],
  }));
}

export function resolveDefaultVisualKind(
  toolCalls: ChatToolCall[],
  options: VisualFormatOption[],
): ContentFormatKind | null {
  if (!options.length) {
    return null;
  }

  const available = options.map((item) => item.kind);
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const fromDecision = mapPresentationDecisionToViewFormat(decision?.selected);

  if (fromDecision) {
    const mapped = mapViewFormatToContentKind(fromDecision);

    if (mapped && available.includes(mapped)) {
      return mapped;
    }
  }

  const preferred = getPreferredFormatFromToolCalls(toolCalls);

  if (preferred) {
    const mapped = mapViewFormatToContentKind(preferred);

    if (mapped && available.includes(mapped)) {
      return mapped;
    }
  }

  return resolveInitialContentKindFromDecision(decision, available);
}

function isTextModeInterleavedSegment(segment: AssistantContentSegment): boolean {
  if (segment.kind === "markdown" || segment.kind === "code") {
    return true;
  }

  if (segment.kind === "table" && isHierarchyDuplicateTable(segment.presentation)) {
    return false;
  }

  return segmentVisualKind(segment) !== null;
}

export function filterSegmentsByVisualKind(
  segments: AssistantContentSegment[],
  activeKind: ContentFormatKind | null,
): AssistantContentSegment[] {
  const filtered = !activeKind
    ? segments
    : segments.filter((segment) => {
        if (segment.kind === "stackSection") {
          return isStackSectionVisible(segment.section, activeKind);
        }

        if (activeKind === "text") {
          return isTextModeInterleavedSegment(segment);
        }

        if (segment.kind === "markdown" || segment.kind === "code") {
          return false;
        }

        if (segment.kind === "table" && isHierarchyDuplicateTable(segment.presentation)) {
          return activeKind === "table";
        }

        if (segment.kind === "tree" && activeKind === "table") {
          return true;
        }

        const kind = segmentVisualKind(segment);

        return kind === activeKind;
      });

  const normalized =
    activeKind === "table" ? expandTreeSegmentsToBlockTables(filtered) : filtered;

  return renumberStackSectionTitles(normalized, activeKind);
}

export function shouldShowCompleteStackView(toolCalls: ChatToolCall[]): boolean {
  return getPresentationDecisionFromToolCalls(toolCalls)?.layoutMode === "stack";
}

export function resolveInitialToolbarKind(
  toolCalls: ChatToolCall[],
  options: VisualFormatOption[],
): ContentFormatKind | null {
  if (options.length < 2) {
    return resolveDefaultVisualKind(toolCalls, options);
  }

  if (isMultiRouteProductPresentation(toolCalls)) {
    return null;
  }

  if (shouldShowCompleteStackView(toolCalls)) {
    if (!hasExplicitPresentationFormatChoice(toolCalls)) {
      return null;
    }

    const decision = getPresentationDecisionFromToolCalls(toolCalls);
    const available = options.map((item) => item.kind);

    return resolveInitialContentKindFromDecision(decision, available);
  }

  return resolveDefaultVisualKind(toolCalls, options);
}

export { mapViewTokenToVisualKind, mapViewTokenToContentKind };
