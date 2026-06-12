import {
  ArrowUpRight,
  ArrowUp,
  Bot,
  Folder,
  Paperclip,
  Plus,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  applyComposerMentionSelection,
  detectActiveComposerMention,
  filterComposerMentionCandidates,
  listComposerMentionCandidates,
} from "../../state/chatComposerMention";
import { ChatComposerMentionMenu } from "./ChatComposerMentionMenu";

import type {
  ChatAgent,
  ChatPresentationFormatId,
  ChatProject,
  ChatResponseModeId,
  ChatResponseModeOption,
} from "../../data/api/chatTypes";
import type { ChatPresentationFormatOption } from "../../state/hooks/useChatPresentationFormat";
import { ChatPresentationFormatSelector } from "./ChatPresentationFormatSelector";
import { ChatResponseModeSelector } from "./ChatResponseModeSelector";
import {
  composerAttachmentStatusLabel,
  type ComposerAttachmentStatus,
} from "../chatAttachmentStatus";
import { useAutoGrowTextarea } from "../hooks/useAutoGrowTextarea";
import type { ComposerContextBarItem } from "../../state/chatAgentActivation";
import type {
  ChatTypingSuggestion,
} from "../../data/api/chatTypes";
import type { MessageComposerTypingCorrectionContent } from "../../content/messageComposerContent";
import {
  workspaceFileComposerAttachmentsHeader,
  workspaceFileComposerLabels,
} from "../../content/workspaceFileIngestContent";
import { useWorkspaceFileIngestPolicy } from "../hooks/useWorkspaceFileIngestPolicy";
import { WorkspaceFileCard } from "./workspace-files/WorkspaceFileCard";

import "./ChatInput.css";
import "./workspace-files/workspaceFileIngest.css";

export type ChatInputAttachment = {
  id: string;
  name: string;
  size: number;
  type: string;
  file: File;
  status?: ComposerAttachmentStatus;
  serverAttachmentId?: string;
  readingStatus?: string;
};

