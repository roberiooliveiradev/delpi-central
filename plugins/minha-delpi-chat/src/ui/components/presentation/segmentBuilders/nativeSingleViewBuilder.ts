import type { ChatToolCall } from "../../../../data/api/chatTypes";
import type { AssistantContentSegment } from "../../message/assistantContentTypes";
import {
  getPresentationDecisionFromToolCalls,
  getTextMarkdownFromToolCalls,
} from "../../chatPresentation";
import {
  buildSegmentsFromRenderPlan,
  resolveRenderPlanForExecution,
  resolveVisualSegmentsForRenderSpec,
} from "./renderPlanSegmentBuilder";
import {
  isNativeSingleViewSelection,
  orderVisualSegments,
  segmentVisualKind,
} from "../../message/assistantContentLayout";
import { parseMarkdownAndCodeSegments } from "./sqlMarkdownNormalizer";
import { appendVisualSegment } from "./segmentDedupe";

export type NativeSingleViewSelection = ReturnType<typeof isNativeSingleViewSelection>;

function renderPlanHasMarkdownLead(
  renderPlan: { segments?: Array<{ kind?: string; slot?: string }> } | null,
): boolean {
  if (!renderPlan?.segments?.length) {
    return false;
  }

  return renderPlan.segments.some(
    (segment) =>
      String(segment.kind || "")
        .trim()
        .toLowerCase() === "markdown" &&
      String(segment.slot || "")
        .trim()
        .toLowerCase() === "lead",
  );
}

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
  const renderPlan = resolveRenderPlanForExecution(toolCalls);

  if (
    renderPlan?.version === 1 &&
    renderPlan.layoutMode !== "stack" &&
    Array.isArray(renderPlan.segments) &&
    renderPlan.segments.length
  ) {
    // Lead markdown (assistantMessage) deve aparecer mesmo com selected=table/kpi/chart.
    // O executor canônico honra o renderPlan; o atalho só-visual ignorava kind=markdown.
    if (renderPlanHasMarkdownLead(renderPlan)) {
      const commentary = String(rawMarkdown || caption || "").trim();
      const fromPlan = buildSegmentsFromRenderPlan(
        commentary,
        visuals,
        parseMarkdownAndCodeSegments,
        appendVisualSegment,
        toolCalls,
      );

      if (fromPlan?.length) {
        return fromPlan;
      }
    }

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
