import {
  ArrowLeft,
  Bot,
  ChevronRight,
  Pencil,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
  Zap,
} from "lucide-react";
import { useMemo, useState } from "react";

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
  isLoading?: boolean;
  onBack: () => void;
  onSelectAgent?: (agentKey: string | null) => void;
  onCreateAgent?: (payload: AgentPayload) => Promise<ChatAgent | null>;
  onUpdateAgent?: (
    agentId: string,
    payload: AgentUpdatePayload,
  ) => Promise<ChatAgent | null>;
  onDeleteAgent?: (agentId: string) => Promise<boolean>;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function canEditAgent(agent: ChatAgent): boolean {
  return ["owner", "editor", "system"].includes(agent.access_role);
}

function canDeleteAgent(agent: ChatAgent): boolean {
  return agent.access_role === "owner";
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
  isLoading,
  onBack,
  onSelectAgent,
  onCreateAgent,
  onUpdateAgent,
  onDeleteAgent,
  getAccessToken,
}: ChatAgentsPageProps) {
  const [editingAgent, setEditingAgent] = useState<ChatAgent | null | undefined>(undefined);
  const [actionsAgent, setActionsAgent] = useState<ChatAgent | null>(null);
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

  if (actionsAgent) {
    return (
      <ChatAgentActionsPage
        agent={actionsAgent}
        onBack={() => setActionsAgent(null)}
        getAccessToken={getAccessToken}
      />
    );
  }

  if (editingAgent !== undefined) {
    return (
      <ChatAgentBuilderPage
        agent={editingAgent}
        onBack={() => setEditingAgent(undefined)}
        onManageActions={
          editingAgent
            ? () => {
                setActionsAgent(editingAgent);
                setEditingAgent(undefined);
              }
            : undefined
        }
        onSelectAgent={onSelectAgent}
        onCreateAgent={onCreateAgent}
        onUpdateAgent={onUpdateAgent}
        onDeleteAgent={onDeleteAgent}
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
              <h2>Meus agentes</h2>
              <p>{agents.length} agente(s) disponível(is)</p>
            </div>
          </div>

          <div className="mdc-chat-agents-directory__list">
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
                const editable = canEditAgent(agent);

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
                            onClick={() => setActionsAgent(agent)}
                            title="Actions do agente"
                          >
                            <Zap size={15} aria-hidden="true" />
                            <span>Actions</span>
                          </button>

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

                      {canDeleteAgent(agent) ? (
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
