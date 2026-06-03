import { useMemo } from "react";

import type { ChatCanvasOpenPayload, ChatToolCall } from "../../data/api/chatTypes";

import {
  buildAssistantContentSegments,
  isPresentationHeadingTitle,
  type AssistantContentSegment,
} from "./assistantContentSegments";
import { ChatMarkdown } from "./ChatMarkdown";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichDashboard } from "./ChatRichDashboard";
import { ChatRichKpi } from "./ChatRichKpi";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichTree } from "./ChatRichTree";
import {
  getDataCoverageNoticeFromToolCalls,
  getPresentationTitle,
} from "./chatPresentation";

import "./ChatAssistantContent.css";
import "./rich-presentation-shared.css";

type ChatAssistantContentProps = {
  content: string;
  toolCalls?: ChatToolCall[];
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
};

function renderSegment(
  segment: AssistantContentSegment,
  index: number,
  options: {
    onDrillDown?: (query: string) => void;
    onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
    title?: string | null;
  },
) {
  const key = `${segment.kind}-${index}`;

  if (segment.kind === "markdown") {
    return <ChatMarkdown key={key} content={segment.markdown} />;
  }

  if (segment.kind === "code") {
    return <ChatMarkdown key={key} content={`\`\`\`${segment.language}\n${segment.code}\n\`\`\``} />;
  }

  if (segment.kind === "table") {
    return (
      <ChatRichTable
        key={key}
        presentation={segment.presentation}
        onDrillDown={options.onDrillDown}
      />
    );
  }

  if (segment.kind === "chart") {
    return (
      <ChatRichChart
        key={key}
        presentation={segment.presentation}
        onDrillDown={options.onDrillDown}
        onOpenCanvas={options.onOpenCanvas}
      />
    );
  }

  if (segment.kind === "tree") {
    return (
      <ChatRichTree
        key={key}
        presentation={segment.presentation}
        onDrillDown={options.onDrillDown}
      />
    );
  }

  if (segment.kind === "kpi") {
    return <ChatRichKpi key={key} presentation={segment.presentation} />;
  }

  return (
    <ChatRichDashboard
      key={key}
      presentation={segment.presentation}
      toolCalls={[]}
      onDrillDown={options.onDrillDown}
      onOpenCanvas={options.onOpenCanvas}
    />
  );
}

export function ChatAssistantContent({
  content,
  toolCalls = [],
  onDrillDown,
  onOpenCanvas,
}: ChatAssistantContentProps) {
  const segments = useMemo(
    () => buildAssistantContentSegments(content, toolCalls),
    [content, toolCalls],
  );
  const title = useMemo(() => getPresentationTitle(content, toolCalls), [content, toolCalls]);
  const dataCoverageNotice = useMemo(
    () => getDataCoverageNoticeFromToolCalls(toolCalls),
    [toolCalls],
  );

  if (!segments.length && !title) {
    return null;
  }

  const showTitle =
    isPresentationHeadingTitle(title) &&
    !segments.some(
      (segment) => segment.kind === "markdown" && segment.markdown.trim() === title,
    );

  return (
    <div className="mdc-assistant-content mdc-rich-presentation mdc-rich-presentation--enter">
      {dataCoverageNotice ? (
        <div className="mdc-rich-presentation__coverage-notice" role="status">
          {dataCoverageNotice.message}
        </div>
      ) : null}

      {showTitle ? <h3 className="mdc-rich-presentation__heading">{title}</h3> : null}

      <div className="mdc-assistant-content__segments">
        {segments.map((segment, index) =>
          renderSegment(segment, index, { onDrillDown, onOpenCanvas, title }),
        )}
      </div>
    </div>
  );
}
