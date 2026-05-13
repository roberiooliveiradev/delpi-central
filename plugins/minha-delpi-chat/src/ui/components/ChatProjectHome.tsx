import {
  Database,
  FileText,
  Folder,
  Link,
  MoreHorizontal,
  Pencil,
  Pin,
  Plus,
  Settings,
  Text,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import type { ChatProject, ChatSession } from "../../data/api/chatTypes";
import { ChatConversationListItem } from "./ChatConversationListItem";
import { ChatConversationMenu } from "./ChatConversationMenu";
import { formatSessionDate } from "./chatSidebarUtils";

import "./ChatProjectHome.css";

type ProjectTab = "chats" | "sources";

type ChatProjectHomeProps = {
  project: ChatProject;
  sessions: ChatSession[];
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
      visibility?: string;
      archived?: boolean;
    },
  ) => Promise<ChatProject | null>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
  onClearProject?: () => void;
  compact?: boolean;
  settingsRequestKey?: number;
};

const sourceTypes = [
  {
    key: "file",
    title: "Enviar arquivos",
    description: "PDF, planilhas, documentos e materiais do projeto.",
    icon: Upload,
    disabled: true,
  },
  {
    key: "link",
    title: "Adicionar link",
    description: "Referências externas, páginas internas e documentação.",
    icon: Link,
    disabled: true,
  },
  {
    key: "text",
    title: "Criar nota",
    description: "Texto livre com regras, contexto ou conhecimento manual.",
    icon: Text,
    disabled: true,
  },
  {
    key: "knowledge",
    title: "Base de conhecimento",
    description: "Conectar documentos já indexados pela plataforma.",
    icon: Database,
    disabled: true,
  },
];

export function ChatProjectHome({
  project,
  sessions,
  activeSessionId,
  composer,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
  onPinSession,
  onUnpinSession,
  onUpdateProject,
  onDeleteProject,
  onClearProject,
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
      {!compact ? (
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
              <span>0 fontes</span>
              {project.default_agent_key ? (
                <span>Agente: {project.default_agent_key}</span>
              ) : (
                <span>Sem agente padrão</span>
              )}
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
      ) : null}

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
        ) : (
          <div className="mdc-chat-project-sources" role="tabpanel">
            <div className="mdc-chat-project-sources__hero">
              <span>
                <FileText size={26} aria-hidden="true" />
              </span>

              <div>
                <h3>Fontes do projeto</h3>
                <p>
                  Adicione arquivos, links e notas para que o assistente use como
                  contexto exclusivo deste projeto.
                </p>
              </div>

              <button type="button" disabled title="Em breve">
                <Plus size={16} aria-hidden="true" />
                <span>Adicionar fonte</span>
              </button>
            </div>

            <div className="mdc-chat-project-sources__grid">
              {sourceTypes.map((sourceType) => {
                const Icon = sourceType.icon;

                return (
                  <button
                    key={sourceType.key}
                    type="button"
                    disabled={sourceType.disabled}
                    title="Em breve"
                  >
                    <span>
                      <Icon size={19} aria-hidden="true" />
                    </span>

                    <strong>{sourceType.title}</strong>
                    <small>{sourceType.description}</small>

                    <em>Em breve</em>
                  </button>
                );
              })}
            </div>

            <div className="mdc-chat-project-sources__empty">
              <div>
                <FileText size={22} aria-hidden="true" />
              </div>

              <strong>Nenhuma fonte adicionada</strong>
              <p>
                Quando a funcionalidade estiver ativa, os documentos adicionados aqui
                serão usados apenas neste projeto.
              </p>
            </div>

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
