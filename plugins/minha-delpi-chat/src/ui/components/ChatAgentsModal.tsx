import { Bot, Check, Pencil, Plus, Share2, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ChatAgent } from "../../data/api/chatTypes";
import { ChatConfirmDialog } from "./ChatConfirmDialog";

import "./ChatAgentsModal.css";

type ChatAgentsModalProps = {
  open: boolean;
  agents: ChatAgent[];
  selectedAgentKey?: string | null;
  isLoading?: boolean;
  onClose: () => void;
  onSelectAgent?: (agentKey: string | null) => void;
  onCreateAgent?: (payload: {
    key?: string | null;
    name: string;
    description?: string | null;
    systemPrompt?: string | null;
    visibility?: string;
    category?: string | null;
    icon?: string | null;
    responseStyle?: string | null;
  }) => Promise<ChatAgent | null>;
  onUpdateAgent?: (
    agentId: string,
    payload: {
      name?: string;
      description?: string | null;
      systemPrompt?: string | null;
      visibility?: string;
      category?: string | null;
      icon?: string | null;
      responseStyle?: string | null;
      enabled?: boolean;
    },
  ) => Promise<ChatAgent | null>;
  onDeleteAgent?: (agentId: string) => Promise<boolean>;
  onShareAgent?: (
    agentId: string,
    payload: { targetUserId: string; role: string },
  ) => Promise<boolean>;
};

type AgentFormMode = "create" | "edit";

function canEditAgent(agent: ChatAgent): boolean {
  return ["owner", "editor"].includes(agent.access_role);
}

function canDeleteAgent(agent: ChatAgent): boolean {
  return agent.access_role === "owner";
}

