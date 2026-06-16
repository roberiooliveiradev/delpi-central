import { ArrowUpRight, Bot, Folder, Plus, Upload } from "lucide-react";
import { useMemo, useRef, type RefObject } from "react";

import type { ChatAgent, ChatProject } from "../../../../data/api/chatTypes";
import { workspaceFileComposerLabels } from "../../../../content/workspaceFileIngestContent";
import { estimateChatInputPlusMenuItemCount } from "../../menuPositionUtils";
import { AnchoredMenuPortal } from "../overlay/AnchoredMenuPortal";

import "../../ChatInput.css";

type ChatInputPlusMenuProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  triggerRef?: RefObject<HTMLButtonElement | null>;
  agents: ChatAgent[];
  projects: ChatProject[];
  selectedAgentIds: string[];
  selectedProjectIds: string[];
  onAttachClick: () => void;
  onToggleAgent?: (agentId: string) => void;
  onToggleProject?: (projectId: string) => void;
  onOpenAgentPage?: (agentId: string) => void;
};

export function ChatInputPlusMenu({
  open,
  onOpenChange,
  triggerRef: triggerRefProp,
  agents,
  projects,
  selectedAgentIds,
  selectedProjectIds,
  onAttachClick,
  onToggleAgent,
  onToggleProject,
  onOpenAgentPage,
}: ChatInputPlusMenuProps) {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const internalTriggerRef = useRef<HTMLButtonElement | null>(null);
  const triggerRef = triggerRefProp ?? internalTriggerRef;
  const selectedAgentIdSet = useMemo(() => new Set(selectedAgentIds), [selectedAgentIds]);
  const selectedProjectIdSet = useMemo(() => new Set(selectedProjectIds), [selectedProjectIds]);

  const menuItemCount = useMemo(
    () =>
      estimateChatInputPlusMenuItemCount({
        agentCount: agents.length,
        projectCount: projects.length,
      }),
    [agents.length, projects.length],
  );

  return (
    <div ref={wrapRef} className="mdc-chat-input__plus-wrap" data-tour="composer-plus">
      <button
        ref={triggerRef}
        type="button"
        className="mdc-chat-input__plus"
        onClick={() => onOpenChange(!open)}
        aria-label="Mais opções"
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <Plus size={20} aria-hidden="true" />
      </button>

      <AnchoredMenuPortal
        open={open}
        triggerRef={wrapRef}
        itemCount={menuItemCount}
        placement="composer-panel"
        menuLabel="Mais opções do composer"
        menuRole="menu"
        panelClassName="mdc-chat-input__menu"
        onClose={() => onOpenChange(false)}
      >
        <div className="mdc-chat-input__menu-section">
          <strong>Arquivos</strong>

          <button
            type="button"
            role="menuitem"
            data-tour="composer-attach"
            onClick={() => {
              onAttachClick();
              onOpenChange(false);
            }}
          >
            <Upload size={16} aria-hidden="true" />
            <span>{workspaceFileComposerLabels().attachMenuLabel}</span>
          </button>
        </div>

        <div className="mdc-chat-input__menu-section" data-tour="composer-plus-menu-agents">
          <strong>Contexto da conversa</strong>
          <p className="mdc-chat-input__menu-hint">
            Selecione até 2 agentes e 3 projetos — o menu permanece aberto para combinar.
          </p>

          {agents.map((agent) => (
            <div key={agent.id} className="mdc-chat-input__agent-menu-row">
              <button
                type="button"
                role="menuitem"
                className={
                  selectedAgentIdSet.has(agent.id)
                    ? "mdc-chat-input__menu-item--active"
                    : undefined
                }
                onClick={() => {
                  onToggleAgent?.(agent.id);
                }}
              >
                <Bot size={16} aria-hidden="true" />
                <span>{agent.name}</span>
              </button>

              <button
                type="button"
                className="mdc-chat-input__open-agent"
                onClick={() => {
                  onOpenAgentPage?.(agent.id);
                  onOpenChange(false);
                }}
                title={`Abrir página de ${agent.name}`}
                aria-label={`Abrir página de ${agent.name}`}
              >
                <ArrowUpRight size={15} aria-hidden="true" />
              </button>
            </div>
          ))}

          {projects.slice(0, 8).map((project) => (
            <button
              key={project.id}
              type="button"
              role="menuitem"
              className={
                selectedProjectIdSet.has(project.id)
                  ? "mdc-chat-input__menu-item--active"
                  : undefined
              }
              onClick={() => {
                onToggleProject?.(project.id);
              }}
            >
              <Folder size={16} aria-hidden="true" />
              <span>{project.name}</span>
            </button>
          ))}
        </div>
      </AnchoredMenuPortal>
    </div>
  );
}
