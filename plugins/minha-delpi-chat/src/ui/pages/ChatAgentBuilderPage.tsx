import {
  ArrowLeft,
  BarChart3,
  Bot,
  Check,
  Copy,
  FileText,
  Plus,
  Send,
  Settings2,
  Sparkles,
  Trash2,
  Upload,
  Wand2,
  X,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createAgentTextSource,
  deleteChatSource,
  duplicateChatAgent,
  getChatAgent,
  getChatAgentStats,
  transferChatAgentOwnership,
  listAgentSources,
  listChatAgentActionProviders,
  listChatAgentShares,
  previewChatAgent,
  revokeChatAgentShare,
  shareChatAgent,
  uploadAgentSource,
} from "../../data/api/chatApi";
import { ChatUserSearchField } from "../components/ChatUserSearchField";
import type {
  ChatAgent,
  ChatAgentActionProvider,
  ChatAgentShare,
  ChatAgentStats,
  ChatWorkspaceSource,
} from "../../data/api/chatTypes";

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
  maxToolCalls?: number;
  requiresConfirmationForWrite?: boolean;
};

type ChatAgentBuilderPageProps = {
  agent?: ChatAgent | null;
  onBack: () => void;
  onCreateAction?: (agent: ChatAgent) => void;
  onConfigureAction?: (agent: ChatAgent, providerKey: string) => void;
  onSelectAgent?: (agentKey: string | null) => void;
  onCreateAgent?: (payload: AgentPayload) => Promise<ChatAgent | null>;
  onUpdateAgent?: (
    agentId: string,
    payload: AgentUpdatePayload,
  ) => Promise<ChatAgent | null>;
  onDeleteAgent?: (agentId: string) => Promise<boolean>;
  onDuplicateAgent?: (agent: ChatAgent) => void;
  canManageOfficialAgents?: boolean;
  onOpenRagAdmin?: (agentId: string) => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
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
  onCreateAction,
  onConfigureAction,
  onSelectAgent,
  onCreateAgent,
  onUpdateAgent,
  onDeleteAgent,
  onDuplicateAgent,
  canManageOfficialAgents = false,
  onOpenRagAdmin,
  getAccessToken,
}: ChatAgentBuilderPageProps) {
  const isEditing = Boolean(agent);
  const [builderMode, setBuilderMode] = useState<"create" | "configure">(
    agent ? "configure" : "create",
  );
  const [createBrief, setCreateBrief] = useState("");
  const [previewInput, setPreviewInput] = useState("");
  const [previewMessages, setPreviewMessages] = useState<
    Array<{ role: "user" | "assistant"; content: string }>
  >([]);

  const [key, setKey] = useState(agent?.key ?? "");
  const [name, setName] = useState(agent?.name ?? "");
  const [description, setDescription] = useState(agent?.description ?? "");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [visibility, setVisibility] = useState(
    agent?.visibility === "system"
      ? "system"
      : agent?.visibility === "public"
        ? "public"
        : "private",
  );
  const [category, setCategory] = useState(agent?.category ?? "");
  const [icon, setIcon] = useState(agent?.icon ?? "bot");
  const [responseStyle, setResponseStyle] = useState(agent?.response_style ?? "objetivo");
  const [enabled, setEnabled] = useState(agent?.enabled ?? true);
  const [maxToolCalls, setMaxToolCalls] = useState(agent?.max_tool_calls ?? 5);
  const [requiresConfirmationForWrite, setRequiresConfirmationForWrite] = useState(
    agent?.requires_confirmation_for_write ?? false,
  );
  const [shareTargetUserId, setShareTargetUserId] = useState("");
  const [shareRole, setShareRole] = useState<"viewer" | "editor">("viewer");
  const [isSharing, setIsSharing] = useState(false);
  const [shareMessage, setShareMessage] = useState<string | null>(null);
  const [agentShares, setAgentShares] = useState<ChatAgentShare[]>([]);
  const [isLoadingShares, setIsLoadingShares] = useState(false);
  const [revokingShareUserId, setRevokingShareUserId] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [isLoadingAgent, setIsLoadingAgent] = useState(false);
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

  const [agentActionProviders, setAgentActionProviders] = useState<ChatAgentActionProvider[]>([]);
  const [agentSources, setAgentSources] = useState<ChatWorkspaceSource[]>([]);
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceContent, setSourceContent] = useState("");
  const [isSavingSource, setIsSavingSource] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDuplicating, setIsDuplicating] = useState(false);
  const [copyActionsOnDuplicate, setCopyActionsOnDuplicate] = useState(true);
  const [copySourcesOnDuplicate, setCopySourcesOnDuplicate] = useState(false);
  const [transferTargetUserId, setTransferTargetUserId] = useState("");
  const [isTransferring, setIsTransferring] = useState(false);
  const [transferMessage, setTransferMessage] = useState<string | null>(null);
  const [updatingShareUserId, setUpdatingShareUserId] = useState<string | null>(null);
  const [agentStats, setAgentStats] = useState<ChatAgentStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);


  useEffect(() => {
    let isMounted = true;

    async function loadAgentDetails() {
      if (!agent?.id || !getAccessToken) {
        setAgentSources([]);
        setAgentActionProviders([]);
        return;
      }

      setIsLoadingAgent(true);
      setLocalError(null);

      try {
        const [details, sources, actionProviders] = await Promise.all([
          getChatAgent(agent.id, { getAccessToken }),
          listAgentSources(agent.id, { getAccessToken }),
          listChatAgentActionProviders(agent.id, { getAccessToken }),
        ]);

        if (!isMounted) {
          return;
        }

        setName(details.name);
        setDescription(details.description ?? "");
        setSystemPrompt(details.system_prompt ?? "");
        setVisibility(
          details.visibility === "system"
            ? "system"
            : details.visibility === "public"
              ? "public"
              : "private",
        );
        setCategory(details.category ?? "");
        setIcon(details.icon ?? "bot");
        setResponseStyle(details.response_style ?? "objetivo");
        setEnabled(details.enabled);
        setMaxToolCalls(details.max_tool_calls);
        setRequiresConfirmationForWrite(details.requires_confirmation_for_write);
        setIcebreakers(
          getAgentIcebreakers(details).length > 0 ? getAgentIcebreakers(details) : [""],
        );

        const nextCapabilities = getMetadataRecord(details.metadata, "capabilities");
        setCapActions(
          typeof nextCapabilities.actions === "boolean" ? nextCapabilities.actions : true,
        );
        setCapFiles(
          typeof nextCapabilities.files === "boolean" ? nextCapabilities.files : true,
        );
        setCapCanvas(
          typeof nextCapabilities.canvas === "boolean" ? nextCapabilities.canvas : true,
        );

        setAgentSources(sources);
        setAgentActionProviders(actionProviders);
      } catch {
        if (isMounted) {
          setLocalError("Não foi possível carregar os detalhes completos do agente.");
        }
      } finally {
        if (isMounted) {
          setIsLoadingAgent(false);
        }
      }
    }

    void loadAgentDetails();

    return () => {
      isMounted = false;
    };
  }, [agent?.id, getAccessToken]);



  async function uploadAgentKnowledgeFile(file: File | null | undefined) {
    if (!agent || !file) {
      return;
    }

    setIsSavingSource(true);

    try {
      await uploadAgentSource(agent.id, file, { getAccessToken });
      setAgentSources(await listAgentSources(agent.id, { getAccessToken }));
    } finally {
      setIsSavingSource(false);
    }
  }

  async function createAgentKnowledgeNote() {
    if (!agent || !sourceContent.trim()) {
      return;
    }

    setIsSavingSource(true);

    try {
      await createAgentTextSource(
        agent.id,
        {
          title: sourceTitle.trim() || "Nota do agente",
          content: sourceContent.trim(),
          metadata: {
            source: "agent_note",
          },
        },
        { getAccessToken },
      );

      setSourceTitle("");
      setSourceContent("");
      setAgentSources(await listAgentSources(agent.id, { getAccessToken }));
    } finally {
      setIsSavingSource(false);
    }
  }

  async function removeAgentSource(sourceId: string) {
    await deleteChatSource(sourceId, { getAccessToken });

    if (agent) {
      setAgentSources(await listAgentSources(agent.id, { getAccessToken }));
    }
  }

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

  function generateDraftFromBrief() {
    const brief = createBrief.trim();

    if (!brief) {
      setLocalError("Descreva o agente que deseja criar.");
      return;
    }

    const firstSentence = brief.split(/[.!?\n]/).find(Boolean)?.trim() || brief;
    const generatedName =
      name.trim() ||
      firstSentence
        .replace(/^crie\s+(um|uma)?\s*/i, "")
        .replace(/^agente\s+(para|de)?\s*/i, "")
        .slice(0, 80);

    const finalName = generatedName || "Novo agente";

    setName(finalName);
    setKey((current) => current.trim() || createKeyFromName(finalName));
    setDescription((current) => current.trim() || firstSentence.slice(0, 240));
    setSystemPrompt((current) => {
      if (current.trim()) {
        return current;
      }

      return [
        `Você é ${finalName}, um agente especializado da Minha DELPI.`,
        "",
        "Objetivo:",
        brief,
        "",
        "Regras:",
        "- Responda com clareza e objetividade.",
        "- Use fontes, arquivos e actions autorizadas quando estiverem configuradas.",
        "- Não invente dados operacionais; quando precisar, consulte as ferramentas disponíveis.",
        "- Explique limitações quando uma informação não estiver disponível.",
      ].join("\n");
    });

    setIcebreakers((current) => {
      const filled = current.map((item) => item.trim()).filter(Boolean);

      if (filled.length > 0) {
        return current;
      }

      return [
        "O que você consegue fazer?",
        "Quais informações você pode consultar?",
        "Me ajude com uma análise inicial.",
      ];
    });

    setBuilderMode("configure");
    setLocalError(null);
  }

  async function sendPreviewMessage(content?: string) {
    const message = (content ?? previewInput).trim();

    if (!message) {
      return;
    }

    setPreviewMessages((current) => [...current, { role: "user", content: message }]);
    setPreviewInput("");

    if (!agent?.id || !getAccessToken) {
      setPreviewMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "Salve o agente para usar a pré-visualização com instruções, fontes e actions reais.",
        },
      ]);
      return;
    }

    setIsPreviewLoading(true);

    try {
      const result = await previewChatAgent(
        agent.id,
        { message, generateAnswer: true },
        { getAccessToken },
      );
      const answer =
        (typeof result.answerPreview === "string" && result.answerPreview) ||
        (typeof result.answer === "string" && result.answer) ||
        "Sem resposta na pré-visualização.";

      setPreviewMessages((current) => [...current, { role: "assistant", content: answer }]);
    } catch {
      setPreviewMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: "Não foi possível gerar a pré-visualização deste agente.",
        },
      ]);
    } finally {
      setIsPreviewLoading(false);
    }
  }

  const loadAgentShares = useCallback(async () => {
    if (!agent?.id || agent.access_role !== "owner" || !getAccessToken) {
      setAgentShares([]);
      return;
    }

    setIsLoadingShares(true);

    try {
      const shares = await listChatAgentShares(agent.id, { getAccessToken });
      setAgentShares(shares);
    } catch {
      setAgentShares([]);
    } finally {
      setIsLoadingShares(false);
    }
  }, [agent?.access_role, agent?.id, getAccessToken]);

  useEffect(() => {
    void loadAgentShares();
  }, [loadAgentShares]);

  useEffect(() => {
    let isMounted = true;

    async function loadStats() {
      if (!agent?.id || !getAccessToken) {
        setAgentStats(null);
        return;
      }

      if (!["owner", "editor", "system"].includes(agent.access_role)) {
        setAgentStats(null);
        return;
      }

      setIsLoadingStats(true);

      try {
        const stats = await getChatAgentStats(agent.id, { getAccessToken, hours: 168 });

        if (isMounted) {
          setAgentStats(stats);
        }
      } catch {
        if (isMounted) {
          setAgentStats(null);
        }
      } finally {
        if (isMounted) {
          setIsLoadingStats(false);
        }
      }
    }

    void loadStats();

    return () => {
      isMounted = false;
    };
  }, [agent?.access_role, agent?.id, getAccessToken]);

  async function revokeAgentShare(targetUserId: string) {
    if (!agent?.id || !getAccessToken) {
      return;
    }

    setRevokingShareUserId(targetUserId);

    try {
      await revokeChatAgentShare(agent.id, targetUserId, { getAccessToken });
      setShareMessage("Acesso revogado.");
      await loadAgentShares();
    } catch {
      setShareMessage("Não foi possível revogar o acesso.");
    } finally {
      setRevokingShareUserId(null);
    }
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
        const updated = await onUpdateAgent?.(agent.id, {
          ...payload,
          enabled,
          maxToolCalls,
          requiresConfirmationForWrite,
        });

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

  async function updateAgentShareRole(targetUserId: string, role: "viewer" | "editor") {
    if (!agent?.id || !getAccessToken) {
      return;
    }

    setUpdatingShareUserId(targetUserId);
    setShareMessage(null);

    try {
      await shareChatAgent(
        agent.id,
        { targetUserId, role },
        { getAccessToken },
      );
      setShareMessage("Papel atualizado.");
      await loadAgentShares();
    } catch {
      setShareMessage("Não foi possível atualizar o papel.");
    } finally {
      setUpdatingShareUserId(null);
    }
  }

  async function transferAgentOwnership() {
    if (!agent?.id || !getAccessToken || agent.access_role !== "owner") {
      return;
    }

    const newOwnerUserId = transferTargetUserId.trim();

    if (!newOwnerUserId) {
      setTransferMessage("Selecione o novo proprietário.");
      return;
    }

    const confirmed = window.confirm(
      "Transferir a propriedade deste agente? Você perderá o papel de dono.",
    );

    if (!confirmed) {
      return;
    }

    setIsTransferring(true);
    setTransferMessage(null);

    try {
      await transferChatAgentOwnership(agent.id, newOwnerUserId, { getAccessToken });
      setTransferMessage("Propriedade transferida. Saindo do builder...");
      setTransferTargetUserId("");
      onBack();
    } catch {
      setTransferMessage("Não foi possível transferir a propriedade.");
    } finally {
      setIsTransferring(false);
    }
  }

  async function shareCurrentAgent() {
    if (!agent || agent.access_role !== "owner") {
      return;
    }

    const targetUserId = shareTargetUserId.trim();

    if (!targetUserId) {
      setShareMessage("Selecione um usuário para compartilhar.");
      return;
    }

    setIsSharing(true);
    setShareMessage(null);

    try {
      await shareChatAgent(
        agent.id,
        { targetUserId, role: shareRole },
        { getAccessToken },
      );
      setShareMessage("Agente compartilhado com sucesso.");
      setShareTargetUserId("");
      await loadAgentShares();
    } catch {
      setShareMessage("Não foi possível compartilhar o agente.");
    } finally {
      setIsSharing(false);
    }
  }

  async function duplicateCurrentAgent() {
    if (!agent?.id || !getAccessToken) {
      return;
    }

    setIsDuplicating(true);
    setLocalError(null);

    try {
      const duplicated = await duplicateChatAgent(agent.id, {
        getAccessToken,
        copyActions: copyActionsOnDuplicate,
        copySources: copySourcesOnDuplicate,
      });
      onDuplicateAgent?.(duplicated);
    } catch {
      setLocalError("Não foi possível duplicar o agente.");
    } finally {
      setIsDuplicating(false);
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
            <>
              <button
                type="button"
                className="mdc-chat-agent-builder__secondary"
                disabled={isDuplicating}
                onClick={() => void duplicateCurrentAgent()}
                title="Cria cópia privada do agente"
              >
                <Copy size={16} aria-hidden="true" />
                <span>{isDuplicating ? "Duplicando..." : "Duplicar"}</span>
              </button>
              <button
                type="button"
                className="mdc-chat-agent-builder__danger"
                onClick={() => void deleteCurrentAgent()}
              >
                <Trash2 size={17} aria-hidden="true" />
                <span>Excluir</span>
              </button>
            </>
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
          <div className="mdc-chat-agent-builder__switch" role="tablist" aria-label="Modo de edição">
            <button
              type="button"
              className={builderMode === "create" ? "is-active" : ""}
              onClick={() => setBuilderMode("create")}
            >
              Criar
            </button>
            <button
              type="button"
              className={builderMode === "configure" ? "is-active" : ""}
              onClick={() => setBuilderMode("configure")}
            >
              Configurar
            </button>
          </div>

          {builderMode === "create" ? (
            <section className="mdc-chat-agent-builder__section mdc-chat-agent-builder__create-mode">
              <div className="mdc-chat-agent-builder__section-title">
                <Wand2 size={18} aria-hidden="true" />
                <div>
                  <h2>Criar com orientação</h2>
                  <p>Descreva o especialista que você quer criar. Vamos gerar um rascunho editável.</p>
                </div>
              </div>

              <label>
                <span>O que este agente deve fazer?</span>
                <textarea
                  value={createBrief}
                  rows={8}
                  onChange={(event) => setCreateBrief(event.target.value)}
                  placeholder="Ex.: Crie um agente especialista em produtos DELPI, capaz de consultar API, interpretar estoque, analisar estrutura e explicar próximos passos."
                />
              </label>

              <button
                type="button"
                className="mdc-chat-agent-builder__secondary"
                onClick={generateDraftFromBrief}
              >
                <Wand2 size={16} aria-hidden="true" />
                <span>Gerar rascunho</span>
              </button>

              <div className="mdc-chat-agent-builder__placeholder">
                <strong>Depois de gerar o rascunho</strong>
                <p>Revise nome, instruções, fontes e actions na aba Configurar antes de salvar.</p>
              </div>
            </section>
          ) : (
            <>
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
                  {canManageOfficialAgents ? (
                    <option value="system">Oficial</option>
                  ) : null}
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
                {isLoadingAgent
                  ? "Carregando instruções salvas..."
                  : "Instruções usadas pelo modelo em cada conversa com este agente."}
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

          {agent && ["owner", "editor", "system"].includes(agent.access_role) ? (
            <section className="mdc-chat-agent-builder__section">
              <div className="mdc-chat-agent-builder__section-title">
                <BarChart3 size={18} aria-hidden="true" />
                <div>
                  <h2>Uso (últimos 7 dias)</h2>
                  <p>Resumo de conversas e configuração deste especialista.</p>
                </div>
              </div>

              {isLoadingStats ? (
                <p className="mdc-chat-muted">Carregando estatísticas...</p>
              ) : agentStats ? (
                <div className="mdc-chat-agent-builder__stats-grid">
                  <article>
                    <strong>{agentStats.sessionsInWindow}</strong>
                    <small>Conversas no período</small>
                  </article>
                  <article>
                    <strong>{agentStats.messagesInWindow}</strong>
                    <small>Mensagens no período</small>
                  </article>
                  <article>
                    <strong>{agentStats.totalSessions}</strong>
                    <small>Total de conversas</small>
                  </article>
                  <article>
                    <strong>{agentStats.actionProvidersCount}</strong>
                    <small>APIs/actions vinculadas</small>
                  </article>
                </div>
              ) : (
                <p className="mdc-chat-muted">Sem dados de uso no período.</p>
              )}

              {agent.access_role === "owner" ? (
                <>
                  <label className="mdc-chat-agent-builder__checkbox">
                    <input
                      type="checkbox"
                      checked={copyActionsOnDuplicate}
                      onChange={(event) => setCopyActionsOnDuplicate(event.target.checked)}
                    />
                    <span>Ao duplicar, copiar também APIs e actions configuradas</span>
                  </label>
                  <label className="mdc-chat-agent-builder__checkbox">
                    <input
                      type="checkbox"
                      checked={copySourcesOnDuplicate}
                      onChange={(event) => setCopySourcesOnDuplicate(event.target.checked)}
                    />
                    <span>Ao duplicar, copiar também fontes de conhecimento do agente</span>
                  </label>
                </>
              ) : null}
            </section>
          ) : null}

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <Settings2 size={18} aria-hidden="true" />
              <div>
                <h2>Execução</h2>
                <p>Controle disponibilidade e limites de ferramentas por conversa.</p>
              </div>
            </div>

            <label className="mdc-chat-agent-builder__checkbox">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(event) => setEnabled(event.target.checked)}
              />
              <span>Agente ativo (visível para uso)</span>
            </label>

            <div className="mdc-chat-agent-builder__grid">
              <label>
                <span>Máximo de chamadas de ferramentas</span>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={maxToolCalls}
                  onChange={(event) =>
                    setMaxToolCalls(Math.max(1, Math.min(20, Number(event.target.value) || 5)))
                  }
                />
              </label>

              <label className="mdc-chat-agent-builder__checkbox">
                <input
                  type="checkbox"
                  checked={requiresConfirmationForWrite}
                  onChange={(event) =>
                    setRequiresConfirmationForWrite(event.target.checked)
                  }
                />
                <span>Exigir confirmação para ações de escrita</span>
              </label>
            </div>
          </section>

          {agent?.access_role === "owner" ? (
            <section className="mdc-chat-agent-builder__section">
              <div className="mdc-chat-agent-builder__section-title">
                <Settings2 size={18} aria-hidden="true" />
                <div>
                  <h2>Compartilhamento</h2>
                  <p>Conceda acesso de visualização ou edição a outro usuário.</p>
                </div>
              </div>

              <div className="mdc-chat-agent-builder__grid">
                <ChatUserSearchField
                  value={shareTargetUserId}
                  onChange={setShareTargetUserId}
                  getAccessToken={getAccessToken}
                  disabled={isSharing}
                />

                <label>
                  <span>Papel</span>
                  <select
                    value={shareRole}
                    onChange={(event) =>
                      setShareRole(event.target.value as "viewer" | "editor")
                    }
                  >
                    <option value="viewer">Visualizador</option>
                    <option value="editor">Editor</option>
                  </select>
                </label>
              </div>

              <button
                type="button"
                disabled={isSharing}
                onClick={() => void shareCurrentAgent()}
              >
                {isSharing ? "Compartilhando..." : "Compartilhar agente"}
              </button>

              {shareMessage ? <p className="mdc-chat-muted">{shareMessage}</p> : null}

              <div className="mdc-chat-agent-builder__share-list">
                {isLoadingShares ? (
                  <p className="mdc-chat-muted">Carregando compartilhamentos...</p>
                ) : agentShares.length === 0 ? (
                  <p className="mdc-chat-muted">Nenhum compartilhamento ativo.</p>
                ) : (
                  agentShares.map((share) => (
                    <article key={share.id}>
                      <span>
                        <strong>
                          {share.target_user_name ||
                            share.target_user_email ||
                            share.target_user_id}
                        </strong>
                        {share.target_user_email ? (
                          <small>{share.target_user_email}</small>
                        ) : null}
                      </span>
                      <select
                        value={share.role}
                        disabled={updatingShareUserId === share.target_user_id}
                        onChange={(event) =>
                          void updateAgentShareRole(
                            share.target_user_id,
                            event.target.value as "viewer" | "editor",
                          )
                        }
                        aria-label="Papel do compartilhamento"
                      >
                        <option value="viewer">Visualizador</option>
                        <option value="editor">Editor</option>
                      </select>
                      <button
                        type="button"
                        disabled={revokingShareUserId === share.target_user_id}
                        onClick={() => void revokeAgentShare(share.target_user_id)}
                      >
                        {revokingShareUserId === share.target_user_id
                          ? "Revogando..."
                          : "Revogar"}
                      </button>
                    </article>
                  ))
                )}
              </div>

              <div className="mdc-chat-agent-builder__transfer">
                <h3>Transferir propriedade</h3>
                <p>Defina outro usuário como dono deste agente.</p>
                <ChatUserSearchField
                  value={transferTargetUserId}
                  onChange={setTransferTargetUserId}
                  getAccessToken={getAccessToken}
                  disabled={isTransferring}
                />
                <button
                  type="button"
                  className="mdc-chat-agent-builder__secondary"
                  disabled={isTransferring}
                  onClick={() => void transferAgentOwnership()}
                >
                  {isTransferring ? "Transferindo..." : "Transferir propriedade"}
                </button>
                {transferMessage ? <p className="mdc-chat-muted">{transferMessage}</p> : null}
              </div>
            </section>
          ) : null}

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
                <h2>Recursos</h2>
                <p>Defina capacidades gerais do agente. Actions são configuradas na página própria de Actions.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-builder__toggles">
              <label>
                <input
                  type="checkbox"
                  checked={capActions}
                  onChange={(event) => setCapActions(event.target.checked)}
                />
                <span>Permitir uso de actions configuradas</span>
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
          </section>
          
          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <Zap size={18} aria-hidden="true" />
              <div>
                <h2>Ações</h2>
                <p>APIs e actions que este agente pode usar. Configure schemas, autenticação e rotas em uma tela própria.</p>
              </div>
            </div>

            {agent ? (
              <div className="mdc-chat-agent-builder__actions-summary">
                {agentActionProviders.length > 0 ? (
                  agentActionProviders.map((provider) => (
                    <article key={provider.providerKey}>
                      <span className="mdc-chat-agent-builder__actions-icon">
                        <Zap size={16} aria-hidden="true" />
                      </span>

                      <span>
                        <strong>{provider.providerName || provider.providerKey}</strong>
                        <small>
                          {provider.providerKey}
                          {provider.enabled ? " · ativo" : " · desativado"}
                          {` · ${provider.actionCount} rota(s)`}
                        </small>
                      </span>

                      <button
                        type="button"
                        onClick={() => onConfigureAction?.(agent, provider.providerKey)}
                        title="Configurar action"
                      >
                        <Settings2 size={16} aria-hidden="true" />
                      </button>
                    </article>
                  ))
                ) : (
                  <div className="mdc-chat-agent-builder__actions-empty">
                    <strong>Nenhuma action configurada</strong>
                    <p>Crie uma action para conectar este agente a uma API OpenAPI.</p>
                  </div>
                )}

                <button
                  type="button"
                  className="mdc-chat-agent-builder__secondary"
                  onClick={() => onCreateAction?.(agent)}
                >
                  <Plus size={16} aria-hidden="true" />
                  <span>Criar nova ação</span>
                </button>
              </div>
            ) : (
              <div className="mdc-chat-agent-builder__actions-empty">
                <strong>Salve o agente para configurar actions</strong>
                <p>Depois de criar o agente, você poderá cadastrar APIs OpenAPI e escolher rotas.</p>
              </div>
            )}
          </section>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <FileText size={18} aria-hidden="true" />
              <div>
                <h2>Fontes do agente</h2>
                <p>Arquivos e notas usados sempre que este agente estiver ativo.</p>
              </div>
            </div>

            {agent ? (
              <>
                {onOpenRagAdmin ? (
                  <button
                    type="button"
                    className="mdc-chat-agent-builder__secondary"
                    onClick={() => onOpenRagAdmin(agent.id)}
                  >
                    Especialização RAG (admin)
                  </button>
                ) : null}

                <label className="mdc-chat-agent-builder__source-upload">
                  <Upload size={16} aria-hidden="true" />
                  <span>{isSavingSource ? "Enviando..." : "Enviar arquivo"}</span>
                  <input
                    type="file"
                    disabled={isSavingSource}
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      void uploadAgentKnowledgeFile(file);
                      event.target.value = "";
                    }}
                  />
                </label>

                <div className="mdc-chat-agent-builder__source-note">
                  <input
                    value={sourceTitle}
                    onChange={(event) => setSourceTitle(event.target.value)}
                    placeholder="Título da nota"
                  />
                  <textarea
                    value={sourceContent}
                    onChange={(event) => setSourceContent(event.target.value)}
                    rows={4}
                    placeholder="Cole contexto, políticas ou conhecimento do agente..."
                  />
                  <button
                    type="button"
                    disabled={isSavingSource || !sourceContent.trim()}
                    onClick={() => void createAgentKnowledgeNote()}
                  >
                    Adicionar nota
                  </button>
                </div>

                <div className="mdc-chat-agent-builder__source-list">
                  {agentSources.length > 0 ? (
                    agentSources.map((source) => (
                      <article key={source.id}>
                        <FileText size={16} aria-hidden="true" />
                        <span>
                          <strong>{source.title}</strong>
                          <small>
                            {source.original_filename || source.source_ref || source.source_type}
                            {typeof source.chunk_count === "number"
                              ? ` · ${source.chunk_count} trecho(s)`
                              : ""}
                          </small>
                        </span>
                        <button
                          type="button"
                          onClick={() => void removeAgentSource(source.id)}
                          title="Remover fonte"
                        >
                          <Trash2 size={15} aria-hidden="true" />
                        </button>
                      </article>
                    ))
                  ) : (
                    <p className="mdc-chat-muted">Nenhuma fonte adicionada.</p>
                  )}
                </div>
              </>
            ) : (
              <p className="mdc-chat-muted">Salve o agente para adicionar fontes.</p>
            )}
          </section>

            </>
          )}

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
                  <button
                    key={icebreaker}
                    type="button"
                    disabled={isPreviewLoading}
                    onClick={() => void sendPreviewMessage(icebreaker)}
                  >
                    {icebreaker}
                  </button>
                ))}
              </div>
            ) : null}

            {previewMessages.length > 0 ? (
              <div className="mdc-chat-agent-builder__preview-messages">
                {previewMessages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={
                      message.role === "user"
                        ? "mdc-chat-agent-builder__preview-message mdc-chat-agent-builder__preview-message--user"
                        : "mdc-chat-agent-builder__preview-message"
                    }
                  >
                    {message.content}
                  </div>
                ))}
              </div>
            ) : null}

            <div className="mdc-chat-agent-builder__preview-input">
              <input
                value={previewInput}
                onChange={(event) => setPreviewInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    void sendPreviewMessage();
                  }
                }}
                placeholder="Pergunte alguma coisa"
                disabled={isPreviewLoading}
              />
              <button
                type="button"
                disabled={isPreviewLoading}
                onClick={() => void sendPreviewMessage()}
              >
                <Send size={16} aria-hidden="true" />
              </button>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