type ChatInputProps = {
  value: string;
  disabled?: boolean;
  isSending?: boolean;
  variant?: "dock" | "center";
  placeholder?: string;
  agents?: ChatAgent[];
  projects?: ChatProject[];
  selectedAgentIds?: string[];
  selectedProjectIds?: string[];
  attachments?: ChatInputAttachment[];
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel?: () => void;
  onToggleAgent?: (agentId: string) => void;
  onRemoveContextAgent?: (agentId: string) => void;
  onOpenAgentPage?: (agentId: string) => void;
  onToggleProject?: (projectId: string) => void;
  onRemoveContextProject?: (projectId: string) => void;
  onAttachFiles?: (files: File[]) => void;
  onRemoveAttachment?: (attachmentId: string) => void;
  onClearAttachments?: () => void;
  plusMenuOpen?: boolean;
  onPlusMenuOpenChange?: (open: boolean) => void;
  responseModes?: ChatResponseModeOption[];
  responseMode?: ChatResponseModeId;
  onResponseModeChange?: (mode: ChatResponseModeId) => void;
  showResponseModeSelector?: boolean;
  presentationFormatOptions?: ChatPresentationFormatOption[];
  presentationFormat?: ChatPresentationFormatId;
  onPresentationFormatChange?: (format: ChatPresentationFormatId) => void;
  showPresentationFormatSelector?: boolean;
  /** Chips de contexto no composer — regra em resolveComposerContextBar (chatAgentActivation). */
  contextBarItems?: ComposerContextBarItem[];
  typingSuggestion?: ChatTypingSuggestion | null;
  typingSuggestionLabels?: MessageComposerTypingCorrectionContent;
  onAcceptTypingSuggestion?: () => void;
  onDismissTypingSuggestion?: () => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export function ChatInput({
  value,
  disabled,
  isSending,
  variant = "dock",
  placeholder = "Pergunte alguma coisa",
  agents = [],
  projects = [],
  selectedAgentIds = [],
  selectedProjectIds = [],
  attachments = [],
  onChange,
  onSubmit,
  onCancel,
  onToggleAgent,
  onRemoveContextAgent,
  onOpenAgentPage,
  onToggleProject,
  onRemoveContextProject,
  onAttachFiles,
  onRemoveAttachment,
  onClearAttachments,
  plusMenuOpen,
  onPlusMenuOpenChange,
  responseModes = [],
  responseMode = "normal",
  onResponseModeChange,
  showResponseModeSelector = false,
  presentationFormatOptions = [],
  presentationFormat = "auto",
  onPresentationFormatChange,
  showPresentationFormatSelector = true,
  contextBarItems = [],
  typingSuggestion = null,
  typingSuggestionLabels,
  onAcceptTypingSuggestion,
  onDismissTypingSuggestion,
  getAccessToken,
}: ChatInputProps) {
  const { accept: sessionAttachmentAccept } = useWorkspaceFileIngestPolicy("session_attachment", {
    getAccessToken,
  });
  const [internalMenuOpen, setInternalMenuOpen] = useState(false);
  const isPlusMenuControlled = plusMenuOpen !== undefined;
  const isMenuOpen = isPlusMenuControlled ? plusMenuOpen : internalMenuOpen;

  function setMenuOpen(open: boolean) {
    if (isPlusMenuControlled) {
      onPlusMenuOpenChange?.(open);
      return;
    }

    setInternalMenuOpen(open);
  }
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const plusMenuRef = useRef<HTMLDivElement | null>(null);
  const [mentionCursor, setMentionCursor] = useState(0);
  const [mentionIndex, setMentionIndex] = useState(0);
  const mentionCandidates = useMemo(
    () =>
      listComposerMentionCandidates({
        agents: agents.map((agent) => ({ id: agent.id, name: agent.name })),
        projects: projects.map((project) => ({ id: project.id, name: project.name })),
      }),
    [agents, projects],
  );
  const activeMention = detectActiveComposerMention(value, mentionCursor);
  const mentionItems = useMemo(
    () =>
      activeMention
        ? filterComposerMentionCandidates(mentionCandidates, activeMention.query, {
            selectedAgentIds,
            selectedProjectIds,
          })
        : [],
    [activeMention, mentionCandidates, selectedAgentIds, selectedProjectIds],
  );
  const isMentionMenuOpen = Boolean(activeMention);

  useEffect(() => {
    setMentionIndex(0);
  }, [activeMention?.query, mentionItems.length]);
  const showResponseMode =
    showResponseModeSelector && responseModes.length > 0 && Boolean(onResponseModeChange);
  const showPresentationFormat =
    showPresentationFormatSelector &&
    presentationFormatOptions.length > 0 &&
    Boolean(onPresentationFormatChange);
  const { ref: textareaRef, syncHeight } = useAutoGrowTextarea({
    value,
    topInset: variant === "dock" ? 112 : 88,
    maxHeightViewportRatio: 0.28,
    maxHeightCapPx: 184,
  });

  useEffect(() => {
    if (!isMenuOpen) {
      return;
    }

    const closeMenu = () => setMenuOpen(false);

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target;

      if (!(target instanceof Node)) {
        return;
      }

      if (plusMenuRef.current?.contains(target)) {
        return;
      }

      closeMenu();
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeMenu();
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMenuOpen]);

  const selectedAgentIdSet = new Set(selectedAgentIds);
  const selectedProjectIdSet = new Set(selectedProjectIds);
  const hasContextBar = contextBarItems.length > 0;
  const hasAttachments = attachments.length > 0;

  function syncMentionCursor() {
    const cursor = textareaRef.current?.selectionStart ?? value.length;
    setMentionCursor(cursor);
  }

  function handleMentionSelect(candidate: (typeof mentionItems)[number]) {
    if (!activeMention) {
      return;
    }

    const next = applyComposerMentionSelection({
      value,
      cursor: mentionCursor,
      mentionStart: activeMention.start,
      candidate,
    });

    onChange(next.value);

    if (candidate.kind === "agent") {
      onToggleAgent?.(candidate.id);
    } else {
      onToggleProject?.(candidate.id);
    }

    requestAnimationFrame(() => {
      const textarea = textareaRef.current;

      if (!textarea) {
        return;
      }

      textarea.focus();
      textarea.setSelectionRange(next.cursor, next.cursor);
      setMentionCursor(next.cursor);
      syncHeight();
    });
  }

  const plusControl = (
    <div className="mdc-chat-input__plus-wrap" ref={plusMenuRef} data-tour="composer-plus">
      <button
        type="button"
        className="mdc-chat-input__plus"
        onClick={() => setMenuOpen(!isMenuOpen)}
        aria-label="Mais opções"
        aria-expanded={isMenuOpen}
      >
        <Plus size={20} aria-hidden="true" />
      </button>

      {isMenuOpen ? (
        <div className="mdc-chat-input__menu">
          <div className="mdc-chat-input__menu-section">
            <strong>Arquivos</strong>

            <button
              type="button"
              data-tour="composer-attach"
              onClick={() => {
                fileInputRef.current?.click();
                setMenuOpen(false);
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
                    setMenuOpen(false);
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
        </div>
      ) : null}
    </div>
  );

  const sendControl = isSending ? (
    <button
      type="button"
      className="mdc-chat-input__send mdc-chat-input__send--cancel"
      onClick={onCancel}
      aria-label="Cancelar resposta"
      title="Cancelar"
    >
      <span aria-hidden="true" />
    </button>
  ) : (
    <button
      type="submit"
      className="mdc-chat-input__send"
      disabled={disabled || !value.trim()}
      aria-label="Enviar mensagem"
      title="Enviar"
    >
      <ArrowUp size={18} aria-hidden="true" />
    </button>
  );

  return (
    <form
      className={
        variant === "center"
          ? "mdc-chat-input mdc-chat-input--center"
          : "mdc-chat-input"
      }
      data-tour="composer"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <input
        ref={fileInputRef}
        className="mdc-chat-input__file-input"
        type="file"
        multiple
        accept={sessionAttachmentAccept}
        onChange={(event) => {
          const files = Array.from(event.target.files ?? []);

          if (files.length > 0) {
            onAttachFiles?.(files);
          }

          event.target.value = "";
        }}
      />

      <div
        className={[
          "mdc-chat-input__box",
          hasContextBar ? "mdc-chat-input__box--with-agent" : "",
          hasAttachments ? "mdc-chat-input__box--with-attachments" : "",
          showResponseMode ? "mdc-chat-input__box--with-response-mode" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {hasContextBar ? (
          <div className="mdc-chat-input__context-bar">
            {contextBarItems.map((item) => {
              if (item.kind === "agent") {
                const agent = agents.find((entry) => entry.id === item.id);

                if (!agent) {
                  return null;
                }

                return (
                  <div key={`agent-${item.id}`} className="mdc-chat-input__agent-context">
                    <span className="mdc-chat-input__agent-avatar">
                      <Bot size={15} aria-hidden="true" />
                    </span>

                    <strong>{agent.name}</strong>

                    <button
                      type="button"
                      onClick={() => onRemoveContextAgent?.(item.id)}
                      aria-label={`Remover ${agent.name} do contexto`}
                      title={`Remover ${agent.name} do contexto`}
                    >
                      <X size={16} aria-hidden="true" />
                    </button>
                  </div>
                );
              }

              const project = projects.find((entry) => entry.id === item.id);

              if (!project) {
                return null;
              }

              return (
                <div key={`project-${item.id}`} className="mdc-chat-input__agent-context">
                  <span className="mdc-chat-input__agent-avatar">
                    <Folder size={15} aria-hidden="true" />
                  </span>

                  <strong>{project.name}</strong>

                  <button
                    type="button"
                    onClick={() => onRemoveContextProject?.(item.id)}
                    aria-label={`Remover ${project.name} do contexto`}
                    title={`Remover ${project.name} do contexto`}
                  >
                    <X size={16} aria-hidden="true" />
                  </button>
                </div>
              );
            })}
          </div>
        ) : null}

        {hasAttachments ? (
          <div className="mdc-chat-input__attachments">
            <div className="mdc-chat-input__attachments-header">
              <span>
                <Paperclip size={15} aria-hidden="true" />
                {workspaceFileComposerAttachmentsHeader(attachments.length)}
              </span>

              <button type="button" onClick={onClearAttachments}>
                <Trash2 size={14} aria-hidden="true" />
                <span>{workspaceFileComposerLabels().clearAttachments}</span>
              </button>
            </div>

            <div className="mdc-chat-input__attachment-list">
              {attachments.map((attachment) => {
                const isImage = attachment.type.startsWith("image/");
                const statusLabel = composerAttachmentStatusLabel(
                  attachment.status ?? "queued",
                  attachment.readingStatus,
                );

                return (
                  <WorkspaceFileCard
                    key={attachment.id}
                    variant="chip"
                    filename={attachment.name}
                    sizeLabel={formatFileSize(attachment.size)}
                    statusLabel={statusLabel}
                    previewKind={isImage ? "image" : "file"}
                    editable
                    onRemove={() => onRemoveAttachment?.(attachment.id)}
                  />
                );
              })}
            </div>
          </div>
        ) : null}

        {typingSuggestion?.corrected?.trim() &&
        typingSuggestion.corrected.trim() !== value.trim() &&
        typingSuggestionLabels ? (
          <div
            className="mdc-chat-input__typing-suggestion"
            role="status"
            aria-live="polite"
          >
            <span className="mdc-chat-input__typing-suggestion-hint">
              {typingSuggestionLabels.hint}
            </span>
            <span className="mdc-chat-input__typing-suggestion-preview">
              {typingSuggestionLabels.previewPrefix} {typingSuggestion.corrected}
            </span>
            <div className="mdc-chat-input__typing-suggestion-actions">
              <button
                type="button"
                className="mdc-chat-input__typing-suggestion-accept"
                onClick={onAcceptTypingSuggestion}
              >
                {typingSuggestionLabels.acceptLabel}
              </button>
              <button
                type="button"
                className="mdc-chat-input__typing-suggestion-dismiss"
                onClick={onDismissTypingSuggestion}
              >
                {typingSuggestionLabels.dismissLabel}
              </button>
            </div>
          </div>
        ) : null}

        <div className="mdc-chat-input__composer-stack">
          <div className="mdc-chat-input__composer-field">
            {isMentionMenuOpen ? (
              <ChatComposerMentionMenu
                items={mentionItems}
                activeIndex={Math.min(mentionIndex, Math.max(mentionItems.length - 1, 0))}
                onHover={setMentionIndex}
                onSelect={handleMentionSelect}
              />
            ) : null}

            <textarea
              ref={textareaRef}
              className="mdc-auto-grow-textarea"
              data-tour="composer-input"
              value={value}
              disabled={disabled || isSending}
              placeholder={placeholder}
              rows={1}
              onChange={(event) => {
                onChange(event.target.value);
                setMentionCursor(event.target.selectionStart ?? event.target.value.length);
                requestAnimationFrame(() => syncHeight());
              }}
              onInput={() => {
                requestAnimationFrame(() => syncHeight());
              }}
              onClick={syncMentionCursor}
              onKeyUp={syncMentionCursor}
              onSelect={syncMentionCursor}
              onKeyDown={(event) => {
                if (typingSuggestion && event.key === "Tab") {
                  event.preventDefault();
                  onAcceptTypingSuggestion?.();
                  return;
                }

                if (typingSuggestion && event.key === "Escape") {
                  event.preventDefault();
                  onDismissTypingSuggestion?.();
                  return;
                }

                if (isMentionMenuOpen && mentionItems.length > 0) {
                  if (event.key === "ArrowDown") {
                    event.preventDefault();
                    setMentionIndex((current) => (current + 1) % mentionItems.length);
                    return;
                  }

                  if (event.key === "ArrowUp") {
                    event.preventDefault();
                    setMentionIndex(
                      (current) => (current - 1 + mentionItems.length) % mentionItems.length,
                    );
                    return;
                  }

                  if (event.key === "Enter" || event.key === "Tab") {
                    event.preventDefault();
                    const selected =
                      mentionItems[Math.min(mentionIndex, mentionItems.length - 1)];

                    if (selected) {
                      handleMentionSelect(selected);
                    }

                    return;
                  }

                  if (event.key === "Escape") {
                    event.preventDefault();
                    return;
                  }
                }

                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  onSubmit();
                }
              }}
            />
          </div>

          <div className="mdc-chat-input__composer-toolbar">
            <div className="mdc-chat-input__composer-toolbar-start">
              {plusControl}

              {showPresentationFormat ? (
                <ChatPresentationFormatSelector
                  options={presentationFormatOptions}
                  value={presentationFormat}
                  disabled={disabled || isSending}
                  onChange={onPresentationFormatChange}
                />
              ) : null}

              {showResponseMode ? (
                <ChatResponseModeSelector
                  modes={responseModes}
                  value={responseMode}
                  disabled={disabled || isSending}
                  onChange={onResponseModeChange}
                />
              ) : null}
            </div>

            <div className="mdc-chat-input__composer-toolbar-end">{sendControl}</div>
          </div>
        </div>
      </div>

      <small>
        {hasAttachments
          ? "Arquivos anexados serão usados como fonte de conhecimento desta conversa."
          : "Digite @ para citar agente ou projeto na pergunta. A resposta será exibida em tempo real."}
      </small>
    </form>
  );
}
