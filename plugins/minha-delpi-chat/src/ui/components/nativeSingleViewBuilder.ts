import type { ChatToolCall } from "../../data/api/chatTypes";
import type { AssistantContentSegment } from "./assistantContentTypes";
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
