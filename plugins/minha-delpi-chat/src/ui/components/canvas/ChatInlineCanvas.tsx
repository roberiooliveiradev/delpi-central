import { Maximize2 } from "lucide-react";

import type { ChatCanvasOpenPayload } from "../../../data/api/chatTypes";
import { ChatMarkdown } from "../message/ChatMarkdown";

import "./ChatInlineCanvas.css";

type ChatInlineCanvasProps = {
  payload: ChatCanvasOpenPayload;
  onOpen?: (payload: ChatCanvasOpenPayload) => void;
};

export function ChatInlineCanvas({ payload, onOpen }: ChatInlineCanvasProps) {
  return (
    <section
      className="mdc-chat-inline-canvas"
      aria-label={`Lousa: ${payload.title}`}
    >
      <header className="mdc-chat-inline-canvas__header">
        <div>
          <p className="mdc-chat-inline-canvas__eyebrow">Lousa</p>
          <h3 className="mdc-chat-inline-canvas__title">{payload.title}</h3>
        </div>

        {onOpen ? (
          <button
            type="button"
            className="mdc-chat-inline-canvas__open-btn"
            onClick={() => onOpen(payload)}
          >
            <Maximize2 size={15} aria-hidden="true" />
            Abrir na lousa
          </button>
        ) : null}
      </header>

      <div className="mdc-chat-inline-canvas__preview">
        <ChatMarkdown content={payload.markdown} />
      </div>
    </section>
  );
}
