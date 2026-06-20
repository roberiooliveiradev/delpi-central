import { useMemo } from "react";

import type { ChatToolCall } from "../../../data/api/chatTypes";

import { buildAssistantContentSegments } from "./assistantContentSegments";
import {
  resolveAvailableVisualFormatOptions,
  resolveInitialToolbarKind,
  resolveVisibleAssistantSegments,
  shouldUsePerSectionFormatToolbar,
} from "./assistantContentVisualFormats";
import {
  collectProductRouteBlocks,
  groupSegmentsByRouteSections,
} from "../presentation/pipeline/presentationMultiRoute";
import { isExplicitTextSessionMode } from "../chatPresentation";

type UseAssistantContentSegmentsArgs = {
  content: string;
  toolCalls: ChatToolCall[];
};

export function useAssistantContentSegments({
  content,
  toolCalls,
}: UseAssistantContentSegmentsArgs) {
  const segments = useMemo(
    () => buildAssistantContentSegments(content, toolCalls),
    [content, toolCalls],
  );
  const visualFormatOptions = useMemo(
    () => resolveAvailableVisualFormatOptions(segments, toolCalls),
    [segments, toolCalls],
  );
  const resolvedVisualKind = useMemo(
    () => resolveInitialToolbarKind(toolCalls, visualFormatOptions),
    [toolCalls, visualFormatOptions],
  );
  const perSectionToolbar = useMemo(
    () => shouldUsePerSectionFormatToolbar(toolCalls),
    [toolCalls],
  );
  const routePresentation = useMemo(
    () => (perSectionToolbar ? groupSegmentsByRouteSections(segments) : null),
    [perSectionToolbar, segments],
  );
  const routeToolCallBySectionId = useMemo(() => {
    const map = new Map<string, ChatToolCall>();

    for (const block of collectProductRouteBlocks(toolCalls)) {
      const code = block.path.match(/\/products\/([^/]+)/i)?.[1]?.trim();
      const sectionId = code
        ? `route-${block.routeKey}-${code}`
        : `route-${block.routeKey}`;

      map.set(sectionId, block.toolCall);
    }

    return map;
  }, [toolCalls]);
  const explicitTextSession = isExplicitTextSessionMode(toolCalls);
  const visibleSegments = useMemo(
    () =>
      resolveVisibleAssistantSegments(segments, toolCalls, {
        perSectionToolbar,
        resolvedVisualKind,
        visualFormatOptionCount: visualFormatOptions.length,
        explicitTextSession,
      }),
    [
      explicitTextSession,
      perSectionToolbar,
      resolvedVisualKind,
      segments,
      toolCalls,
      visualFormatOptions.length,
    ],
  );

  return {
    segments,
    visualFormatOptions,
    resolvedVisualKind,
    perSectionToolbar,
    routePresentation,
    routeToolCallBySectionId,
    visibleSegments,
  };
}
