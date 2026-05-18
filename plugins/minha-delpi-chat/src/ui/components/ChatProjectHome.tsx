import {
  ArrowUpRight,
  Bot,
  Database,
  FileText,
  Folder,
  MoreHorizontal,
  Pencil,
  Pin,
  Plus,
  Settings,
  Trash2,
  Upload,
  X,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";

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
import { ChatUserSearchField } from "./ChatUserSearchField";
import { ChatConversationListItem } from "./ChatConversationListItem";
import { ChatConversationMenu } from "./ChatConversationMenu";
import { formatSessionDate } from "./chatSidebarUtils";

import { ModalPortal } from "./ModalPortal";
import "./ChatProjectHome.css";

type ProjectTab = "chats" | "sources" | "agents";

type ChatProjectHomeProps = {
  project: ChatProject;
  sessions: ChatSession[];
  agents?: ChatAgent[];
  contextAgentKey?: string | null;
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
      defaultAgentKey?: string | null;
      visibility?: string;
      archived?: boolean;
    },
  ) => Promise<ChatProject | null>;
  onUseAgent?: (agentKey: string | null) => void;
  onOpenAgentPage?: (agentKey: string) => void;
  onSetDefaultAgent?: (agentKey: string | null) => Promise<ChatProject | null>;
  onUploadSource?: (file: File) => Promise<ChatWorkspaceSource>;
  onCreateTextSource?: (payload: { title: string; content: string; metadata?: Record<string, unknown> | null }) => Promise<ChatWorkspaceSource>;
  onDeleteSource?: (sourceId: string) => Promise<void>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
  onClearProject?: () => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  compact?: boolean;
  settingsRequestKey?: number;
};

