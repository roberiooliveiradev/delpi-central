import { X, Maximize2 } from "lucide-react";
import { useState } from "react";
import type { ChatPresentation } from "../../data/api/chatTypes";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import { ModalPortal } from "./ModalPortal";

export function ChatExpandModal({
  presentation,
  onClose,
}: {
  presentation: ChatPresentation;
  onClose: () => void;
}) {
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
            <span className="mdc-expand-modal__title">
              {"title" in presentation ? presentation.title : "Visualização"}
            </span>
            <button
              className="mdc-expand-modal__close"
              onClick={onClose}
              aria-label="Fechar"
            >
              <X size={18} />
            </button>
          </div>
          <div className="mdc-expand-modal__body">
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
