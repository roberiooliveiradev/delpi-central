import { X, Maximize2, Copy } from "lucide-react";
import { useRef, useState } from "react";
import type { ChatCanvasOpenPayload, ChatPresentation } from "../../../data/api/chatTypes";
import { ChatRichTable } from "../presentation/ChatRichTable";
import { ChatRichChart } from "../presentation/ChatRichChart";
import { ChatRichDashboard } from "../presentation/ChatRichDashboard";
import { ChatRichKpi } from "../presentation/ChatRichKpi";
import { ChatRichTree } from "../presentation/ChatRichTree";
import { ChatModal } from "../shared/modal/ChatModal";
import "./ChatExpandModal.css";
import type { ChartViewState } from "../presentation/chartViewState";
import type {
  RichTableViewState,
  RichTreeViewState,
} from "../presentation/richPresentationViewState";
import { ChatPresentationExportButtons } from "../presentation/ChatPresentationExportButtons";

function copyKpiToClipboard(presentation: Extract<ChatPresentation, { type: "kpi" }>) {
  const lines = presentation.cards.map(
    (c) => `${c.label}: ${c.value}${c.unit || ""}${c.delta ? ` (${c.delta})` : ""}`,
  );
  navigator.clipboard?.writeText(`${presentation.title}\n${lines.join("\n")}`);
}

export function ChatExpandModal({
  presentation,
  chartViewState,
  tableViewState,
  treeViewState,
  onClose,
  onDrillDown,
  onOpenCanvas,
}: {
  presentation: ChatPresentation;
  chartViewState?: ChartViewState;
  tableViewState?: RichTableViewState;
  treeViewState?: RichTreeViewState;
  onClose: () => void;
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
}) {
  const chartRef = useRef<HTMLDivElement>(null);
  const title =
    "title" in presentation ? presentation.title : "Visualização";
  /** Tabela/árvore já expõem busca+filtro+export na toolbar do corpo. */
  const bodyOwnsFilterToolbar =
    presentation.type === "table" || presentation.type === "tree";

  return (
    <ChatModal
      open
      onClose={onClose}
      size="none"
      panelClassName="mdc-expand-modal"
      ariaLabelledBy="mdc-expand-modal-title"
    >
      <div className="mdc-expand-modal__header">
        <span id="mdc-expand-modal-title" className="mdc-expand-modal__title">
          {title}
        </span>
        <div className="mdc-expand-modal__toolbar">
          {presentation.type === "kpi" ? (
            <button
              className="mdc-expand-modal__tool-btn mdc-chat-modal-tool-btn"
              onClick={() => copyKpiToClipboard(presentation)}
              title="Copiar dados"
            >
              <Copy size={15} /> Copiar
            </button>
          ) : null}
          {!bodyOwnsFilterToolbar &&
          (presentation.type === "chart" ||
            presentation.type === "kpi" ||
            presentation.type === "dashboard") ? (
            <ChatPresentationExportButtons
              presentation={presentation}
              buttonClassName="mdc-expand-modal__tool-btn"
              getChartRoot={() => chartRef.current}
            />
          ) : null}
          <button
            className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--sm"
            onClick={onClose}
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>
      </div>
      <div className="mdc-expand-modal__body" ref={chartRef}>
        {presentation.type === "table" && (
          <ChatRichTable
            presentation={presentation}
            hideTitle
            expanded
            initialViewState={tableViewState}
            onDrillDown={onDrillDown}
          />
        )}
        {presentation.type === "chart" && (
          <ChatRichChart
            presentation={presentation}
            hideTitle
            expanded
            initialViewState={chartViewState}
            onDrillDown={onDrillDown}
            onOpenCanvas={onOpenCanvas}
          />
        )}
        {presentation.type === "kpi" && (
          <ChatRichKpi presentation={presentation} hideToolbar />
        )}
        {presentation.type === "dashboard" && (
          <ChatRichDashboard presentation={presentation} onDrillDown={onDrillDown} />
        )}
        {presentation.type === "tree" && (
          <ChatRichTree
            presentation={presentation}
            hideTitle
            expanded
            initialViewState={treeViewState}
            onDrillDown={onDrillDown}
          />
        )}
      </div>
    </ChatModal>
  );
}

export function ExpandButton({
  presentation,
  chartViewState,
  tableViewState,
  treeViewState,
  onDrillDown,
  onOpenCanvas,
  disabled = false,
}: {
  presentation: ChatPresentation;
  chartViewState?: ChartViewState;
  tableViewState?: RichTableViewState;
  treeViewState?: RichTreeViewState;
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
  /** Evita abrir outro modal quando já está em contexto expandido. */
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);

  if (disabled) {
    return null;
  }

  return (
    <>
      <button
        type="button"
        className="mdc-rich-chart__btn"
        onClick={() => setOpen(true)}
        title="Expandir"
        aria-haspopup="dialog"
        aria-expanded={open}
      >
        <Maximize2 size={12} /> Expandir
      </button>
      {open ? (
        <ChatExpandModal
          presentation={presentation}
          chartViewState={chartViewState}
          tableViewState={tableViewState}
          treeViewState={treeViewState}
          onClose={() => setOpen(false)}
          onDrillDown={onDrillDown}
          onOpenCanvas={onOpenCanvas}
        />
      ) : null}
    </>
  );
}
