import { Check, X } from "lucide-react";
import { useState } from "react";

import type { ChatSession } from "../../data/api/chatTypes";
import { ChatConversationMenu } from "./ChatConversationMenu";
import { formatSessionDate, type SessionGroup } from "./chatSidebarUtils";

type ChatSidebarSessionListProps = {
  groupedSessions: SessionGroup[];
  activeSessionId?: string;
  isLoading?: boolean;
  searchTerm: string;
  selectedProjectName?: string | null;
  onSelectSession: (session: ChatSession) => void;
  onRenameSession: (sessionId: string, title: string) => Promise<ChatSession | null>;
  onDeleteSessionRequest: (session: ChatSession) => void;
  onPinSession?: (sessionId: string) => Promise<ChatSession | null>;
  onUnpinSession?: (sessionId: string) => Promise<ChatSession | null>;
  onArchiveSession?: (sessionId: string) => Promise<ChatSession | null>;
};

export function ChatSidebarSessionList({
  groupedSessions,
  activeSessionId,
  isLoading,
  searchTerm,
  selectedProjectName,
  onSelectSession,
  onRenameSession,
  onDeleteSessionRequest,
  onPinSession,
  onUnpinSession,
  onArchiveSession,
}: ChatSidebarSessionListProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [openMenuSessionId, setOpenMenuSessionId] = useState<string | null>(null);

  function startEditingSession(session: ChatSession) {
    setEditingSessionId(session.id);
    setEditingTitle(session.title || "");
  }

  function cancelEditingSession() {
    setEditingSessionId(null);
    setEditingTitle("");
  }

  function handleShareSession(session: ChatSession) {
    const title = session.title || "Conversa sem título";
    void navigator.clipboard?.writeText(title);
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

  function renderSessionRow(session: ChatSession) {
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
              <span>
                {session.is_pinned ? "📌 " : ""}
                {session.title || "Conversa sem título"}
              </span>
              <small>
                {session.context || "geral"}
                {formatSessionDate(session.updated_at) ? (
                  <> · {formatSessionDate(session.updated_at)}</>
                ) : null}
              </small>
            </button>

            <div className="mdc-chat-session-actions">
              <ChatConversationMenu
                open={openMenuSessionId === session.id}
                onOpenChange={(open) =>
                  setOpenMenuSessionId(open ? session.id : null)
                }
                onShare={() => handleShareSession(session)}
                onRename={() => startEditingSession(session)}
                pinLabel={session.is_pinned ? "Desafixar chat" : "Fixar chat"}
                archiveLabel="Arquivar"
                onPin={
                  session.is_pinned
                    ? () => void onUnpinSession?.(session.id)
                    : () => void onPinSession?.(session.id)
                }
                onArchive={() => void onArchiveSession?.(session.id)}
                onDelete={() => onDeleteSessionRequest(session)}
              />
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <>
      <div className="mdc-chat-sidebar__section-title">
        <span>
          {selectedProjectName ? `Conversas · ${selectedProjectName}` : "Conversas"}
        </span>
        <small>
          {groupedSessions.reduce((total, group) => total + group.sessions.length, 0)}
        </small>
      </div>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando sessões...</p>
      ) : groupedSessions.length === 0 ? (
        <p className="mdc-chat-muted">
          {searchTerm
            ? "Nenhuma conversa encontrada."
            : selectedProjectName
              ? "Nenhuma conversa neste projeto ainda."
              : "Nenhuma conversa criada ainda."}
        </p>
      ) : (
        <div className="mdc-chat-session-list">
          {groupedSessions.map((group) => (
            <section key={group.label} className="mdc-chat-session-group">
              <h3>{group.label}</h3>
              {group.sessions.map(renderSessionRow)}
            </section>
          ))}
        </div>
      )}
    </>
  );
}
