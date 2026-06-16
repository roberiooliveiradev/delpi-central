import { useEffect, useId, useState } from "react";
import { FileText } from "lucide-react";

import type { ConversationContextPick } from "../chatContextFromMessage";
import type { ContextItemPayload } from "../chatContextFromMessage";
import {
  workspaceFileContextBinaryLine,
  workspaceFileContextIngestLabels,
} from "../../content/workspaceFileIngestContent";
import { WorkspaceFileDropzone } from "./workspace-files/WorkspaceFileDropzone";
import { ChatModal } from "./shared/modal/ChatModal";

import "./ChatAddContextDialog.css";
import "./workspace-files/workspaceFileIngest.css";

export type UserContextPayload = ContextItemPayload;

type ChatAddContextDialogProps = {
  open: boolean;
  onCancel: () => void;
  onConfirm: (payload: UserContextPayload) => void;
  recentConversation?: ConversationContextPick[];
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
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
  getAccessToken,
}: ChatAddContextDialogProps) {
  const contextLabels = workspaceFileContextIngestLabels();
  const formId = useId();
  const [content, setContent] = useState("");
  const [filename, setFilename] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isReadingFile, setIsReadingFile] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);
  const [pendingPickId, setPendingPickId] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    setContent("");
    setFilename(null);
    setError(null);
    setIsReadingFile(false);
    setIsDragActive(false);
    setPendingPickId(null);
  }, [open]);

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
            workspaceFileContextBinaryLine(file.name, file.type || "binário");

          return merged.slice(0, MAX_CHARS);
        });
        setFilename(file.name);
      }
    } catch {
      setError(contextLabels.readError);
    } finally {
      setIsReadingFile(false);
    }
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    const trimmed = content.trim();

    if (!trimmed && !filename) {
      setError(contextLabels.emptySubmitError);
      return;
    }

    onConfirm({
      content: trimmed,
      filename: filename ?? undefined,
    });
  }

  return (
    <ChatModal
      open={open}
      onClose={onCancel}
      size="lg"
      ariaLabelledBy={`${formId}-title`}
      panelClassName="mdc-chat-add-context"
      backdropClassName="mdc-chat-add-context-backdrop"
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

        <WorkspaceFileDropzone
          compact
          disabled={isReadingFile}
          isBusy={isReadingFile}
          isDragActive={isDragActive}
          contentVariant="context"
          ingestFamily="context_paste"
          getAccessToken={getAccessToken}
          onDragActiveChange={setIsDragActive}
          onFilesSelected={(files) => {
            void ingestFiles(files);
          }}
        />

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
    </ChatModal>
  );
}
