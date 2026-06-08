import {
  ChevronDown,
  ChevronRight,
  Plus,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ChatProject, ChatSession } from "../../data/api/chatTypes";
import { buildChatProjectHref, buildChatSessionHrefForSession } from "../../navigation/chatRoutes";
import { ChatConversationListItem } from "./ChatConversationListItem";
import { ChatProjectCard } from "./ChatProjectCard";
import { useConfirmDialog } from "./useConfirmDialog";
import { usePromptDialog } from "./usePromptDialog";

const PROJECT_SESSION_LIMIT = 5;
const PROJECT_LIST_LIMIT = 5;

type ChatSidebarProjectsSectionProps = {
  projects: ChatProject[];
  sessions: ChatSession[];
  selectedProjectId?: string | null;
  activeSessionId?: string;
  isLoading?: boolean;
  onSelectProject?: (projectId: string | null) => void;
  onSelectSession?: (session: ChatSession) => void;
  onOpenProjectsDirectory?: () => void;
  onNewProject: () => void;
  onRenameProject?: (projectId: string, name: string) => Promise<ChatProject | null>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
  isSessionProcessing?: (sessionId: string) => boolean;
};

export function ChatSidebarProjectsSection({
  projects,
  sessions,
  selectedProjectId,
  activeSessionId,
  isLoading,
  onSelectProject,
  onSelectSession: _onSelectSession,
  onOpenProjectsDirectory,
  onNewProject,
  onRenameProject,
  onDeleteProject,
  isSessionProcessing,
}: ChatSidebarProjectsSectionProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const { prompt, dialog: promptDialog } = usePromptDialog();
  const [isExpanded, setIsExpanded] = useState(true);
  const [showAllProjects, setShowAllProjects] = useState(false);
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

  const orderedProjects = useMemo(() => {
    return [...projects].sort((left, right) => {
      const leftSessionDate = sessionsByProject.get(left.id)?.[0]?.updated_at;
      const rightSessionDate = sessionsByProject.get(right.id)?.[0]?.updated_at;

      const leftDate = new Date(leftSessionDate || left.updated_at || left.created_at || 0).getTime();
      const rightDate = new Date(rightSessionDate || right.updated_at || right.created_at || 0).getTime();

      return rightDate - leftDate;
    });
  }, [projects, sessionsByProject]);

  const visibleProjects = showAllProjects
    ? orderedProjects
    : orderedProjects.slice(0, PROJECT_LIST_LIMIT);

  const hiddenProjectsCount = Math.max(0, orderedProjects.length - PROJECT_LIST_LIMIT);

  function toggleShowAll(projectId: string) {
    setShowAllByProject((current) => ({
      ...current,
      [projectId]: !current[projectId],
    }));
  }

  return (
    <>
      {confirmDialog}
      {promptDialog}
      <div className="mdc-chat-sidebar__section-title mdc-chat-sidebar__section-title--button">
        <div className="mdc-chat-sidebar__section-heading">
          <button
            type="button"
            className="mdc-chat-sidebar__section-chevron"
            onClick={() => setIsExpanded((current) => !current)}
            aria-expanded={isExpanded}
            aria-label={isExpanded ? "Recolher projetos" : "Expandir projetos"}
          >
            {isExpanded ? (
              <ChevronDown size={13} aria-hidden="true" />
            ) : (
              <ChevronRight size={13} aria-hidden="true" />
            )}
          </button>
          <button
            type="button"
            className="mdc-chat-sidebar__section-link"
            onClick={() => onOpenProjectsDirectory?.()}
          >
            Projetos
          </button>
        </div>

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
            {isLoading ? (
              <p className="mdc-chat-muted">Carregando projetos...</p>
            ) : projects.length === 0 ? (
              <p className="mdc-chat-muted">Nenhum projeto criado.</p>
            ) : (
              <>
                {visibleProjects.map((project) => {
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
                      <ChatProjectCard
                        project={project}
                        active={isProjectActive}
                        href={buildChatProjectHref(project.id)}
                        onSelect={() => onSelectProject?.(project.id)}
                        onRename={() => {
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
                        onOpenSettings={() => onSelectProject?.(project.id)}
                        onDelete={() => {
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
                      />

                      {isProjectActive && projectSessions.length > 0 ? (
                        <div className="mdc-chat-sidebar-project-children">
                          {visibleSessions.map((session) => (
                            <ChatConversationListItem
                              key={session.id}
                              session={session}
                              variant="project"
                              active={session.id === activeSessionId}
                              isProcessing={isSessionProcessing?.(session.id) ?? false}
                              href={buildChatSessionHrefForSession(session)}
                            />
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
                })}

                {hiddenProjectsCount > 0 ? (
                  <button
                    type="button"
                    className="mdc-chat-sidebar-project-more mdc-chat-sidebar-project-more--root"
                    onClick={() => setShowAllProjects((current) => !current)}
                  >
                    {showAllProjects
                      ? "Mostrar menos"
                      : `Mostrar mais ${hiddenProjectsCount}`}
                  </button>
                ) : null}
              </>
            )}
          </div>
        </>
      ) : null}
    </>
  );
}
