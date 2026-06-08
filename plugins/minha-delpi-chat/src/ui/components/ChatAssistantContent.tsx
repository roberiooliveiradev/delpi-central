import { useEffect, useMemo, useState } from "react";

import type { ChatCanvasOpenPayload, ChatToolCall } from "../../data/api/chatTypes";

import { AssistantContentFormatToolbar } from "./AssistantContentFormatToolbar";
import { AssistantContentChrome } from "./AssistantContentChrome";
import type { ContentFormatKind } from "./assistantContentLayout";
import { buildAssistantContentSegments } from "./assistantContentSegments";
import {
  resolveAssistantPresentationTitle,
  shouldRenderPresentationHeading,
} from "./assistantProseRendering";
import { renderAssistantContentSegment } from "./assistantContentRegistry";
import {
  filterSegmentsByVisualKind,
  resolveAvailableVisualFormatOptions,
  resolveInitialToolbarKind,
  shouldShowCompleteStackView,
  shouldUsePerSectionFormatToolbar,
} from "./assistantContentVisualFormats";
import { renumberStackSectionTitles } from "./presentationStackSections";
import { AssistantContentRouteSection } from "./AssistantContentRouteSection";
import {
  collectProductRouteBlocks,
  groupSegmentsByRouteSections,
} from "./presentationMultiRoute";
import { getTextMarkdownFromToolCalls } from "./chatPresentation";
import {
  getStackPresentationPlanFromToolCalls,
  planUsesHumanizedSections,
} from "./presentationStackPlan";
import { getChartExplanationFromToolCalls } from "./chartExplain";
import {
  getDataCoverageNoticeFromToolCalls,
  getDepthStateFromToolCalls,
  getPaginationStateFromToolCalls,
  getPresentationInsightFromToolCalls,
  getPresentationRecommendationsFromToolCalls,
} from "./chatPresentation";

import "./ChatAssistantContent.css";
import "./rich-presentation-shared.css";

type ChatAssistantContentProps = {
  content: string;
  toolCalls?: ChatToolCall[];
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
  requestChartExplanation?: boolean;
  onChartExplanationHandled?: () => void;
};

