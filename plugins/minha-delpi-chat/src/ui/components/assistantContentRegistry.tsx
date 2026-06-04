import type { ReactNode } from "react";

import type { ChatCanvasOpenPayload, ChatPresentation } from "../../data/api/chatTypes";

import type { AssistantContentSegment } from "./assistantContentTypes";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichDashboard } from "./ChatRichDashboard";
import { ChatRichKpi } from "./ChatRichKpi";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichTree } from "./ChatRichTree";
import { AssistantStackSection } from "./AssistantStackSection";
import { ChatMarkdown } from "./ChatMarkdown";

export type AssistantSegmentRenderContext = {
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
  chartExplanation?: string;
  showChartExplanation?: boolean;
  onChartExplanationChange?: (open: boolean) => void;
};

export type AssistantSegmentRenderer = (
  segment: AssistantContentSegment,
  index: number,
  context: AssistantSegmentRenderContext,
) => ReactNode;

const BASE_RENDERERS: Record<AssistantContentSegment["kind"], AssistantSegmentRenderer> = {
  stackSection: (segment, index) => {
    if (segment.kind !== "stackSection") {
      return null;
    }

    return <AssistantStackSection key={`stack-section-${index}`} section={segment.section} />;
  },
  markdown: (segment, index) => {
    if (segment.kind !== "markdown") {
      return null;
    }

    return <ChatMarkdown key={`markdown-${index}`} content={segment.markdown} />;
  },
  code: (segment, index) => {
    if (segment.kind !== "code") {
      return null;
    }

    return (
      <ChatMarkdown
        key={`code-${index}`}
        content={`\`\`\`${segment.language}\n${segment.code}\n\`\`\``}
      />
    );
  },
  table: (segment, index, context) => {
    if (segment.kind !== "table") {
      return null;
    }

    return (
      <ChatRichTable
        key={`table-${index}`}
        presentation={segment.presentation}
        onDrillDown={context.onDrillDown}
      />
    );
  },
  chart: (segment, index, context) => {
    if (segment.kind !== "chart") {
      return null;
    }

    return (
      <ChatRichChart
        key={`chart-${index}`}
        presentation={segment.presentation}
        chartExplanation={context.chartExplanation}
        showExplanation={context.showChartExplanation}
        onShowExplanationChange={context.onChartExplanationChange}
        onDrillDown={context.onDrillDown}
        onOpenCanvas={context.onOpenCanvas}
      />
    );
  },
  tree: (segment, index, context) => {
    if (segment.kind !== "tree") {
      return null;
    }

    return (
      <ChatRichTree
        key={`tree-${index}`}
        presentation={segment.presentation}
        onDrillDown={context.onDrillDown}
      />
    );
  },
  kpi: (segment, index) => {
    if (segment.kind !== "kpi") {
      return null;
    }

    return <ChatRichKpi key={`kpi-${index}`} presentation={segment.presentation} />;
  },
  dashboard: (segment, index, context) => {
    if (segment.kind !== "dashboard") {
      return null;
    }

    return (
      <ChatRichDashboard
        key={`dashboard-${index}`}
        presentation={segment.presentation}
        toolCalls={[]}
        onDrillDown={context.onDrillDown}
        onOpenCanvas={context.onOpenCanvas}
      />
    );
  },
};

const customRenderers: Partial<
  Record<AssistantContentSegment["kind"], AssistantSegmentRenderer>
> = {};

/** Permite registrar novos tipos de segmento no ChatAssistantContent. */
export function registerAssistantSegmentRenderer(
  kind: AssistantContentSegment["kind"],
  renderer: AssistantSegmentRenderer,
): void {
  customRenderers[kind] = renderer;
}

export function renderAssistantContentSegment(
  segment: AssistantContentSegment,
  index: number,
  context: AssistantSegmentRenderContext,
): ReactNode {
  const renderer = customRenderers[segment.kind] ?? BASE_RENDERERS[segment.kind];

  return renderer(segment, index, context);
}

/** Tipos de `ChatPresentation` suportados nativamente no assistente. */
export const SUPPORTED_ASSISTANT_PRESENTATION_TYPES = new Set<ChatPresentation["type"]>([
  "table",
  "chart",
  "tree",
  "kpi",
  "dashboard",
  "markdown",
]);
