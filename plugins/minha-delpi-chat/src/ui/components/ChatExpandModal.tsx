import { X, Maximize2, Copy } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChatPresentation } from "../../data/api/chatTypes";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichDashboard } from "./ChatRichDashboard";
import { ChatRichKpi } from "./ChatRichKpi";
import { ChatRichTree } from "./ChatRichTree";
import { ModalPortal } from "./ModalPortal";
import "./chat-modal-surface.css";
import "./ChatExpandModal.css";
import type { ChatCanvasOpenPayload } from "../../data/api/chatTypes";
import type { ChartViewState } from "./chartViewState";
import { ChatPresentationExportButtons } from "./ChatPresentationExportButtons";
import { treePresentationToClipboardText } from "./treePresentationUtils";

function copyKpiToClipboard(presentation: Extract<ChatPresentation, { type: "kpi" }>) {
  const lines = presentation.cards.map(
    (c) => `${c.label}: ${c.value}${c.unit || ""}${c.delta ? ` (${c.delta})` : ""}`
  );
  navigator.clipboard?.writeText(`${presentation.title}\n${lines.join("\n")}`);
}

export function ChatExpandModal({
  presentation,
  chartViewState,
  onClose,
  onDrillDown,
  onOpenCanvas,
}: {
  presentation: ChatPresentation;
  chartViewState?: ChartViewState;
  onClose: () => void;
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
}) {
  const chartRef = useRef<HTMLDivElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const title =
    "title" in presentation ? presentation.title : "Visualização";

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    modalRef.current?.focus();
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <ModalPortal>
      <div
        className="mdc-chat-overlay-scrim mdc-chat-overlay-scrim--centered mdc-expand-modal__backdrop"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={modalRef}
        tabIndex={-1}
        onMouseDown={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <div className="mdc-chat-overlay-panel mdc-expand-modal">
          <div className="mdc-expand-modal__header">
            <span className="mdc-expand-modal__title">{title}</span>
            <div className="mdc-expand-modal__toolbar">
              {presentation.type === "tree" ? (
                <button
                  className="mdc-expand-modal__tool-btn"
                  onClick={() =>
                    navigator.clipboard?.writeText(
                      treePresentationToClipboardText(presentation),
                    )
                  }
                  title="Copiar árvore"
                >
                  <Copy size={15} /> Copiar
                </button>
              ) : null}
              {presentation.type === "kpi" ? (
                <button
                  className="mdc-expand-modal__tool-btn"
                  onClick={() => copyKpiToClipboard(presentation)}
                  title="Copiar dados"
                >
                  <Copy size={15} /> Copiar
                </button>
              ) : null}
              {presentation.type === "table" ||
              presentation.type === "chart" ||
              presentation.type === "tree" ||
              presentation.type === "kpi" ||
              presentation.type === "dashboard" ? (
                <ChatPresentationExportButtons
                  presentation={presentation}
                  buttonClassName="mdc-expand-modal__tool-btn"
                  getChartRoot={() => chartRef.current}
                />
              ) : null}
              <button
                className="mdc-expand-modal__close"
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
                hideToolbar
                hideTitle
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
              <ChatRichDashboard
                presentation={presentation}
                onDrillDown={onDrillDown}
              />
            )}
            {presentation.type === "tree" && (
              <ChatRichTree
                presentation={presentation}
                hideToolbar
                hideTitle
                onDrillDown={onDrillDown}
              />
            )}
          </div>
        </div>
      </div>
    </ModalPortal>
  );
}

export function ExpandButton({
  presentation,
  chartViewState,
  onDrillDown,
  onOpenCanvas,
  disabled = false,
}: {
  presentation: ChatPresentation;
  chartViewState?: ChartViewState;
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
          onClose={() => setOpen(false)}
          onDrillDown={onDrillDown}
          onOpenCanvas={onOpenCanvas}
        />
      ) : null}
    </>
  );
}
