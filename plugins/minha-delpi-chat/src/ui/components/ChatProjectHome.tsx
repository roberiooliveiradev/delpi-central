import {
  ArrowUpRight,
  Bot,
  Copy,
  Download,
  FileText,
  Folder,
  Loader2,
  MoreHorizontal,
  Pencil,
  Plus,
  Settings,
  Trash2,
  X,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  listChatProjectShares,
  revokeChatProjectShare,
  shareChatProject,
} from "../../data/api/chatApi";
import type {
  ChatAgent,
  ChatProject,
  ChatProjectShare,
  ChatSession,
  ChatWorkspaceSource,
} from "../../data/api/chatTypes";
import { ChatAnimatedPanel } from "./ChatAnimatedPanel";
import { useConfirmDialog } from "./useConfirmDialog";
import { ChatUserSearchField } from "./ChatUserSearchField";
import { buildChatProjectHref, buildChatSessionHrefForSession } from "../../navigation/chatRoutes";
import { handleChatNavClick } from "../../navigation/chatNavigation";
import { ChatConversationMenu } from "./ChatConversationMenu";
import { formatSessionDate } from "./chatSidebarUtils";

import { ModalPortal } from "./ModalPortal";
import "./ChatProjectHome.css";

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
  const [activeTab, setActiveTab] = useState<ProjectTab>("chats");
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [openSessionMenuId, setOpenSessionMenuId] = useState<string | null>(null);
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || "");
  const [instructions, setInstructions] = useState(project.instructions || "");
  const [isSaving, setIsSaving] = useState(false);
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceContent, setSourceContent] = useState("");
  const [isSavingSource, setIsSavingSource] = useState(false);
  const [projectShares, setProjectShares] = useState<ChatProjectShare[]>([]);
  const [shareTargetUserId, setShareTargetUserId] = useState("");
  const [shareRole, setShareRole] = useState<"viewer" | "editor">("viewer");
  const [isSharingProject, setIsSharingProject] = useState(false);
  const [isLoadingShares, setIsLoadingShares] = useState(false);
  const [shareMessage, setShareMessage] = useState<string | null>(null);
  const [revokingShareUserId, setRevokingShareUserId] = useState<string | null>(null);
  const [projectLinkCopied, setProjectLinkCopied] = useState(false);
  const projectUsagePath = useMemo(
    () => buildChatProjectHref(project.id),
    [project.id],
  );
  const projectUsageUrl = useMemo(() => {
    if (typeof window === "undefined") {
      return projectUsagePath;
    }

    return `${window.location.origin}${projectUsagePath}`;
  }, [projectUsagePath]);

  function closeSettings() {
    onSettingsOpenChange?.(false);
  }

  function openSettings() {
    onSettingsOpenChange?.(true);
  }

  async function copyProjectUsageLink() {
    try {
      await navigator.clipboard.writeText(projectUsageUrl);
      setProjectLinkCopied(true);
      window.setTimeout(() => setProjectLinkCopied(false), 1800);
    } catch {
      setShareMessage("Não foi possível copiar o link do projeto.");
    }
  }

  useEffect(() => {
    setName(project.name);
    setDescription(project.description || "");
    setInstructions(project.instructions || "");
  }, [project.description, project.instructions, project.name]);

  const loadProjectShares = useCallback(async () => {
    if (!getAccessToken || project.access_role !== "owner") {
      setProjectShares([]);
      return;
    }

    setIsLoadingShares(true);

    try {
      const shares = await listChatProjectShares(project.id, { getAccessToken });
      setProjectShares(shares);
    } catch {
      setProjectShares([]);
    } finally {
      setIsLoadingShares(false);
    }
  }, [getAccessToken, project.access_role, project.id]);

  useEffect(() => {
    if (settingsOpen) {
      void loadProjectShares();
    }
  }, [settingsOpen, loadProjectShares]);

  async function shareCurrentProject() {
    if (project.access_role !== "owner" || !getAccessToken) {
      return;
    }

    const targetUserId = shareTargetUserId.trim();

    if (!targetUserId) {
      setShareMessage("Selecione um usuário para compartilhar.");
      return;
    }

    setIsSharingProject(true);
    setShareMessage(null);

    try {
      await shareChatProject(
        project.id,
        { targetUserId, role: shareRole },
        { getAccessToken },
      );
      setShareMessage("Projeto compartilhado com sucesso.");
      setShareTargetUserId("");
      await loadProjectShares();
    } catch {
      setShareMessage("Não foi possível compartilhar o projeto.");
    } finally {
      setIsSharingProject(false);
    }
  }

  async function revokeProjectShare(targetUserId: string) {
    if (!getAccessToken) {
      return;
    }

    setRevokingShareUserId(targetUserId);

    try {
      await revokeChatProjectShare(project.id, targetUserId, { getAccessToken });
      setShareMessage("Acesso revogado.");
      await loadProjectShares();
    } catch {
      setShareMessage("Não foi possível revogar o acesso.");
    } finally {
      setRevokingShareUserId(null);
    }
  }

  const defaultAgent = agents.find((agent) => agent.id === project.default_agent_id);
  const contextAgent = agents.find((agent) => agent.id === contextAgentId);

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

      closeSettings();
    } finally {
      setIsSaving(false);
    }
  }


  async function uploadSourceFile(file: File | null | undefined) {
    if (!file) {
      return;
    }

    setIsSavingSource(true);

    try {
      await onUploadSource?.(file);
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
    const nextName = window.prompt("Novo nome do projeto", project.name)?.trim();

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
    const nextTitle = window.prompt(
      "Novo título da conversa",
      session.title || "Conversa sem título",
    )?.trim();

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
                  openSettings();
                }}
              >
                <Settings size={18} aria-hidden="true" />
                <span>Configurações do projeto</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setIsMenuOpen(false);
                  void renameProject();
                }}
              >
                <Pencil size={18} aria-hidden="true" />
                <span>Renomear</span>
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
            <label className="mdc-chat-project-sources__add">
              <Plus size={16} aria-hidden="true" />
              <span>{isSavingSource ? "Enviando..." : "Adicionar fontes"}</span>
              <input
                type="file"
                disabled={isSavingSource}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  void uploadSourceFile(file);
                  event.target.value = "";
                }}
              />
            </label>

            {isLoadingSources ? (
              <p className="mdc-chat-project-home__empty">Carregando fontes...</p>
            ) : sources.length > 0 ? (
              <div className="mdc-chat-project-source-list">
                {sources.map((source) => (
                  <article key={source.id} className="mdc-chat-project-source-row">
                    <span className="mdc-chat-project-source-row__icon">
                      <FileText size={18} aria-hidden="true" />
                    </span>
                    <div className="mdc-chat-project-source-row__copy">
                      <strong>{source.title}</strong>
                      <small>
                        Arquivo
                        {formatSourceDate(source.updated_at || source.created_at)
                          ? ` · ${formatSourceDate(source.updated_at || source.created_at)}`
                          : ""}
                      </small>
                    </div>
                    <div className="mdc-chat-project-source-row__actions">
                      {onDownloadSource ? (
                        <button
                          type="button"
                          onClick={() => void onDownloadSource(source.id)}
                          title="Baixar arquivo"
                          aria-label={`Baixar ${source.title}`}
                        >
                          <Download size={16} aria-hidden="true" />
                        </button>
                      ) : null}
                      <button
                        type="button"
                        onClick={() => void onDeleteSource?.(source.id)}
                        title="Remover fonte"
                        aria-label={`Remover ${source.title}`}
                      >
                        <Trash2 size={16} aria-hidden="true" />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="mdc-chat-project-home__empty">
                Nenhuma fonte adicionada. Use o botão acima para enviar arquivos.
              </p>
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

      {settingsOpen ? (
        <ModalPortal>
        <div
          className="mdc-chat-project-settings-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeSettings();
            }
          }}
        >
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
                onClick={closeSettings}
                aria-label="Fechar"
              >
                <X size={20} aria-hidden="true" />
              </button>
            </header>

            <label className="mdc-chat-project-settings__field">
              <span>Nome do projeto</span>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>

            <label className="mdc-chat-project-settings__field">
              <span>Descrição</span>
              <input
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Explique o objetivo deste projeto..."
              />
            </label>

            <label className="mdc-chat-project-settings__field">
              <span>Instruções</span>
              <textarea
                value={instructions}
                onChange={(event) => setInstructions(event.target.value)}
                rows={6}
                placeholder="Defina o contexto e personalize como o assistente responde neste projeto."
              />
              <small className="mdc-chat-project-settings__help">
                O projeto só usa estas instruções nas conversas deste espaço.
              </small>
            </label>

            <div className="mdc-chat-project-settings__link">
              <span className="mdc-chat-project-settings__link-label">Link de uso</span>
              <div className="mdc-chat-project-settings__link-row">
                <a
                  href={projectUsagePath}
                  onClick={(event) => handleChatNavClick(event, projectUsagePath)}
                >
                  {projectUsageUrl}
                </a>
                <button
                  type="button"
                  className="mdc-chat-ws-outline-btn"
                  onClick={() => void copyProjectUsageLink()}
                  title="Copiar link do projeto"
                >
                  <Copy size={15} aria-hidden="true" />
                  <span>{projectLinkCopied ? "Copiado" : "Copiar"}</span>
                </button>
              </div>
              <small>Mesma URL usada ao abrir o projeto no chat.</small>
            </div>

            {project.access_role === "owner" ? (
              <section className="mdc-chat-project-settings__share">
                <h4>Compartilhamento</h4>
                <p className="mdc-chat-muted">
                  Conceda acesso de visualização ou edição a outro usuário.
                </p>

                <div className="mdc-chat-project-settings__share-form">
                  <ChatUserSearchField
                    value={shareTargetUserId}
                    onChange={setShareTargetUserId}
                    getAccessToken={getAccessToken}
                    disabled={isSharingProject}
                  />

                  <label>
                    <span>Papel</span>
                    <select
                      value={shareRole}
                      onChange={(event) =>
                        setShareRole(event.target.value as "viewer" | "editor")
                      }
                    >
                      <option value="viewer">Visualizador</option>
                      <option value="editor">Editor</option>
                    </select>
                  </label>
                </div>

                <button
                  type="button"
                  className="mdc-chat-ws-outline-btn mdc-chat-project-settings__share-btn"
                  disabled={isSharingProject}
                  onClick={() => void shareCurrentProject()}
                >
                  <span>
                    {isSharingProject ? "Compartilhando..." : "Compartilhar projeto"}
                  </span>
                </button>

                {shareMessage ? <p className="mdc-chat-muted">{shareMessage}</p> : null}

                <div className="mdc-chat-project-settings__share-list">
                  {isLoadingShares ? (
                    <p className="mdc-chat-muted">Carregando compartilhamentos...</p>
                  ) : projectShares.length === 0 ? (
                    <p className="mdc-chat-muted">Nenhum compartilhamento ativo.</p>
                  ) : (
                    projectShares.map((share) => (
                      <article key={share.id}>
                        <span>
                          <strong>
                            {share.target_user_name ||
                              share.target_user_email ||
                              share.target_user_id}
                          </strong>
                          <small>
                            {share.target_user_email
                              ? `${share.target_user_email} · ${share.role}`
                              : share.role}
                          </small>
                        </span>
                        <button
                          type="button"
                          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--danger"
                          disabled={revokingShareUserId === share.target_user_id}
                          onClick={() => void revokeProjectShare(share.target_user_id)}
                        >
                          {revokingShareUserId === share.target_user_id
                            ? "Revogando..."
                            : "Revogar"}
                        </button>
                      </article>
                    ))
                  )}
                </div>
              </section>
            ) : null}

            <footer className="mdc-chat-project-settings__footer">
              <button
                type="button"
                className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--danger"
                onClick={() => void deleteProject()}
              >
                <span>Excluir projeto?</span>
              </button>

              <button
                type="button"
                className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
                onClick={() => void saveSettings()}
                disabled={isSaving}
              >
                <span>{isSaving ? "Salvando..." : "Salvar"}</span>
              </button>
            </footer>
          </section>
        </div>
        </ModalPortal>
      ) : null}
    </section>
  );
}
