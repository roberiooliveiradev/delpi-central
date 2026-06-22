import type { ReactNode } from "react";

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
      <input
        type="text"
        value={title}
        onChange={(event) => onTitleChange(event.target.value)}
        placeholder={titlePlaceholder}
      />
      <textarea
        value={content}
        onChange={(event) => onContentChange(event.target.value)}
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
