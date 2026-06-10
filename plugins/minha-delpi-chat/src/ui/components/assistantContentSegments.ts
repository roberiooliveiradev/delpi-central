import type { ChatToolCall } from "../../data/api/chatTypes";
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
  isExplicitTextSessionMode,
} from "./chatPresentation";
import {
  hasPresentationMarkerSyntax,
  splitMarkdownWithPresentationMarkers,
} from "./markerSegmentBuilder";
import { buildNativeSingleViewSegments } from "./nativeSingleViewBuilder";
import {
  appendEmbeddedTablesForExplicitText,
  buildStackedSegments,
} from "./stackSegmentBuilder";
import {
  filterRedundantSqlIntroSegments,
  parseMarkdownAndCodeSegments,
} from "./sqlMarkdownNormalizer";
import { collectVisualSegments } from "./visualSegmentCollector";

export {
  dedupeSqlFencesInMarkdown,
  parseMarkdownAndCodeSegments,
} from "./sqlMarkdownNormalizer";

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
    return withDecisionLayer(parseMarkdownAndCodeSegments(rawMarkdown), toolCalls);
  }

  const nativeSingleSegments = buildNativeSingleViewSegments(rawMarkdown, toolCalls, visuals);

  if (nativeSingleSegments) {
    return withDecisionLayer(nativeSingleSegments, toolCalls);
  }

  if (layoutMode === "stack") {
    return withDecisionLayer(buildStackedSegments(content, toolCalls, visuals), toolCalls);
  }

  if (hasPresentationMarkerSyntax(rawMarkdown)) {
    return withDecisionLayer(
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
    return withDecisionLayer(buildStackedSegments(content, toolCalls, visuals), toolCalls);
  }

  return withDecisionLayer([...textSegments, ...visuals], toolCalls);
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
