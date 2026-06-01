import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  ChatCanvasOpenPayload,
  ChatDepthState,
  ChatPaginationState,
  ChatToolCall,
} from "../../data/api/chatTypes";
import {
  getDataCoverageNoticeFromToolCalls,
  getDepthStateFromToolCalls,
  getPaginationStateFromToolCalls,
  countRichVisualFormats,
  getPresentationPairFromToolCalls,
  resolveDefaultRichViewMode,
  resolveRichFormatToggles,
  getPresentationInsightFromToolCalls,
  getPresentationTitle,
  getChartPresentationFromPair,
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
import { ChatRichDashboard } from "./ChatRichDashboard";
import { ChatRichKpi } from "./ChatRichKpi";
import { ChatRichTree } from "./ChatRichTree";
import { ExpandButton } from "./ChatExpandModal";
import { recordPresentationTelemetry } from "./presentationTelemetry";
import "./ChatRichKpi.css";
import "./ChatRichTree.css";
import "./ChatExpandModal.css";

type ChatRichPresentationProps = {
  toolCalls: ChatToolCall[];
  textContent?: string | null;
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
};

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

function CoverageNavigation({
  pagination,
  depth,
  onNavigate,
}: {
  pagination: ChatPaginationState | null;
  depth: ChatDepthState | null;
  onNavigate?: (query: string) => void;
}) {
  if (!onNavigate || (!pagination && !depth)) {
    return null;
  }

  const showPagination =
    pagination && (pagination.hasPrevious || pagination.hasNext || (pagination.totalPages ?? 0) > 1);

  if (!showPagination && !depth?.canIncrease) {
    return null;
  }

  return (
    <div className="mdc-rich-presentation__navigation" role="navigation" aria-label="Navegação dos dados">
      {showPagination && pagination ? (
        <div className="mdc-rich-presentation__pagination">
          <button
            type="button"
            className="mdc-rich-presentation__nav-btn"
            disabled={!pagination.hasPrevious}
            onClick={() => onNavigate("página anterior")}
          >
            Anterior
          </button>
          <span className="mdc-rich-presentation__pagination-label">
            Página {pagination.page}
            {pagination.totalPages ? ` de ${pagination.totalPages}` : ""}
            {pagination.total !== undefined
              ? ` · ${pagination.total} registro(s)`
              : ""}
          </span>
          <button
            type="button"
            className="mdc-rich-presentation__nav-btn"
            disabled={!pagination.hasNext}
            onClick={() => onNavigate("próxima página")}
          >
            Próxima
          </button>
        </div>
      ) : null}

      {depth?.canIncrease ? (
        <button
          type="button"
          className="mdc-rich-presentation__nav-btn mdc-rich-presentation__nav-btn--secondary"
          onClick={() => onNavigate("aumente a profundidade para 99")}
        >
          Ampliar níveis
        </button>
      ) : null}
    </div>
  );
}

export function ChatRichPresentation({
  toolCalls,
  textContent,
  onDrillDown,
  onOpenCanvas,
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
  const paginationState = useMemo(
    () => getPaginationStateFromToolCalls(toolCalls),
    [toolCalls],
  );
  const depthState = useMemo(
    () => getDepthStateFromToolCalls(toolCalls),
    [toolCalls],
  );
  const presentationTitle = useMemo(
    () => getPresentationTitle(textContent, toolCalls),
    [textContent, toolCalls],
  );
  const presentationInsight = useMemo(
    () => getPresentationInsightFromToolCalls(toolCalls),
    [toolCalls],
  );
  const commentaryBody = useMemo(
    () => resolveCommentaryTextBody(textContent, toolCalls, pair),
    [textContent, toolCalls, pair],
  );
  const textBody = useMemo(
    () => resolveRichTextBody(textContent, toolCalls),
    [textContent, toolCalls],
  );

  const chartPresentation = useMemo(
    () => getChartPresentationFromPair(pair, toolCalls),
    [pair, toolCalls],
  );
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

  const formatToggles = resolveRichFormatToggles({
    hasText,
    hasChart: hasChartView,
    hasTable: hasTableView,
    hasTree: hasTreeView,
    isCommentaryVisual,
  });
  const visualFormatCount = countRichVisualFormats(formatToggles);
  const showVisualToggle = isCommentaryVisual
    ? visualFormatCount >= 2
    : [
        formatToggles.showText,
        formatToggles.showTree,
        formatToggles.showTable,
        formatToggles.showChart,
      ].filter(Boolean).length >= 2;

  const defaultMode = resolveDefaultRichViewMode(toolCalls, {
    hasText,
    hasChart: hasChartView,
    hasTable: hasTableView,
    hasTree: hasTreeView,
    commentaryVisual: isCommentaryVisual,
  });

  const [viewMode, setViewMode] = useState<ViewFormat>(defaultMode);

  const switchViewMode = useCallback((mode: ViewFormat) => {
    setViewMode((previous) => {
      if (previous !== mode) {
        recordPresentationTelemetry("presentation_view_switch", {
          from: previous,
          to: mode,
        });
      }

      return mode;
    });
  }, []);

  useEffect(() => {
    setViewMode(defaultMode);
  }, [defaultMode, toolCalls]);

  if (!primary && !table && !tree && !textBody && !commentaryBody && !presentationTitle) {
    return null;
  }

  if (primary?.type === "dashboard") {
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
        <ChatRichDashboard presentation={primary} onDrillDown={onDrillDown} onOpenCanvas={onOpenCanvas} />
      </div>
    );
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

  const insightBanner = presentationInsight ? (
    <p className="mdc-rich-presentation__insight" role="note" title="Por que este formato">
      {presentationInsight}
    </p>
  ) : null;

  const coverageNavigation = (
    <CoverageNavigation
      pagination={paginationState}
      depth={depthState}
      onNavigate={onDrillDown}
    />
  );

  const showSharedTitle = Boolean(presentationTitle) && !isCommentaryVisual;

  const formatToolbar = showVisualToggle ? (
    <div className="mdc-rich-presentation__toolbar">
      <div
        className="mdc-rich-presentation__format-toggle"
        role="group"
        aria-label="Formato da visualização"
      >
        {formatToggles.showText ? (
          <FormatToggle
            active={viewMode === "text"}
            label="Texto"
            onClick={() => switchViewMode("text")}
          />
        ) : null}
        {formatToggles.showTree ? (
          <FormatToggle
            active={viewMode === "tree"}
            label="Árvore"
            onClick={() => switchViewMode("tree")}
          />
        ) : null}
        {formatToggles.showTable ? (
          <FormatToggle
            active={viewMode === "table"}
            label="Tabela"
            onClick={() => switchViewMode("table")}
          />
        ) : null}
        {formatToggles.showChart ? (
          <FormatToggle
            active={viewMode === "chart"}
            label="Gráfico"
            onClick={() => switchViewMode("chart")}
          />
        ) : null}
      </div>
    </div>
  ) : null;

  if (isCommentaryVisual) {
    return (
      <div className="mdc-rich-presentation mdc-rich-presentation--enter mdc-rich-presentation--commentary">
        {coverageBanner}
        {insightBanner}
        {coverageNavigation}

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
            {viewMode === "tree" && hasTreeView && treePresentation ? (
              <ChatRichTree presentation={treePresentation} onDrillDown={onDrillDown} />
            ) : null}

            {viewMode === "table" && hasTableView && tablePresentation ? (
              <ChatRichTable presentation={tablePresentation} onDrillDown={onDrillDown} />
            ) : null}

            {viewMode === "chart" && formatToggles.showChart && hasChartView && chartPresentation ? (
              <ChatRichChart
                presentation={chartPresentation}
                onDrillDown={onDrillDown}
                onOpenCanvas={onOpenCanvas}
              />
            ) : null}
          </>
        ) : hasTreeView && treePresentation ? (
          <ChatRichTree presentation={treePresentation} onDrillDown={onDrillDown} />
        ) : hasTableView && tablePresentation ? (
          <ChatRichTable presentation={tablePresentation} onDrillDown={onDrillDown} />
        ) : hasChartView && chartPresentation ? (
          <ChatRichChart presentation={chartPresentation} onDrillDown={onDrillDown} onOpenCanvas={onOpenCanvas} />
        ) : null}
      </div>
    );
  }

  return (
    <div className="mdc-rich-presentation mdc-rich-presentation--enter">
      {coverageBanner}
      {insightBanner}
      {coverageNavigation}
      {formatToolbar}

      {showSharedTitle ? (
        <h3 className="mdc-rich-presentation__heading">{presentationTitle}</h3>
      ) : null}

      {viewMode === "text" && hasText && textBody ? (
        <div className="mdc-rich-presentation__text">
          <ChatMarkdown content={textBody} />
        </div>
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

      {viewMode === "chart" && formatToggles.showChart && hasChartView && chartPresentation ? (
        <ChatRichChart
          presentation={chartPresentation}
          hideTitle={showSharedTitle}
          onDrillDown={onDrillDown}
          onOpenCanvas={onOpenCanvas}
        />
      ) : null}
    </div>
  );
}
