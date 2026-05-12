import { FileText, Maximize2 } from "lucide-react";

import type { ChatCanvasDocument } from "./ChatCanvas";
import "./ChatCanvasInline.css";

type ChatCanvasInlineProps = {
  document: ChatCanvasDocument;
  onOpen: (document: ChatCanvasDocument) => void;
};

export function ChatCanvasInline({ document, onOpen }: ChatCanvasInlineProps) {
  const preview = document.markdown
    .replace(/[#*_`>-]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 180);

  return (
    <button
      type="button"
      className="mdc-chat-canvas-inline"
      onClick={() => onOpen(document)}
    >
      <span className="mdc-chat-canvas-inline__icon">
        <FileText size={18} aria-hidden="true" />
      </span>

      <span className="mdc-chat-canvas-inline__content">
        <strong>{document.title}</strong>
        <small>{preview || "Abrir conteúdo na lousa"}</small>
      </span>

      <span className="mdc-chat-canvas-inline__action">
        <Maximize2 size={15} aria-hidden="true" />
      </span>
    </button>
  );
}
