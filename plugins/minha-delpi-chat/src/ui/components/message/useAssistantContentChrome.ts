import { useMemo } from "react";

import type { ChatToolCall } from "../../../data/api/chatTypes";

import { getChartExplanationFromToolCalls } from "../chartExplain";
import {
  getDepthStateFromToolCalls,
  getPaginationStateFromToolCalls,
  getPresentationInsightFromToolCalls,
  getPresentationRecommendationsFromToolCalls,
} from "../chatPresentation";
import { resolveHumanizedCoverageNotice } from "../humanizedCoverageNotice";

type UseAssistantContentChromeArgs = {
  toolCalls: ChatToolCall[];
  perSectionToolbar: boolean;
};

export function useAssistantContentChrome({
  toolCalls,
  perSectionToolbar,
}: UseAssistantContentChromeArgs) {
  const dataCoverageNotice = useMemo(
    () => (perSectionToolbar ? null : resolveHumanizedCoverageNotice(toolCalls)),
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

  return {
    dataCoverageNotice,
    presentationInsight,
    presentationRecommendations,
    paginationState,
    depthState,
    chartExplanation,
  };
}
