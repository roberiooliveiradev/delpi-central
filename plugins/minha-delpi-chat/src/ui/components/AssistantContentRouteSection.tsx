import { useMemo } from "react";

import {
  filterSegmentsByVisualKind,
  resolveInitialToolbarKindForRoute,
  resolveRouteSectionFormatOptions,
  type VisualFormatOption,
} from "./assistantContentVisualFormats";
import type { ContentFormatKind } from "./assistantContentLayout";
import {
  renderAssistantContentSegment,
  type AssistantSegmentRenderContext,
} from "./assistantContentRegistry";
import { parseMarkdownAndCodeSegments } from "./assistantContentSegments";
import type { ChatToolCall } from "../../data/api/chatTypes";
import { AssistantContentRouteCoverage } from "./AssistantContentRouteCoverage";
import {
  getDepthStateFromToolCall,
  getPaginationStateFromToolCall,
} from "./chatPresentation";
import { resolveHumanizedCoverageNoticeFromToolCall } from "./humanizedCoverageNotice";
import {
  resolveRouteTextDetailMarkdown,
  routeKeyFromSectionId,
  type RouteSectionGroup,
} from "./presentationMultiRoute";

type AssistantContentRouteSectionProps = {
  group: RouteSectionGroup;
  toolCall?: ChatToolCall;
  renderContext: AssistantSegmentRenderContext;
  onDrillDown?: (query: string) => void;
};

export function AssistantContentRouteSection({
  group,
  toolCall,
  renderContext,
  onDrillDown,
}: AssistantContentRouteSectionProps) {
  const routeKey = routeKeyFromSectionId(group.section.id);
  const sectionSegments = group.segments;

  const visualFormatOptions = useMemo((): VisualFormatOption[] => {
    if (!routeKey) {
      return [];
    }

    return resolveRouteSectionFormatOptions(sectionSegments, routeKey, toolCall);
  }, [routeKey, sectionSegments, toolCall]);

  const resolvedVisualKind = useMemo((): ContentFormatKind | null => {
    if (!routeKey) {
      return null;
    }

    return resolveInitialToolbarKindForRoute(routeKey, visualFormatOptions, toolCall);
  }, [routeKey, toolCall, visualFormatOptions]);

  const { headerSegments, bodySegments } = useMemo(() => {
    const header: typeof sectionSegments = [];
    const body: typeof sectionSegments = [];

    for (const segment of sectionSegments) {
      if (segment.kind === "stackSection") {
        header.push(segment);
      } else {
        body.push(segment);
      }
    }

    return { headerSegments: header, bodySegments: body };
  }, [sectionSegments]);

  const textDetailMarkdown = useMemo(
    () => resolveRouteTextDetailMarkdown(toolCall),
    [toolCall],
  );

  const visibleBodySegments = useMemo(() => {
    if (resolvedVisualKind === "text" && textDetailMarkdown.trim()) {
      return parseMarkdownAndCodeSegments(textDetailMarkdown);
    }

    if (visualFormatOptions.length < 2) {
      return bodySegments;
    }

    return filterSegmentsByVisualKind(bodySegments, resolvedVisualKind);
  }, [
    resolvedVisualKind,
    bodySegments,
    textDetailMarkdown,
    visualFormatOptions.length,
  ]);
  const dataCoverageNotice = useMemo(
    () => resolveHumanizedCoverageNoticeFromToolCall(toolCall),
    [toolCall],
  );
  const paginationState = useMemo(
    () => getPaginationStateFromToolCall(toolCall),
    [toolCall],
  );
  const depthState = useMemo(() => getDepthStateFromToolCall(toolCall), [toolCall]);

  return (
    <div className="mdc-assistant-content__route-section">
      {headerSegments.map((segment, index) =>
        renderAssistantContentSegment(segment, index, renderContext),
      )}
      {dataCoverageNotice ? (
        <AssistantContentRouteCoverage
          message={dataCoverageNotice.message}
          pagination={paginationState}
          depth={depthState}
          onNavigate={onDrillDown}
        />
      ) : null}
      {visibleBodySegments.map((segment, index) =>
        renderAssistantContentSegment(
          segment,
          headerSegments.length + index,
          renderContext,
        ),
      )}
    </div>
  );
}
