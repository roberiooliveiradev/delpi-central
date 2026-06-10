import { useEffect, useMemo, useState } from "react";

import {
  filterSegmentsByVisualKind,
  resolveInitialToolbarKindForRoute,
  resolveRouteSectionFormatOptions,
  type VisualFormatOption,
} from "./assistantContentVisualFormats";
import type { ContentFormatKind } from "./assistantContentLayout";
import { AssistantContentFormatToolbar } from "./AssistantContentFormatToolbar";
import {
  renderAssistantContentSegment,
  type AssistantSegmentRenderContext,
} from "./assistantContentRegistry";
import { parseMarkdownAndCodeSegments } from "./assistantContentSegments";
import type { ChatToolCall } from "../../data/api/chatTypes";
import { AssistantContentRouteCoverage } from "./AssistantContentRouteCoverage";
import {
  getDataCoverageNoticeFromToolCall,
  getDepthStateFromToolCall,
  getPaginationStateFromToolCall,
} from "./chatPresentation";
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

  const initialVisualKind = useMemo((): ContentFormatKind | null => {
    if (!routeKey) {
      return null;
    }

    return resolveInitialToolbarKindForRoute(routeKey, visualFormatOptions, toolCall);
  }, [routeKey, toolCall, visualFormatOptions]);

  const [activeVisualKind, setActiveVisualKind] = useState<ContentFormatKind | null>(
    initialVisualKind,
  );

  useEffect(() => {
    setActiveVisualKind(initialVisualKind);
  }, [group.section.id, initialVisualKind]);

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
    let body =
      visualFormatOptions.length < 2
        ? bodySegments
        : filterSegmentsByVisualKind(bodySegments, activeVisualKind);

    if (activeVisualKind === "text" && textDetailMarkdown) {
      body = [
        ...body,
        ...parseMarkdownAndCodeSegments(textDetailMarkdown),
      ];
    }

    return body;
  }, [
    activeVisualKind,
    bodySegments,
    textDetailMarkdown,
    visualFormatOptions.length,
  ]);

  const showFormatToolbar = visualFormatOptions.length >= 2;
  const dataCoverageNotice = useMemo(
    () => getDataCoverageNoticeFromToolCall(toolCall),
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
      {showFormatToolbar ? (
        <AssistantContentFormatToolbar
          options={visualFormatOptions}
          activeKind={activeVisualKind}
          showCompleteOption
          onChange={setActiveVisualKind}
        />
      ) : null}
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
