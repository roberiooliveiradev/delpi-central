import { ArrowLeft, ChevronRight, Folder, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";

import type { ChatProject, ChatSession } from "../../data/api/chatTypes";
import { ChatProjectCreateModal } from "../components/ChatProjectCreateModal";
import "./ChatProjectsPage.css";

type ChatProjectsPageProps = {
  projects: ChatProject[];
  sessions?: ChatSession[];
  selectedProjectId?: string | null;
  isLoading?: boolean;
  onBack: () => void;
  onSelectProject?: (projectId: string) => void;
  onCreateProject?: (payload: {
    name: string;
    description?: string | null;
    instructions?: string | null;
  }) => Promise<ChatProject | null>;
  onRenameProject?: (projectId: string, name: string) => Promise<ChatProject | null>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
};

function getSessionCount(projectId: string, sessions: ChatSession[]): number {
  return sessions.filter((session) => session.project_id === projectId).length;
}

export function ChatProjectsPage({
  projects,
  sessions = [],
  selectedProjectId,
  isLoading,
  onBack,
  onSelectProject,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
}: ChatProjectsPageProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const filteredProjects = useMemo(() => {
    const normalized = searchTerm.trim().toLowerCase();

    if (!normalized) {
      return projects;
    }

    return projects.filter((project) =>
      [project.name, project.description, project.instructions]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalized),
    );
  }, [projects, searchTerm]);

  const orderedProjects = useMemo(() => {
    return [...filteredProjects].sort((left, right) => {
      const leftDate = new Date(left.updated_at || left.created_at || 0).getTime();
      const rightDate = new Date(right.updated_at || right.created_at || 0).getTime();

      return rightDate - leftDate;
    });
  }, [filteredProjects]);

  return (
    <section className="mdc-chat-ws-directory" aria-label="Projetos">
      <header className="mdc-chat-ws-topbar mdc-chat-ws-directory__topbar">
        <div className="mdc-chat-ws-topbar__start">
          <button type="button" className="mdc-chat-ws-topbar__back" onClick={onBack}>
            <ArrowLeft size={18} aria-hidden="true" />
            <span>Voltar ao chat</span>
          </button>
        </div>

        <div className="mdc-chat-ws-topbar__title mdc-chat-ws-directory__title">
          <Folder size={18} aria-hidden="true" />
          <span>Projetos</span>
        </div>

        <div className="mdc-chat-ws-topbar__actions">
          <button
            type="button"
            className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
            onClick={() => setIsCreateModalOpen(true)}
          >
            <Plus size={16} aria-hidden="true" />
            <span>Novo projeto</span>
          </button>
        </div>
      </header>

      <main className="mdc-chat-ws-directory__main">
        <div className="mdc-chat-ws-directory__toolbar">
          <p className="mdc-chat-ws-directory__lead">
            Organize conversas, fontes e agentes por contexto de trabalho.
          </p>

          <label className="mdc-chat-ws-directory__search">
            <Search size={17} aria-hidden="true" />
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Buscar projetos"
            />
          </label>
        </div>

        <div className="mdc-chat-ws-directory__meta-row">
          <span>{projects.length} projeto(s)</span>
        </div>

        {isLoading ? (
          <p className="mdc-chat-ws-empty">Carregando projetos...</p>
        ) : orderedProjects.length === 0 ? (
          <div className="mdc-chat-ws-directory__empty">
            <Folder size={22} aria-hidden="true" />
            <strong>Nenhum projeto encontrado</strong>
            <p>Crie um projeto para agrupar chats e fontes.</p>
          </div>
        ) : (
          <ul className="mdc-chat-ws-directory__list">
            {orderedProjects.map((project) => {
              const chatCount = getSessionCount(project.id, sessions);
              const isActive = project.id === selectedProjectId;

              return (
                <li key={project.id}>
                  <article
                    className={[
                      "mdc-chat-ws-directory__card",
                      isActive ? "mdc-chat-ws-directory__card--active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    <button
                      type="button"
                      className="mdc-chat-ws-directory__card-main"
                      onClick={() => onSelectProject?.(project.id)}
                    >
                      <span className="mdc-chat-ws-directory__card-icon">
                        <Folder size={18} aria-hidden="true" />
                      </span>
                      <span className="mdc-chat-ws-directory__card-copy">
                        <strong>{project.name}</strong>
                        <small>
                          {project.description?.trim() ||
                            "Projeto sem descrição"}
                        </small>
                      </span>
                      <ChevronRight size={16} aria-hidden="true" />
                    </button>

                    <div className="mdc-chat-ws-directory__card-meta">
                      <span>{chatCount} chat(s)</span>
                      <span>{project.access_role}</span>
                      {project.default_agent_key ? (
                        <span>Agente: {project.default_agent_key}</span>
                      ) : null}
                    </div>

                    <div className="mdc-chat-ws-directory__card-actions">
                      <button
                        type="button"
                        className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
                        onClick={() => onSelectProject?.(project.id)}
                      >
                        Abrir
                      </button>

                      {project.access_role === "owner" || project.access_role === "editor" ? (
                        <button
                          type="button"
                          className="mdc-chat-ws-toolbar-btn"
                          onClick={() => {
                            const nextName = window.prompt(
                              "Novo nome do projeto",
                              project.name,
                            )?.trim();

                            if (nextName && nextName !== project.name) {
                              void onRenameProject?.(project.id, nextName);
                            }
                          }}
                        >
                          Renomear
                        </button>
                      ) : null}

                      {project.access_role === "owner" ? (
                        <button
                          type="button"
                          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--danger"
                          onClick={() => {
                            const confirmed = window.confirm(
                              `Excluir o projeto "${project.name}"?`,
                            );

                            if (confirmed) {
                              void onDeleteProject?.(project.id);
                            }
                          }}
                        >
                          Excluir
                        </button>
                      ) : null}
                    </div>
                  </article>
                </li>
              );
            })}
          </ul>
        )}
      </main>

      <ChatProjectCreateModal
        open={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreateProject={onCreateProject}
        onSelectProject={(projectId) => {
          setIsCreateModalOpen(false);

          if (projectId) {
            onSelectProject?.(projectId);
          }
        }}
      />
    </section>
  );
}
