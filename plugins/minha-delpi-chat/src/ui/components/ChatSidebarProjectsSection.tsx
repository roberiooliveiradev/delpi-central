import {
  ChevronDown,
  ChevronRight,
  Folder,
  MessageSquare,
  Plus,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ChatProject, ChatSession } from "../../data/api/chatTypes";
import { ChatSidebarWorkspaceItem } from "./ChatSidebarWorkspaceItem";
import { formatSessionDate } from "./chatSidebarUtils";

const PROJECT_SESSION_LIMIT = 5;

type ChatSidebarProjectsSectionProps = {
  projects: ChatProject[];
  sessions: ChatSession[];
  selectedProjectId?: string | null;
  activeSessionId?: string;
  isLoading?: boolean;
  onSelectProject?: (projectId: string | null) => void;
  onSelectSession?: (session: ChatSession) => void;
  onNewProject: () => void;
};

export function ChatSidebarProjectsSection({
  projects,
  sessions,
  selectedProjectId,
  activeSessionId,
  isLoading,
  onSelectProject,
  onSelectSession,
  onNewProject,
}: ChatSidebarProjectsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showAllByProject, setShowAllByProject] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (selectedProjectId) {
      setIsExpanded(true);
    }
  }, [selectedProjectId]);

  const sessionsByProject = useMemo(() => {
    const map = new Map<string, ChatSession[]>();

    for (const session of sessions) {
      if (!session.project_id) {
        continue;
      }

      map.set(session.project_id, [...(map.get(session.project_id) ?? []), session]);
    }

    for (const [projectId, projectSessions] of map.entries()) {
      map.set(
        projectId,
        [...projectSessions].sort((left, right) => {
          const leftDate = new Date(left.updated_at || left.created_at || 0).getTime();
          const rightDate = new Date(right.updated_at || right.created_at || 0).getTime();

          return rightDate - leftDate;
        }),
      );
    }

    return map;
  }, [sessions]);

  function toggleShowAll(projectId: string) {
    setShowAllByProject((current) => ({
      ...current,
      [projectId]: !current[projectId],
    }));
  }

  return (
    <>
      <div className="mdc-chat-sidebar__section-title mdc-chat-sidebar__section-title--button">
        <button
          type="button"
          onClick={() => setIsExpanded((current) => !current)}
          aria-expanded={isExpanded}
        >
          {isExpanded ? (
            <ChevronDown size={13} aria-hidden="true" />
          ) : (
            <ChevronRight size={13} aria-hidden="true" />
          )}
          <span>Projetos</span>
        </button>

        <small>{projects.length}</small>
      </div>

      {isExpanded ? (
        <>
          <div className="mdc-chat-sidebar__project-new">
            <button type="button" onClick={onNewProject}>
              <Plus size={15} aria-hidden="true" />
              <span>Novo projeto</span>
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
              projects.map((project) => {
                const projectSessions = sessionsByProject.get(project.id) ?? [];
                const isProjectActive = project.id === selectedProjectId;
                const showAll = Boolean(showAllByProject[project.id]);
                const visibleSessions = showAll
                  ? projectSessions
                  : projectSessions.slice(0, PROJECT_SESSION_LIMIT);
                const hiddenCount = Math.max(
                  0,
                  projectSessions.length - PROJECT_SESSION_LIMIT,
                );

                return (
                  <div key={project.id} className="mdc-chat-sidebar-project-node">
                    <ChatSidebarWorkspaceItem
                      icon={Folder}
                      title={project.name}
                      subtitle={project.description || "Projeto de trabalho"}
                      active={isProjectActive}
                      onClick={() =>
                        onSelectProject?.(
                          project.id === selectedProjectId ? null : project.id,
                        )
                      }
                    />

                    {isProjectActive && projectSessions.length > 0 ? (
                      <div className="mdc-chat-sidebar-project-children">
                        {visibleSessions.map((session) => (
                          <button
                            key={session.id}
                            type="button"
                            className={
                              session.id === activeSessionId
                                ? "mdc-chat-sidebar-project-session mdc-chat-sidebar-project-session--active"
                                : "mdc-chat-sidebar-project-session"
                            }
                            onClick={() => onSelectSession?.(session)}
                          >
                            <MessageSquare size={13} aria-hidden="true" />

                            <span>
                              <strong>{session.title || "Conversa sem título"}</strong>
                              <small>
                                {session.context || "geral"}
                                {formatSessionDate(session.updated_at) ? (
                                  <> · {formatSessionDate(session.updated_at)}</>
                                ) : null}
                              </small>
                            </span>
                          </button>
                        ))}

                        {hiddenCount > 0 ? (
                          <button
                            type="button"
                            className="mdc-chat-sidebar-project-more"
                            onClick={() => toggleShowAll(project.id)}
                          >
                            {showAll ? "Mostrar menos" : `Mostrar mais ${hiddenCount}`}
                          </button>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                );
              })
            )}
          </div>
        </>
      ) : null}
    </>
  );
}
