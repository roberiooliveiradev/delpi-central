import {
  ArrowUpRight,
  ArrowUp,
  Bot,
  FileText,
  Folder,
  Image as ImageIcon,
  Paperclip,
  Plus,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type {
  ChatAgent,
  ChatProject,
  ChatResponseModeId,
  ChatResponseModeOption,
} from "../../data/api/chatTypes";
import { ChatResponseModeSelector } from "./ChatResponseModeSelector";
import {
  composerAttachmentStatusLabel,
  type ComposerAttachmentStatus,
} from "../chatAttachmentStatus";
import { CHAT_TEXT_HOME_STARTERS } from "../chatHomeStarters";
import { CHAT_TEXT_TEMPLATES } from "../chatTextTemplates";
import { useAutoGrowTextarea } from "../hooks/useAutoGrowTextarea";

import "./ChatInput.css";

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
  selectedAgentId?: string | null;
  selectedProjectId?: string | null;
  attachments?: ChatInputAttachment[];
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel?: () => void;
  onSelectAgent?: (agentId: string | null) => void;
  onOpenAgentPage?: (agentId: string) => void;
  onSelectProject?: (projectId: string | null) => void;
  onAttachFiles?: (files: File[]) => void;
  onRemoveAttachment?: (attachmentId: string) => void;
  onClearAttachments?: () => void;
  onInsertQuery?: (query: string) => void;
  plusMenuOpen?: boolean;
  onPlusMenuOpenChange?: (open: boolean) => void;
  responseModes?: ChatResponseModeOption[];
  responseMode?: ChatResponseModeId;
  onResponseModeChange?: (mode: ChatResponseModeId) => void;
  showResponseModeSelector?: boolean;
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
  selectedAgentId,
  selectedProjectId,
  attachments = [],
  onChange,
  onSubmit,
  onCancel,
  onSelectAgent,
  onOpenAgentPage,
  onSelectProject,
  onAttachFiles,
  onRemoveAttachment,
  onClearAttachments,
  onInsertQuery,
  plusMenuOpen,
  onPlusMenuOpenChange,
  responseModes = [],
  responseMode = "normal",
  onResponseModeChange,
  showResponseModeSelector = false,
}: ChatInputProps) {
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
  const showResponseMode =
    showResponseModeSelector && responseModes.length > 0 && Boolean(onResponseModeChange);
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

  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId);
  const selectedProject = projects.find((project) => project.id === selectedProjectId);
  const hasAttachments = attachments.length > 0;

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
              <span>Anexar arquivos</span>
            </button>
          </div>

          {onInsertQuery ? (
            <div className="mdc-chat-input__menu-section">
              <strong>Textos</strong>

              {CHAT_TEXT_HOME_STARTERS.map((starter) => (
                <button
                  key={starter.label}
                  type="button"
                  onClick={() => {
                    onInsertQuery(starter.query);
                    setMenuOpen(false);
                  }}
                >
                  <FileText size={16} aria-hidden="true" />
                  <span>{starter.label}</span>
                </button>
              ))}

              <p className="mdc-chat-input__menu-hint">Modelos</p>

              {CHAT_TEXT_TEMPLATES.map((template) => (
                <button
                  key={template.label}
                  type="button"
                  onClick={() => {
                    onInsertQuery(template.draft);
                    setMenuOpen(false);
                  }}
                >
                  <FileText size={16} aria-hidden="true" />
                  <span>{template.label}</span>
                </button>
              ))}
            </div>
          ) : null}

          <div className="mdc-chat-input__menu-section" data-tour="composer-plus-menu-agents">
            <strong>Usar agente neste contexto</strong>

            {selectedAgent ? (
              <button
                type="button"
                onClick={() => {
                  onSelectAgent?.(null);
                  setMenuOpen(false);
                }}
              >
                <X size={16} aria-hidden="true" />
                <span>Remover agente deste contexto</span>
              </button>
            ) : null}

            {agents.map((agent) => (
              <div key={agent.id} className="mdc-chat-input__agent-menu-row">
                <button
                  type="button"
                  className={
                    agent.id === selectedAgentId
                      ? "mdc-chat-input__menu-item--active"
                      : undefined
                  }
                  onClick={() => {
                    onSelectAgent?.(agent.id);
                    setMenuOpen(false);
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
          </div>

          <div className="mdc-chat-input__menu-section">
            <strong>Usar projeto neste contexto</strong>

            {selectedProject ? (
              <button
                type="button"
                onClick={() => {
                  onSelectProject?.(null);
                  setMenuOpen(false);
                }}
              >
                <X size={16} aria-hidden="true" />
                <span>Remover projeto deste contexto</span>
              </button>
            ) : null}

            {projects.slice(0, 8).map((project) => (
              <button
                key={project.id}
                type="button"
                className={
                  project.id === selectedProjectId
                    ? "mdc-chat-input__menu-item--active"
                    : undefined
                }
                onClick={() => {
                  onSelectProject?.(project.id);
                  setMenuOpen(false);
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
        accept=".pdf,.txt,.md,.doc,.docx,.xls,.xlsx,.csv,.json,.png,.jpg,.jpeg,.webp"
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
          selectedAgent ? "mdc-chat-input__box--with-agent" : "",
          hasAttachments ? "mdc-chat-input__box--with-attachments" : "",
          showResponseMode ? "mdc-chat-input__box--with-response-mode" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {selectedAgent ? (
          <div className="mdc-chat-input__agent-context">
            <span className="mdc-chat-input__agent-avatar">
              <Bot size={15} aria-hidden="true" />
            </span>

            <strong>{selectedAgent.name}</strong>

            <button
              type="button"
              onClick={() => onSelectAgent?.(null)}
              aria-label="Remover agente do contexto"
              title="Remover agente do contexto"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        ) : null}

        {hasAttachments ? (
          <div className="mdc-chat-input__attachments">
            <div className="mdc-chat-input__attachments-header">
              <span>
                <Paperclip size={15} aria-hidden="true" />
                {attachments.length} arquivo(s) anexado(s)
              </span>

              <button type="button" onClick={onClearAttachments}>
                <Trash2 size={14} aria-hidden="true" />
                <span>Limpar</span>
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
                <span key={attachment.id} className="mdc-chat-input__attachment-chip">
                  {isImage ? (
                    <ImageIcon size={14} aria-hidden="true" />
                  ) : (
                    <FileText size={14} aria-hidden="true" />
                  )}

                  <strong>{attachment.name}</strong>
                  <small>{formatFileSize(attachment.size)}</small>
                  <small className="mdc-chat-input__attachment-chip-status">{statusLabel}</small>

                  <button
                    type="button"
                    onClick={() => onRemoveAttachment?.(attachment.id)}
                    aria-label={`Remover ${attachment.name}`}
                  >
                    <X size={13} aria-hidden="true" />
                  </button>
                </span>
                );
              })}
            </div>
          </div>
        ) : null}

        <div className="mdc-chat-input__composer-stack">
          <div className="mdc-chat-input__composer-field">
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
                requestAnimationFrame(() => syncHeight());
              }}
              onInput={() => {
                requestAnimationFrame(() => syncHeight());
              }}
              onKeyDown={(event) => {
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
          : "A resposta será exibida em tempo real e salva no histórico ao concluir."}
      </small>
    </form>
  );
}
