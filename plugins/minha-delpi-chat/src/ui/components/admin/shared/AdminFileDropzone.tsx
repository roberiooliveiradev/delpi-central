import type { ReactNode } from "react";

import { WorkspaceFileDropzone } from "../../workspace-files/WorkspaceFileDropzone";

import "./AdminFileDropzone.css";

type AdminFileDropzoneProps = {
  label: string;
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  isBusy?: boolean;
  isDragActive?: boolean;
  title?: string;
  hint?: string;
  actionLabel?: string;
  onFilesSelected: (files: File[]) => void;
  onDragActiveChange?: (active: boolean) => void;
  footerSlot?: ReactNode;
};

export function AdminFileDropzone({
  label,
  accept,
  multiple = false,
  disabled = false,
  isBusy = false,
  isDragActive = false,
  title,
  hint,
  actionLabel,
  onFilesSelected,
  onDragActiveChange,
  footerSlot,
}: AdminFileDropzoneProps) {
  return (
    <WorkspaceFileDropzone
      showFieldLabel={label}
      accept={accept}
      multiple={multiple}
      disabled={disabled}
      isBusy={isBusy}
      isDragActive={isDragActive}
      title={title}
      hint={hint}
      actionLabel={actionLabel}
      contentVariant="workspace"
      ariaLabel={label}
      onFilesSelected={onFilesSelected}
      onDragActiveChange={onDragActiveChange}
      footerSlot={footerSlot}
    />
  );
}
