import type { ChatSession } from "../../data/api/chatTypes";

type ChatSidebarProps = {
  sessions: ChatSession[];
  activeSessionId?: string;
  isLoading?: boolean;
  onNewSession: () => void;
  onSelectSession: (session: ChatSession) => void;
};

export function ChatSidebar({
  sessions,
  activeSessionId,
  isLoading,
  onNewSession,
  onSelectSession,
}: ChatSidebarProps) {
  return (
    <aside className="mdc-chat-sidebar" aria-label="Conversas">
      <div className="mdc-chat-sidebar__header">
        <div>
          <p className="mdc-chat-eyebrow">Conversas</p>
          <h2>Histórico</h2>
        </div>

        <button type="button" onClick={onNewSession}>
          Nova
        </button>
      </div>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando sessões...</p>
      ) : sessions.length === 0 ? (
        <p className="mdc-chat-muted">Nenhuma conversa criada ainda.</p>
      ) : (
        <div className="mdc-chat-session-list">
          {sessions.map((session) => (
            <button
              key={session.id}
              type="button"
              className={
                session.id === activeSessionId
                  ? "mdc-chat-session mdc-chat-session--active"
                  : "mdc-chat-session"
              }
              onClick={() => onSelectSession(session)}
            >
              <span>{session.title || "Conversa sem título"}</span>
              <small>{session.context || "geral"}</small>
            </button>
          ))}
        </div>
      )}
    </aside>
  );
}
