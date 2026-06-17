import {
  ArrowLeft,
  ChevronRight,
  Folder,
  Pencil,
  Plus,
  Search,
  Settings,
  Trash2,
} from "lucide-react";
import { useMemo, useState } from "react";

import type { ChatAgent, ChatProject, ChatSession } from "../../data/api/chatTypes";
import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";
import { ChatProjectCreateModal } from "../components/workspace";
import { useConfirmDialog, usePromptDialog } from "../components/shared";
import "./ChatProjectsPage.css";

type ChatProjectsPageProps = {
  projects: ChatProject[];
  agents?: ChatAgent[];
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
  onConfigureProject?: (projectId: string) => void;
};

function getSessionCount(projectId: string, sessions: ChatSession[]): number {
  return sessions.filter((session) => session.project_id === projectId).length;
}

function formatAccessRole(role: string | null | undefined): string {
  switch (role) {
    case "owner":
      return "Proprietário";
    case "editor":
      return "Editor";
    case "viewer":
      return "Visualizador";
    default:
      return role?.trim() || "Membro";
  }
}

function canEditProject(role: string | null | undefined): boolean {
  return role === "owner" || role === "editor";
}

export function ChatProjectsPage({
  projects,
  agents = [],
  sessions = [],
  selectedProjectId,
  isLoading,
  onBack,
  onSelectProject,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
  onConfigureProject,
}: ChatProjectsPageProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const { prompt, dialog: promptDialog } = usePromptDialog();
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
    <ChatAnimatedPanel
      panelKey="projects-directory"
      variant="page"
      className="mdc-chat-page-panel--fill"
    >
    {confirmDialog}
    {promptDialog}
    <section
      className="mdc-chat-ws-directory mdc-chat-projects-page"
      aria-label="Projetos"
    >
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
          <div className="mdc-chat-ws-directory__empty mdc-chat-projects-page__empty">
            <Folder size={22} aria-hidden="true" />
            <strong>Nenhum projeto encontrado</strong>
            <p>
              {searchTerm.trim()
                ? "Ajuste a busca ou crie um novo projeto."
                : "Crie um projeto para agrupar chats, fontes e agentes."}
            </p>
            {!searchTerm.trim() ? (
              <button
                type="button"
                className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
                onClick={() => setIsCreateModalOpen(true)}
              >
                <Plus size={16} aria-hidden="true" />
                <span>Criar projeto</span>
              </button>
            ) : null}
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
                      <span className="mdc-chat-projects-page__role">
                        {formatAccessRole(project.access_role)}
                      </span>
                      {project.default_agent_id ? (
                        <span>
                          Agente:{" "}
                          {agents.find((agent) => agent.id === project.default_agent_id)?.name ??
                            project.default_agent_id}
                        </span>
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

                      {canEditProject(project.access_role) ? (
                        <>
                          <button
                            type="button"
                            className="mdc-chat-ws-toolbar-btn"
                            onClick={() => onConfigureProject?.(project.id)}
                          >
                            <Settings size={16} aria-hidden="true" />
                            <span>Configurar</span>
                          </button>

                          <button
                            type="button"
                            className="mdc-chat-ws-toolbar-btn"
                            onClick={() => {
                              void (async () => {
                                const nextName = await prompt({
                                  title: "Renomear projeto",
                                  label: "Nome do projeto",
                                  defaultValue: project.name,
                                  confirmLabel: "Salvar",
                                });

                                if (nextName && nextName !== project.name) {
                                  await onRenameProject?.(project.id, nextName);
                                }
                              })();
                            }}
                          >
                            <Pencil size={16} aria-hidden="true" />
                            <span>Renomear</span>
                          </button>
                        </>
                      ) : null}

                      {project.access_role === "owner" ? (
                        <button
                          type="button"
                          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--danger"
                          onClick={() => {
                            void confirm({
                              title: "Excluir projeto",
                              description: `Excluir o projeto "${project.name}"?`,
                              confirmLabel: "Excluir",
                              cancelLabel: "Cancelar",
                              danger: true,
                            }).then((confirmed) => {
                              if (confirmed) {
                                void onDeleteProject?.(project.id);
                              }
                            });
                          }}
                        >
                          <Trash2 size={16} aria-hidden="true" />
                          <span>Excluir</span>
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
    </ChatAnimatedPanel>
  );
}
