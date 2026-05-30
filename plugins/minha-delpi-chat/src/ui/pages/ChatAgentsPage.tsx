import { ArrowLeft, Bot, ChevronRight, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ChatAgent } from "../../data/api/chatTypes";
import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";
import { AgentBuilderCheckbox } from "../components/agent-builder/AgentBuilderCheckbox";
import { useConfirmDialog } from "../components/useConfirmDialog";
import { ChatAgentActionsPage } from "./ChatAgentActionsPage";
import { ChatAgentBuilderPage } from "./ChatAgentBuilderPage";
import { ChatAgentSkillsPage } from "./ChatAgentSkillsPage";

import "./ChatAgentsPage.css";

type AgentPayload = {
  name: string;
  description?: string | null;
  systemPrompt?: string | null;
  visibility?: string;
  category?: string | null;
  icon?: string | null;
  responseStyle?: string | null;
  metadata?: Record<string, unknown> | null;
};

type AgentUpdatePayload = Partial<AgentPayload> & {
  enabled?: boolean;
};

type ChatAgentsPageProps = {
  agents: ChatAgent[];
  selectedAgentId?: string | null;
  canManageAgents?: boolean;
  canManageOfficialAgents?: boolean;
  editAgentId?: string | null;
  editRequestKey?: number;
  isLoading?: boolean;
  onBack: () => void;
  onSelectAgent?: (agentId: string | null) => void;
  onCreateAgent?: (payload: AgentPayload) => Promise<ChatAgent | null>;
  onUpdateAgent?: (
    agentId: string,
    payload: AgentUpdatePayload,
  ) => Promise<ChatAgent | null>;
  onAgentPublished?: (agent: ChatAgent) => void;
  onDeleteAgent?: (agentId: string) => Promise<boolean>;
  onAgentDuplicated?: (agent: ChatAgent) => void;
  onReloadAgents?: (
    includeDisabled: boolean,
    includeStats?: boolean,
  ) => void | Promise<void>;
  onOpenAgentConfig?: (agentId: string) => void;
  onCloseAgentConfig?: () => void;
  onOpenAgentSkills?: (agentId: string) => void;
  onOpenAgentActions?: (agentId: string, providerKey?: string | null) => void;
  agentSubRoute?: {
    kind: "skills" | "actions";
    agentId: string;
    providerKey?: string | null;
  } | null;
  agentSubRouteKey?: string;
  onOpenRagAdmin?: (agentId: string) => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function isOfficialAgent(agent: ChatAgent): boolean {
  return agent.visibility === "system" || agent.access_role === "system";
}

function canEditAgent(
  agent: ChatAgent,
  canManageOwnAgents: boolean,
  canManageOfficialAgents: boolean,
): boolean {
  if (isOfficialAgent(agent)) {
    return canManageOfficialAgents;
  }

  return canManageOwnAgents && ["owner", "editor"].includes(agent.access_role);
}

function canDeleteAgent(
  agent: ChatAgent,
  canManageOwnAgents: boolean,
  canManageOfficialAgents: boolean,
): boolean {
  if (isOfficialAgent(agent)) {
    return canManageOfficialAgents;
  }

  return canManageOwnAgents && agent.access_role === "owner";
}

function getAgentIcebreakerCount(agent: ChatAgent): number {
  const value = agent.metadata?.icebreakers;

  if (!Array.isArray(value)) {
    return 0;
  }

  return value.filter((item) => typeof item === "string" && item.trim()).length;
}

function getAgentCapabilities(agent: ChatAgent): string[] {
  const capabilities = agent.metadata?.capabilities;

  if (!capabilities || typeof capabilities !== "object" || Array.isArray(capabilities)) {
    return [];
  }

  return Object.entries(capabilities)
    .filter(([, enabled]) => enabled === true)
    .map(([name]) => name);
}

function getOwnerLabel(agent: ChatAgent): string {
  if (agent.visibility === "system") {
    return "Oficial";
  }

  if (agent.visibility === "public") {
    return "Público interno";
  }

  return "Privado";
}

export function ChatAgentsPage({
  agents,
  selectedAgentId,
  canManageAgents = false,
  canManageOfficialAgents = false,
  editAgentId,
  editRequestKey,
  isLoading,
  onBack,
  onSelectAgent,
  onCreateAgent,
  onUpdateAgent,
  onAgentPublished,
  onDeleteAgent,
  onAgentDuplicated,
  onReloadAgents,
  onOpenAgentConfig,
  onCloseAgentConfig,
  onOpenAgentSkills,
  onOpenAgentActions,
  agentSubRoute,
  agentSubRouteKey,
  onOpenRagAdmin,
  getAccessToken,
}: ChatAgentsPageProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const [showInactive, setShowInactive] = useState(false);
  const [editingAgent, setEditingAgent] = useState<ChatAgent | null | undefined>(undefined);
  const [actionEditor, setActionEditor] = useState<{
    agent: ChatAgent;
    providerKey?: string | null;
    returnToBuilder?: boolean;
  } | null>(null);
  const [skillsEditor, setSkillsEditor] = useState<{
    agent: ChatAgent;
    returnToBuilder?: boolean;
  } | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredAgents = useMemo(() => {
    const normalized = searchTerm.trim().toLowerCase();

    if (!normalized) {
      return agents;
    }

    return agents.filter((agent) => {
      return [
        agent.name,
        agent.description,
        agent.category,
        agent.visibility,
        agent.response_style,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalized);
    });
  }, [agents, searchTerm]);

  useEffect(() => {
    if (canManageAgents) {
      void onReloadAgents?.(false, true);
    }
  }, [canManageAgents, onReloadAgents]);

  useEffect(() => {
    if (!editAgentId) {
      if (!agentSubRoute) {
        return;
      }

      return;
    }

    const targetAgent = agents.find((agent) => agent.id === editAgentId);

    if (
      targetAgent &&
      canEditAgent(targetAgent, canManageAgents, canManageOfficialAgents)
    ) {
      setEditingAgent(targetAgent);
      setSkillsEditor(null);
      setActionEditor(null);
    }
  }, [agents, editAgentId, editRequestKey, agentSubRoute, canManageAgents, canManageOfficialAgents]);

  useEffect(() => {
    if (!agentSubRoute) {
      setSkillsEditor(null);
      setActionEditor(null);
      return;
    }

    const targetAgent = agents.find((agent) => agent.id === agentSubRoute.agentId);

    if (
      !targetAgent ||
      !canEditAgent(targetAgent, canManageAgents, canManageOfficialAgents)
    ) {
      return;
    }

    if (agentSubRoute.kind === "skills") {
      setSkillsEditor({ agent: targetAgent, returnToBuilder: true });
      setActionEditor(null);
      setEditingAgent(undefined);
      return;
    }

    setActionEditor({
      agent: targetAgent,
      providerKey: agentSubRoute.providerKey ?? null,
      returnToBuilder: true,
    });
    setSkillsEditor(null);
    setEditingAgent(undefined);
  }, [agents, agentSubRoute, agentSubRouteKey, canManageAgents, canManageOfficialAgents]);

  if (skillsEditor) {
    return (
      <ChatAnimatedPanel panelKey="agent-skills" variant="page" className="mdc-chat-page-panel--fill">
      <ChatAgentSkillsPage
        agent={skillsEditor.agent}
        backLabel={
          skillsEditor.returnToBuilder ? "Voltar ao agente" : "Voltar para agentes"
        }
        onBack={() => {
          if (skillsEditor.returnToBuilder) {
            onOpenAgentConfig?.(skillsEditor.agent.id);
          } else {
            setSkillsEditor(null);
          }
        }}
        onOpenActions={(target) => {
          onOpenAgentActions?.(target.id, null);
        }}
        getAccessToken={getAccessToken}
      />
      </ChatAnimatedPanel>
    );
  }

  if (actionEditor) {
    return (
      <ChatAnimatedPanel panelKey="agent-actions" variant="page" className="mdc-chat-page-panel--fill">
      <ChatAgentActionsPage
        agent={actionEditor.agent}
        providerKey={actionEditor.providerKey}
        backLabel={
          actionEditor.returnToBuilder ? "Voltar ao agente" : "Voltar para agentes"
        }
        onBack={() => {
          if (actionEditor.returnToBuilder) {
            onOpenAgentConfig?.(actionEditor.agent.id);
          } else {
            setActionEditor(null);
          }
        }}
        getAccessToken={getAccessToken}
      />
      </ChatAnimatedPanel>
    );
  }

  if (editingAgent !== undefined && (editingAgent !== null || canManageAgents)) {
    return (
      <ChatAnimatedPanel panelKey="agent-builder" variant="page" className="mdc-chat-page-panel--fill">
      <ChatAgentBuilderPage
        agent={editingAgent}
        onBack={() => {
          setEditingAgent(undefined);
          onCloseAgentConfig?.();
        }}
        onCreateAction={
          editingAgent
            ? () => {
                onOpenAgentActions?.(editingAgent.id, null);
              }
            : undefined
        }
        onConfigureAction={
          editingAgent
            ? (_agent, providerKey) => {
                onOpenAgentActions?.(editingAgent.id, providerKey);
              }
            : undefined
        }
        onConfigureSkills={
          editingAgent
            ? () => {
                onOpenAgentSkills?.(editingAgent.id);
              }
            : undefined
        }
        onAgentCreated={(created) => {
          setEditingAgent(created);
          onOpenAgentConfig?.(created.id);
        }}
        onSelectAgent={onSelectAgent}
        onCreateAgent={onCreateAgent}
        onUpdateAgent={onUpdateAgent}
        onAgentPublished={onAgentPublished}
        onDeleteAgent={onDeleteAgent}
        onDuplicateAgent={(duplicated) => {
          onAgentDuplicated?.(duplicated);
          setEditingAgent(duplicated);
          onOpenAgentConfig?.(duplicated.id);
        }}
        canManageOfficialAgents={canManageOfficialAgents}
        onOpenRagAdmin={onOpenRagAdmin}
        getAccessToken={getAccessToken}
      />
      </ChatAnimatedPanel>
    );
  }

  return (
    <ChatAnimatedPanel panelKey="agents-directory" variant="page" className="mdc-chat-page-panel--fill">
    {confirmDialog}
    <section className="mdc-chat-ws-directory" aria-label="Agentes">
      <header className="mdc-chat-ws-topbar mdc-chat-ws-directory__topbar">
        <div className="mdc-chat-ws-topbar__start">
          <button type="button" className="mdc-chat-ws-topbar__back" onClick={onBack}>
            <ArrowLeft size={18} aria-hidden="true" />
            <span>Voltar ao chat</span>
          </button>
        </div>

        <div className="mdc-chat-ws-topbar__title mdc-chat-ws-directory__title">
          <Bot size={18} aria-hidden="true" />
          <span>Apps e agentes</span>
        </div>

        {canManageAgents ? (
          <div className="mdc-chat-ws-topbar__actions">
            <button
              type="button"
              className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
              onClick={() => setEditingAgent(null)}
            >
              <Plus size={16} aria-hidden="true" />
              <span>Criar agente</span>
            </button>
          </div>
        ) : null}
      </header>

      <main className="mdc-chat-ws-directory__main">
        <div className="mdc-chat-ws-directory__toolbar">
          <p className="mdc-chat-ws-directory__lead">
            Especialistas com instruções, conhecimento, quebra-gelos e actions OpenAPI.
          </p>

          <label className="mdc-chat-ws-directory__search">
            <Search size={17} aria-hidden="true" />
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Buscar agentes"
            />
          </label>
        </div>

        <div className="mdc-chat-ws-directory__meta-row">
          <span>{agents.length} agente(s)</span>
          {canManageAgents ? (
            <AgentBuilderCheckbox
              checked={showInactive}
              onChange={(event) => {
                const includeDisabled = event.target.checked;
                setShowInactive(includeDisabled);
                void onReloadAgents?.(includeDisabled, canManageAgents);
              }}
              label="Mostrar inativos"
            />
          ) : null}
        </div>

        {isLoading ? (
          <p className="mdc-chat-ws-empty">Carregando agentes...</p>
        ) : filteredAgents.length === 0 ? (
          <div className="mdc-chat-ws-directory__empty">
            <Bot size={22} aria-hidden="true" />
            <strong>Nenhum agente encontrado</strong>
            <p>Crie um especialista ou ajuste a busca.</p>
          </div>
        ) : (
          <ul className="mdc-chat-ws-directory__list">
            {filteredAgents.map((agent) => {
              const icebreakerCount = getAgentIcebreakerCount(agent);
              const isPrivateAgent = agent.visibility === "private";
              const capabilities = getAgentCapabilities(agent);
              const editable = canEditAgent(
                agent,
                canManageAgents,
                canManageOfficialAgents,
              );

              return (
                <li key={agent.id}>
                  <article
                    className={[
                      "mdc-chat-ws-directory__card",
                      agent.id === selectedAgentId
                        ? "mdc-chat-ws-directory__card--active"
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    <button
                      type="button"
                      className="mdc-chat-ws-directory__card-main"
                      onClick={() => onSelectAgent?.(agent.id)}
                    >
                      <span className="mdc-chat-ws-directory__card-icon">
                        <Bot size={18} aria-hidden="true" />
                      </span>
                      <span className="mdc-chat-ws-directory__card-copy">
                        <strong>{agent.name}</strong>
                        <small>
                          {agent.description ||
                            agent.category ||
                            "Especialista configurável"}
                        </small>
                      </span>
                      <ChevronRight size={16} aria-hidden="true" />
                    </button>

                    <div className="mdc-chat-ws-directory__card-meta">
                      {!agent.enabled ? <span>Inativo</span> : null}
                      <span>{getOwnerLabel(agent)}</span>
                      {!isPrivateAgent && icebreakerCount > 0 ? (
                        <span>{icebreakerCount} quebra-gelos</span>
                      ) : null}
                      {!isPrivateAgent && capabilities.length > 0 ? (
                        <span>{capabilities.length} recursos</span>
                      ) : null}
                      {typeof agent.sessions_in_window === "number" ? (
                        <span>{agent.sessions_in_window} conversas (7d)</span>
                      ) : null}
                    </div>

                    <div className="mdc-chat-ws-directory__card-actions">
                      <button
                        type="button"
                        className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
                        onClick={() => onSelectAgent?.(agent.id)}
                      >
                        Usar
                      </button>

                      {editable ? (
                        <button
                          type="button"
                          className="mdc-chat-ws-toolbar-btn"
                          onClick={() => {
                            setEditingAgent(agent);
                            onOpenAgentConfig?.(agent.id);
                          }}
                        >
                          <Pencil size={16} aria-hidden="true" />
                          <span>Configurar</span>
                        </button>
                      ) : null}

                      {canDeleteAgent(agent, canManageAgents, canManageOfficialAgents) ? (
                        <button
                          type="button"
                          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--danger"
                          onClick={() => {
                            void confirm({
                              title: "Excluir agente",
                              description: `Excluir o agente "${agent.name}"?`,
                              confirmLabel: "Excluir",
                              cancelLabel: "Cancelar",
                              danger: true,
                            }).then((confirmed) => {
                              if (confirmed) {
                                void onDeleteAgent?.(agent.id);
                              }
                            });
                          }}
                        >
                          <Trash2 size={16} aria-hidden="true" />
                          <span>Excluir</span>
                        </button>
                      ) : null}
                    </div>
                  </article>
                </li>
              );
            })}
          </ul>
        )}
      </main>
    </section>
    </ChatAnimatedPanel>
  );
}
