import type { ChatToolCall } from "../../data/api/chatTypes";
import type { AssistantContentSegment } from "./message/assistantContentTypes";
import {
  getPresentationDecisionFromToolCalls,
  getTextMarkdownFromToolCalls,
} from "./chatPresentation";
import {
  resolveRenderPlanForExecution,
  resolveVisualSegmentsForRenderSpec,
} from "./renderPlanSegmentBuilder";
import {
  isNativeSingleViewSelection,
  orderVisualSegments,
  segmentVisualKind,
} from "./message/assistantContentLayout";
import { parseMarkdownAndCodeSegments } from "./sqlMarkdownNormalizer";

export type NativeSingleViewSelection = ReturnType<typeof isNativeSingleViewSelection>;

export function buildNativeSingleViewSegments(
  rawMarkdown: string,
  toolCalls: ChatToolCall[],
  visuals: AssistantContentSegment[],
): AssistantContentSegment[] | null {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const selected = String(decision?.selected ?? "").trim().toLowerCase();
  const useFullText = !selected || selected === "text";
  const caption = useFullText
    ? rawMarkdown.trim() || getTextMarkdownFromToolCalls(toolCalls) || ""
    : rawMarkdown.trim();
  const renderPlan = resolveRenderPlanForExecution(toolCalls, caption, {
    hasTableVisuals: visuals.some((segment) => segment.kind === "table"),
    visualKinds: new Set(
      visuals.map((segment) => String(segment.kind || "").trim().toLowerCase()).filter(Boolean),
    ),
  });

  if (
    renderPlan?.version === 1 &&
    renderPlan.layoutMode !== "stack" &&
    Array.isArray(renderPlan.segments) &&
    renderPlan.segments.length
  ) {
    const segments: AssistantContentSegment[] = [];

    if (caption && useFullText) {
      segments.push(...parseMarkdownAndCodeSegments(caption));
    }

    for (const spec of renderPlan.segments) {
      segments.push(...resolveVisualSegmentsForRenderSpec(spec, visuals, toolCalls));
    }

    return segments.length ? segments : null;
  }

  const nativeSingle = isNativeSingleViewSelection(toolCalls);

  if (
    !nativeSingle.active ||
    !nativeSingle.kind ||
    nativeSingle.kind === "text" ||
    !visuals.length
  ) {
    return null;
  }

  const legacyCaption = rawMarkdown.trim();
  const segments: AssistantContentSegment[] = [];

  if (legacyCaption) {
    segments.push(...parseMarkdownAndCodeSegments(legacyCaption));
  }

  const orderedVisuals = orderVisualSegments(visuals, [nativeSingle.kind]);

  for (const visual of orderedVisuals) {
    if (segmentVisualKind(visual) === nativeSingle.kind) {
      segments.push(visual);
    }
  }

  return segments.length ? segments : orderedVisuals;
}
