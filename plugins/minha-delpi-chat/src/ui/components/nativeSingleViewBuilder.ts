import type { ChatToolCall } from "../../data/api/chatTypes";
import type { AssistantContentSegment } from "./assistantContentTypes";
import {
  getRenderPlanFromToolCalls,
  getTextMarkdownFromToolCalls,
} from "./chatPresentation";
import {
  isNativeSingleViewSelection,
  orderVisualSegments,
  segmentVisualKind,
} from "./assistantContentLayout";
import { parseMarkdownAndCodeSegments } from "./sqlMarkdownNormalizer";

export type NativeSingleViewSelection = ReturnType<typeof isNativeSingleViewSelection>;

export function buildNativeSingleViewSegments(
  rawMarkdown: string,
  toolCalls: ChatToolCall[],
  visuals: AssistantContentSegment[],
): AssistantContentSegment[] | null {
  const renderPlan = getRenderPlanFromToolCalls(toolCalls);

  if (
    renderPlan?.version === 1 &&
    renderPlan.layoutMode !== "stack" &&
    Array.isArray(renderPlan.segments) &&
    renderPlan.segments.length
  ) {
    const segments: AssistantContentSegment[] = [];
    const caption = rawMarkdown.trim() || getTextMarkdownFromToolCalls(toolCalls) || "";

    if (caption) {
      segments.push(...parseMarkdownAndCodeSegments(caption));
    }

    for (const spec of renderPlan.segments) {
      const kind = String(spec.kind || "").trim().toLowerCase();

      if (kind === "decision" || kind === "markdown") {
        continue;
      }

      const match = visuals.find((visual) => visual.kind === kind);

      if (match) {
        segments.push(match);
      }
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
