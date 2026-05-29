import { useEffect, useMemo, useState } from "react";
import type { ChatToolCall } from "../../data/api/chatTypes";
import {
  getDataCoverageNoticeFromToolCalls,
  getPreferredFormatFromToolCalls,
  getPresentationPairFromToolCalls,
  getPresentationTitle,
  getTablePresentationFromPair,
  getTreePresentationFromPair,
  hasDisplayableRichText,
  resolveCommentaryTextBody,
  resolvePresentationLayoutMode,
  resolveRichTextBody,
  type ViewFormat,
} from "./chatPresentation";
import { ChatMarkdown } from "./ChatMarkdown";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import { ChatRichTree } from "./ChatRichTree";
import { ExpandButton } from "./ChatExpandModal";
import "./ChatRichKpi.css";
import "./ChatRichTree.css";
import "./ChatExpandModal.css";

type ChatRichPresentationProps = {
  toolCalls: ChatToolCall[];
  textContent?: string | null;
  onDrillDown?: (query: string) => void;
};

function resolveDefaultVisualMode(
  toolCalls: ChatToolCall[],
  hasChart: boolean,
  hasTable: boolean,
  hasTree: boolean,
): ViewFormat {
  const preferred = getPreferredFormatFromToolCalls(toolCalls);

  if (preferred === "tree" && hasTree) {
    return "tree";
  }

  if (preferred === "chart" && hasChart) {
    return "chart";
  }

  if (preferred === "table" && hasTable) {
    return "table";
  }

  if (hasTree) {
    return "tree";
  }

  if (hasChart) {
    return "chart";
  }

  if (hasTable) {
    return "table";
  }

  return "tree";
}

function resolveDefaultViewMode(
  toolCalls: ChatToolCall[],
  hasText: boolean,
  hasChart: boolean,
  hasTable: boolean,
  hasTree: boolean,
): ViewFormat {
  const preferred = getPreferredFormatFromToolCalls(toolCalls);

  if (preferred === "text" && hasText) {
    return "text";
  }

  return resolveDefaultVisualMode(toolCalls, hasChart, hasTable, hasTree);
}

