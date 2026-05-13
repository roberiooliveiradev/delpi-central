import {
  ArrowLeft,
  Bot,
  Check,
  FileText,
  Plus,
  Sparkles,
  Trash2,
  X,
  Zap,
} from "lucide-react";
import { useMemo, useState } from "react";

import type { ChatAgent } from "../../data/api/chatTypes";

import "./ChatAgentBuilderPage.css";

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

type ChatAgentBuilderPageProps = {
  agent?: ChatAgent | null;
  onBack: () => void;
  onSelectAgent?: (agentKey: string | null) => void;
  onCreateAgent?: (payload: AgentPayload) => Promise<ChatAgent | null>;
  onUpdateAgent?: (
    agentId: string,
    payload: AgentUpdatePayload,
  ) => Promise<ChatAgent | null>;
  onDeleteAgent?: (agentId: string) => Promise<boolean>;
};

function createKeyFromName(name: string): string {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function getAgentIcebreakers(agent?: ChatAgent | null): string[] {
  const value = agent?.metadata?.icebreakers;

  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean);
}

function getMetadataRecord(
  metadata: Record<string, unknown> | null | undefined,
  key: string,
): Record<string, unknown> {
  const value = metadata?.[key];

  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }

  return value as Record<string, unknown>;
}

function getMetadataStringArray(
  metadata: Record<string, unknown> | null | undefined,
  key: string,
): string[] {
  const value = metadata?.[key];

  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

export function ChatAgentBuilderPage({
  agent,
  onBack,
  onSelectAgent,
  onCreateAgent,
  onUpdateAgent,
  onDeleteAgent,
}: ChatAgentBuilderPageProps) {
  const isEditing = Boolean(agent);

  const [key, setKey] = useState(agent?.key ?? "");
  const [name, setName] = useState(agent?.name ?? "");
  const [description, setDescription] = useState(agent?.description ?? "");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [visibility, setVisibility] = useState(agent?.visibility === "public" ? "public" : "private");
  const [category, setCategory] = useState(agent?.category ?? "");
  const [icon, setIcon] = useState(agent?.icon ?? "bot");
  const [responseStyle, setResponseStyle] = useState(agent?.response_style ?? "objetivo");
  const [icebreakers, setIcebreakers] = useState<string[]>(
    getAgentIcebreakers(agent).length > 0 ? getAgentIcebreakers(agent) : [""],
  );

  const capabilities = getMetadataRecord(agent?.metadata, "capabilities");

  const [capActions, setCapActions] = useState(
    typeof capabilities.actions === "boolean" ? capabilities.actions : true,
  );
  const [capFiles, setCapFiles] = useState(
    typeof capabilities.files === "boolean" ? capabilities.files : true,
  );
  const [capCanvas, setCapCanvas] = useState(
    typeof capabilities.canvas === "boolean" ? capabilities.canvas : true,
  );

  const [allowedActions] = useState<string[]>(
    getMetadataStringArray(agent?.metadata, "allowed_actions"),
  );

  const [localError, setLocalError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const normalizedIcebreakers = useMemo(
    () => icebreakers.map((item) => item.trim()).filter(Boolean).slice(0, 8),
    [icebreakers],
  );

  function updateIcebreaker(index: number, value: string) {
    setIcebreakers((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? value : item)),
    );
  }

  function removeIcebreaker(index: number) {
    setIcebreakers((current) => {
      const next = current.filter((_, itemIndex) => itemIndex !== index);
      return next.length > 0 ? next : [""];
    });
  }

  function addIcebreaker() {
    setIcebreakers((current) => {
      if (current.length >= 8) {
        return current;
      }

      return [...current, ""];
    });
  }

  async function submitForm() {
    const normalizedName = name.trim();

    if (!normalizedName) {
      setLocalError("Informe o nome do agente.");
      return;
    }

    const normalizedKey = key.trim() || createKeyFromName(normalizedName);

    if (!normalizedKey) {
      setLocalError("Informe uma chave válida para o agente.");
      return;
    }

    const metadata = {
      ...(agent?.metadata ?? {}),
      icebreakers: normalizedIcebreakers,
      allowed_actions: allowedActions,
      capabilities: {
        ...capabilities,
        actions: capActions,
        files: capFiles,
        canvas: capCanvas,
      },
    };

    const payload: AgentPayload = {
      key: normalizedKey,
      name: normalizedName,
      description: description.trim() || null,
      systemPrompt: systemPrompt.trim() || null,
      visibility,
      category: category.trim() || null,
      icon: icon.trim() || null,
      responseStyle,
      metadata,
    };

    setIsSaving(true);
    setLocalError(null);

    try {
      if (agent) {
        const updated = await onUpdateAgent?.(agent.id, payload);

        if (updated) {
          onSelectAgent?.(updated.key);
          onBack();
        }

        return;
      }

      const created = await onCreateAgent?.(payload);

      if (created) {
        onSelectAgent?.(created.key);
        onBack();
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteCurrentAgent() {
    if (!agent) {
      return;
    }

    const confirmed = window.confirm(`Excluir o agente "${agent.name}"?`);

    if (!confirmed) {
      return;
    }

    const deleted = await onDeleteAgent?.(agent.id);

    if (deleted) {
      onSelectAgent?.(null);
      onBack();
    }
  }

  return (
    <section className="mdc-chat-agent-builder" aria-label="Configurar agente">
      <header className="mdc-chat-agent-builder__topbar">
        <button type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Voltar para agentes</span>
        </button>

        <div>
          <span>{isEditing ? "Configurar agente" : "Criar agente"}</span>
          {isEditing ? <small>Última edição salva no agente</small> : null}
        </div>

        <div className="mdc-chat-agent-builder__topbar-actions">
          {agent ? (
            <button
              type="button"
              className="mdc-chat-agent-builder__danger"
              onClick={() => void deleteCurrentAgent()}
            >
              <Trash2 size={17} aria-hidden="true" />
              <span>Excluir</span>
            </button>
          ) : null}

          <button
            type="button"
            className="mdc-chat-agent-builder__primary"
            disabled={isSaving}
            onClick={() => void submitForm()}
          >
            <Check size={17} aria-hidden="true" />
            <span>{isSaving ? "Salvando..." : isEditing ? "Atualizar" : "Criar"}</span>
          </button>
        </div>
      </header>

      <div className="mdc-chat-agent-builder__layout">
        <form
          className="mdc-chat-agent-builder__form"
          onSubmit={(event) => {
            event.preventDefault();
            void submitForm();
          }}
        >
          <div className="mdc-chat-agent-builder__switch">
            <span>Criar</span>
            <strong>Configurar</strong>
          </div>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <Bot size={18} aria-hidden="true" />
              <div>
                <h2>Identidade</h2>
                <p>Nome, descrição e aparência do especialista.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-builder__grid">
              <label>
                <span>Nome</span>
                <input
                  value={name}
                  maxLength={120}
                  onChange={(event) => {
                    const nextName = event.target.value;
                    setName(nextName);

                    if (!isEditing && !key.trim()) {
                      setKey(createKeyFromName(nextName));
                    }
                  }}
                  placeholder="Especialista em Produtos DELPI"
                />
              </label>

              <label>
                <span>Chave</span>
                <input
                  value={key}
                  maxLength={80}
                  disabled={isEditing}
                  onChange={(event) => setKey(event.target.value)}
                  placeholder="especialista-produtos"
                />
              </label>
            </div>

            <label>
              <span>Descrição</span>
              <textarea
                value={description}
                rows={3}
                maxLength={900}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Explique quando este agente deve ser usado..."
              />
            </label>

            <div className="mdc-chat-agent-builder__grid mdc-chat-agent-builder__grid--three">
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
                  placeholder="Produtos"
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
            </div>
          </section>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <FileText size={18} aria-hidden="true" />
              <div>
                <h2>Instruções</h2>
                <p>Defina comportamento, regras, limites e estilo de resposta.</p>
              </div>
            </div>

            <label>
              <span>Instruções do agente</span>
              <textarea
                className="mdc-chat-agent-builder__prompt"
                value={systemPrompt}
                maxLength={12000}
                onChange={(event) => setSystemPrompt(event.target.value)}
                placeholder="Defina comportamento, tom, limites, regras e ações permitidas..."
              />
              <small>
                Ao editar, preencha apenas se quiser substituir as instruções atuais.
              </small>
            </label>

            <label>
              <span>Estilo de resposta</span>
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
          </section>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <Sparkles size={18} aria-hidden="true" />
              <div>
                <h2>Quebra-gelos</h2>
                <p>Perguntas iniciais opcionais exibidas na home do agente.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-builder__icebreakers">
              {icebreakers.map((icebreaker, index) => (
                <div key={`${index}-${icebreakers.length}`}>
                  <input
                    value={icebreaker}
                    maxLength={180}
                    onChange={(event) => updateIcebreaker(index, event.target.value)}
                    placeholder="Ex.: Quero verificar um desenho."
                  />

                  <button
                    type="button"
                    onClick={() => removeIcebreaker(index)}
                    aria-label="Remover quebra-gelo"
                  >
                    <X size={16} aria-hidden="true" />
                  </button>
                </div>
              ))}

              <button
                type="button"
                className="mdc-chat-agent-builder__secondary"
                onClick={addIcebreaker}
                disabled={icebreakers.length >= 8}
              >
                <Plus size={16} aria-hidden="true" />
                <span>Adicionar quebra-gelo</span>
              </button>
            </div>
          </section>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <Zap size={18} aria-hidden="true" />
              <div>
                <h2>Recursos e actions</h2>
                <p>Preparado no front; o backend conectará catálogo e permissões.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-builder__toggles">
              <label>
                <input
                  type="checkbox"
                  checked={capActions}
                  onChange={(event) => setCapActions(event.target.checked)}
                />
                <span>Permitir actions</span>
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={capFiles}
                  onChange={(event) => setCapFiles(event.target.checked)}
                />
                <span>Permitir documentos/fontes</span>
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={capCanvas}
                  onChange={(event) => setCapCanvas(event.target.checked)}
                />
                <span>Permitir lousa/canvas</span>
              </label>
            </div>

            <div className="mdc-chat-agent-builder__placeholder">
              <strong>Actions disponíveis</strong>
              <p>
                A interface já salva <code>metadata.allowed_actions</code>. A listagem
                real das actions será conectada no backend.
              </p>
            </div>
          </section>

          {localError ? (
            <p className="mdc-chat-agent-builder__error">{localError}</p>
          ) : null}
        </form>

        <aside className="mdc-chat-agent-builder__preview">
          <div className="mdc-chat-agent-builder__preview-label">Pré-visualizar</div>

          <div className="mdc-chat-agent-builder__preview-card">
            <div className="mdc-chat-agent-builder__preview-avatar">
              <Bot size={26} aria-hidden="true" />
            </div>

            <h2>{name.trim() || "Novo agente"}</h2>

            <p>
              {description.trim() ||
                "Configure comportamento, instruções e quebra-gelos deste especialista."}
            </p>

            {normalizedIcebreakers.length > 0 ? (
              <div className="mdc-chat-agent-builder__preview-icebreakers">
                {normalizedIcebreakers.slice(0, 3).map((icebreaker) => (
                  <button key={icebreaker} type="button">
                    {icebreaker}
                  </button>
                ))}
              </div>
            ) : null}

            <div className="mdc-chat-agent-builder__preview-input">
              Pergunte alguma coisa
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
