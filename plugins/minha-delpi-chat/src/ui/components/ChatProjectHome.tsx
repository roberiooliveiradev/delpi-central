import {
  Folder,
  MessageSquare,
  MoreHorizontal,
  Settings,
  Trash2,
  X,
} from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";

import type { ChatProject, ChatSession } from "../../data/api/chatTypes";
import { ChatConversationListItem } from "./ChatConversationListItem";

import "./ChatProjectHome.css";

type ChatProjectHomeProps = {
  project: ChatProject;
  sessions: ChatSession[];
  composer?: ReactNode;
  onSelectSession: (session: ChatSession) => void;
  onUpdateProject?: (
    projectId: string,
    payload: {
      name?: string;
      description?: string | null;
      instructions?: string | null;
      visibility?: string;
      archived?: boolean;
    },
  ) => Promise<ChatProject | null>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
  onClearProject?: () => void;
};

export function ChatProjectHome({
  project,
  sessions,
  composer,
  onSelectSession,
  onUpdateProject,
  onDeleteProject,
  onClearProject,
}: ChatProjectHomeProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || "");
  const [instructions, setInstructions] = useState(project.instructions || "");
  const [isSaving, setIsSaving] = useState(false);

  const recentSessions = [...sessions].sort((left, right) => {
    const leftDate = new Date(left.updated_at || left.created_at || 0).getTime();
    const rightDate = new Date(right.updated_at || right.created_at || 0).getTime();

    return rightDate - leftDate;
  });

  async function saveSettings() {
    setIsSaving(true);

    try {
      await onUpdateProject?.(project.id, {
        name: name.trim() || project.name,
        description: description.trim() || null,
        instructions: instructions.trim() || null,
      });

      setIsSettingsOpen(false);
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteProject() {
    const confirmed = window.confirm(
      `Excluir o projeto "${project.name}"? As conversas não serão excluídas agora, mas perderão o vínculo com este projeto se o backend aplicar essa regra.`,
    );

    if (!confirmed) {
      return;
    }

    const deleted = await onDeleteProject?.(project.id);

    if (deleted) {
      onClearProject?.();
    }
  }

  return (
    <section className="mdc-chat-project-home" aria-label={`Projeto ${project.name}`}>
      <div className="mdc-chat-project-home__topbar">
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

        <div className="mdc-chat-project-home__actions">
          <button
            type="button"
            aria-label="Opções do projeto"
            aria-expanded={isMenuOpen}
            onClick={() => setIsMenuOpen((current) => !current)}
          >
            <MoreHorizontal size={20} aria-hidden="true" />
          </button>

          {isMenuOpen ? (
            <div className="mdc-chat-project-home__menu">
              <button
                type="button"
                onClick={() => {
                  setIsMenuOpen(false);
                  setIsSettingsOpen(true);
                }}
              >
                <Settings size={18} aria-hidden="true" />
                <span>Configurações do projeto</span>
              </button>

              <button
                type="button"
                className="mdc-chat-project-home__danger"
                onClick={() => {
                  setIsMenuOpen(false);
                  void deleteProject();
                }}
              >
                <Trash2 size={18} aria-hidden="true" />
                <span>Excluir projeto</span>
              </button>
            </div>
          ) : null}
        </div>
      </div>

      {composer ? (
        <div className="mdc-chat-project-home__composer">{composer}</div>
      ) : null}

      <div className="mdc-chat-project-home__sessions">
        <div className="mdc-chat-project-home__tabs">
          <strong>Chats</strong>
          <span>Fontes</span>
        </div>

        {recentSessions.length > 0 ? (
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
        ) : (
          <p className="mdc-chat-project-home__empty">
            Nenhuma conversa neste projeto ainda. Escreva acima para começar.
          </p>
        )}
      </div>

      {isSettingsOpen ? (
        <div className="mdc-chat-project-settings-backdrop" role="presentation">
          <section
            className="mdc-chat-project-settings"
            role="dialog"
            aria-modal="true"
            aria-label="Configurações do projeto"
          >
            <header>
              <h3>Configurações do projeto</h3>
              <button
                type="button"
                onClick={() => setIsSettingsOpen(false)}
                aria-label="Fechar"
              >
                <X size={20} aria-hidden="true" />
              </button>
            </header>

            <label>
              <span>Nome do projeto</span>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>

            <label>
              <span>Descrição</span>
              <input
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Explique o objetivo deste projeto..."
              />
            </label>

            <label>
              <span>Instruções</span>
              <textarea
                value={instructions}
                onChange={(event) => setInstructions(event.target.value)}
                rows={5}
                placeholder="Defina o contexto e personalize como o assistente responde neste projeto."
              />
            </label>

            <footer>
              <button
                type="button"
                className="mdc-chat-project-home__danger-outline"
                onClick={() => void deleteProject()}
              >
                Excluir projeto
              </button>

              <button
                type="button"
                onClick={() => void saveSettings()}
                disabled={isSaving}
              >
                {isSaving ? "Salvando..." : "Salvar"}
              </button>
            </footer>
          </section>
        </div>
      ) : null}
    </section>
  );
}
