import { ArrowLeft, Bot, ChevronRight, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ChatAgent } from "../../data/api/chatTypes";
import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";
import { AgentBuilderCheckbox } from "../components/agent-builder/AgentBuilderCheckbox";
import { ChatAgentActionsPage } from "./ChatAgentActionsPage";
import { ChatAgentBuilderPage } from "./ChatAgentBuilderPage";
import { ChatAgentSkillsPage } from "./ChatAgentSkillsPage";

import "./ChatAgentsPage.css";

type AgentPayload = {
  key?: string | null;
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
  selectedAgentKey?: string | null;
  canManageAgents?: boolean;
  canManageOfficialAgents?: boolean;
  editAgentKey?: string | null;
  editRequestKey?: number;
  isLoading?: boolean;
  onBack: () => void;
  onSelectAgent?: (agentKey: string | null) => void;
  onCreateAgent?: (payload: AgentPayload) => Promise<ChatAgent | null>;
  onUpdateAgent?: (
    agentId: string,
    payload: AgentUpdatePayload,
  ) => Promise<ChatAgent | null>;
  onDeleteAgent?: (agentId: string) => Promise<boolean>;
  onAgentDuplicated?: (agent: ChatAgent) => void;
  onReloadAgents?: (
    includeDisabled: boolean,
    includeStats?: boolean,
  ) => void | Promise<void>;
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
  selectedAgentKey,
  canManageAgents = false,
  canManageOfficialAgents = false,
  editAgentKey,
  editRequestKey,
  isLoading,
  onBack,
  onSelectAgent,
  onCreateAgent,
  onUpdateAgent,
  onDeleteAgent,
  onAgentDuplicated,
  onReloadAgents,
  onOpenRagAdmin,
  getAccessToken,
}: ChatAgentsPageProps) {
  const [showInactive, setShowInactive] = useState(false);
  const [editingAgent, setEditingAgent] = useState<ChatAgent | null | undefined>(undefined);
  const [resumeBuilderAgent, setResumeBuilderAgent] = useState<ChatAgent | null>(null);
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
    if (!editAgentKey) {
      return;
    }

    const targetAgent = agents.find((agent) => agent.key === editAgentKey);

    if (
      targetAgent &&
      canEditAgent(targetAgent, canManageAgents, canManageOfficialAgents)
    ) {
      setEditingAgent(targetAgent);
    }
  }, [agents, editAgentKey, editRequestKey, canManageAgents, canManageOfficialAgents]);

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
            setEditingAgent(skillsEditor.agent);
            setResumeBuilderAgent(null);
          }

          setSkillsEditor(null);
        }}
        onOpenActions={(target) => {
          setResumeBuilderAgent(skillsEditor.returnToBuilder ? skillsEditor.agent : null);
          setSkillsEditor(null);
          setActionEditor({
            agent: target,
            providerKey: null,
            returnToBuilder: skillsEditor.returnToBuilder,
          });
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
            setEditingAgent(resumeBuilderAgent ?? actionEditor.agent);
          }

          setResumeBuilderAgent(null);
          setActionEditor(null);
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
        onBack={() => setEditingAgent(undefined)}
        onCreateAction={
          editingAgent
            ? () => {
                setResumeBuilderAgent(editingAgent);
                setEditingAgent(undefined);
                setActionEditor({
                  agent: editingAgent,
                  providerKey: null,
                  returnToBuilder: true,
                });
              }
            : undefined
        }
        onConfigureAction={
          editingAgent
            ? (_agent, providerKey) => {
                setResumeBuilderAgent(editingAgent);
                setEditingAgent(undefined);
                setActionEditor({
                  agent: editingAgent,
                  providerKey,
                  returnToBuilder: true,
                });
              }
            : undefined
        }
        onConfigureSkills={
          editingAgent
            ? () => {
                setResumeBuilderAgent(editingAgent);
                setEditingAgent(undefined);
                setSkillsEditor({ agent: editingAgent, returnToBuilder: true });
              }
            : undefined
        }
        onSelectAgent={onSelectAgent}
        onCreateAgent={onCreateAgent}
        onUpdateAgent={onUpdateAgent}
        onDeleteAgent={onDeleteAgent}
        onDuplicateAgent={(duplicated) => {
          onAgentDuplicated?.(duplicated);
          setEditingAgent(duplicated);
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
                      agent.key === selectedAgentKey
                        ? "mdc-chat-ws-directory__card--active"
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    <button
                      type="button"
                      className="mdc-chat-ws-directory__card-main"
                      onClick={() => onSelectAgent?.(agent.key)}
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
                      <span>{icebreakerCount} quebra-gelos</span>
                      {capabilities.length > 0 ? (
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
                        onClick={() => onSelectAgent?.(agent.key)}
                      >
                        Usar
                      </button>

                      {editable ? (
                        <button
                          type="button"
                          className="mdc-chat-ws-toolbar-btn"
                          onClick={() => setEditingAgent(agent)}
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
                            const confirmed = window.confirm(
                              `Excluir o agente "${agent.name}"?`,
                            );

                            if (confirmed) {
                              void onDeleteAgent?.(agent.id);
                            }
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
