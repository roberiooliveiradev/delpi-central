import { Check, Copy, Maximize2, Minimize2, Save, X } from "lucide-react";
import { useState } from "react";
import { ChatMarkdown } from "./ChatMarkdown";

import "./ChatCanvas.css";

export type ChatCanvasDocument = {
  id?: string;
  messageId?: string | null;
  title: string;
  markdown: string;
  isSaving?: boolean;
  isSaved?: boolean;
};

type ChatCanvasProps = {
  document?: ChatCanvasDocument | null;
  onChange?: (document: ChatCanvasDocument) => void;
  onSave?: (document: ChatCanvasDocument) => void | Promise<void>;
  onClose?: () => void;
};

export function ChatCanvas({ document, onChange, onSave, onClose }: ChatCanvasProps) {
  const [mode, setMode] = useState<"edit" | "preview">("preview");
  const [expanded, setExpanded] = useState(false);

  if (!document) {
    return null;
  }

  async function copyCanvas() {
    await navigator.clipboard?.writeText(document.markdown);
  }

  function updateDocument(next: ChatCanvasDocument) {
    onChange?.({
      ...next,
      isSaved: false,
    });
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
                updateDocument({
                  ...document,
                  title: event.target.value,
                })
              }
              aria-label="Título da lousa"
            />
          </div>

          <div className="mdc-chat-canvas__actions">
            {onSave ? (
              <button
                type="button"
                onClick={() => void onSave(document)}
                disabled={document.isSaving}
                title={document.isSaved ? "Salvo" : "Salvar lousa"}
              >
                {document.isSaved ? (
                  <Check size={16} aria-hidden="true" />
                ) : (
                  <Save size={16} aria-hidden="true" />
                )}
                <span>{document.isSaving ? "Salvando" : document.isSaved ? "Salvo" : "Salvar"}</span>
              </button>
            ) : null}

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
                updateDocument({
                  ...document,
                  markdown: event.target.value,
                })
              }
              aria-label="Conteúdo markdown da lousa"
            />
          ) : (
            <article className="mdc-chat-canvas__preview">
              <ChatMarkdown content={document.markdown} />
            </article>
          )}
        </div>
      </aside>
    </div>
  );
}
