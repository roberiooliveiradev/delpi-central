import { useEffect, useMemo, useState } from "react";

import type { ChatCanvasOpenPayload, ChatToolCall } from "../../data/api/chatTypes";

import { AssistantContentChrome } from "./AssistantContentChrome";
import {
  resolveAssistantPresentationTitle,
  shouldRenderPresentationHeading,
  stripLeadingMarkdownTitleSafely,
} from "./assistantProseRendering";
import { renderAssistantContentSegment } from "./assistantContentRegistry";
import {
  shouldShowCompleteStackView,
} from "./assistantContentVisualFormats";
import { AssistantContentRouteSection } from "./AssistantContentRouteSection";
import {
  getTextMarkdownFromToolCalls,
} from "./chatPresentation";
import {
  getStackPresentationPlanFromToolCalls,
  planUsesHumanizedSections,
} from "./presentationStackPlan";
import { useAssistantContentChrome } from "./useAssistantContentChrome";
import { useAssistantContentSegments } from "./useAssistantContentSegments";

import "./ChatAssistantContent.css";
import "./presentation/rich-presentation-shared.css";

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
  const {
    segments,
    visualFormatOptions,
    resolvedVisualKind,
    perSectionToolbar,
    routePresentation,
    routeToolCallBySectionId,
    visibleSegments,
  } = useAssistantContentSegments({ content, toolCalls });
  const {
    dataCoverageNotice,
    presentationInsight,
    presentationRecommendations,
    paginationState,
    depthState,
    chartExplanation,
  } = useAssistantContentChrome({ toolCalls, perSectionToolbar });
  const [chartExplanationOpen, setChartExplanationOpen] = useState(false);

  useEffect(() => {
    if (!requestChartExplanation) {
      return;
    }

    if (
      resolvedVisualKind === "chart" ||
      visualFormatOptions.some((item) => item.kind === "chart")
    ) {
      setChartExplanationOpen(true);
    }

    onChartExplanationHandled?.();
  }, [
    onChartExplanationHandled,
    requestChartExplanation,
    resolvedVisualKind,
    visualFormatOptions,
  ]);

  const title = useMemo(
    () => resolveAssistantPresentationTitle(content, toolCalls),
    [content, toolCalls],
  );

  if (!segments.length && !title) {
    return null;
  }

  const hasDecisionCard = visibleSegments.some((segment) => segment.kind === "decision");

  const showTitle =
    !hasDecisionCard &&
    !perSectionToolbar &&
    shouldRenderPresentationHeading(title) &&
    !visibleSegments.some((segment) => {
      if (segment.kind !== "markdown") {
        return false;
      }

      const prose = segment.markdown.trim();

      if (!prose || prose === title) {
        return true;
      }

      const withoutTitle = stripLeadingMarkdownTitleSafely(prose, title).trim();
      const firstLine = prose.split("\n")[0]?.trim() ?? "";

      return (
        withoutTitle !== prose ||
        firstLine === title ||
        firstLine === `### ${title}` ||
        firstLine === `## ${title}` ||
        firstLine === `# ${title}`
      );
    });

  const stackPlan = useMemo(
    () => getStackPresentationPlanFromToolCalls(toolCalls),
    [toolCalls],
  );
  const showCompleteStackView = shouldShowCompleteStackView(toolCalls);
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
    hasDecisionCard ||
    (showCompleteStackView &&
      Boolean(narrativeMarkdown.trim()) &&
      (planUsesHumanizedSections(stackPlan) ||
        segments.some(
          (segment) =>
            segment.kind === "table" ||
            segment.kind === "tree" ||
            segment.kind === "stackSection",
        )));

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
