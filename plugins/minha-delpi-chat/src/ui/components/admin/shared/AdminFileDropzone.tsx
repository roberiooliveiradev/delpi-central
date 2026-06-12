import type { ReactNode } from "react";

import type { WorkspaceFileIngestPolicyFamily } from "../../../../data/api/chatTypes";
import { WorkspaceFileDropzone } from "../../workspace-files/WorkspaceFileDropzone";

import "./AdminFileDropzone.css";

type TokenProvider = () => string | undefined | Promise<string | undefined>;

type AdminFileDropzoneProps = {
  label: string;
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
  onFilesSelected: (files: File[]) => void;
  onDragActiveChange?: (active: boolean) => void;
  footerSlot?: ReactNode;
};

export function AdminFileDropzone({
  label,
  accept,
  ingestFamily = "global_knowledge",
  getAccessToken,
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
      ingestFamily={ingestFamily}
      getAccessToken={getAccessToken}
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
