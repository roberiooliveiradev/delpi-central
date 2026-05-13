import {
  ArrowLeft,
  Bot,
  Check,
  MessageSquarePlus,
  Pencil,
  Plus,
  Settings,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ChatAgent } from "../../data/api/chatTypes";

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
};

type AgentFormMode = "create" | "edit";

function canEditAgent(agent: ChatAgent): boolean {
  return ["owner", "editor", "system"].includes(agent.access_role);
}

function canDeleteAgent(agent: ChatAgent): boolean {
  return agent.access_role === "owner";
}

function getAgentIcebreakers(agent: ChatAgent | null): string[] {
  const value = agent?.metadata?.icebreakers;

  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean);
}

function createKeyFromName(name: string): string {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
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
}: ChatAgentsPageProps) {
  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.key === selectedAgentKey) ?? null,
    [agents, selectedAgentKey],
  );

  const [mode, setMode] = useState<AgentFormMode>("create");
  const [editingAgent, setEditingAgent] = useState<ChatAgent | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [visibility, setVisibility] = useState("private");
  const [category, setCategory] = useState("");
  const [icon, setIcon] = useState("bot");
  const [responseStyle, setResponseStyle] = useState("objetivo");
  const [icebreakers, setIcebreakers] = useState("");

  const previewIcebreakers = useMemo(() => {
    const currentLines = icebreakers
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);

    if (currentLines.length > 0) {
      return currentLines.slice(0, 6);
    }

    return getAgentIcebreakers(selectedAgent).slice(0, 6);
  }, [icebreakers, selectedAgent]);

  useEffect(() => {
    if (selectedAgent && mode === "create") {
      fillFormFromAgent(selectedAgent);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAgentKey]);

  function resetForm() {
    setMode("create");
    setEditingAgent(null);
    setKey("");
    setName("");
    setDescription("");
    setSystemPrompt("");
    setVisibility("private");
    setCategory("");
    setIcon("bot");
    setResponseStyle("objetivo");
    setIcebreakers("");
    setLocalError(null);
  }

  function fillFormFromAgent(agent: ChatAgent) {
    setMode("edit");
    setEditingAgent(agent);
    setKey(agent.key);
    setName(agent.name);
    setDescription(agent.description ?? "");
    setSystemPrompt("");
    setVisibility(agent.visibility === "public" ? "public" : "private");
    setCategory(agent.category ?? "");
    setIcon(agent.icon ?? "bot");
    setResponseStyle(agent.response_style ?? "objetivo");
    setIcebreakers(getAgentIcebreakers(agent).join("\n"));
    setLocalError(null);
  }

  async function submitForm() {
    const normalizedName = name.trim();

    if (!normalizedName) {
      setLocalError("Informe o nome do agente.");
      return;
    }

    const normalizedIcebreakers = icebreakers
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, 8);

    const nextMetadata = {
      ...(editingAgent?.metadata ?? {}),
      icebreakers: normalizedIcebreakers,
    };

    const payload: AgentPayload = {
      key: key.trim() || createKeyFromName(normalizedName) || null,
      name: normalizedName,
      description: description.trim() || null,
      systemPrompt: systemPrompt.trim() || null,
      visibility,
      category: category.trim() || null,
      icon: icon.trim() || null,
      responseStyle: responseStyle.trim() || null,
      metadata: nextMetadata,
    };

    setIsSaving(true);
    setLocalError(null);

    try {
      if (mode === "create") {
        const created = await onCreateAgent?.(payload);

        if (created) {
          onSelectAgent?.(created.key);
          fillFormFromAgent(created);
        }

        return;
      }

      if (!editingAgent) {
        setLocalError("Agente inválido para edição.");
        return;
      }

      const updated = await onUpdateAgent?.(editingAgent.id, payload);

      if (updated) {
        onSelectAgent?.(updated.key);
        fillFormFromAgent(updated);
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteAgent(agent: ChatAgent) {
    const confirmed = window.confirm(`Excluir o agente "${agent.name}"?`);

    if (!confirmed) {
      return;
    }

    const deleted = await onDeleteAgent?.(agent.id);

    if (deleted) {
      if (selectedAgentKey === agent.key) {
        onSelectAgent?.(null);
      }

      resetForm();
    }
  }

  return (
    <section className="mdc-chat-agents-page" aria-label="Gerenciamento de agentes">
      <header className="mdc-chat-agents-page__topbar">
        <button type="button" onClick={onBack}>
          <ArrowLeft size={17} aria-hidden="true" />
          <span>Voltar ao chat</span>
        </button>

        <div>
          <Bot size={18} aria-hidden="true" />
          <span>Agentes</span>
        </div>
      </header>

      <div className="mdc-chat-agents-page__layout">
        <aside className="mdc-chat-agents-page__sidebar">
          <div className="mdc-chat-agents-page__sidebar-header">
            <div>
              <p className="mdc-chat-eyebrow">Especialistas</p>
              <h1>Agentes</h1>
            </div>

            <button type="button" onClick={resetForm} title="Novo agente">
              <Plus size={17} aria-hidden="true" />
            </button>
          </div>

          <button
            type="button"
            className={
              selectedAgentKey
                ? "mdc-chat-agent-list-item"
                : "mdc-chat-agent-list-item mdc-chat-agent-list-item--active"
            }
            onClick={() => {
              onSelectAgent?.(null);
              resetForm();
            }}
          >
            <span>
              <MessageSquarePlus size={16} aria-hidden="true" />
            </span>
            <strong>Chat comum</strong>
            <small>Sem agente ativo</small>
          </button>

          {isLoading ? (
            <p className="mdc-chat-muted">Carregando agentes...</p>
          ) : agents.length === 0 ? (
            <p className="mdc-chat-muted">Nenhum agente disponível.</p>
          ) : (
            <div className="mdc-chat-agents-page__list">
              {agents.map((agent) => {
                const icebreakerCount = getAgentIcebreakers(agent).length;

                return (
                  <article
                    key={agent.id}
                    className={
                      agent.key === selectedAgentKey
                        ? "mdc-chat-agent-list-item mdc-chat-agent-list-item--active"
                        : "mdc-chat-agent-list-item"
                    }
                  >
                    <button
                      type="button"
                      onClick={() => {
                        onSelectAgent?.(agent.key);
                        fillFormFromAgent(agent);
                      }}
                    >
                      <span>
                        <Bot size={16} aria-hidden="true" />
                      </span>

                      <strong>{agent.name}</strong>
                      <small>
                        {agent.category || agent.visibility}
                        {icebreakerCount > 0 ? ` · ${icebreakerCount} quebra-gelos` : ""}
                      </small>
                    </button>

                    <div className="mdc-chat-agent-list-item__actions">
                      {canEditAgent(agent) ? (
                        <button
                          type="button"
                          onClick={() => fillFormFromAgent(agent)}
                          title="Editar"
                        >
                          <Pencil size={14} aria-hidden="true" />
                        </button>
                      ) : null}

                      {canDeleteAgent(agent) ? (
                        <button
                          type="button"
                          onClick={() => void deleteAgent(agent)}
                          title="Excluir"
                        >
                          <Trash2 size={14} aria-hidden="true" />
                        </button>
                      ) : null}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </aside>

        <main className="mdc-chat-agents-page__main">
          <section className="mdc-chat-agent-preview">
            <div className="mdc-chat-agent-preview__hero">
              <span>
                <Bot size={24} aria-hidden="true" />
              </span>

              <div>
                <p className="mdc-chat-eyebrow">Agente</p>
                <h2>{name.trim() || selectedAgent?.name || "Novo agente"}</h2>
                <p>
                  {description.trim() ||
                    selectedAgent?.description ||
                    "Configure comportamento, instruções e quebra-gelos deste especialista."}
                </p>
              </div>
            </div>

            <div className="mdc-chat-agent-preview__composer">
              <span>Pergunte a este agente...</span>
            </div>

            {previewIcebreakers.length > 0 ? (
              <div className="mdc-chat-agent-preview__icebreakers">
                <strong>Quebra-gelos</strong>

                <div>
                  {previewIcebreakers.map((icebreaker) => (
                    <button
                      key={icebreaker}
                      type="button"
                      title="Preview do quebra-gelo"
                    >
                      <Sparkles size={14} aria-hidden="true" />
                      <span>{icebreaker}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="mdc-chat-agent-preview__empty">
                <Sparkles size={18} aria-hidden="true" />
                <span>Este agente ainda não possui quebra-gelos.</span>
              </div>
            )}
          </section>

          <form
            className="mdc-chat-agent-form"
            onSubmit={(event) => {
              event.preventDefault();
              void submitForm();
            }}
          >
            <div className="mdc-chat-agent-form__title">
              {mode === "create" ? (
                <Plus size={18} aria-hidden="true" />
              ) : (
                <Settings size={18} aria-hidden="true" />
              )}

              <div>
                <h3>{mode === "create" ? "Criar agente" : "Configurar agente"}</h3>
                <p>
                  Defina como o especialista se comporta e quais perguntas iniciais
                  aparecem para o usuário.
                </p>
              </div>
            </div>

            <div className="mdc-chat-agent-form__grid">
              <label>
                <span>Nome</span>
                <input
                  value={name}
                  maxLength={120}
                  onChange={(event) => {
                    setName(event.target.value);

                    if (mode === "create" && !key.trim()) {
                      setKey(createKeyFromName(event.target.value));
                    }
                  }}
                  placeholder="Ex.: Produtos e estoque"
                />
              </label>

              <label>
                <span>Chave</span>
                <input
                  value={key}
                  maxLength={80}
                  disabled={mode === "edit"}
                  onChange={(event) => setKey(event.target.value)}
                  placeholder="produtos-estoque"
                />
              </label>
            </div>

            <label>
              <span>Descrição</span>
              <textarea
                value={description}
                maxLength={800}
                rows={3}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Explique quando este agente deve ser usado..."
              />
            </label>

            <label>
              <span>Instruções do agente</span>
              <textarea
                value={systemPrompt}
                className="mdc-chat-agent-form__prompt"
                maxLength={12000}
                onChange={(event) => setSystemPrompt(event.target.value)}
                placeholder="Defina comportamento, tom, limites, regras e ações permitidas..."
              />
              <small>
                Ao editar um agente, preencha apenas se quiser substituir as instruções atuais.
              </small>
            </label>

            <label>
              <span>Quebra-gelos</span>
              <textarea
                value={icebreakers}
                rows={5}
                maxLength={1600}
                onChange={(event) => setIcebreakers(event.target.value)}
                placeholder={"Um por linha. Ex.:\nConsultar produto 10080022\nQuais apps eu tenho acesso?\nListe minhas LMPs recentes"}
              />
              <small>
                Opcional. Se vazio, o agente não exibirá quebra-gelos próprios.
              </small>
            </label>

            <div className="mdc-chat-agent-form__grid">
              <label>
                <span>Visibilidade</span>
                <select
                  value={visibility}
                  onChange={(event) => setVisibility(event.target.value)}
                >
                  <option value="private">Privado</option>
                  <option value="public">Público interno</option>
                </select>
              </label>

              <label>
                <span>Categoria</span>
                <input
                  value={category}
                  maxLength={80}
                  onChange={(event) => setCategory(event.target.value)}
                  placeholder="Ex.: Estoque"
                />
              </label>

              <label>
                <span>Ícone</span>
                <input
                  value={icon}
                  maxLength={60}
                  onChange={(event) => setIcon(event.target.value)}
                  placeholder="bot"
                />
              </label>

              <label>
                <span>Estilo</span>
                <select
                  value={responseStyle}
                  onChange={(event) => setResponseStyle(event.target.value)}
                >
                  <option value="objetivo">Objetivo</option>
                  <option value="tecnico">Técnico</option>
                  <option value="executivo">Executivo</option>
                  <option value="detalhado">Detalhado</option>
                </select>
              </label>
            </div>

            {localError ? (
              <p className="mdc-chat-agent-form__error">{localError}</p>
            ) : null}

            <footer>
              {mode === "edit" ? (
                <button type="button" onClick={resetForm}>
                  Novo agente
                </button>
              ) : null}

              <button
                type="submit"
                className="mdc-chat-agent-form__primary"
                disabled={isSaving}
              >
                <Check size={16} aria-hidden="true" />
                <span>
                  {isSaving
                    ? "Salvando..."
                    : mode === "create"
                      ? "Criar agente"
                      : "Salvar agente"}
                </span>
              </button>
            </footer>
          </form>
        </main>
      </div>
    </section>
  );
}
