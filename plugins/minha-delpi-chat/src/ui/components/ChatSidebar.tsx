import { Check, Pencil, Plus, X } from "lucide-react";
import { useState } from "react";

import type { ChatSession } from "../../data/api/chatTypes";

type ChatSidebarProps = {
  sessions: ChatSession[];
  activeSessionId?: string;
  isLoading?: boolean;
  onNewSession: () => void;
  onSelectSession: (session: ChatSession) => void;
  onRenameSession: (sessionId: string, title: string) => Promise<ChatSession | null>;
};

export function ChatSidebar({
  sessions,
  activeSessionId,
  isLoading,
  onNewSession,
  onSelectSession,
  onRenameSession,
}: ChatSidebarProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  function startEditingSession(session: ChatSession) {
    setEditingSessionId(session.id);
    setEditingTitle(session.title || "");
  }

  function cancelEditingSession() {
    setEditingSessionId(null);
    setEditingTitle("");
  }

  async function saveEditingSession(session: ChatSession) {
    const normalizedTitle = editingTitle.trim();
    const currentTitle = session.title || "";

    if (!normalizedTitle || normalizedTitle === currentTitle) {
      cancelEditingSession();
      return;
    }

    const updated = await onRenameSession(session.id, normalizedTitle);

    if (updated) {
      cancelEditingSession();
    }
  }

  return (
    <aside className="mdc-chat-sidebar" aria-label="Conversas">
      <div className="mdc-chat-sidebar__header">
        <div>
          <p className="mdc-chat-eyebrow">Conversas</p>
          <h2>Histórico</h2>
        </div>

        <button
          type="button"
          className="mdc-chat-icon-button"
          onClick={onNewSession}
          aria-label="Nova conversa"
          title="Nova conversa"
        >
          <Plus size={18} aria-hidden="true" />
        </button>
      </div>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando sessões...</p>
      ) : sessions.length === 0 ? (
        <p className="mdc-chat-muted">Nenhuma conversa criada ainda.</p>
      ) : (
        <div className="mdc-chat-session-list">
          {sessions.map((session) => {
            const isEditing = editingSessionId === session.id;

            return (
              <div
                key={session.id}
                className={
                  session.id === activeSessionId
                    ? "mdc-chat-session-row mdc-chat-session-row--active"
                    : "mdc-chat-session-row"
                }
              >
                {isEditing ? (
                  <div className="mdc-chat-session-edit-card">
                    <input
                      className="mdc-chat-session-edit-input"
                      value={editingTitle}
                      autoFocus
                      maxLength={120}
                      onChange={(event) => setEditingTitle(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          void saveEditingSession(session);
                        }

                        if (event.key === "Escape") {
                          event.preventDefault();
                          cancelEditingSession();
                        }
                      }}
                      aria-label="Nome da conversa"
                    />

                    <div className="mdc-chat-session-edit-actions">
                      <button
                        type="button"
                        className="mdc-chat-session-action"
                        onClick={() => void saveEditingSession(session)}
                        aria-label="Salvar nome da conversa"
                        title="Salvar"
                      >
                        <Check size={15} aria-hidden="true" />
                      </button>

                      <button
                        type="button"
                        className="mdc-chat-session-action"
                        onClick={cancelEditingSession}
                        aria-label="Cancelar edição"
                        title="Cancelar"
                      >
                        <X size={15} aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      className="mdc-chat-session"
                      onClick={() => onSelectSession(session)}
                    >
                      <span>{session.title || "Conversa sem título"}</span>
                      <small>{session.context || "geral"}</small>
                    </button>

                    <button
                      type="button"
                      className="mdc-chat-session-action"
                      onClick={() => startEditingSession(session)}
                      aria-label={`Renomear conversa ${
                        session.title || "sem título"
                      }`}
                      title="Renomear conversa"
                    >
                      <Pencil size={15} aria-hidden="true" />
                    </button>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </aside>
  );
}
