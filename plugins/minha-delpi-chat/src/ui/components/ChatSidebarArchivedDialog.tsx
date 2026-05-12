import { X } from "lucide-react";

import type { ChatSession } from "../../data/api/chatTypes";
import { formatSessionDate } from "./chatSidebarUtils";

type ChatSidebarArchivedDialogProps = {
  open: boolean;
  archivedSessions: ChatSession[];
  isLoading?: boolean;
  onClose: () => void;
  onRestoreSession: (session: ChatSession) => void;
};

export function ChatSidebarArchivedDialog({
  open,
  archivedSessions,
  isLoading,
  onClose,
  onRestoreSession,
}: ChatSidebarArchivedDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div
      className="mdc-chat-archived-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        className="mdc-chat-archived-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mdc-chat-archived-title"
      >
        <header>
          <div>
            <h2 id="mdc-chat-archived-title">Conversas arquivadas</h2>
            <p>Restaure uma conversa para voltar ao histórico principal.</p>
          </div>

          <button type="button" onClick={onClose} aria-label="Fechar">
            <X size={17} aria-hidden="true" />
          </button>
        </header>

        {isLoading ? (
          <p className="mdc-chat-muted">Carregando arquivadas...</p>
        ) : archivedSessions.length === 0 ? (
          <p className="mdc-chat-muted">Nenhuma conversa arquivada.</p>
        ) : (
          <div className="mdc-chat-archived-list">
            {archivedSessions.map((session) => (
              <article key={session.id} className="mdc-chat-archived-item">
                <div>
                  <strong>{session.title || "Conversa sem título"}</strong>
                  <small>
                    Arquivada em{" "}
                    {session.archived_at
                      ? formatSessionDate(session.archived_at)
                      : "data não informada"}
                  </small>
                </div>

                <button type="button" onClick={() => onRestoreSession(session)}>
                  Restaurar
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
