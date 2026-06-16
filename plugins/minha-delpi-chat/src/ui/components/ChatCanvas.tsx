import { Check, Copy, Download, Edit3, Eye, Maximize2, Minimize2, Save, X } from "lucide-react";
import { useState } from "react";
import { ChatMarkdown } from "./ChatMarkdown";

import { ChatModal } from "./shared/modal/ChatModal";
import "./ChatCanvas.css";

export type ChatCanvasDocument = {
  id?: string;
  messageId?: string | null;
  title: string;
  markdown: string;
  version?: number | null;
  documentType?: string | null;
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

  function downloadCanvasMarkdown() {
    const safeTitle = (document.title || "lousa")
      .trim()
      .replace(/[^\w\-]+/g, "_")
      .slice(0, 80);
    const blob = new Blob([document.markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = window.document.createElement("a");
    link.href = url;
    link.download = `${safeTitle || "lousa"}.md`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function updateDocument(next: ChatCanvasDocument) {
    onChange?.({
      ...next,
      isSaved: false,
    });
  }

  const isPreview = mode === "preview";

  return (
    <ChatModal
      open
      onClose={() => onClose?.()}
      size="none"
      panelClassName={
        expanded
          ? "mdc-chat-canvas mdc-chat-canvas--expanded"
          : "mdc-chat-canvas"
      }
      backdropClassName="mdc-chat-canvas-backdrop"
      ariaLabel="Lousa do Chat DELPI"
    >
      <header className="mdc-chat-canvas__header">
        <div className="mdc-chat-canvas__title-area">
          <p className="mdc-chat-eyebrow">
            Lousa
            {typeof document.version === "number" && document.version > 0
              ? ` · v${document.version}`
              : null}
            {document.documentType ? ` · ${document.documentType}` : null}
          </p>
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

        <div className="mdc-chat-canvas__actions" aria-label="Ações da lousa">
          {onSave ? (
            <button
              type="button"
              className={
                document.isSaved
                  ? "mdc-chat-canvas__action mdc-chat-canvas__action--text mdc-chat-canvas__action--success"
                  : "mdc-chat-canvas__action mdc-chat-canvas__action--text"
              }
              onClick={() => void onSave(document)}
              disabled={document.isSaving}
              title={document.isSaved ? "Lousa salva" : "Salvar lousa"}
            >
              {document.isSaved ? (
                <Check size={16} aria-hidden="true" />
              ) : (
                <Save size={16} aria-hidden="true" />
              )}
              <span>
                {document.isSaving ? "Salvando..." : document.isSaved ? "Salvo" : "Salvar"}
              </span>
            </button>
          ) : null}

          <button
            type="button"
            className="mdc-chat-canvas__action mdc-chat-canvas__action--text"
            onClick={() =>
              setMode((current) => (current === "edit" ? "preview" : "edit"))
            }
            title={isPreview ? "Editar lousa" : "Visualizar prévia"}
          >
            {isPreview ? (
              <Edit3 size={16} aria-hidden="true" />
            ) : (
              <Eye size={16} aria-hidden="true" />
            )}
            <span>{isPreview ? "Editar" : "Prévia"}</span>
          </button>

          <button
            type="button"
            className="mdc-chat-canvas__action mdc-chat-canvas__action--icon"
            onClick={copyCanvas}
            title="Copiar markdown"
            aria-label="Copiar markdown"
          >
            <Copy size={16} aria-hidden="true" />
          </button>

          <button
            type="button"
            className="mdc-chat-canvas__action mdc-chat-canvas__action--icon"
            onClick={downloadCanvasMarkdown}
            title="Baixar markdown"
            aria-label="Baixar markdown"
          >
            <Download size={16} aria-hidden="true" />
          </button>

          <button
            type="button"
            className="mdc-chat-canvas__action mdc-chat-canvas__action--icon"
            onClick={() => setExpanded((current) => !current)}
            title={expanded ? "Reduzir" : "Expandir"}
            aria-label={expanded ? "Reduzir lousa" : "Expandir lousa"}
          >
            {expanded ? (
              <Minimize2 size={16} aria-hidden="true" />
            ) : (
              <Maximize2 size={16} aria-hidden="true" />
            )}
          </button>

          <button
            type="button"
            className="mdc-chat-canvas__action mdc-chat-canvas__action--icon"
            onClick={() => onClose?.()}
            title="Fechar"
            aria-label="Fechar lousa"
          >
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
    </ChatModal>
  );
}
