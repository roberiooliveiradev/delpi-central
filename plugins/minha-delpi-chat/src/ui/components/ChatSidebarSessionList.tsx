import { Archive, Check, X } from "lucide-react";
import { useMemo, useState } from "react";

import type { ChatSession } from "../../data/api/chatTypes";
import { ChatConversationListItem } from "./ChatConversationListItem";
import { ChatConversationMenu } from "./ChatConversationMenu";
import { type SessionGroup } from "./chatSidebarUtils";

const DEFAULT_VISIBLE_SESSIONS = 20;

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
  onOpenArchived?: () => void;
  hideTitle?: boolean;
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
  onOpenArchived,
  hideTitle,
}: ChatSidebarSessionListProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [openMenuSessionId, setOpenMenuSessionId] = useState<string | null>(null);
  const [showAllSessions, setShowAllSessions] = useState(false);

  const totalSessions = useMemo(
    () => groupedSessions.reduce((total, group) => total + group.sessions.length, 0),
    [groupedSessions],
  );

  const visibleGroups = useMemo(() => {
    if (showAllSessions || searchTerm.trim()) {
      return groupedSessions;
    }

    let remaining = DEFAULT_VISIBLE_SESSIONS;

    return groupedSessions
      .map((group) => {
        if (remaining <= 0) {
          return {
            ...group,
            sessions: [],
          };
        }

        const sessions = group.sessions.slice(0, remaining);
        remaining -= sessions.length;

        return {
          ...group,
          sessions,
        };
      })
      .filter((group) => group.sessions.length > 0);
  }, [groupedSessions, searchTerm, showAllSessions]);

  const visibleSessionsCount = useMemo(
    () => visibleGroups.reduce((total, group) => total + group.sessions.length, 0),
    [visibleGroups],
  );

  const hiddenSessionsCount = Math.max(0, totalSessions - visibleSessionsCount);

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
            <ChatConversationListItem
              session={{
                ...session,
                title: session.is_pinned
                  ? `📌 ${session.title || "Conversa sem título"}`
                  : session.title,
              }}
              active={session.id === activeSessionId}
              onClick={() => onSelectSession(session)}
            />

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
      {!hideTitle ? (
        <div className="mdc-chat-sidebar__section-title mdc-chat-sidebar__section-title--conversations">
          <span>Conversas</span>

          <div className="mdc-chat-sidebar__section-actions">
            <button
              type="button"
              onClick={onOpenArchived}
              aria-label="Abrir conversas arquivadas"
              title="Arquivadas"
            >
              <Archive size={13} aria-hidden="true" />
            </button>

            <small>{totalSessions}</small>
          </div>
        </div>
      ) : null}

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
          {visibleGroups.map((group) => (
            <section key={group.label} className="mdc-chat-session-group">
              <h3>{group.label}</h3>
              {group.sessions.map(renderSessionRow)}
            </section>
          ))}

          {hiddenSessionsCount > 0 ? (
            <button
              type="button"
              className="mdc-chat-sidebar-more-button mdc-chat-sidebar-more-button--sessions"
              onClick={() => setShowAllSessions((current) => !current)}
            >
              {showAllSessions
                ? "Mostrar menos"
                : `Mostrar mais ${hiddenSessionsCount}`}
            </button>
          ) : null}
        </div>
      )}
    </>
  );
}
