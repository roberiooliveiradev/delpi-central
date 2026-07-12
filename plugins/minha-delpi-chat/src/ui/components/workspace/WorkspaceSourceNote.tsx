import { ChatNativeTextInput } from "../shared/chatNativeFormFields";
import type { ReactNode } from "react";

import { ChatNativeTextAreaControl } from "../admin/shared/chatAdminFormFields";

type WorkspaceSourceNoteDetailsProps = {
  children: ReactNode;
  summary?: string;
};

export function WorkspaceSourceNoteDetails({
  children,
  summary = "Adicionar nota de texto",
}: WorkspaceSourceNoteDetailsProps) {
  return (
    <details className="mdc-chat-ws-details mdc-workspace-sources-panel__note">
      <summary>{summary}</summary>
      <div className="mdc-chat-ws-details-body">{children}</div>
    </details>
  );
}

type WorkspaceSourceNoteFormProps = {
  title: string;
  content: string;
  onTitleChange: (value: string) => void;
  onContentChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  titlePlaceholder?: string;
  contentPlaceholder?: string;
  submitLabel?: string;
};

export function WorkspaceSourceNoteForm({
  title,
  content,
  onTitleChange,
  onContentChange,
  onSubmit,
  disabled = false,
  titlePlaceholder = "Título da nota",
  contentPlaceholder = "Cole contexto, regras ou conhecimento...",
  submitLabel = "Adicionar nota",
}: WorkspaceSourceNoteFormProps) {
  return (
    <div className="mdc-workspace-source-note">
      <ChatNativeTextInput
        type="text"
        value={title}
        onChange={(event) => onTitleChange(event.target.value)}
        placeholder={titlePlaceholder}
      />
      <ChatNativeTextAreaControl
        value={content}
        onChange={onContentChange}
        placeholder={contentPlaceholder}
        rows={4}
      />
      <button
        type="button"
        className="mdc-chat-ws-outline-btn"
        disabled={disabled || !content.trim()}
        onClick={onSubmit}
      >
        {submitLabel}
      </button>
    </div>
  );
}
