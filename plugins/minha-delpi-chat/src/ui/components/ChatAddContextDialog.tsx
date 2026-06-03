import { useEffect, useId, useRef, useState } from "react";
import { FileText, Upload } from "lucide-react";

import type { ConversationContextPick } from "../chatContextFromMessage";
import type { ContextItemPayload } from "../chatContextFromMessage";

import { ModalPortal } from "./ModalPortal";
import "./ChatAddContextDialog.css";

export type UserContextPayload = ContextItemPayload;

type ChatAddContextDialogProps = {
  open: boolean;
  onCancel: () => void;
  onConfirm: (payload: UserContextPayload) => void;
  recentConversation?: ConversationContextPick[];
};

const MAX_CHARS = 12_000;
const TEXT_EXTENSIONS = /\.(txt|md|csv|tsv|json)$/i;

async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(new Error("Não foi possível ler o arquivo."));
    reader.readAsText(file);
  });
}

export function ChatAddContextDialog({
  open,
  onCancel,
  onConfirm,
  recentConversation = [],
}: ChatAddContextDialogProps) {
  const formId = useId();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [content, setContent] = useState("");
  const [filename, setFilename] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isReadingFile, setIsReadingFile] = useState(false);
  const [pendingPickId, setPendingPickId] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    setContent("");
    setFilename(null);
    setError(null);
    setIsReadingFile(false);
    setPendingPickId(null);
  }, [open]);

  if (!open) {
    return null;
  }

  async function ingestFiles(files: FileList | File[]) {
    const list = Array.from(files);

    if (!list.length) {
      return;
    }

    const file = list[0];
    setIsReadingFile(true);
    setError(null);

    try {
      if (TEXT_EXTENSIONS.test(file.name)) {
        const text = await readFileAsText(file);
        setContent((current) => (current ? `${current}\n\n${text}` : text).slice(0, MAX_CHARS));
        setFilename(file.name);
      } else {
        setContent((current) => {
          const merged =
            (current ? `${current}\n\n` : "") +
            `Arquivo de contexto: ${file.name} (${file.type || "binário"})`;

          return merged.slice(0, MAX_CHARS);
        });
        setFilename(file.name);
      }
    } catch {
      setError("Não foi possível ler o arquivo selecionado.");
    } finally {
      setIsReadingFile(false);
    }
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    const trimmed = content.trim();

    if (!trimmed && !filename) {
      setError("Cole texto, uma tabela ou anexe um arquivo.");
      return;
    }

    onConfirm({
      content: trimmed,
      filename: filename ?? undefined,
    });
  }

  return (
    <ModalPortal>
      <div
        className="mdc-chat-add-context-backdrop"
        role="presentation"
        onMouseDown={(event) => {
          if (event.target === event.currentTarget) {
            onCancel();
          }
        }}
      >
        <section
          className="mdc-chat-add-context"
          role="dialog"
          aria-modal="true"
          aria-labelledby={`${formId}-title`}
        >
          <header className="mdc-chat-add-context__header">
            <h2 id={`${formId}-title`}>Adicionar ao contexto</h2>
            <p>
              Cole texto, tabela ou arquivo — ou escolha uma pergunta ou resposta da conversa. O
              sistema classifica e usa nas próximas respostas.
            </p>
          </header>

          <form id={formId} className="mdc-chat-add-context__form" onSubmit={handleSubmit}>
            {recentConversation.length > 0 ? (
              <div className="mdc-chat-add-context__conversation">
                <span className="mdc-chat-add-context__conversation-label">Da conversa</span>
                <ul className="mdc-chat-add-context__conversation-list">
                  {recentConversation.map((pick) => (
                    <li key={`${pick.role}:${pick.id}`}>
                      <button
                        type="button"
                        className="mdc-chat-add-context__conversation-item"
                        disabled={pendingPickId !== null}
                        onClick={() => {
                          if (pendingPickId) {
                            return;
                          }

                          setPendingPickId(pick.id);
                          onConfirm({
                            content: pick.content,
                            role: pick.role,
                            messageId: pick.id,
                            kind: pick.role === "assistant" ? "answer" : "question",
                          });
                        }}
                      >
                        <span
                          className={`mdc-chat-add-context__conversation-role mdc-chat-add-context__conversation-role--${pick.role}`}
                        >
                          {pick.role === "assistant" ? "Resposta" : "Pergunta"}
                        </span>
                        <span className="mdc-chat-add-context__conversation-preview">
                          {pick.preview}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <label className="mdc-chat-add-context__field">
              <span>Conteúdo</span>
              <textarea
                value={content}
                rows={7}
                maxLength={MAX_CHARS}
                placeholder={
                  "Ex.: produto 10080001, filial 01\n" +
                  "Ou cole uma tabela, regras, e-mail, SQL, resumo de reunião…"
                }
                autoFocus
                onChange={(event) => {
                  setContent(event.target.value);
                  setError(null);
                }}
              />
            </label>

            {filename ? (
              <p className="mdc-chat-add-context__file-hint">
                <FileText size={14} aria-hidden /> {filename}
              </p>
            ) : null}

            <div
              className="mdc-chat-add-context__dropzone"
              onDragOver={(event) => {
                event.preventDefault();
              }}
              onDrop={(event) => {
                event.preventDefault();

                if (event.dataTransfer.files.length > 0) {
                  void ingestFiles(event.dataTransfer.files);
                }
              }}
            >
              <Upload size={18} aria-hidden />
              <p>Arraste um arquivo ou</p>
              <button
                type="button"
                className="mdc-chat-add-context__link"
                disabled={isReadingFile}
                onClick={() => fileInputRef.current?.click()}
              >
                selecione do computador
              </button>
              <input
                ref={fileInputRef}
                type="file"
                hidden
                accept=".txt,.md,.csv,.tsv,.json,text/plain,text/markdown"
                onChange={(event) => {
                  const files = event.target.files;

                  if (files && files.length > 0) {
                    void ingestFiles(files);
                  }

                  event.target.value = "";
                }}
              />
            </div>

            {error ? <p className="mdc-chat-add-context__error">{error}</p> : null}

            <footer className="mdc-chat-add-context__actions">
              <button type="button" className="mdc-chat-add-context__secondary" onClick={onCancel}>
                Cancelar
              </button>
              <button
                type="submit"
                className="mdc-chat-add-context__primary"
                disabled={isReadingFile}
              >
                Adicionar
              </button>
            </footer>
          </form>
        </section>
      </div>
    </ModalPortal>
  );
}
