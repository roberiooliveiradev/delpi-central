import {
  ArrowUp,
  Bot,
  Folder,
  Paperclip,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  applyComposerMentionSelection,
  detectActiveComposerMention,
  filterComposerMentionCandidates,
  listComposerMentionCandidates,
} from "../../../state/chatComposerMention";
import { ChatComposerMentionMenu } from "./ChatComposerMentionMenu";

import type {
  ChatAgent,
  ChatPresentationFormatId,
  ChatProject,
  ChatResponseModeId,
  ChatResponseModeOption,
} from "../../../data/api/chatTypes";
import type { ChatPresentationFormatOption } from "../../../state/hooks/useChatPresentationFormat";
import { ChatPresentationFormatSelector } from "./ChatPresentationFormatSelector";
import { ChatResponseModeSelector } from "./ChatResponseModeSelector";
import { ChatInputPlusMenu } from "../shared/composer/ChatInputPlusMenu";
import { formatAttachmentSize } from "../../chatAttachmentPreview";
import type { ComposerAttachmentStatus } from "../../chatAttachmentStatus";
import { useAutoGrowTextarea } from "../../hooks/useAutoGrowTextarea";
import type { ComposerContextBarItem } from "../../../state/chatAgentActivation";
import type {
  ChatTypingSuggestion,
} from "../../../data/api/chatTypes";
import type { MessageComposerTypingCorrectionContent } from "../../../content/messageComposerContent";
import {
  workspaceFileComposerAttachmentsHeader,
  workspaceFileComposerLabels,
  workspaceFileAttachmentIndexPresentation,
  workspaceFileIconToneForAttachment,
} from "../../../content/workspaceFileIngestContent";
import {
  buildWorkspaceLocalFilePreviewTarget,
  useWorkspaceFilePreviewModal,
} from "../../hooks/useWorkspaceFilePreviewModal";
import { useWorkspaceFileIngestPolicy } from "../../hooks/useWorkspaceFileIngestPolicy";
import { WorkspaceFileCard } from "../workspace-files/WorkspaceFileCard";

import "./ChatInput.css";
import "../workspace-files/workspaceFileIngest.css";

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
  const { openPreview, previewModal } = useWorkspaceFilePreviewModal({ getAccessToken });
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
    <ChatInputPlusMenu
      open={isMenuOpen}
      onOpenChange={setMenuOpen}
      agents={agents}
      projects={projects}
      selectedAgentIds={selectedAgentIds}
      selectedProjectIds={selectedProjectIds}
      onAttachClick={() => fileInputRef.current?.click()}
      onToggleAgent={onToggleAgent}
      onToggleProject={onToggleProject}
      onOpenAgentPage={onOpenAgentPage}
    />
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
                const indexPresentation = workspaceFileAttachmentIndexPresentation({
                  status: attachment.status ?? "queued",
                  parsed: attachment.status === "indexed",
                  readingStatus: attachment.readingStatus,
                });

                const previewKind = isImage ? "image" : "file";
                const sizeLabel = formatAttachmentSize(attachment.size);

                return (
                  <WorkspaceFileCard
                    key={attachment.id}
                    variant="card"
                    filename={attachment.name}
                    sizeLabel={sizeLabel || undefined}
                    statusLabel={indexPresentation.statusLabel}
                    statusTone={indexPresentation.statusTone}
                    iconTone={workspaceFileIconToneForAttachment(
                      attachment.name,
                      previewKind,
                      indexPresentation.statusTone,
                    )}
                    previewKind={previewKind}
                    editable
                    showInlineActions={false}
                    dismissRemove
                    onPreview={() => {
                      openPreview(buildWorkspaceLocalFilePreviewTarget(attachment.file));
                    }}
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

      {previewModal}
    </form>
  );
}
