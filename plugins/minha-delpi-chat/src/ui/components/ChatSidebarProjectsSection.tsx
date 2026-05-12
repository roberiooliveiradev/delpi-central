import { Folder, Settings } from "lucide-react";

import type { ChatProject } from "../../data/api/chatTypes";
import { ChatSidebarWorkspaceItem } from "./ChatSidebarWorkspaceItem";

type ChatSidebarProjectsSectionProps = {
  projects: ChatProject[];
  selectedProjectId?: string | null;
  isLoading?: boolean;
  onSelectProject?: (projectId: string | null) => void;
  onManageProjects: () => void;
};

export function ChatSidebarProjectsSection({
  projects,
  selectedProjectId,
  isLoading,
  onSelectProject,
  onManageProjects,
}: ChatSidebarProjectsSectionProps) {
  return (
    <>
      <div className="mdc-chat-sidebar__section-title">
        <span>Projetos</span>
        <small>{projects.length}</small>
      </div>

      <div className="mdc-chat-sidebar__project-manage">
        <button type="button" onClick={onManageProjects}>
          <Settings size={15} aria-hidden="true" />
          <span>Gerenciar projetos</span>
        </button>
      </div>

      <div className="mdc-chat-sidebar__link-list">
        <ChatSidebarWorkspaceItem
          icon={Folder}
          title="Todos os projetos"
          subtitle="Conversas sem filtro de projeto"
          active={!selectedProjectId}
          onClick={() => onSelectProject?.(null)}
        />

        {isLoading ? (
          <p className="mdc-chat-muted">Carregando projetos...</p>
        ) : projects.length === 0 ? (
          <p className="mdc-chat-muted">Nenhum projeto criado.</p>
        ) : (
          projects.map((project) => (
            <ChatSidebarWorkspaceItem
              key={project.id}
              icon={Folder}
              title={project.name}
              subtitle={project.description || "Projeto de trabalho"}
              active={project.id === selectedProjectId}
              onClick={() =>
                onSelectProject?.(
                  project.id === selectedProjectId ? null : project.id,
                )
              }
            />
          ))
        )}
      </div>
    </>
  );
}