export function ChatAgentsModal({
  open,
  agents,
  selectedAgentKey,
  isLoading,
  onClose,
  onSelectAgent,
  onCreateAgent,
  onUpdateAgent,
  onDeleteAgent,
  onShareAgent,
}: ChatAgentsModalProps) {
  const [mode, setMode] = useState<AgentFormMode>("create");
  const [editingAgentId, setEditingAgentId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ChatAgent | null>(null);
  const [shareTarget, setShareTarget] = useState<ChatAgent | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [visibility, setVisibility] = useState("private");
  const [category, setCategory] = useState("");
  const [icon, setIcon] = useState("bot");
  const [responseStyle, setResponseStyle] = useState("objetivo");
  const [targetUserId, setTargetUserId] = useState("");
  const [shareRole, setShareRole] = useState("viewer");

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.key === selectedAgentKey) ?? null,
    [agents, selectedAgentKey],
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    startCreate();
    setShareTarget(null);
    setDeleteTarget(null);
  }, [open]);

  if (!open) {
    return null;
  }

  function startCreate() {
    setMode("create");
    setEditingAgentId(null);
    setKey("");
    setName("");
    setDescription("");
    setSystemPrompt("");
    setVisibility("private");
    setCategory("");
    setIcon("bot");
    setResponseStyle("objetivo");
    setTargetUserId("");
    setShareRole("viewer");
    setLocalError(null);
  }

  function startEdit(agent: ChatAgent) {
    setMode("edit");
    setEditingAgentId(agent.id);
    setKey(agent.key);
    setName(agent.name);
    setDescription(agent.description ?? "");
    setSystemPrompt("");
    setVisibility(agent.visibility === "public" ? "public" : "private");
    setCategory(agent.category ?? "");
    setIcon(agent.icon ?? "bot");
    setResponseStyle(agent.response_style ?? "objetivo");
    setLocalError(null);
  }

  async function submitForm() {
    const normalizedName = name.trim();

    if (!normalizedName) {
      setLocalError("Informe o nome do agente.");
      return;
    }

    const payload = {
      key: key.trim() || null,
      name: normalizedName,
      description: description.trim() || null,
      systemPrompt: systemPrompt.trim() || null,
      visibility,
      category: category.trim() || null,
      icon: icon.trim() || null,
      responseStyle: responseStyle.trim() || null,
    };

    if (mode === "create") {
      const created = await onCreateAgent?.(payload);

      if (created) {
        onSelectAgent?.(created.key);
        startCreate();
      }

      return;
    }

    if (!editingAgentId) {
      setLocalError("Agente inválido para edição.");
      return;
    }

    const updated = await onUpdateAgent?.(editingAgentId, payload);

    if (updated) {
      startCreate();
    }
  }

  async function confirmDeleteAgent() {
    if (!deleteTarget) {
      return;
    }

    const deleted = await onDeleteAgent?.(deleteTarget.id);

    if (deleted) {
      if (selectedAgentKey === deleteTarget.key) {
        onSelectAgent?.(null);
      }

      setDeleteTarget(null);
      startCreate();
    }
  }

  async function submitShare() {
    if (!shareTarget || !targetUserId.trim()) {
      setLocalError("Informe o ID do usuário que receberá acesso.");
      return;
    }

    const shared = await onShareAgent?.(shareTarget.id, {
      targetUserId: targetUserId.trim(),
      role: shareRole,
    });

    if (shared) {
      setShareTarget(null);
      setTargetUserId("");
      setShareRole("viewer");
      setLocalError(null);
    }
  }

  return (
    <div
      className="mdc-chat-agents-modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        className="mdc-chat-agents-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mdc-chat-agents-modal-title"
      >
        <header className="mdc-chat-agents-modal__header">
          <div>
            <p className="mdc-chat-eyebrow">Especialistas</p>
            <h2 id="mdc-chat-agents-modal-title">Agentes</h2>
            <span>
              Agentes definem comportamento, conhecimento e actions disponíveis.
            </span>
          </div>

          <button type="button" onClick={onClose} aria-label="Fechar">
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <div className="mdc-chat-agents-modal__body">
          <aside className="mdc-chat-agents-modal__list">
            <button
              type="button"
              className={
                selectedAgentKey
                  ? "mdc-chat-agents-modal__all"
                  : "mdc-chat-agents-modal__all mdc-chat-agents-modal__all--active"
              }
              onClick={() => onSelectAgent?.(null)}
            >
              <Bot size={17} aria-hidden="true" />
              <span>Chat comum</span>
            </button>

            {isLoading ? (
              <p className="mdc-chat-muted">Carregando agentes...</p>
            ) : agents.length === 0 ? (
              <p className="mdc-chat-muted">Nenhum agente disponível.</p>
            ) : (
              <div className="mdc-chat-agents-modal__items">
                {agents.map((agent) => (
                  <article
                    key={agent.id}
                    className={
                      agent.key === selectedAgentKey
                        ? "mdc-chat-agents-modal__item mdc-chat-agents-modal__item--active"
                        : "mdc-chat-agents-modal__item"
                    }
                  >
                    <button
                      type="button"
                      className="mdc-chat-agents-modal__item-main"
                      onClick={() => onSelectAgent?.(agent.key)}
                    >
                      <Bot size={17} aria-hidden="true" />
                      <span>
                        <strong>{agent.name}</strong>
                        <small>
                          {agent.category || agent.visibility} · {agent.access_role}
                        </small>
                      </span>
                    </button>

                    <div className="mdc-chat-agents-modal__item-actions">
                      {canEditAgent(agent) ? (
                        <button
                          type="button"
                          onClick={() => startEdit(agent)}
                          aria-label="Editar agente"
                          title="Editar"
                        >
                          <Pencil size={15} aria-hidden="true" />
                        </button>
                      ) : null}

                      {agent.access_role === "owner" ? (
                        <button
                          type="button"
                          onClick={() => setShareTarget(agent)}
                          aria-label="Compartilhar agente"
                          title="Compartilhar"
                        >
                          <Share2 size={15} aria-hidden="true" />
                        </button>
                      ) : null}

                      {canDeleteAgent(agent) ? (
                        <button
                          type="button"
                          onClick={() => setDeleteTarget(agent)}
                          aria-label="Excluir agente"
                          title="Excluir"
                        >
                          <Trash2 size={15} aria-hidden="true" />
                        </button>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </aside>

          <form
            className="mdc-chat-agents-modal__form"
            onSubmit={(event) => {
              event.preventDefault();
              void submitForm();
            }}
          >
            <div className="mdc-chat-agents-modal__form-title">
              {mode === "create" ? (
                <Plus size={18} aria-hidden="true" />
              ) : (
                <Pencil size={18} aria-hidden="true" />
              )}
              <div>
                <h3>{mode === "create" ? "Novo agente" : "Editar agente"}</h3>
                <p>
                  Configure o especialista usado em chats comuns ou dentro de projetos.
                </p>
              </div>
            </div>

            {selectedAgent ? (
              <div className="mdc-chat-agents-modal__selected">
                Agente ativo: <strong>{selectedAgent.name}</strong>
              </div>
            ) : (
              <div className="mdc-chat-agents-modal__selected">
                Sem agente ativo. O chat usará o comportamento geral.
              </div>
            )}

            <div className="mdc-chat-agents-modal__grid">
              <label>
                <span>Nome</span>
                <input value={name} maxLength={120} onChange={(event) => setName(event.target.value)} />
              </label>

              <label>
                <span>Chave</span>
                <input
                  value={key}
                  maxLength={80}
                  disabled={mode === "edit"}
                  onChange={(event) => setKey(event.target.value)}
                  placeholder="ex.: produtos-estoque"
                />
              </label>
            </div>

            <label>
              <span>Descrição</span>
              <textarea value={description} maxLength={800} onChange={(event) => setDescription(event.target.value)} />
            </label>

            <label>
              <span>System prompt</span>
              <textarea
                value={systemPrompt}
                className="mdc-chat-agents-modal__prompt"
                maxLength={12000}
                onChange={(event) => setSystemPrompt(event.target.value)}
                placeholder="Defina como o agente deve se comportar..."
              />
            </label>

            <div className="mdc-chat-agents-modal__grid">
              <label>
                <span>Visibilidade</span>
                <select value={visibility} onChange={(event) => setVisibility(event.target.value)}>
                  <option value="private">Privado</option>
                  <option value="public">Público interno</option>
                </select>
              </label>

              <label>
                <span>Categoria</span>
                <input value={category} maxLength={80} onChange={(event) => setCategory(event.target.value)} />
              </label>

              <label>
                <span>Ícone</span>
                <input value={icon} maxLength={60} onChange={(event) => setIcon(event.target.value)} />
              </label>

              <label>
                <span>Estilo</span>
                <select value={responseStyle} onChange={(event) => setResponseStyle(event.target.value)}>
                  <option value="objetivo">Objetivo</option>
                  <option value="tecnico">Técnico</option>
                  <option value="executivo">Executivo</option>
                  <option value="detalhado">Detalhado</option>
                </select>
              </label>
            </div>

            {shareTarget ? (
              <div className="mdc-chat-agents-modal__share">
                <strong>Compartilhar: {shareTarget.name}</strong>
                <div className="mdc-chat-agents-modal__grid">
                  <label>
                    <span>ID do usuário</span>
                    <input value={targetUserId} onChange={(event) => setTargetUserId(event.target.value)} />
                  </label>

                  <label>
                    <span>Permissão</span>
                    <select value={shareRole} onChange={(event) => setShareRole(event.target.value)}>
                      <option value="viewer">Visualizador</option>
                      <option value="editor">Editor</option>
                    </select>
                  </label>
                </div>

                <div className="mdc-chat-agents-modal__form-actions">
                  <button type="button" onClick={() => setShareTarget(null)}>
                    Cancelar
                  </button>
                  <button type="button" className="mdc-chat-agents-modal__primary" onClick={() => void submitShare()}>
                    Compartilhar
                  </button>
                </div>
              </div>
            ) : null}

            {localError ? <p className="mdc-chat-agents-modal__error">{localError}</p> : null}

            <div className="mdc-chat-agents-modal__form-actions">
              {mode === "edit" ? (
                <button type="button" onClick={startCreate}>
                  Cancelar edição
                </button>
              ) : null}

              <button type="submit" className="mdc-chat-agents-modal__primary">
                <Check size={16} aria-hidden="true" />
                <span>{mode === "create" ? "Criar agente" : "Salvar agente"}</span>
              </button>
            </div>
          </form>
        </div>
      </section>

      <ChatConfirmDialog
        open={Boolean(deleteTarget)}
        danger
        title="Excluir agente?"
        description={`O agente "${deleteTarget?.name || "sem nome"}" será excluído.`}
        confirmLabel="Excluir"
        cancelLabel="Cancelar"
        onConfirm={confirmDeleteAgent}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
