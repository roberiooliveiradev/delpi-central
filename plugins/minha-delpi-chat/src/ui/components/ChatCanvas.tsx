import { Copy, Maximize2, Minimize2, X } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import "./ChatCanvas.css";

export type ChatCanvasDocument = {
  title: string;
  markdown: string;
};

type ChatCanvasProps = {
  document?: ChatCanvasDocument | null;
  onChange?: (document: ChatCanvasDocument) => void;
  onClose?: () => void;
};

export function ChatCanvas({ document, onChange, onClose }: ChatCanvasProps) {
  const [mode, setMode] = useState<"edit" | "preview">("preview");
  const [expanded, setExpanded] = useState(false);

  if (!document) {
    return null;
  }

  async function copyCanvas() {
    await navigator.clipboard?.writeText(document.markdown);
  }

  return (
    <div
      className="mdc-chat-canvas-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose?.();
        }
      }}
    >
      <aside
        className={
          expanded
            ? "mdc-chat-canvas mdc-chat-canvas--expanded"
            : "mdc-chat-canvas"
        }
        aria-label="Lousa do Chat DELPI"
        role="dialog"
        aria-modal="true"
      >
        <header className="mdc-chat-canvas__header">
          <div>
            <p className="mdc-chat-eyebrow">Lousa</p>
            <input
              value={document.title}
              onChange={(event) =>
                onChange?.({
                  ...document,
                  title: event.target.value,
                })
              }
              aria-label="Título da lousa"
            />
          </div>

          <div className="mdc-chat-canvas__actions">
            <button
              type="button"
              onClick={() =>
                setMode((current) => (current === "edit" ? "preview" : "edit"))
              }
              title={mode === "edit" ? "Visualizar" : "Editar"}
            >
              {mode === "edit" ? "Prévia" : "Editar"}
            </button>

            <button type="button" onClick={copyCanvas} title="Copiar markdown">
              <Copy size={16} aria-hidden="true" />
            </button>

            <button
              type="button"
              onClick={() => setExpanded((current) => !current)}
              title={expanded ? "Reduzir" : "Expandir"}
            >
              {expanded ? (
                <Minimize2 size={16} aria-hidden="true" />
              ) : (
                <Maximize2 size={16} aria-hidden="true" />
              )}
            </button>

            <button type="button" onClick={onClose} title="Fechar">
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        </header>

        <div className="mdc-chat-canvas__body">
          {mode === "edit" ? (
            <textarea
              value={document.markdown}
              onChange={(event) =>
                onChange?.({
                  ...document,
                  markdown: event.target.value,
                })
              }
              aria-label="Conteúdo markdown da lousa"
            />
          ) : (
            <article className="mdc-chat-canvas__preview">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {document.markdown}
              </ReactMarkdown>
            </article>
          )}
        </div>
      </aside>
    </div>
  );
}
