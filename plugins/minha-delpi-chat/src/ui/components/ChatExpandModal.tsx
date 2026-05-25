import { X, Maximize2, FileSpreadsheet, FileText, Image } from "lucide-react";
import { useRef, useState } from "react";
import type { ChatPresentation } from "../../data/api/chatTypes";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import { ModalPortal } from "./ModalPortal";
import { exportToXlsx, exportToPdf, exportChartToPng } from "./exportUtils";

export function ChatExpandModal({
  presentation,
  onClose,
}: {
  presentation: ChatPresentation;
  onClose: () => void;
}) {
  const chartRef = useRef<HTMLDivElement>(null);
  const title =
    "title" in presentation ? presentation.title : "Visualização";

  return (
    <ModalPortal>
      <div
        className="mdc-expand-modal__backdrop"
        role="presentation"
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
              <ChatRichTable presentation={presentation} />
            )}
            {presentation.type === "chart" && (
              <ChatRichChart presentation={presentation} />
            )}
            {presentation.type === "kpi" && (
              <ChatRichKpi presentation={presentation} />
            )}
          </div>
        </div>
      </div>
    </ModalPortal>
  );
}

export function ExpandButton({
  presentation,
}: {
  presentation: ChatPresentation;
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
        />
      )}
    </>
  );
}
