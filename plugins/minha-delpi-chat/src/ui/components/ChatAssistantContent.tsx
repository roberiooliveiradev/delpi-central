import { useEffect, useMemo, useState } from "react";

import type { ChatCanvasOpenPayload, ChatToolCall } from "../../data/api/chatTypes";

import { AssistantContentFormatToolbar } from "./AssistantContentFormatToolbar";
import { AssistantContentChrome } from "./AssistantContentChrome";
import {
  shouldShowAllVisualSegments,
  type AssistantVisualKind,
} from "./assistantContentLayout";
import {
  buildAssistantContentSegments,
  isPresentationHeadingTitle,
} from "./assistantContentSegments";
import { renderAssistantContentSegment } from "./assistantContentRegistry";
import {
  filterSegmentsByVisualKind,
  resolveAvailableVisualFormatOptions,
  resolveDefaultVisualKind,
} from "./assistantContentVisualFormats";
import { getChartExplanationFromToolCalls } from "./chartExplain";
import {
  getDataCoverageNoticeFromToolCalls,
  getDepthStateFromToolCalls,
  getPaginationStateFromToolCalls,
  getPresentationInsightFromToolCalls,
  getPresentationRecommendationsFromToolCalls,
  getPresentationTitle,
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
  const defaultVisualKind = useMemo(
    () => resolveDefaultVisualKind(toolCalls, visualFormatOptions),
    [toolCalls, visualFormatOptions],
  );
  const [activeVisualKind, setActiveVisualKind] = useState<AssistantVisualKind | null>(
    defaultVisualKind,
  );

  useEffect(() => {
    setActiveVisualKind(defaultVisualKind);
  }, [defaultVisualKind, toolCalls, segments]);

  const combineAllVisuals = useMemo(
    () => shouldShowAllVisualSegments(toolCalls),
    [toolCalls],
  );

  const visibleSegments = useMemo(() => {
    if (combineAllVisuals || visualFormatOptions.length < 2) {
      return segments;
    }

    return filterSegmentsByVisualKind(segments, activeVisualKind);
  }, [activeVisualKind, combineAllVisuals, segments, visualFormatOptions.length]);

  const title = useMemo(() => getPresentationTitle(content, toolCalls), [content, toolCalls]);
  const dataCoverageNotice = useMemo(
    () => getDataCoverageNoticeFromToolCalls(toolCalls),
    [toolCalls],
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
    () => getPaginationStateFromToolCalls(toolCalls),
    [toolCalls],
  );
  const depthState = useMemo(
    () => getDepthStateFromToolCalls(toolCalls),
    [toolCalls],
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
    isPresentationHeadingTitle(title) &&
    !visibleSegments.some(
      (segment) => segment.kind === "markdown" && segment.markdown.trim() === title,
    );

  const showFormatToolbar =
    !combineAllVisuals && visualFormatOptions.length >= 2 && activeVisualKind !== null;

  return (
    <div className="mdc-assistant-content mdc-rich-presentation mdc-rich-presentation--enter mdc-rich-presentation--commentary">
      {dataCoverageNotice ? (
        <div className="mdc-rich-presentation__coverage-notice" role="status">
          {dataCoverageNotice.message}
        </div>
      ) : null}

      <AssistantContentChrome
        insight={presentationInsight}
        recommendations={presentationRecommendations}
        pagination={paginationState}
        depth={depthState}
        onNavigate={onDrillDown}
      />

      {showTitle ? <h3 className="mdc-rich-presentation__heading">{title}</h3> : null}

      {showFormatToolbar ? (
        <AssistantContentFormatToolbar
          options={visualFormatOptions}
          activeKind={activeVisualKind}
          onChange={setActiveVisualKind}
        />
      ) : null}

      <div className="mdc-assistant-content__segments">
        {visibleSegments.map((segment, index) =>
          renderAssistantContentSegment(segment, index, {
            onDrillDown,
            onOpenCanvas,
            chartExplanation,
            showChartExplanation: chartExplanationOpen,
            onChartExplanationChange: setChartExplanationOpen,
          }),
        )}
      </div>
    </div>
  );
}