export function ChatProjectHome({
  project,
  sessions,
  agents = [],
  contextAgentKey,
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
  onDeleteProject,
  onClearProject,
  getAccessToken,
  compact,
  settingsRequestKey,
}: ChatProjectHomeProps) {
  const [activeTab, setActiveTab] = useState<ProjectTab>("chats");
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
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

  useEffect(() => {
    setName(project.name);
    setDescription(project.description || "");
    setInstructions(project.instructions || "");
  }, [project.description, project.instructions, project.name]);

  useEffect(() => {
    if (settingsRequestKey) {
      setIsSettingsOpen(true);
    }
  }, [settingsRequestKey]);

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
    if (isSettingsOpen) {
      void loadProjectShares();
    }
  }, [isSettingsOpen, loadProjectShares]);

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

  const defaultAgent = agents.find((agent) => agent.key === project.default_agent_key);
  const contextAgent = agents.find((agent) => agent.key === contextAgentKey);

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
    const confirmed = window.confirm(`Excluir o projeto "${project.name}"?`);

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
    const confirmed = window.confirm(
      `Excluir a conversa "${session.title || "sem título"}"?`,
    );

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
      <div className="mdc-chat-project-home__topbar">
        <div className="mdc-chat-project-home__header">
          <span>
            <Folder size={20} aria-hidden="true" />
          </span>

          <div>
            <p className="mdc-chat-eyebrow">Projeto</p>
            <h2>{project.name}</h2>

            <div className="mdc-chat-project-home__meta">
              <span>{project.visibility === "public" ? "Público" : "Privado"}</span>
              <span>{recentSessions.length} chats</span>
              <span>{sources.length} fontes</span>
              {defaultAgent ? (
                <span>Agente padrão: {defaultAgent.name}</span>
              ) : (
                <span>Sem agente padrão</span>
              )}
              {contextAgent ? <span>Usando: {contextAgent.name}</span> : null}
            </div>

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
                  void renameProject();
                }}
              >
                <Pencil size={18} aria-hidden="true" />
                <span>Renomear</span>
              </button>

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

      <div className="mdc-chat-project-home__workspace">
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

        {activeTab === "chats" ? (
          <div className="mdc-chat-project-home__sessions" role="tabpanel">
            {recentSessions.length > 0 ? (
              <div className="mdc-chat-project-home__list">
                {recentSessions.map((session) => (
                  <div
                    key={session.id}
                    className={
                      session.id === activeSessionId
                        ? "mdc-chat-project-home-session-row mdc-chat-project-home-session-row--active"
                        : "mdc-chat-project-home-session-row"
                    }
                  >
                    <ChatConversationListItem
                      session={session}
                      variant="home"
                      leading={
                        <span className="mdc-chat-conversation-item__avatar">
                          D
                        </span>
                      }
                      trailing={
                        <span className="mdc-chat-project-home-session-date">
                          {formatSessionDate(session.updated_at)}
                        </span>
                      }
                      onClick={() => onSelectSession(session)}
                    />

                    <div className="mdc-chat-project-home-session-actions">
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
            <div className="mdc-chat-project-agents__hero">
              <span>
                <Bot size={26} aria-hidden="true" />
              </span>

              <div>
                <h3>Agentes do projeto</h3>
                <p>
                  Escolha um agente para usar neste projeto ou defina um agente
                  padrão para novas conversas.
                </p>
              </div>

              {contextAgent ? (
                <button
                  type="button"
                  onClick={() => onUseAgent?.(null)}
                  title="Remover agente do contexto atual"
                >
                  <X size={16} aria-hidden="true" />
                  <span>Remover agente atual</span>
                </button>
              ) : null}
            </div>

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
                  const isDefault = agent.key === project.default_agent_key;
                  const isContext = agent.key === contextAgentKey;

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
                        <button type="button" onClick={() => onUseAgent?.(agent.key)}>
                          Usar neste projeto
                        </button>

                        <button
                          type="button"
                          onClick={() => void onSetDefaultAgent?.(agent.key)}
                          disabled={isDefault}
                        >
                          {isDefault ? "Padrão" : "Definir padrão"}
                        </button>

                        <button
                          type="button"
                          onClick={() => onOpenAgentPage?.(agent.key)}
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
            <div className="mdc-chat-project-sources__hero">
              <span>
                <FileText size={26} aria-hidden="true" />
              </span>

              <div>
                <h3>Fontes do projeto</h3>
                <p>
                  Adicione arquivos e notas para que o assistente use como contexto
                  exclusivo deste projeto.
                </p>
              </div>

              <label className="mdc-chat-project-source-upload">
                <Upload size={16} aria-hidden="true" />
                <span>{isSavingSource ? "Enviando..." : "Enviar arquivo"}</span>
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
            </div>

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
                disabled={isSavingSource || !sourceContent.trim()}
                onClick={() => void createTextSource()}
              >
                <Plus size={16} aria-hidden="true" />
                <span>Adicionar nota</span>
              </button>
            </div>

            {isLoadingSources ? (
              <p className="mdc-chat-project-home__empty">Carregando fontes...</p>
            ) : sources.length > 0 ? (
              <div className="mdc-chat-project-source-list">
                {sources.map((source) => (
                  <article key={source.id} className="mdc-chat-project-source-card">
                    <span>
                      <FileText size={18} aria-hidden="true" />
                    </span>
                    <div>
                      <strong>{source.title}</strong>
                      <small>
                        {source.original_filename ||
                          source.source_ref ||
                          source.source_type}
                        {typeof source.chunk_count === "number"
                          ? ` · ${source.chunk_count} trecho(s)`
                          : ""}
                      </small>
                    </div>
                    <button
                      type="button"
                      onClick={() => void onDeleteSource?.(source.id)}
                      title="Remover fonte"
                    >
                      <Trash2 size={16} aria-hidden="true" />
                    </button>
                  </article>
                ))}
              </div>
            ) : (
              <div className="mdc-chat-project-sources__empty">
                <div>
                  <FileText size={22} aria-hidden="true" />
                </div>

                <strong>Nenhuma fonte adicionada</strong>
                <p>
                  Arquivos e notas adicionados aqui serão usados apenas neste projeto.
                </p>
              </div>
            )}

            <div className="mdc-chat-project-sources__rules">
              <h4>Como as fontes serão usadas</h4>

              <ul>
                <li>
                  <Pin size={15} aria-hidden="true" />
                  <span>As fontes ficam vinculadas ao projeto atual.</span>
                </li>
                <li>
                  <Database size={15} aria-hidden="true" />
                  <span>O assistente poderá buscar trechos relevantes durante a conversa.</span>
                </li>
                <li>
                  <Folder size={15} aria-hidden="true" />
                  <span>Outros projetos não herdam essas fontes automaticamente.</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {isSettingsOpen ? (
        <ModalPortal>
        <div
          className="mdc-chat-project-settings-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setIsSettingsOpen(false);
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
                  disabled={isSharingProject}
                  onClick={() => void shareCurrentProject()}
                >
                  {isSharingProject ? "Compartilhando..." : "Compartilhar projeto"}
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
        </ModalPortal>
      ) : null}
    </section>
  );
}
