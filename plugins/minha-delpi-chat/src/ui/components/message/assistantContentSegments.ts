import type { ChatToolCall } from "../../../data/api/chatTypes";
import {
  resolveAssistantRenderableMarkdown,
  shouldRenderPresentationHeading,
} from "./assistantProseRendering";
import type { AssistantContentSegment } from "./assistantContentTypes";

export type { AssistantContentSegment } from "./assistantContentTypes";

import {
  isNativeSingleViewSelection,
  resolveAssistantContentLayout,
} from "./assistantContentLayout";
import { withDecisionLayer } from "./assistantContentDecisionLayer";
import {
  getPresentationDecisionFromToolCalls,
  getPresentationPairFromToolCalls,
  getRenderPlanFromToolCalls,
  isExplicitTextSessionMode,
  renderPlanHasOnlyProseSegments,
} from "../chatPresentation";
import {
  hasPresentationMarkerSyntax,
  splitMarkdownWithPresentationMarkers,
} from "../presentation/segmentBuilders/markerSegmentBuilder";
import { buildNativeSingleViewSegments } from "../presentation/segmentBuilders/nativeSingleViewBuilder";
import {
  appendEmbeddedTablesForExplicitText,
  buildStackedSegments,
} from "../presentation/segmentBuilders/stackSegmentBuilder";
import {
  filterRedundantSqlIntroSegments,
  parseMarkdownAndCodeSegments,
} from "../presentation/segmentBuilders/sqlMarkdownNormalizer";
import { collectVisualSegments } from "../presentation/segmentBuilders/visualSegmentCollector";
import { filterSegmentsWithoutHierarchyTableDuplicates } from "../presentationStructureDedup";

export {
  dedupeSqlFencesInMarkdown,
  parseMarkdownAndCodeSegments,
} from "../presentation/segmentBuilders/sqlMarkdownNormalizer";

function finalizePresentationSegments(
  segments: AssistantContentSegment[],
  toolCalls: ChatToolCall[],
): AssistantContentSegment[] {
  return filterSegmentsWithoutHierarchyTableDuplicates(segments, toolCalls);
}

function withPresentationLayer(
  segments: AssistantContentSegment[],
  toolCalls: ChatToolCall[],
): AssistantContentSegment[] {
  return withDecisionLayer(finalizePresentationSegments(segments, toolCalls), toolCalls);
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

    return withDecisionLayer(parseMarkdownAndCodeSegments(markdown), toolCalls);
  }

  const pair = getPresentationPairFromToolCalls(toolCalls);
  const renderPlan = getRenderPlanFromToolCalls(toolCalls);
  const layoutMode =
    String(renderPlan?.layoutMode || "").trim() ||
    resolveAssistantContentLayout(content, toolCalls, pair);
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const selected = String(decision?.selected ?? "").trim().toLowerCase();
  const visuals = collectVisualSegments(toolCalls);
  const rawMarkdown = resolveAssistantRenderableMarkdown(content, toolCalls);
  const nativeSingle = isNativeSingleViewSelection(toolCalls);

  const proseOnlyRenderPlan =
    renderPlan?.version === 1 && renderPlanHasOnlyProseSegments(renderPlan);

  if (
    selected === "text" &&
    proseOnlyRenderPlan &&
    !(nativeSingle.active && nativeSingle.kind && nativeSingle.kind !== "text" && visuals.length)
  ) {
    return withDecisionLayer(parseMarkdownAndCodeSegments(rawMarkdown), toolCalls);
  }

  if (
    layoutMode !== "stack" &&
    selected === "text" &&
    !renderPlan &&
    !(nativeSingle.active && nativeSingle.kind && nativeSingle.kind !== "text" && visuals.length)
  ) {
    return withDecisionLayer(parseMarkdownAndCodeSegments(rawMarkdown), toolCalls);
  }

  const nativeSingleSegments = buildNativeSingleViewSegments(rawMarkdown, toolCalls, visuals);

  if (nativeSingleSegments) {
    return withPresentationLayer(nativeSingleSegments, toolCalls);
  }

  if (layoutMode === "stack") {
    return withPresentationLayer(buildStackedSegments(content, toolCalls, visuals), toolCalls);
  }

  if (hasPresentationMarkerSyntax(rawMarkdown)) {
    return withPresentationLayer(
      splitMarkdownWithPresentationMarkers(rawMarkdown, visuals),
      toolCalls,
    );
  }

  const textSegments = parseMarkdownAndCodeSegments(rawMarkdown);

  if (!visuals.length) {
    return withDecisionLayer(textSegments, toolCalls);
  }

  const proseOnly = textSegments.every((item) => item.kind === "markdown" || item.kind === "code");
  const hasSqlCode = textSegments.some((item) => item.kind === "code");

  if (proseOnly && hasSqlCode) {
    return withDecisionLayer(filterRedundantSqlIntroSegments(textSegments), toolCalls);
  }

  if (textSegments.length && visuals.length) {
    return withPresentationLayer(buildStackedSegments(content, toolCalls, visuals), toolCalls);
  }

  return withPresentationLayer([...textSegments, ...visuals], toolCalls);
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
