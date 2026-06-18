import { ArrowUpRight, Plus, Upload } from "lucide-react";
import { useMemo, useRef, type RefObject } from "react";

import {
  formatComposerPlusMenuText,
  getComposerPlusMenuContent,
} from "../../../../content/messageComposerContent";
import type { ChatAgent, ChatProject } from "../../../../data/api/chatTypes";
import { MAX_COMPOSER_AGENTS, MAX_COMPOSER_PROJECTS } from "../../../../state/chatComposerContext";
import { excludeInUseComposerContextItems } from "../../../../state/chatComposerMention";
import { workspaceFileComposerLabels } from "../../../../content/workspaceFileIngestContent";
import { estimateChatInputPlusMenuItemCount } from "../overlay/menuPositionUtils";
import { AnchoredMenuPortal } from "../overlay/AnchoredMenuPortal";
import { ChatAgentIcon } from "../../workspace/ChatAgentIcon";
import { ChatProjectIcon } from "../../workspace/ChatProjectIcon";

import "../../composer/ChatInput.css";

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
  const internalTriggerRef = useRef<HTMLButtonElement | null>(null);
  const triggerRef = triggerRefProp ?? internalTriggerRef;
  const plusMenuLabels = useMemo(() => getComposerPlusMenuContent(), []);
  const selectedAgentIdSet = useMemo(() => new Set(selectedAgentIds), [selectedAgentIds]);
  const selectedProjectIdSet = useMemo(() => new Set(selectedProjectIds), [selectedProjectIds]);
  const selectableAgents = useMemo(
    () => excludeInUseComposerContextItems(agents, selectedAgentIds),
    [agents, selectedAgentIds],
  );
  const selectableProjects = useMemo(
    () => excludeInUseComposerContextItems(projects, selectedProjectIds).slice(0, 8),
    [projects, selectedProjectIds],
  );

  const menuItemCount = useMemo(
    () =>
      estimateChatInputPlusMenuItemCount({
        agentCount: selectableAgents.length,
        projectCount: selectableProjects.length,
      }),
    [selectableAgents.length, selectableProjects.length],
  );

  return (
    <div className="mdc-chat-input__plus-wrap" data-tour="composer-plus">
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
        triggerRef={triggerRef}
        itemCount={menuItemCount}
        placement="composer-panel"
        menuLabel="Mais opções do composer"
        menuRole="menu"
        panelClassName="mdc-chat-input__menu"
        onClose={() => onOpenChange(false)}
      >
        <div className="mdc-chat-input__menu-section">
          <strong>{plusMenuLabels.filesSectionTitle}</strong>

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

        <div
          className="mdc-chat-input__menu-section mdc-chat-input__menu-section--context"
          data-tour="composer-plus-menu-agents"
        >
          <strong>{plusMenuLabels.agentsSectionTitle}</strong>
          <p className="mdc-chat-input__menu-hint">
            {formatComposerPlusMenuText(plusMenuLabels.agentsHint, {
              maxAgents: MAX_COMPOSER_AGENTS,
            })}
          </p>

          {selectableAgents.length === 0 ? (
            <p className="mdc-chat-input__menu-empty">{plusMenuLabels.emptyAgents}</p>
          ) : (
            selectableAgents.map((agent) => (
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
                  <ChatAgentIcon icon={agent.icon} size={16} />
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
            ))
          )}
        </div>

        <div
          className="mdc-chat-input__menu-section mdc-chat-input__menu-section--context"
          data-tour="composer-plus-menu-projects"
        >
          <strong>{plusMenuLabels.projectsSectionTitle}</strong>
          <p className="mdc-chat-input__menu-hint">
            {formatComposerPlusMenuText(plusMenuLabels.projectsHint, {
              maxProjects: MAX_COMPOSER_PROJECTS,
            })}
          </p>

          {selectableProjects.length === 0 ? (
            <p className="mdc-chat-input__menu-empty">{plusMenuLabels.emptyProjects}</p>
          ) : (
            selectableProjects.map((project) => (
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
                <ChatProjectIcon icon={project.icon} size={16} />
                <span>{project.name}</span>
              </button>
            ))
          )}
        </div>
      </AnchoredMenuPortal>
    </div>
  );
}
