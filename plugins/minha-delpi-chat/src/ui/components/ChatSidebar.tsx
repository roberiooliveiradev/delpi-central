import {
  Archive,
  Box,
  ChevronDown,
  ChevronRight,
  Folder,
  MessageSquarePlus,
  Search,
  Settings2,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import type { ChatAgent, ChatProject, ChatSession } from "../../data/api/chatTypes";
import { ChatConfirmDialog } from "./ChatConfirmDialog";
import { ChatProjectCreateModal } from "./ChatProjectCreateModal";
import { ChatSidebarAgentsSection } from "./ChatSidebarAgentsSection";
import { ChatSidebarArchivedDialog } from "./ChatSidebarArchivedDialog";
import { ChatSidebarBrand } from "./ChatSidebarBrand";
import { ChatSidebarNav } from "./ChatSidebarNav";
import { ChatSidebarProjectsSection } from "./ChatSidebarProjectsSection";
import { ChatSidebarSessionList } from "./ChatSidebarSessionList";
import { groupSessions } from "./chatSidebarUtils";

import "./ChatSidebar.css";
import "./ChatSidebarBrand.css";
import "./ChatSidebarNav.css";
import "./ChatSidebarAgentsSection.css";
import "./ChatSidebarProjectsSection.css";
import "./ChatSidebarSessionList.css";
import "./ChatSidebarArchivedDialog.css";
import "./ChatProjectCreateModal.css";
import "./ChatProjectCard.css";

export type ChatSidebarView = "chat" | "agents";

type ChatSidebarProps = {
  sessions: ChatSession[];
  archivedSessions?: ChatSession[];
  agents?: ChatAgent[];
  projects?: ChatProject[];
  activeSessionId?: string;
  selectedProjectId?: string | null;
  selectedAgentKey?: string | null;
  isLoading?: boolean;
  isLoadingArchivedSessions?: boolean;
  isLoadingAgents?: boolean;
  isLoadingProjects?: boolean;
  canManageAgents?: boolean;
  isCollapsed?: boolean;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
  onToggleCollapsed?: () => void;
  onViewChange?: (view: ChatSidebarView) => void;
  onOpenAdmin?: () => void;
  onNewSession: () => void;
  onSelectSession: (session: ChatSession) => void;
  onRenameSession: (sessionId: string, title: string) => Promise<ChatSession | null>;
  onDeleteSession: (sessionId: string) => Promise<boolean>;
  onPinSession?: (sessionId: string) => Promise<ChatSession | null>;
  onUnpinSession?: (sessionId: string) => Promise<ChatSession | null>;
  onArchiveSession?: (sessionId: string) => Promise<ChatSession | null>;
  onUnarchiveSession?: (sessionId: string) => Promise<ChatSession | null>;
  onLoadArchivedSessions?: () => Promise<void>;
  onCreateProject?: (payload: {
    name: string;
    description?: string | null;
    instructions?: string | null;
  }) => Promise<ChatProject | null>;
  onRenameProject?: (projectId: string, name: string) => Promise<ChatProject | null>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
  onSelectProject?: (projectId: string | null) => void;
  onSelectAgent?: (agentKey: string | null) => void;
  isSessionProcessing?: (sessionId: string) => boolean;
};

export function ChatSidebar({
  sessions,
  archivedSessions = [],
  agents = [],
  projects = [],
  activeSessionId,
  selectedProjectId,
  selectedAgentKey,
  isLoading,
  isLoadingArchivedSessions,
  isLoadingAgents,
  isLoadingProjects,
  canManageAgents = false,
  isCollapsed,
  isMobileOpen = false,
  onCloseMobile,
  onToggleCollapsed,
  onViewChange,
  onOpenAdmin,
  onNewSession,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
  onPinSession,
  onUnpinSession,
  onArchiveSession,
  onUnarchiveSession,
  onLoadArchivedSessions,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
  onSelectProject,
  onSelectAgent,
  isSessionProcessing,
}: ChatSidebarProps) {
  const [deleteTargetSession, setDeleteTargetSession] = useState<ChatSession | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isArchivedOpen, setIsArchivedOpen] = useState(false);
  const [isProjectsModalOpen, setIsProjectsModalOpen] = useState(false);
  const [isAgentsSectionOpen, setIsAgentsSectionOpen] = useState(true);
  const [isConversationsSectionOpen, setIsConversationsSectionOpen] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const searchInputRef = useRef<HTMLInputElement | null>(null);

  const filteredSessions = useMemo(() => {
    const normalized = searchTerm.trim().toLowerCase();

    return sessions.filter((session) => {
      if (session.project_id) {
        return false;
      }

      if (!normalized) {
        return true;
      }

      const title = session.title || "Conversa sem título";

      return title.toLowerCase().includes(normalized);
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

  async function openArchivedSessions() {
    setIsArchivedOpen(true);
    await onLoadArchivedSessions?.();
  }

  async function confirmDeleteSession() {
    if (!deleteTargetSession) {
      return;
    }

    await onDeleteSession(deleteTargetSession.id);
    setDeleteTargetSession(null);
  }

  async function restoreArchivedSession(session: ChatSession) {
    const restored = await onUnarchiveSession?.(session.id);

    if (restored) {
      setIsArchivedOpen(false);
      onSelectSession(restored);
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
          onClick={() => void openArchivedSessions()}
          aria-label="Arquivadas"
          title="Arquivadas"
        >
          <Archive size={19} aria-hidden="true" />
        </button>

        <button
          type="button"
          className="mdc-chat-sidebar__rail-button"
          onClick={() => onViewChange?.("agents")}
          aria-label="Apps"
          title="Apps"
        >
          <Box size={19} aria-hidden="true" />
        </button>

        <button
          type="button"
          className="mdc-chat-sidebar__rail-button"
          onClick={() => setIsProjectsModalOpen(true)}
          aria-label="Projetos"
          title="Projetos"
        >
          <Folder size={19} aria-hidden="true" />
        </button>

        {onOpenAdmin ? (
          <button
            type="button"
            className="mdc-chat-sidebar__rail-button mdc-chat-sidebar__rail-button--admin"
            onClick={onOpenAdmin}
            aria-label="Administração"
            title="Administração"
          >
            <Settings2 size={19} aria-hidden="true" />
          </button>
        ) : null}
      </aside>
    );
  }

  const sidebarClassName = [
    "mdc-chat-sidebar",
    isMobileOpen ? "mdc-chat-sidebar--drawer-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <aside className={sidebarClassName} aria-label="Conversas">
      <div className="mdc-chat-sidebar__top">
        <ChatSidebarBrand
          onToggleCollapsed={onToggleCollapsed}
          onCloseMobile={onCloseMobile}
        />

        <ChatSidebarNav
          isSearchOpen={isSearchOpen}
          searchTerm={searchTerm}
          searchInputRef={searchInputRef}
          onNewSession={onNewSession}
          onOpenAdmin={onOpenAdmin}
          onToggleSearch={() => {
            setIsSearchOpen((current) => !current);
            setSearchTerm("");
          }}
          onClearSearch={() => setSearchTerm("")}
          onSearchChange={setSearchTerm}
        />
      </div>

      <div className="mdc-chat-sidebar__agents-pane">
        <div className="mdc-chat-sidebar__section-title mdc-chat-sidebar__section-title--button">
          <button
            type="button"
            onClick={() => setIsAgentsSectionOpen((current) => !current)}
            aria-expanded={isAgentsSectionOpen}
          >
            {isAgentsSectionOpen ? (
              <ChevronDown size={13} aria-hidden="true" />
            ) : (
              <ChevronRight size={13} aria-hidden="true" />
            )}
            <span>Apps e agentes</span>
          </button>

          <small>{agents.length}</small>
        </div>

        {isAgentsSectionOpen ? (
          <ChatSidebarAgentsSection
            agents={agents}
            selectedAgentKey={selectedAgentKey}
            isLoading={isLoadingAgents}
            onSelectAgent={onSelectAgent}
            canManageAgents={canManageAgents}
            onManageAgents={() => onViewChange?.("agents")}
            hideTitle
          />
        ) : null}
      </div>

      <div className="mdc-chat-sidebar__projects-pane">
        <ChatSidebarProjectsSection
          projects={projects}
          sessions={sessions}
          selectedProjectId={selectedProjectId}
          activeSessionId={activeSessionId}
          isLoading={isLoadingProjects}
          isSessionProcessing={isSessionProcessing}
          onSelectProject={onSelectProject}
          onSelectSession={onSelectSession}
          onNewProject={() => setIsProjectsModalOpen(true)}
          onRenameProject={onRenameProject}
          onDeleteProject={onDeleteProject}
        />
      </div>

      <div className="mdc-chat-sidebar__sessions-pane">
        <div className="mdc-chat-sidebar__section-title mdc-chat-sidebar__section-title--conversations">
          <button
            type="button"
            className="mdc-chat-sidebar__section-toggle"
            onClick={() => setIsConversationsSectionOpen((current) => !current)}
            aria-expanded={isConversationsSectionOpen}
          >
            {isConversationsSectionOpen ? (
              <ChevronDown size={13} aria-hidden="true" />
            ) : (
              <ChevronRight size={13} aria-hidden="true" />
            )}
            <span>Conversas</span>
          </button>

          <div className="mdc-chat-sidebar__section-actions">
            <button
              type="button"
              onClick={() => void openArchivedSessions()}
              aria-label="Abrir conversas arquivadas"
              title="Arquivadas"
            >
              <Archive size={13} aria-hidden="true" />
            </button>

            <small>
              {groupedSessions.reduce((total, group) => total + group.sessions.length, 0)}
            </small>
          </div>
        </div>

        {isConversationsSectionOpen ? (
          <ChatSidebarSessionList
            groupedSessions={groupedSessions}
            activeSessionId={activeSessionId}
            isLoading={isLoading}
            searchTerm={searchTerm}
            selectedProjectName={null}
            hideTitle
            isSessionProcessing={isSessionProcessing}
            onOpenArchived={() => void openArchivedSessions()}
            onSelectSession={onSelectSession}
            onRenameSession={onRenameSession}
            onDeleteSessionRequest={setDeleteTargetSession}
            onPinSession={onPinSession}
            onUnpinSession={onUnpinSession}
            onArchiveSession={onArchiveSession}
          />
        ) : null}
      </div>

      <div className="mdc-chat-sidebar__footer">
        {onOpenAdmin ? (
          <button
            type="button"
            className="mdc-chat-sidebar__footer-admin"
            onClick={onOpenAdmin}
          >
            <Settings2 size={16} aria-hidden="true" />
            <span>Administração</span>
          </button>
        ) : null}
        <span>DELPI Central</span>
        <small>APIs, conhecimento e ações autorizadas</small>
      </div>

      <ChatProjectCreateModal
        open={isProjectsModalOpen}
        onClose={() => setIsProjectsModalOpen(false)}
        onCreateProject={onCreateProject}
        onSelectProject={onSelectProject}
      />

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

      <ChatSidebarArchivedDialog
        open={isArchivedOpen}
        archivedSessions={archivedSessions}
        isLoading={isLoadingArchivedSessions}
        onClose={() => setIsArchivedOpen(false)}
        onRestoreSession={(session) => void restoreArchivedSession(session)}
      />
    </aside>
  );
}
