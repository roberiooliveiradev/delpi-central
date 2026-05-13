import { Folder, MessageSquare } from "lucide-react";

import type { ChatProject, ChatSession } from "../../data/api/chatTypes";
import { ChatConversationListItem } from "./ChatConversationListItem";

import "./ChatProjectHome.css";

type ChatProjectHomeProps = {
  project: ChatProject;
  sessions: ChatSession[];
  onSelectSession: (session: ChatSession) => void;
};

export function ChatProjectHome({
  project,
  sessions,
  onSelectSession,
}: ChatProjectHomeProps) {
  const recentSessions = [...sessions]
    .sort((left, right) => {
      const leftDate = new Date(left.updated_at || left.created_at || 0).getTime();
      const rightDate = new Date(right.updated_at || right.created_at || 0).getTime();

      return rightDate - leftDate;
    })
    .slice(0, 8);

  return (
    <section className="mdc-chat-project-home" aria-label={`Projeto ${project.name}`}>
      <div className="mdc-chat-project-home__header">
        <span>
          <Folder size={20} aria-hidden="true" />
        </span>

        <div>
          <p className="mdc-chat-eyebrow">Projeto</p>
          <h2>{project.name}</h2>
          {project.description ? <p>{project.description}</p> : null}
        </div>
      </div>

      <div className="mdc-chat-project-home__composer-title">
        Novo chat em {project.name}
      </div>

      {recentSessions.length > 0 ? (
        <div className="mdc-chat-project-home__sessions">
          <div className="mdc-chat-project-home__tabs">
            <strong>Chats</strong>
            <span>Fontes</span>
          </div>

          <div className="mdc-chat-project-home__list">
            {recentSessions.map((session) => (
              <ChatConversationListItem
                key={session.id}
                session={session}
                variant="home"
                leading={<span className="mdc-chat-conversation-item__avatar">D</span>}
                trailing={<MessageSquare size={15} aria-hidden="true" />}
                onClick={() => onSelectSession(session)}
              />
            ))}
          </div>
        </div>
      ) : (
        <p className="mdc-chat-project-home__empty">
          Nenhuma conversa neste projeto ainda. Escreva abaixo para começar.
        </p>
      )}
    </section>
  );
}
