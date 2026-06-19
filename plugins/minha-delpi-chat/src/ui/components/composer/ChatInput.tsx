import {
  ArrowUp,
  Paperclip,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  applyComposerMentionSelection,
  detectActiveComposerMention,
  filterComposerMentionCandidates,
  listComposerMentionCandidates,
  removeComposerMentionTokenForName,
  stripComposerMentionTokens,
} from "../../../state/chatComposerMention";
import { ChatComposerContextBadges } from "./ChatComposerContextBadges";
import { ChatComposerMentionMenu } from "./ChatComposerMentionMenu";
import { ComposerMentionMenuPortal } from "./ComposerMentionMenuPortal";

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
  workspaceFileComposerAttachmentStatusLabel,
  workspaceFileIconToneForAttachment,
  workspaceFileIngestProgressState,
} from "../../../content/workspaceFileIngestContent";
import {
  buildWorkspaceLocalFilePreviewTarget,
  useWorkspaceFilePreviewModal,
} from "../../hooks/useWorkspaceFilePreviewModal";
import { useWorkspaceFileIngestPolicy } from "../../hooks/useWorkspaceFileIngestPolicy";
import { WorkspaceFileCard } from "../workspace/WorkspaceFileCard";

import "./ChatInput.css";
import "../workspace/workspaceFileIngest.css";

export type ChatInputAttachment = {
  id: string;
  name: string;
  size: number;
  type: string;
  file: File;
  status?: ComposerAttachmentStatus;
  serverAttachmentId?: string;
  readingStatus?: string;
  uploadPercent?: number;
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
  /** Badges de agente/projeto na área da pergunta — regra em resolveComposerContextBar (chatAgentActivation). */
  contextBadgeItems?: ComposerContextBarItem[];
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
  contextBadgeItems = [],
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
        agents: agents.map((agent) => ({
          id: agent.id,
          name: agent.name,
          icon: agent.icon,
        })),
        projects: projects.map((project) => ({
          id: project.id,
          name: project.name,
          icon: project.icon,
        })),
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
            inUseAgentIds: selectedAgentIds,
            inUseProjectIds: selectedProjectIds,
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

  const hasContextBadges = contextBadgeItems.length > 0;
  const hasAttachments = attachments.length > 0;
  const selectedAgentIdSet = useMemo(() => new Set(selectedAgentIds), [selectedAgentIds]);
  const selectedProjectIdSet = useMemo(() => new Set(selectedProjectIds), [selectedProjectIds]);

  function handleDraftChange(nextValue: string) {
    onChange(stripComposerMentionTokens(nextValue));
  }

  function handleRemoveContextBadge(
    item: ComposerContextBarItem,
    entityName: string,
  ) {
    onChange(removeComposerMentionTokenForName(value, entityName));

    if (item.kind === "agent") {
      onRemoveContextAgent?.(item.id);
      return;
    }

    onRemoveContextProject?.(item.id);
  }

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

    handleDraftChange(next.value);

    if (candidate.kind === "agent") {
      if (!selectedAgentIdSet.has(candidate.id)) {
        onToggleAgent?.(candidate.id);
      }
    } else if (!selectedProjectIdSet.has(candidate.id)) {
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

  const composerIngestLabels = workspaceFileComposerLabels();

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
          hasContextBadges ? "mdc-chat-input__box--with-context-badges" : "",
          hasAttachments ? "mdc-chat-input__box--with-attachments" : "",
          showResponseMode ? "mdc-chat-input__box--with-response-mode" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
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
                const attachmentStatus = attachment.status ?? "queued";
                const isIngesting =
                  attachmentStatus === "queued" || attachmentStatus === "uploading";
                const indexPresentation = workspaceFileAttachmentIndexPresentation({
                  status: attachmentStatus,
                  parsed: attachment.status === "indexed",
                  readingStatus: attachment.readingStatus,
                });
                const statusLabel = workspaceFileComposerAttachmentStatusLabel({
                  status: attachmentStatus,
                  parsed: attachment.status === "indexed",
                  readingStatus: attachment.readingStatus,
                  uploadPercent: isIngesting ? undefined : attachment.uploadPercent,
                });
                const previewKind = isImage ? "image" : "file";
                const sizeLabel = formatAttachmentSize(attachment.size);
                const ingestProgress = workspaceFileIngestProgressState({
                  status: attachmentStatus,
                  uploadPercent: attachment.uploadPercent,
                  label: composerIngestLabels.uploadingStatus,
                });

                return (
                  <WorkspaceFileCard
                    key={attachment.id}
                    variant="card"
                    filename={attachment.name}
                    sizeLabel={sizeLabel || undefined}
                    statusLabel={statusLabel}
                    statusTone={indexPresentation.statusTone}
                    iconTone={workspaceFileIconToneForAttachment(
                      attachment.name,
                      previewKind,
                      indexPresentation.statusTone,
                      ingestProgress?.active,
                    )}
                    previewKind={previewKind}
                    editable
                    showInlineActions={false}
                    dismissRemove
                    ingestProgress={ingestProgress}
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
            {isMentionMenuOpen && activeMention ? (
              <ComposerMentionMenuPortal
                open
                textareaRef={textareaRef}
                anchorIndex={activeMention.start}
                itemCount={Math.max(mentionItems.length, 1)}
                value={value}
              >
                <ChatComposerMentionMenu
                  items={mentionItems}
                  activeIndex={Math.min(mentionIndex, Math.max(mentionItems.length - 1, 0))}
                  onHover={setMentionIndex}
                  onSelect={handleMentionSelect}
                  variant="portal"
                />
              </ComposerMentionMenuPortal>
            ) : null}

            {hasContextBadges ? (
              <ChatComposerContextBadges
                items={contextBadgeItems}
                agents={agents}
                projects={projects}
                onRemoveAgent={(agentId) => {
                  const agent = agents.find((entry) => entry.id === agentId);

                  if (agent) {
                    handleRemoveContextBadge({ kind: "agent", id: agentId }, agent.name);
                  }
                }}
                onRemoveProject={(projectId) => {
                  const project = projects.find((entry) => entry.id === projectId);

                  if (project) {
                    handleRemoveContextBadge({ kind: "project", id: projectId }, project.name);
                  }
                }}
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
                handleDraftChange(event.target.value);
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
          : "Digite @ ou use + para combinar agentes e projetos na pergunta. A resposta será exibida em tempo real."}
      </small>

      {previewModal}
    </form>
  );
}
