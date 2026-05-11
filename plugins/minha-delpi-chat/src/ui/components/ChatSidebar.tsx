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
  async function handleRenameSession(session: ChatSession) {
    const currentTitle = session.title || "Conversa sem título";
    const nextTitle = window.prompt("Novo nome da conversa:", currentTitle);

    if (nextTitle === null) {
      return;
    }

    const normalizedTitle = nextTitle.trim();

    if (!normalizedTitle || normalizedTitle === currentTitle) {
      return;
    }

    await onRenameSession(session.id, normalizedTitle);
  }

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
            <div
              key={session.id}
              className={
                session.id === activeSessionId
                  ? "mdc-chat-session-row mdc-chat-session-row--active"
                  : "mdc-chat-session-row"
              }
            >
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
                onClick={() => void handleRenameSession(session)}
                aria-label={`Renomear conversa ${session.title || "sem título"}`}
                title="Renomear conversa"
              >
                Renomear
              </button>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
