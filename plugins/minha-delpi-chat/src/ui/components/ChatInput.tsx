import {
  ArrowUpRight,
  Bot,
  FileText,
  Folder,
  Paperclip,
  Plus,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { useRef, useState } from "react";

import type { ChatAgent, ChatProject } from "../../data/api/chatTypes";

import "./ChatInput.css";

export type ChatInputAttachment = {
  id: string;
  name: string;
  size: number;
  type: string;
  file: File;
};

type ChatInputProps = {
  value: string;
  disabled?: boolean;
  isSending?: boolean;
  variant?: "dock" | "center";
  placeholder?: string;
  agents?: ChatAgent[];
  projects?: ChatProject[];
  selectedAgentKey?: string | null;
  selectedProjectId?: string | null;
  attachments?: ChatInputAttachment[];
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel?: () => void;
  onSelectAgent?: (agentKey: string | null) => void;
  onOpenAgentPage?: (agentKey: string) => void;
  onSelectProject?: (projectId: string | null) => void;
  onAttachFiles?: (files: File[]) => void;
  onRemoveAttachment?: (attachmentId: string) => void;
  onClearAttachments?: () => void;
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
  selectedAgentKey,
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
}: ChatInputProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const selectedAgent = agents.find((agent) => agent.key === selectedAgentKey);
  const selectedProject = projects.find((project) => project.id === selectedProjectId);
  const hasAttachments = attachments.length > 0;

  return (
    <form
      className={
        variant === "center"
          ? "mdc-chat-input mdc-chat-input--center"
          : "mdc-chat-input"
      }
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
              {attachments.map((attachment) => (
                <span key={attachment.id} className="mdc-chat-input__attachment-chip">
                  <FileText size={14} aria-hidden="true" />

                  <strong>{attachment.name}</strong>
                  <small>{formatFileSize(attachment.size)}</small>

                  <button
                    type="button"
                    onClick={() => onRemoveAttachment?.(attachment.id)}
                    aria-label={`Remover ${attachment.name}`}
                  >
                    <X size={13} aria-hidden="true" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mdc-chat-input__plus-wrap">
          <button
            type="button"
            className="mdc-chat-input__plus"
            onClick={() => setIsMenuOpen((current) => !current)}
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
                  onClick={() => {
                    fileInputRef.current?.click();
                    setIsMenuOpen(false);
                  }}
                >
                  <Upload size={16} aria-hidden="true" />
                  <span>Anexar arquivos</span>
                </button>
              </div>

              <div className="mdc-chat-input__menu-section">
                <strong>Usar agente neste contexto</strong>

                {selectedAgent ? (
                  <button
                    type="button"
                    onClick={() => {
                      onSelectAgent?.(null);
                      setIsMenuOpen(false);
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
                        agent.key === selectedAgentKey
                          ? "mdc-chat-input__menu-item--active"
                          : undefined
                      }
                      onClick={() => {
                        onSelectAgent?.(agent.key);
                        setIsMenuOpen(false);
                      }}
                    >
                      <Bot size={16} aria-hidden="true" />
                      <span>{agent.name}</span>
                    </button>

                    <button
                      type="button"
                      className="mdc-chat-input__open-agent"
                      onClick={() => {
                        onOpenAgentPage?.(agent.key);
                        setIsMenuOpen(false);
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
                      setIsMenuOpen(false);
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
                      setIsMenuOpen(false);
                    }}
                  >
                    <Folder size={16} aria-hidden="true" />
                    <span>{project.name}</span>
                  </button>
                ))}
              </div>

              <div className="mdc-chat-input__menu-section">
                <strong>Em breve</strong>

                <button type="button" disabled>
                  <Sparkles size={16} aria-hidden="true" />
                  <span>Escolher action</span>
                </button>
              </div>
            </div>
          ) : null}
        </div>

        <textarea
          value={value}
          disabled={disabled || isSending}
          placeholder={placeholder}
          rows={variant === "center" ? 1 : 3}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              onSubmit();
            }
          }}
        />
      </div>

      {isSending ? (
        <button type="button" onClick={onCancel}>
          Cancelar
        </button>
      ) : (
        <button type="submit" disabled={disabled || !value.trim()}>
          Enviar
        </button>
      )}

      <small>
        {hasAttachments
          ? "Arquivos anexados serão usados como fonte de conhecimento desta conversa."
          : "A resposta será exibida em tempo real e salva no histórico ao concluir."}
      </small>
    </form>
  );
}