export function ChatAssistantContent({
  content,
  toolCalls = [],
  onDrillDown,
  onOpenCanvas,
  requestChartExplanation = false,
  onChartExplanationHandled,
}: ChatAssistantContentProps) {
  const segments = useMemo(
    () => buildAssistantContentSegments(content, toolCalls),
    [content, toolCalls],
  );
  const visualFormatOptions = useMemo(
    () => resolveAvailableVisualFormatOptions(segments, toolCalls),
    [segments, toolCalls],
  );
  const initialVisualKind = useMemo(
    () => resolveInitialToolbarKind(toolCalls, visualFormatOptions),
    [toolCalls, visualFormatOptions],
  );
  const [activeVisualKind, setActiveVisualKind] = useState<ContentFormatKind | null>(
    initialVisualKind,
  );

  useEffect(() => {
    setActiveVisualKind(initialVisualKind);
  }, [initialVisualKind, toolCalls, segments]);

  const perSectionToolbar = useMemo(
    () => shouldUsePerSectionFormatToolbar(toolCalls),
    [toolCalls],
  );
  const routePresentation = useMemo(
    () => (perSectionToolbar ? groupSegmentsByRouteSections(segments) : null),
    [perSectionToolbar, segments],
  );
  const routeToolCallBySectionId = useMemo(() => {
    const map = new Map<string, (typeof toolCalls)[number]>();

    for (const block of collectProductRouteBlocks(toolCalls)) {
      const code = block.path.match(/\/products\/([^/]+)/i)?.[1]?.trim();
      const sectionId = code
        ? `route-${block.routeKey}-${code}`
        : `route-${block.routeKey}`;

      map.set(sectionId, block.toolCall);
    }

    return map;
  }, [toolCalls]);

  const visibleSegments = useMemo(() => {
    if (perSectionToolbar) {
      return renumberStackSectionTitles(segments, null);
    }

    if (visualFormatOptions.length < 2) {
      return renumberStackSectionTitles(segments, null);
    }

    return filterSegmentsByVisualKind(segments, activeVisualKind);
  }, [activeVisualKind, perSectionToolbar, segments, visualFormatOptions.length]);

  const title = useMemo(
    () => resolveAssistantPresentationTitle(content, toolCalls),
    [content, toolCalls],
  );
  const dataCoverageNotice = useMemo(
    () =>
      perSectionToolbar ? null : getDataCoverageNoticeFromToolCalls(toolCalls),
    [perSectionToolbar, toolCalls],
  );
  const presentationInsight = useMemo(
    () => getPresentationInsightFromToolCalls(toolCalls),
    [toolCalls],
  );
  const presentationRecommendations = useMemo(
    () => getPresentationRecommendationsFromToolCalls(toolCalls),
    [toolCalls],
  );
  const paginationState = useMemo(
    () => (perSectionToolbar ? null : getPaginationStateFromToolCalls(toolCalls)),
    [perSectionToolbar, toolCalls],
  );
  const depthState = useMemo(
    () => (perSectionToolbar ? null : getDepthStateFromToolCalls(toolCalls)),
    [perSectionToolbar, toolCalls],
  );
  const chartExplanation = useMemo(
    () => getChartExplanationFromToolCalls(toolCalls),
    [toolCalls],
  );
  const [chartExplanationOpen, setChartExplanationOpen] = useState(false);

  useEffect(() => {
    if (!requestChartExplanation) {
      return;
    }

    if (activeVisualKind === "chart" || visualFormatOptions.some((item) => item.kind === "chart")) {
      setActiveVisualKind("chart");
      setChartExplanationOpen(true);
    }

    onChartExplanationHandled?.();
  }, [
    activeVisualKind,
    onChartExplanationHandled,
    requestChartExplanation,
    visualFormatOptions,
  ]);

  if (!segments.length && !title) {
    return null;
  }

  const showTitle =
    !perSectionToolbar &&
    shouldRenderPresentationHeading(title) &&
    !visibleSegments.some(
      (segment) => segment.kind === "markdown" && segment.markdown.trim() === title,
    );

  const stackPlan = useMemo(
    () => getStackPresentationPlanFromToolCalls(toolCalls),
    [toolCalls],
  );
  const showCompleteStackView = shouldShowCompleteStackView(toolCalls);
  const showFormatToolbar = !perSectionToolbar && visualFormatOptions.length >= 2;
  const segmentRenderContext = {
    onDrillDown,
    onOpenCanvas,
    chartExplanation,
    showChartExplanation: chartExplanationOpen,
    onChartExplanationChange: setChartExplanationOpen,
  };
  const narrativeMarkdown = useMemo(
    () => getTextMarkdownFromToolCalls(toolCalls),
    [toolCalls],
  );
  const suppressPresentationChrome =
    showCompleteStackView &&
    Boolean(narrativeMarkdown.trim()) &&
    (planUsesHumanizedSections(stackPlan) ||
      segments.some(
        (segment) =>
          segment.kind === "table" ||
          segment.kind === "tree" ||
          segment.kind === "stackSection",
      ));

  return (
    <div className="mdc-assistant-content mdc-rich-presentation mdc-rich-presentation--enter mdc-rich-presentation--commentary">
      {dataCoverageNotice ? (
        <div className="mdc-rich-presentation__coverage-notice" role="status">
          {dataCoverageNotice.message}
        </div>
      ) : null}

      {!suppressPresentationChrome ? (
        <AssistantContentChrome
          insight={presentationInsight}
          recommendations={presentationRecommendations}
          pagination={paginationState}
          depth={depthState}
          onNavigate={onDrillDown}
        />
      ) : null}

      {showTitle ? <h3 className="mdc-rich-presentation__heading">{title}</h3> : null}

      {showFormatToolbar ? (
        <AssistantContentFormatToolbar
          options={visualFormatOptions}
          activeKind={activeVisualKind}
          showCompleteOption={showCompleteStackView}
          onChange={setActiveVisualKind}
        />
      ) : null}

      <div className="mdc-assistant-content__segments">
        {routePresentation ? (
          <>
            {routePresentation.lead.map((segment, index) =>
              renderAssistantContentSegment(segment, index, segmentRenderContext),
            )}
            {routePresentation.sections.map((group) => (
              <AssistantContentRouteSection
                key={group.section.id}
                group={group}
                toolCall={routeToolCallBySectionId.get(group.section.id)}
                renderContext={segmentRenderContext}
                onDrillDown={onDrillDown}
              />
            ))}
          </>
        ) : (
          visibleSegments.map((segment, index) =>
            renderAssistantContentSegment(segment, index, segmentRenderContext),
          )
        )}
      </div>
    </div>
  );
}
