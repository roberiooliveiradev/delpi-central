import { X, Maximize2, FileSpreadsheet, FileText, Image, Copy } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChatPresentation } from "../../data/api/chatTypes";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichDashboard } from "./ChatRichDashboard";
import { ChatRichKpi } from "./ChatRichKpi";
import { ChatRichTree } from "./ChatRichTree";
import { ModalPortal } from "./ModalPortal";
import { exportToXlsx, exportToPdf, exportChartToPng, exportTreeToPdf, exportTreeToXlsx } from "./exportUtils";
import { treePresentationToClipboardText } from "./treePresentationUtils";

function copyKpiToClipboard(presentation: Extract<ChatPresentation, { type: "kpi" }>) {
  const lines = presentation.cards.map(
    (c) => `${c.label}: ${c.value}${c.unit || ""}${c.delta ? ` (${c.delta})` : ""}`
  );
  navigator.clipboard?.writeText(`${presentation.title}\n${lines.join("\n")}`);
}

export function ChatExpandModal({
  presentation,
  onClose,
  onDrillDown,
}: {
  presentation: ChatPresentation;
  onClose: () => void;
  onDrillDown?: (query: string) => void;
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
        className="mdc-expand-modal__backdrop"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={modalRef}
        tabIndex={-1}
        onMouseDown={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <div className="mdc-expand-modal">
          <div className="mdc-expand-modal__header">
            <span className="mdc-expand-modal__title">{title}</span>
            <div className="mdc-expand-modal__toolbar">
              {presentation.type === "table" && (
                <>
                  <button
                    className="mdc-expand-modal__tool-btn"
                    onClick={() => exportToXlsx(presentation)}
                    title="Exportar XLSX"
                  >
                    <FileSpreadsheet size={15} /> XLSX
                  </button>
                  <button
                    className="mdc-expand-modal__tool-btn"
                    onClick={() => exportToPdf(presentation)}
                    title="Exportar PDF"
                  >
                    <FileText size={15} /> PDF
                  </button>
                </>
              )}
              {presentation.type === "chart" && (
                <button
                  className="mdc-expand-modal__tool-btn"
                  onClick={() => exportChartToPng(chartRef.current, title)}
                  title="Exportar PNG"
                >
                  <Image size={15} /> PNG
                </button>
              )}
              {presentation.type === "kpi" && (
                <button
                  className="mdc-expand-modal__tool-btn"
                  onClick={() => copyKpiToClipboard(presentation)}
                  title="Copiar dados"
                >
                  <Copy size={15} /> Copiar
                </button>
              )}
              {presentation.type === "tree" && (
                <>
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
                  <button
                    className="mdc-expand-modal__tool-btn"
                    onClick={() => exportTreeToXlsx(presentation)}
                    title="Exportar XLSX"
                  >
                    <FileSpreadsheet size={15} /> XLSX
                  </button>
                  <button
                    className="mdc-expand-modal__tool-btn"
                    onClick={() => exportTreeToPdf(presentation)}
                    title="Exportar PDF"
                  >
                    <FileText size={15} /> PDF
                  </button>
                </>
              )}
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
              <ChatRichTable presentation={presentation} onDrillDown={onDrillDown} />
            )}
            {presentation.type === "chart" && (
              <ChatRichChart presentation={presentation} />
            )}
            {presentation.type === "kpi" && (
              <ChatRichKpi presentation={presentation} />
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
  onDrillDown,
}: {
  presentation: ChatPresentation;
  onDrillDown?: (query: string) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        className="mdc-rich-chart__btn"
        onClick={() => setOpen(true)}
        title="Expandir"
      >
        <Maximize2 size={12} /> Expandir
      </button>
      {open && (
        <ChatExpandModal
          presentation={presentation}
          onClose={() => setOpen(false)}
          onDrillDown={onDrillDown}
        />
      )}
    </>
  );
}
