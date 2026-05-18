import {
  ArrowLeft,
  BarChart3,
  Bot,
  ChevronRight,
  Pencil,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import type { ChatAgent } from "../../data/api/chatTypes";
import { ChatAgentActionsPage } from "./ChatAgentActionsPage";
import { ChatAgentBuilderPage } from "./ChatAgentBuilderPage";

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
  const [actionEditor, setActionEditor] = useState<{
    agent: ChatAgent;
    providerKey?: string | null;
  } | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const onReloadAgentsRef = useRef(onReloadAgents);
  onReloadAgentsRef.current = onReloadAgents;

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
      void onReloadAgentsRef.current?.(false, true);
    }
  }, [canManageAgents]);

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

  if (actionEditor) {
    return (
      <ChatAgentActionsPage
        agent={actionEditor.agent}
        providerKey={actionEditor.providerKey}
        onBack={() => setActionEditor(null)}
        getAccessToken={getAccessToken}
      />
    );
  }

  if (editingAgent !== undefined && (editingAgent !== null || canManageAgents)) {
    return (
      <ChatAgentBuilderPage
        agent={editingAgent}
        onBack={() => setEditingAgent(undefined)}
        onCreateAction={
          editingAgent
            ? () => {
                setActionEditor({ agent: editingAgent, providerKey: null });
                setEditingAgent(undefined);
              }
            : undefined
        }
        onConfigureAction={
          editingAgent
            ? (_agent, providerKey) => {
                setActionEditor({ agent: editingAgent, providerKey });
                setEditingAgent(undefined);
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
    );
  }

  return (
    <section className="mdc-chat-agents-directory" aria-label="Agentes">
      <header className="mdc-chat-agents-directory__topbar">
        <button type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Voltar ao chat</span>
        </button>

        <div>
          <Bot size={18} aria-hidden="true" />
          <span>Agentes</span>
        </div>
      </header>

      <main className="mdc-chat-agents-directory__main">
        <section className="mdc-chat-agents-directory__hero">
          <p className="mdc-chat-eyebrow">Especialistas da Minha DELPI</p>
          <h1>Agentes</h1>
          <p>
            Crie especialistas com instruções, conhecimento, quebra-gelos e actions
            OpenAPI configuradas por agente.
          </p>

          <div className="mdc-chat-agents-directory__search">
            <Search size={18} aria-hidden="true" />
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Buscar agentes"
            />
          </div>
        </section>

        <section className="mdc-chat-agents-directory__mine">
          <div className="mdc-chat-agents-directory__section-header">
            <div>
              <h2>Agentes disponíveis</h2>
              <p>{agents.length} agente(s) disponível(is)</p>
            </div>

            {canManageAgents ? (
              <label className="mdc-chat-agents-directory__inactive-toggle">
                <input
                  type="checkbox"
                  checked={showInactive}
                  onChange={(event) => {
                    const includeDisabled = event.target.checked;
                    setShowInactive(includeDisabled);
                    void onReloadAgents?.(includeDisabled, canManageAgents);
                  }}
                />
                <span>Mostrar inativos</span>
              </label>
            ) : null}
          </div>

          <div className="mdc-chat-agents-directory__list">
            {canManageAgents ? (
              <article
                className="mdc-chat-agents-directory__item mdc-chat-agents-directory__item--create"
                role="button"
                tabIndex={0}
                onClick={() => setEditingAgent(null)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setEditingAgent(null);
                  }
                }}
              >
                <span className="mdc-chat-agents-directory__avatar mdc-chat-agents-directory__avatar--create">
                  <Plus size={20} aria-hidden="true" />
                </span>

                <span className="mdc-chat-agents-directory__item-copy">
                  <strong>Criar um agente</strong>
                  <small>Configure um especialista para um processo, API ou área específica.</small>
                </span>

                <span className="mdc-chat-agents-directory__item-arrow">
                  <ChevronRight size={18} aria-hidden="true" />
                </span>
              </article>
            ) : null}

            {isLoading ? (
              <p className="mdc-chat-muted">Carregando agentes...</p>
            ) : filteredAgents.length === 0 ? (
              <div className="mdc-chat-agents-directory__empty">
                <Bot size={22} aria-hidden="true" />
                <strong>Nenhum agente encontrado</strong>
                <p>Crie um especialista ou ajuste a busca.</p>
              </div>
            ) : (
              filteredAgents.map((agent) => {
                const icebreakerCount = getAgentIcebreakerCount(agent);
                const capabilities = getAgentCapabilities(agent);
                const editable = canEditAgent(
                  agent,
                  canManageAgents,
                  canManageOfficialAgents,
                );

                return (
                  <article
                    key={agent.id}
                    className={
                      agent.key === selectedAgentKey
                        ? "mdc-chat-agents-directory__item mdc-chat-agents-directory__item--active"
                        : "mdc-chat-agents-directory__item"
                    }
                  >
                    <button
                      type="button"
                      className="mdc-chat-agents-directory__item-main"
                      onClick={() => onSelectAgent?.(agent.key)}
                    >
                      <span className="mdc-chat-agents-directory__avatar">
                        <Bot size={20} aria-hidden="true" />
                      </span>

                      <span className="mdc-chat-agents-directory__item-copy">
                        <strong>{agent.name}</strong>
                        <small>
                          {agent.description ||
                            agent.category ||
                            "Especialista configurável"}
                        </small>
                      </span>
                    </button>

                    <div className="mdc-chat-agents-directory__meta">
                      {!agent.enabled ? <span className="mdc-chat-agents-directory__badge">Inativo</span> : null}
                      <span className="mdc-chat-agents-directory__badge">{agent.access_role}</span>
                      <span>
                        <Sparkles size={14} aria-hidden="true" />
                        {icebreakerCount} quebra-gelos
                      </span>

                      <span>
                        <ShieldCheck size={14} aria-hidden="true" />
                        {getOwnerLabel(agent)}
                      </span>

                      {capabilities.length > 0 ? (
                        <span>{capabilities.length} recursos</span>
                      ) : null}

                      {typeof agent.sessions_in_window === "number" ? (
                        <span>
                          <BarChart3 size={14} aria-hidden="true" />
                          {agent.sessions_in_window} conversas (7d)
                        </span>
                      ) : null}

                      {typeof agent.total_sessions === "number" && agent.total_sessions > 0 ? (
                        <span>{agent.total_sessions} conversas no total</span>
                      ) : null}
                    </div>

                    <div className="mdc-chat-agents-directory__actions">
                      <button
                        type="button"
                        className="mdc-chat-agents-directory__action-primary"
                        onClick={() => onSelectAgent?.(agent.key)}
                      >
                        Usar
                      </button>

                      {editable ? (
                        <>
                          <button
                            type="button"
                            className="mdc-chat-agents-directory__action-pill"
                            onClick={() => setEditingAgent(agent)}
                            title="Configurar agente"
                          >
                            <Pencil size={15} aria-hidden="true" />
                            <span>Configurar</span>
                          </button>
                        </>
                      ) : null}

                      {canDeleteAgent(agent, canManageAgents, canManageOfficialAgents) ? (
                        <button
                          type="button"
                          className="mdc-chat-agents-directory__danger"
                          onClick={() => {
                            const confirmed = window.confirm(
                              `Excluir o agente "${agent.name}"?`,
                            );

                            if (confirmed) {
                              void onDeleteAgent?.(agent.id);
                            }
                          }}
                          title="Excluir agente"
                        >
                          <Trash2 size={16} aria-hidden="true" />
                        </button>
                      ) : null}
                    </div>
                  </article>
                );
              })
            )}
          </div>
        </section>
      </main>
    </section>
  );
}
