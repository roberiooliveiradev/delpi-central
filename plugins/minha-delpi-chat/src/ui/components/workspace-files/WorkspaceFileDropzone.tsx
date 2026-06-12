import { Plus, Upload } from "lucide-react";
import { useRef, type DragEvent, type ReactNode } from "react";

import type { WorkspaceFileIngestPolicyFamily } from "../../../data/api/chatTypes";
import { workspaceFileDropzoneContent } from "../../../content/workspaceFileIngestContent";
import {
  useWorkspaceFileIngestPolicy,
  workspaceFileIngestFamilyForContentVariant,
} from "../../hooks/useWorkspaceFileIngestPolicy";

import "./workspaceFileIngest.css";

type TokenProvider = () => string | undefined | Promise<string | undefined>;

type WorkspaceFileDropzoneProps = {
  accept?: string;
  ingestFamily?: WorkspaceFileIngestPolicyFamily;
  getAccessToken?: TokenProvider;
  multiple?: boolean;
  disabled?: boolean;
  isBusy?: boolean;
  isDragActive?: boolean;
  title?: string;
  hint?: string;
  actionLabel?: string;
  contentVariant?: Parameters<typeof workspaceFileDropzoneContent>[0];
  ariaLabel?: string;
  onFilesSelected: (files: File[]) => void;
  onDragActiveChange?: (active: boolean) => void;
  footerSlot?: ReactNode;
  showFieldLabel?: string;
  compact?: boolean;
};

export function WorkspaceFileDropzone({
  accept,
  ingestFamily,
  getAccessToken,
  multiple = false,
  disabled = false,
  isBusy = false,
  isDragActive = false,
  title,
  hint,
  actionLabel,
  contentVariant = "workspace",
  ariaLabel,
  onFilesSelected,
  onDragActiveChange,
  footerSlot,
  showFieldLabel,
  compact = false,
}: WorkspaceFileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const resolvedFamily =
    ingestFamily ?? workspaceFileIngestFamilyForContentVariant(contentVariant);
  const shouldLoadPolicy = accept === undefined;
  const { accept: policyAccept } = useWorkspaceFileIngestPolicy(
    shouldLoadPolicy ? resolvedFamily : undefined,
    { getAccessToken },
  );
  const resolvedAccept = accept ?? policyAccept;
  const content = workspaceFileDropzoneContent(contentVariant);
  const resolvedTitle = title ?? content.title;
  const resolvedHint = hint ?? content.hint;
  const resolvedAction =
    actionLabel ?? (compact ? content.actionSelect : content.actionAdd);

  function handleDragOver(event: DragEvent<HTMLElement>) {
    if (disabled || isBusy) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    onDragActiveChange?.(true);
  }

  function handleDragLeave(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    event.stopPropagation();
    onDragActiveChange?.(false);
  }

  function handleDrop(event: DragEvent<HTMLElement>) {
    if (disabled || isBusy) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    onDragActiveChange?.(false);

    const files = Array.from(event.dataTransfer.files ?? []);

    if (files.length > 0) {
      onFilesSelected(multiple ? files : files.slice(0, 1));
    }
  }

  function openPicker() {
    if (!disabled && !isBusy) {
      inputRef.current?.click();
    }
  }

  const dropzone = (
    <div
      className={[
        "mdc-workspace-file-dropzone",
        compact ? "mdc-workspace-file-dropzone--compact" : "",
        isDragActive ? "mdc-workspace-file-dropzone--active" : "",
        isBusy ? "mdc-workspace-file-dropzone--busy" : "",
        disabled ? "mdc-workspace-file-dropzone--disabled" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onDragEnter={handleDragOver}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={openPicker}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openPicker();
        }
      }}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled || isBusy}
      aria-label={ariaLabel ?? resolvedTitle}
    >
      <span className="mdc-workspace-file-dropzone__icon">
        <Upload size={20} aria-hidden="true" />
      </span>

      <div className="mdc-workspace-file-dropzone__copy">
        <strong>{resolvedTitle}</strong>
        <span>{resolvedHint}</span>
      </div>

      <span className="mdc-chat-ws-outline-btn mdc-workspace-file-dropzone__action">
        <Plus size={16} aria-hidden="true" />
        <span>{resolvedAction}</span>
      </span>

      <input
        ref={inputRef}
        type="file"
        hidden
        accept={resolvedAccept}
        multiple={multiple}
        disabled={disabled || isBusy}
        onChange={(event) => {
          const files = Array.from(event.target.files ?? []);

          if (files.length > 0) {
            onFilesSelected(files);
          }

          event.target.value = "";
        }}
      />
    </div>
  );

  if (!showFieldLabel) {
    return (
      <>
        {dropzone}
        {footerSlot}
      </>
    );
  }

  return (
    <div className="mdc-admin-file-dropzone-field">
      <span className="mdc-admin-file-dropzone-field__label">{showFieldLabel}</span>
      {dropzone}
      {footerSlot}
    </div>
  );
}
