import {
  ArrowUpRight,
  Bot,
  Folder,
  Loader2,
  Pencil,
  Settings,
  Trash2,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";

import type {
  ChatAgent,
  ChatProject,
  ChatSession,
  ChatWorkspaceSource,
} from "../../../data/api/chatTypes";
import { ChatAnimatedPanel } from "../shared/ChatAnimatedPanel";
import { useConfirmDialog, usePromptDialog } from "../shared";
import { buildChatSessionHrefForSession } from "../../../navigation/chatRoutes";
import { ChatConversationMenu } from "../shell/ChatConversationMenu";
import { formatSessionDate } from "../shell/chatSidebarUtils";
import { ChatProjectSettingsModal } from "./ChatProjectSettingsModal";
import {
  workspaceFileKindLabel,
  workspaceFileProjectIngestLabels,
  workspaceFileSourceIndexPresentation,
} from "../../../content/workspaceFileIngestContent";
import { formatAttachmentSize } from "../../chatAttachmentPreview";
import {
  buildWorkspaceSourcePreviewTarget,
  useWorkspaceFilePreviewModal,
} from "../../hooks/useWorkspaceFilePreviewModal";
import { IngestProgressIndicator } from "../shared/IngestProgressIndicator";
import { DropdownMenuTrigger } from "../shared/menus/DropdownMenuTrigger";
import { WorkspaceFileCard } from "./WorkspaceFileCard";
import { WorkspaceFileDropzone } from "./WorkspaceFileDropzone";

import "./ChatProjectHome.css";
import "./workspaceFileIngest.css";

type ProjectTab = "chats" | "sources" | "agents";

function getSessionInitials(session: ChatSession): string {
  const title = (session.title || "C").trim();
  const words = title.split(/\s+/).filter(Boolean);

  if (words.length >= 2) {
    return `${words[0][0] ?? ""}${words[1][0] ?? ""}`.toUpperCase();
  }

  return title.slice(0, 2).toUpperCase();
}

function formatSourceDate(value: string | null | undefined): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleDateString("pt-BR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

type ChatProjectHomeProps = {
  project: ChatProject;
  sessions: ChatSession[];
  agents?: ChatAgent[];
  contextAgentId?: string | null;
  sources?: ChatWorkspaceSource[];
  isLoadingSources?: boolean;
  activeSessionId?: string;
  composer?: ReactNode;
  onSelectSession: (session: ChatSession) => void;
  onRenameSession?: (sessionId: string, title: string) => Promise<ChatSession | null>;
  onDeleteSession?: (sessionId: string) => Promise<boolean>;
  onPinSession?: (sessionId: string) => Promise<ChatSession | null>;
  onUnpinSession?: (sessionId: string) => Promise<ChatSession | null>;
  onUpdateProject?: (
    projectId: string,
    payload: {
      name?: string;
      description?: string | null;
      instructions?: string | null;
      defaultAgentId?: string | null;
      visibility?: string;
      shareConversationContext?: boolean;
      archived?: boolean;
    },
  ) => Promise<ChatProject | null>;
  onUseAgent?: (agentId: string | null) => void;
  onOpenAgentPage?: (agentId: string) => void;
  onSetDefaultAgent?: (agentId: string | null) => Promise<ChatProject | null>;
  onUploadSource?: (file: File) => Promise<ChatWorkspaceSource>;
  onCreateTextSource?: (payload: { title: string; content: string; metadata?: Record<string, unknown> | null }) => Promise<ChatWorkspaceSource>;
  onDeleteSource?: (sourceId: string) => Promise<void>;
  onDownloadSource?: (sourceId: string) => Promise<void>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
  onClearProject?: () => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  compact?: boolean;
  settingsOpen?: boolean;
  onSettingsOpenChange?: (open: boolean) => void;
  isSessionProcessing?: (sessionId: string) => boolean;
};

export function ChatProjectHome({
  project,
  sessions,
  agents = [],
  contextAgentId,
  sources = [],
  isLoadingSources,
  activeSessionId,
  composer,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
  onPinSession,
  onUnpinSession,
  onUpdateProject,
  onUseAgent,
  onOpenAgentPage,
  onSetDefaultAgent,
  onUploadSource,
  onCreateTextSource,
  onDeleteSource,
  onDownloadSource,
  onDeleteProject,
  onClearProject,
  getAccessToken,
  compact,
  settingsOpen = false,
  onSettingsOpenChange,
  isSessionProcessing,
}: ChatProjectHomeProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const { prompt, dialog: promptDialog } = usePromptDialog();
  const [activeTab, setActiveTab] = useState<ProjectTab>("chats");
  const [openSessionMenuId, setOpenSessionMenuId] = useState<string | null>(null);
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceContent, setSourceContent] = useState("");
  const [isSavingSource, setIsSavingSource] = useState(false);
  const [isSourceDragActive, setIsSourceDragActive] = useState(false);
  const [uploadSourceError, setUploadSourceError] = useState<string | null>(null);
  const projectIngestLabels = workspaceFileProjectIngestLabels();
  const { openPreview, previewModal } = useWorkspaceFilePreviewModal({ getAccessToken });

  function closeSettings() {
    onSettingsOpenChange?.(false);
  }

  function openSettings() {
    onSettingsOpenChange?.(true);
  }

  const defaultAgent = agents.find((agent) => agent.id === project.default_agent_id);
  const contextAgent = agents.find((agent) => agent.id === contextAgentId);

  const recentSessions = [...sessions].sort((left, right) => {
    const leftDate = new Date(left.updated_at || left.created_at || 0).getTime();
    const rightDate = new Date(right.updated_at || right.created_at || 0).getTime();

    return rightDate - leftDate;
  });

  async function uploadSourceFile(file: File | null | undefined) {
    if (!file) {
      return;
    }

    setIsSavingSource(true);
    setUploadSourceError(null);

    try {
      await onUploadSource?.(file);
    } catch (error) {
      setUploadSourceError(
        error instanceof Error
          ? error.message
          : workspaceFileProjectIngestLabels().emptyState,
      );
    } finally {
      setIsSavingSource(false);
    }
  }

  async function createTextSource() {
    const title = sourceTitle.trim() || "Nota do projeto";
    const content = sourceContent.trim();

    if (!content) {
      return;
    }

    setIsSavingSource(true);

    try {
      await onCreateTextSource?.({
        title,
        content,
        metadata: {
          source: "project_note",
        },
      });

      setSourceTitle("");
      setSourceContent("");
    } finally {
      setIsSavingSource(false);
    }
  }

  async function renameProject() {
    const nextName = await prompt({
      title: "Renomear projeto",
      label: "Nome do projeto",
      defaultValue: project.name,
      confirmLabel: "Salvar",
    });

    if (!nextName || nextName === project.name) {
      return;
    }

    await onUpdateProject?.(project.id, {
      name: nextName,
    });
  }

  async function deleteProject() {
    const confirmed = await confirm({
      title: "Excluir projeto",
      description: `Excluir o projeto "${project.name}"?`,
      confirmLabel: "Excluir",
      cancelLabel: "Cancelar",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    const deleted = await onDeleteProject?.(project.id);

    if (deleted) {
      onClearProject?.();
    }
  }

  async function renameSession(session: ChatSession) {
    const nextTitle = await prompt({
      title: "Renomear conversa",
      label: "Título da conversa",
      defaultValue: session.title || "Conversa sem título",
      confirmLabel: "Salvar",
    });

    if (!nextTitle || nextTitle === session.title) {
      return;
    }

    await onRenameSession?.(session.id, nextTitle);
  }

  async function deleteSession(session: ChatSession) {
    const confirmed = await confirm({
      title: "Excluir conversa",
      description: `Excluir a conversa "${session.title || "sem título"}"?`,
      confirmLabel: "Excluir",
      cancelLabel: "Cancelar",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    await onDeleteSession?.(session.id);
  }

  const projectMenuItems = [
    {
      id: "settings",
      label: "Configurações do projeto",
      icon: <Settings size={18} aria-hidden="true" />,
      onSelect: () => openSettings(),
    },
    {
      id: "rename",
      label: "Renomear",
      icon: <Pencil size={18} aria-hidden="true" />,
      onSelect: () => {
        void renameProject();
      },
    },
    {
      id: "delete",
      label: "Excluir projeto",
      icon: <Trash2 size={18} aria-hidden="true" />,
      variant: "danger" as const,
      onSelect: () => {
        void deleteProject();
      },
    },
  ];

  return (
    <section
      className={
        compact
          ? "mdc-chat-project-home mdc-chat-project-home--compact"
          : "mdc-chat-project-home"
      }
      aria-label={`Projeto ${project.name}`}
    >
      {confirmDialog}
      {promptDialog}
      <header className="mdc-chat-project-home__hero">
        <div className="mdc-chat-project-home__hero-title">
          <span
            className="mdc-chat-project-home__icon"
            style={
              project.color
                ? {
                    backgroundColor: `color-mix(in srgb, ${project.color} 18%, transparent)`,
                    color: project.color,
                  }
                : undefined
            }
          >
            {project.icon?.trim() && project.icon.trim().length <= 3 ? (
              project.icon.trim()
            ) : (
              <Folder size={22} aria-hidden="true" />
            )}
          </span>
          <h1>{project.name}</h1>
        </div>

        <div className="mdc-chat-project-home__hero-actions">
          <DropdownMenuTrigger
            items={projectMenuItems}
            menuLabel="Opções do projeto"
            ariaLabel="Opções do projeto"
            iconSize={20}
            triggerClassName="mdc-chat-project-home__hero-menu-trigger"
          />
        </div>
      </header>

      {composer ? (
        <div className="mdc-chat-project-home__composer">{composer}</div>
      ) : null}

      <div className="mdc-chat-project-home__workspace">
        <div className="mdc-chat-project-home__toolbar">
        <div className="mdc-chat-project-home__tabs" role="tablist" aria-label="Áreas do projeto">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "chats"}
            className={activeTab === "chats" ? "is-active" : undefined}
            onClick={() => setActiveTab("chats")}
          >
            Chats
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "sources"}
            className={activeTab === "sources" ? "is-active" : undefined}
            onClick={() => setActiveTab("sources")}
          >
            Fontes
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "agents"}
            className={activeTab === "agents" ? "is-active" : undefined}
            onClick={() => setActiveTab("agents")}
          >
            Agentes
          </button>
        </div>
        </div>

        <ChatAnimatedPanel
          panelKey={activeTab}
          variant="tab"
          className="mdc-chat-project-home__tab-panel"
        >
        {activeTab === "chats" ? (
          <div className="mdc-chat-project-home__sessions" role="tabpanel">
            {recentSessions.length > 0 ? (
              <div className="mdc-chat-project-home__list">
                {recentSessions.map((session) => (
                  <div
                    key={session.id}
                    className={
                      session.id === activeSessionId
                        ? "mdc-chat-project-chat-row mdc-chat-project-chat-row--active"
                        : "mdc-chat-project-chat-row"
                    }
                  >
                    <a
                      href={buildChatSessionHrefForSession(session)}
                      className="mdc-chat-project-chat-row__link"
                      onClick={(event) => {
                        event.preventDefault();
                        onSelectSession(session);
                      }}
                    >
                      <span className="mdc-chat-project-chat-row__avatar">
                        {getSessionInitials(session)}
                      </span>

                      <span className="mdc-chat-project-chat-row__copy">
                        <strong>{session.title || "Conversa sem título"}</strong>
                        <small>
                          {session.context?.trim() ||
                            (session.agent_id
                              ? `Agente: ${
                                  agents.find((agent) => agent.id === session.agent_id)?.name ??
                                  session.agent_id
                                }`
                              : "Conversa neste projeto")}
                        </small>
                      </span>

                      <span className="mdc-chat-project-chat-row__meta">
                        {isSessionProcessing?.(session.id) ? (
                          <Loader2
                            size={14}
                            className="mdc-chat-project-chat-row__spinner"
                            aria-hidden="true"
                          />
                        ) : null}
                        <time className="mdc-chat-project-chat-row__date">
                          {formatSessionDate(session.updated_at)}
                        </time>
                      </span>
                    </a>

                    <div className="mdc-chat-project-chat-row__menu">
                      <ChatConversationMenu
                        open={openSessionMenuId === session.id}
                        onOpenChange={(open) =>
                          setOpenSessionMenuId(open ? session.id : null)
                        }
                        onRename={() => void renameSession(session)}
                        pinLabel={session.is_pinned ? "Desfixar chat" : "Fixar chat"}
                        onPin={() =>
                          session.is_pinned
                            ? void onUnpinSession?.(session.id)
                            : void onPinSession?.(session.id)
                        }
                        archiveLabel="Arquivar"
                        onDelete={() => void deleteSession(session)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mdc-chat-project-home__empty">
                Nenhuma conversa neste projeto ainda. Escreva acima para começar.
              </p>
            )}
          </div>
        ) : activeTab === "agents" ? (
          <div className="mdc-chat-project-agents" role="tabpanel">
            {contextAgent ? (
              <div className="mdc-chat-project-agents__context">
                <span>
                  Usando <strong>{contextAgent.name}</strong> neste contexto
                </span>
                <button type="button" onClick={() => onUseAgent?.(null)}>
                  Remover
                </button>
              </div>
            ) : null}

            {defaultAgent ? (
              <div className="mdc-chat-project-agents__default">
                <ShieldCheck size={18} aria-hidden="true" />
                <span>Agente padrão do projeto: <strong>{defaultAgent.name}</strong></span>
                <button type="button" onClick={() => void onSetDefaultAgent?.(null)}>
                  Remover padrão
                </button>
              </div>
            ) : (
              <div className="mdc-chat-project-agents__default">
                <ShieldCheck size={18} aria-hidden="true" />
                <span>Este projeto ainda não possui agente padrão.</span>
              </div>
            )}

            <div className="mdc-chat-project-agents__list">
              {agents.length > 0 ? (
                agents.map((agent) => {
                  const isDefault = agent.id === project.default_agent_id;
                  const isContext = agent.id === contextAgentId;

                  return (
                    <article
                      key={agent.id}
                      className={
                        isContext
                          ? "mdc-chat-project-agent-card mdc-chat-project-agent-card--active"
                          : "mdc-chat-project-agent-card"
                      }
                    >
                      <span className="mdc-chat-project-agent-card__icon">
                        <Bot size={18} aria-hidden="true" />
                      </span>

                      <div>
                        <strong>{agent.name}</strong>
                        <p>{agent.description || agent.category || "Agente configurável"}</p>

                        <div>
                          {isDefault ? <em>Padrão</em> : null}
                          {isContext ? <em>Em uso neste contexto</em> : null}
                          <em>{agent.visibility === "public" ? "Público" : "Privado"}</em>
                        </div>
                      </div>

                      <footer>
                        <button type="button" onClick={() => onUseAgent?.(agent.id)}>
                          Usar neste projeto
                        </button>

                        <button
                          type="button"
                          onClick={() => void onSetDefaultAgent?.(agent.id)}
                          disabled={isDefault}
                        >
                          {isDefault ? "Padrão" : "Definir padrão"}
                        </button>

                        <button
                          type="button"
                          onClick={() => onOpenAgentPage?.(agent.id)}
                          title={`Abrir página de ${agent.name}`}
                        >
                          <ArrowUpRight size={15} aria-hidden="true" />
                          <span>Abrir</span>
                        </button>
                      </footer>
                    </article>
                  );
                })
              ) : (
                <p className="mdc-chat-project-home__empty">
                  Nenhum agente disponível para este projeto.
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="mdc-chat-project-sources" role="tabpanel">
            <WorkspaceFileDropzone
              disabled={isSavingSource}
              isBusy={isSavingSource}
              isDragActive={isSourceDragActive}
              contentVariant="project"
              ingestFamily="project_source"
              getAccessToken={getAccessToken}
              onDragActiveChange={setIsSourceDragActive}
              onFilesSelected={(files) => {
                void uploadSourceFile(files[0]);
              }}
            />

            {isSavingSource ? (
              <IngestProgressIndicator label={projectIngestLabels.uploadingStatus} />
            ) : null}

            {uploadSourceError ? (
              <p className="mdc-chat-project-sources__error" role="alert">
                {uploadSourceError}
              </p>
            ) : null}

            {isLoadingSources ? (
              <p className="mdc-chat-project-home__empty">{projectIngestLabels.loadingSources}</p>
            ) : sources.length > 0 ? (
              <div
                className="mdc-chat-project-source-list"
                aria-label={projectIngestLabels.listAriaLabel}
              >
                {sources.map((source) => {
                  const sourceDate = formatSourceDate(source.updated_at || source.created_at);
                  const label = source.original_filename || source.title || "Arquivo";
                  const indexStatus = workspaceFileSourceIndexPresentation(source);
                  const sizeBytes = source.metadata?.sizeBytes;
                  const sizeLabel =
                    typeof sizeBytes === "number" ? formatAttachmentSize(sizeBytes) : undefined;

                  return (
                    <WorkspaceFileCard
                      key={source.id}
                      variant="row"
                      filename={label}
                      iconTone="brand"
                      kindLabel={workspaceFileKindLabel(label)}
                      sizeLabel={sizeLabel}
                      statusLabel={indexStatus.statusLabel}
                      statusTone={indexStatus.statusTone}
                      secondaryLabel={sourceDate || undefined}
                      previewKind="file"
                      editable
                      onPreview={() => {
                        openPreview(buildWorkspaceSourcePreviewTarget(source));
                      }}
                      onDownload={
                        onDownloadSource
                          ? () => {
                              void onDownloadSource(source.id);
                            }
                          : undefined
                      }
                      onRemove={() => {
                        void onDeleteSource?.(source.id);
                      }}
                    />
                  );
                })}
              </div>
            ) : (
              <p className="mdc-chat-project-home__empty">{projectIngestLabels.emptyState}</p>
            )}

            <details className="mdc-chat-project-sources__note">
              <summary>Adicionar nota de texto</summary>
              <div className="mdc-chat-project-source-note">
                <input
                  value={sourceTitle}
                  onChange={(event) => setSourceTitle(event.target.value)}
                  placeholder="Título da nota"
                />
                <textarea
                  value={sourceContent}
                  onChange={(event) => setSourceContent(event.target.value)}
                  placeholder="Cole aqui regras, contexto ou conhecimento do projeto..."
                  rows={4}
                />
                <button
                  type="button"
                  className="mdc-chat-project-sources__ghost"
                  disabled={isSavingSource || !sourceContent.trim()}
                  onClick={() => void createTextSource()}
                >
                  Adicionar nota
                </button>
              </div>
            </details>
          </div>
        )}
        </ChatAnimatedPanel>
      </div>

      <ChatProjectSettingsModal
        project={project}
        open={settingsOpen}
        onClose={closeSettings}
        onUpdateProject={onUpdateProject}
        onDeleteProject={onDeleteProject}
        onClearProject={onClearProject}
        getAccessToken={getAccessToken}
      />

      {previewModal}
    </section>
  );
}