function FormatToggle({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`mdc-rich-chart__toggle-btn ${active ? "mdc-rich-chart__toggle-btn--active" : ""}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

export function ChatRichPresentation({
  toolCalls,
  textContent,
  onDrillDown,
}: ChatRichPresentationProps) {
  const pair = useMemo(
    () => getPresentationPairFromToolCalls(toolCalls),
    [toolCalls],
  );
  const { primary, table, tree } = pair;
  const layoutMode = useMemo(
    () => resolvePresentationLayoutMode(toolCalls, pair),
    [toolCalls, pair],
  );
  const dataCoverageNotice = useMemo(
    () => getDataCoverageNoticeFromToolCalls(toolCalls),
    [toolCalls],
  );
  const presentationTitle = useMemo(
    () => getPresentationTitle(textContent, toolCalls),
    [textContent, toolCalls],
  );
  const commentaryBody = useMemo(
    () => resolveCommentaryTextBody(textContent, toolCalls, pair),
    [textContent, toolCalls, pair],
  );
  const textBody = useMemo(
    () => resolveRichTextBody(textContent, toolCalls),
    [textContent, toolCalls],
  );

  const chartPresentation =
    primary?.type === "chart" ? primary : null;
  const tablePresentation = useMemo(
    () => getTablePresentationFromPair({ primary, table, tree }),
    [primary, table, tree],
  );
  const treePresentation = useMemo(
    () => getTreePresentationFromPair({ primary, table, tree }),
    [primary, table, tree],
  );

  const hasCommentary = hasDisplayableRichText(commentaryBody);
  const hasText = hasDisplayableRichText(textBody);
  const hasChartView = Boolean(chartPresentation);
  const hasTableView = Boolean(tablePresentation);
  const hasTreeView = Boolean(treePresentation);
  const isCommentaryVisual = layoutMode === "commentary-visual";

  const visualFormatCount = [hasChartView, hasTableView, hasTreeView].filter(Boolean).length;
  const showVisualToggle = isCommentaryVisual
    ? visualFormatCount >= 2
    : [hasText, hasChartView, hasTableView, hasTreeView].filter(Boolean).length >= 2;

  const defaultMode = isCommentaryVisual
    ? resolveDefaultVisualMode(toolCalls, hasChartView, hasTableView, hasTreeView)
    : resolveDefaultViewMode(toolCalls, hasText, hasChartView, hasTableView, hasTreeView);

  const [viewMode, setViewMode] = useState<ViewFormat>(defaultMode);

  useEffect(() => {
    setViewMode(defaultMode);
  }, [defaultMode, toolCalls]);

  if (!primary && !table && !tree && !textBody && !commentaryBody && !presentationTitle) {
    return null;
  }

  if (primary?.type === "kpi") {
    return (
      <div className="mdc-rich-presentation mdc-rich-presentation--enter">
        {dataCoverageNotice ? (
          <div className="mdc-rich-presentation__coverage-notice" role="status">
            {dataCoverageNotice.message}
          </div>
        ) : null}
        <div className="mdc-rich-presentation__toolbar">
          <ExpandButton presentation={primary} />
        </div>
        <ChatRichKpi presentation={primary} />
      </div>
    );
  }

  const coverageBanner = dataCoverageNotice ? (
    <div className="mdc-rich-presentation__coverage-notice" role="status">
      {dataCoverageNotice.message}
    </div>
  ) : null;

  const showSharedTitle = Boolean(presentationTitle) && !isCommentaryVisual;

  const formatToolbar = showVisualToggle ? (
    <div className="mdc-rich-presentation__toolbar">
      <div
        className="mdc-rich-presentation__format-toggle"
        role="group"
        aria-label="Formato da visualização"
      >
        {!isCommentaryVisual && hasText ? (
          <FormatToggle
            active={viewMode === "text"}
            label="Texto"
            onClick={() => setViewMode("text")}
          />
        ) : null}
        {hasChartView ? (
          <FormatToggle
            active={viewMode === "chart"}
            label="Gráfico"
            onClick={() => setViewMode("chart")}
          />
        ) : null}
        {hasTreeView ? (
          <FormatToggle
            active={viewMode === "tree"}
            label="Árvore"
            onClick={() => setViewMode("tree")}
          />
        ) : null}
        {hasTableView ? (
          <FormatToggle
            active={viewMode === "table"}
            label="Tabela"
            onClick={() => setViewMode("table")}
          />
        ) : null}
      </div>
    </div>
  ) : null;

  if (isCommentaryVisual) {
    return (
      <div className="mdc-rich-presentation mdc-rich-presentation--enter mdc-rich-presentation--commentary">
        {coverageBanner}

        {hasCommentary ? (
          <div className="mdc-rich-presentation__text mdc-rich-presentation__text--commentary">
            <ChatMarkdown content={commentaryBody} />
          </div>
        ) : presentationTitle ? (
          <h3 className="mdc-rich-presentation__heading">{presentationTitle}</h3>
        ) : null}

        {formatToolbar}

        {showVisualToggle ? (
          <>
            {viewMode === "chart" && hasChartView && chartPresentation ? (
              <ChatRichChart
                presentation={chartPresentation}
                onDrillDown={onDrillDown}
              />
            ) : null}

            {viewMode === "tree" && hasTreeView && treePresentation ? (
              <ChatRichTree
                presentation={treePresentation}
                onDrillDown={onDrillDown}
              />
            ) : null}

            {viewMode === "table" && hasTableView && tablePresentation ? (
              <ChatRichTable
                presentation={tablePresentation}
                onDrillDown={onDrillDown}
              />
            ) : null}
          </>
        ) : hasTreeView && treePresentation ? (
          <ChatRichTree presentation={treePresentation} onDrillDown={onDrillDown} />
        ) : hasTableView && tablePresentation ? (
          <ChatRichTable presentation={tablePresentation} onDrillDown={onDrillDown} />
        ) : hasChartView && chartPresentation ? (
          <ChatRichChart presentation={chartPresentation} onDrillDown={onDrillDown} />
        ) : null}
      </div>
    );
  }

  return (
    <div className="mdc-rich-presentation mdc-rich-presentation--enter">
      {coverageBanner}
      {formatToolbar}

      {showSharedTitle ? (
        <h3 className="mdc-rich-presentation__heading">{presentationTitle}</h3>
      ) : null}

      {viewMode === "text" && hasText && textBody ? (
        <div className="mdc-rich-presentation__text">
          <ChatMarkdown content={textBody} />
        </div>
      ) : null}

      {viewMode === "chart" && hasChartView && chartPresentation ? (
        <ChatRichChart
          presentation={chartPresentation}
          hideTitle={showSharedTitle}
          onDrillDown={onDrillDown}
        />
      ) : null}

      {viewMode === "tree" && hasTreeView && treePresentation ? (
        <ChatRichTree
          presentation={treePresentation}
          hideTitle={showSharedTitle}
          onDrillDown={onDrillDown}
        />
      ) : null}

      {viewMode === "table" && hasTableView && tablePresentation ? (
        <ChatRichTable
          presentation={tablePresentation}
          hideTitle={showSharedTitle}
          onDrillDown={onDrillDown}
        />
      ) : null}
    </div>
  );
}
