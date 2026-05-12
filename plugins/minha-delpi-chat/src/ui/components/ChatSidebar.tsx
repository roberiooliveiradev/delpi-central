import {
  Bot,
  Box,
  Check,
  ChevronLeft,
  ChevronRight,
  Folder,
  MessageSquarePlus,
  Search,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import type { ChatSession } from "../../data/api/chatTypes";
import { ChatConfirmDialog } from "./ChatConfirmDialog";
import { ChatConversationMenu } from "./ChatConversationMenu";

import "./ChatSidebar.css";

type ChatSidebarProps = {
  sessions: ChatSession[];
  activeSessionId?: string;
  isLoading?: boolean;
  isCollapsed?: boolean;
  onToggleCollapsed?: () => void;
  onNewSession: () => void;
  onSelectSession: (session: ChatSession) => void;
  onRenameSession: (sessionId: string, title: string) => Promise<ChatSession | null>;
  onDeleteSession: (sessionId: string) => Promise<boolean>;
};

type SessionGroup = {
  label: string;
  sessions: ChatSession[];
};

const apps = [
  { label: "Minha DELPI Chat", icon: Bot },
  { label: "Ações OpenAPI", icon: Box },
];

const projects = [
  { label: "App - DELPI Central", icon: Folder },
  { label: "Produtos e estoque", icon: Folder },
];

function getSessionDate(session: ChatSession): Date | null {
  const value = session.updated_at || session.created_at;

  if (!value) {
    return null;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date;
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function getSessionGroupLabel(session: ChatSession): string {
  const date = getSessionDate(session);

  if (!date) {
    return "Sem data";
  }

  const today = startOfDay(new Date());
  const target = startOfDay(date);
  const diffMs = today.getTime() - target.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffDays === 0) {
    return "Hoje";
  }

  if (diffDays === 1) {
    return "Ontem";
  }

  if (diffDays <= 7) {
    return "Últimos 7 dias";
  }

  if (diffDays <= 30) {
    return "Últimos 30 dias";
  }

  return "Anteriores";
}

function groupSessions(sessions: ChatSession[]): SessionGroup[] {
  const order = ["Hoje", "Ontem", "Últimos 7 dias", "Últimos 30 dias", "Anteriores", "Sem data"];
  const groups = new Map<string, ChatSession[]>();

  for (const session of sessions) {
    const label = getSessionGroupLabel(session);
    groups.set(label, [...(groups.get(label) ?? []), session]);
  }

  return order
    .map((label) => ({
      label,
      sessions: groups.get(label) ?? [],
    }))
    .filter((group) => group.sessions.length > 0);
}

function formatSessionDate(value?: string): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function ChatSidebar({
  sessions,
  activeSessionId,
  isLoading,
  isCollapsed,
  onToggleCollapsed,
  onNewSession,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
}: ChatSidebarProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [openMenuSessionId, setOpenMenuSessionId] = useState<string | null>(null);
  const [deleteTargetSession, setDeleteTargetSession] = useState<ChatSession | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const searchInputRef = useRef<HTMLInputElement | null>(null);

  const filteredSessions = useMemo(() => {
    const normalized = searchTerm.trim().toLowerCase();

    if (!normalized) {
      return sessions;
    }

    return sessions.filter((session) => {
      const title = session.title || "Conversa sem título";
      const context = session.context || "geral";

      return `${title} ${context}`.toLowerCase().includes(normalized);
    });
  }, [searchTerm, sessions]);

  const groupedSessions = useMemo(
    () => groupSessions(filteredSessions),
    [filteredSessions],
  );

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setIsSearchOpen(true);
        window.setTimeout(() => searchInputRef.current?.focus(), 0);
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  useEffect(() => {
    if (isSearchOpen) {
      searchInputRef.current?.focus();
    }
  }, [isSearchOpen]);

  function startEditingSession(session: ChatSession) {
    setEditingSessionId(session.id);
    setEditingTitle(session.title || "");
  }

  function cancelEditingSession() {
    setEditingSessionId(null);
    setEditingTitle("");
  }

  function requestDeleteSession(session: ChatSession) {
    setDeleteTargetSession(session);
  }

  async function confirmDeleteSession() {
    if (!deleteTargetSession) {
      return;
    }

    await onDeleteSession(deleteTargetSession.id);
    setDeleteTargetSession(null);
  }

  function handleShareSession(session: ChatSession) {
    const title = session.title || "Conversa sem título";

    void navigator.clipboard?.writeText(title);
  }

  async function saveEditingSession(session: ChatSession) {
    const normalizedTitle = editingTitle.trim();
    const currentTitle = session.title || "";

    if (!normalizedTitle || normalizedTitle === currentTitle) {
      cancelEditingSession();
      return;
    }

    const updated = await onRenameSession(session.id, normalizedTitle);

    if (updated) {
      cancelEditingSession();
    }
  }

  if (isCollapsed) {
    return (
      <aside
        className="mdc-chat-sidebar mdc-chat-sidebar--collapsed"
        aria-label="Conversas"
      >
        <button
          type="button"
          className="mdc-chat-sidebar__collapse-button"
          onClick={onToggleCollapsed}
          aria-label="Expandir barra lateral"
          title="Expandir"
        >
          <ChevronRight size={18} aria-hidden="true" />
        </button>

        <button
          type="button"
          className="mdc-chat-sidebar__rail-button"
          onClick={onNewSession}
          aria-label="Nova conversa"
          title="Nova conversa"
        >
          <MessageSquarePlus size={19} aria-hidden="true" />
        </button>

        <button
          type="button"
          className="mdc-chat-sidebar__rail-button"
          onClick={() => {
            onToggleCollapsed?.();
            setIsSearchOpen(true);
          }}
          aria-label="Buscar conversas"
          title="Buscar conversas"
        >
          <Search size={19} aria-hidden="true" />
        </button>

        <button
          type="button"
          className="mdc-chat-sidebar__rail-button"
          aria-label="Apps"
          title="Apps"
        >
          <Box size={19} aria-hidden="true" />
        </button>

        <button
          type="button"
          className="mdc-chat-sidebar__rail-button"
          aria-label="Projetos"
          title="Projetos"
        >
          <Folder size={19} aria-hidden="true" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="mdc-chat-sidebar" aria-label="Conversas">
      <div className="mdc-chat-sidebar__brand">
        <div>
          <strong>Minha DELPI</strong>
          <small>Chat corporativo</small>
        </div>

        <button
          type="button"
          className="mdc-chat-sidebar__collapse-button"
          onClick={onToggleCollapsed}
          aria-label="Recolher barra lateral"
          title="Recolher"
        >
          <ChevronLeft size={18} aria-hidden="true" />
        </button>
      </div>

      <nav className="mdc-chat-sidebar__nav" aria-label="Ações do chat">
        <button type="button" onClick={onNewSession}>
          <MessageSquarePlus size={17} aria-hidden="true" />
          <span>Nova conversa</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setIsSearchOpen((current) => !current);
            setSearchTerm("");
          }}
        >
          <Search size={17} aria-hidden="true" />
          <span>Buscar conversas</span>
          <kbd>Ctrl K</kbd>
        </button>
      </nav>

      {isSearchOpen ? (
        <label className="mdc-chat-sidebar__search">
          <Search size={15} aria-hidden="true" />
          <input
            ref={searchInputRef}
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Buscar no histórico..."
          />
          {searchTerm ? (
            <button
              type="button"
              onClick={() => setSearchTerm("")}
              aria-label="Limpar busca"
            >
              <X size={14} aria-hidden="true" />
            </button>
          ) : null}
        </label>
      ) : null}

      <div className="mdc-chat-sidebar__scroll">
        <div className="mdc-chat-sidebar__section-title">
          <span>Apps e agentes</span>
        </div>

        <div className="mdc-chat-sidebar__link-list">
          {apps.map((item) => {
            const Icon = item.icon;

            return (
              <button key={item.label} type="button">
                <Icon size={16} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        <div className="mdc-chat-sidebar__section-title">
          <span>Projetos</span>
        </div>

        <div className="mdc-chat-sidebar__link-list">
          {projects.map((item) => {
            const Icon = item.icon;

            return (
              <button key={item.label} type="button">
                <Icon size={16} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        <div className="mdc-chat-sidebar__section-title">
          <span>Conversas</span>
          <small>{filteredSessions.length}</small>
        </div>

        {isLoading ? (
          <p className="mdc-chat-muted">Carregando sessões...</p>
        ) : groupedSessions.length === 0 ? (
          <p className="mdc-chat-muted">
            {searchTerm ? "Nenhuma conversa encontrada." : "Nenhuma conversa criada ainda."}
          </p>
        ) : (
          <div className="mdc-chat-session-list">
            {groupedSessions.map((group) => (
              <section key={group.label} className="mdc-chat-session-group">
                <h3>{group.label}</h3>

                {group.sessions.map((session) => {
                  const isEditing = editingSessionId === session.id;

                  return (
                    <div
                      key={session.id}
                      className={
                        session.id === activeSessionId
                          ? "mdc-chat-session-row mdc-chat-session-row--active"
                          : "mdc-chat-session-row"
                      }
                    >
                      {isEditing ? (
                        <div className="mdc-chat-session-edit-card">
                          <input
                            className="mdc-chat-session-edit-input"
                            value={editingTitle}
                            autoFocus
                            maxLength={120}
                            onChange={(event) => setEditingTitle(event.target.value)}
                            onKeyDown={(event) => {
                              if (event.key === "Enter") {
                                event.preventDefault();
                                void saveEditingSession(session);
                              }

                              if (event.key === "Escape") {
                                event.preventDefault();
                                cancelEditingSession();
                              }
                            }}
                            aria-label="Nome da conversa"
                          />

                          <div className="mdc-chat-session-edit-actions">
                            <button
                              type="button"
                              className="mdc-chat-session-action"
                              onClick={() => void saveEditingSession(session)}
                              aria-label="Salvar nome da conversa"
                              title="Salvar"
                            >
                              <Check size={15} aria-hidden="true" />
                            </button>

                            <button
                              type="button"
                              className="mdc-chat-session-action"
                              onClick={cancelEditingSession}
                              aria-label="Cancelar edição"
                              title="Cancelar"
                            >
                              <X size={15} aria-hidden="true" />
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <button
                            type="button"
                            className="mdc-chat-session"
                            onClick={() => onSelectSession(session)}
                          >
                            <span>{session.title || "Conversa sem título"}</span>
                            <small>
                              {session.context || "geral"}
                              {formatSessionDate(session.updated_at) ? (
                                <> · {formatSessionDate(session.updated_at)}</>
                              ) : null}
                            </small>
                          </button>

                          <div className="mdc-chat-session-actions">
                            <ChatConversationMenu
                              open={openMenuSessionId === session.id}
                              onOpenChange={(open) =>
                                setOpenMenuSessionId(open ? session.id : null)
                              }
                              onShare={() => handleShareSession(session)}
                              onRename={() => startEditingSession(session)}
                              onDelete={() => requestDeleteSession(session)}
                            />
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </section>
            ))}
          </div>
        )}
      </div>

      <div className="mdc-chat-sidebar__footer">
        <span>DELPI Central</span>
        <small>APIs, conhecimento e ações autorizadas</small>
      </div>

      <ChatConfirmDialog
        open={Boolean(deleteTargetSession)}
        danger
        title="Excluir conversa?"
        description={`A conversa "${
          deleteTargetSession?.title || "sem título"
        }" será removida com todo o histórico de mensagens.`}
        confirmLabel="Excluir"
        cancelLabel="Cancelar"
        onConfirm={confirmDeleteSession}
        onCancel={() => setDeleteTargetSession(null)}
      />
    </aside>
  );
}
