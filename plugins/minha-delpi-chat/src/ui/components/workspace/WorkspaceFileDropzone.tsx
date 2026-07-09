import type { ReactNode } from "react";

import type { WorkspaceFileIngestPolicyFamily } from "../../../data/api/chatTypes";
import { workspaceFileDropzoneContent } from "../../../content/workspaceFileIngestContent";
import {
  useWorkspaceFileIngestPolicy,
  workspaceFileIngestFamilyForContentVariant,
} from "../../hooks/useWorkspaceFileIngestPolicy";

import {
  ChatWorkspaceFileDropzoneBase,
  WorkspaceFileDropzoneEmptyContent,
} from "./chatWorkspaceFileDropzone";

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

  return (
    <ChatWorkspaceFileDropzoneBase
      accept={resolvedAccept}
      multiple={multiple}
      disabled={disabled}
      busy={isBusy}
      dragActive={isDragActive}
      onDragActiveChange={onDragActiveChange}
      onFilesSelected={onFilesSelected}
      hideInput
      ariaLabel={ariaLabel ?? resolvedTitle}
      className={compact ? "mdc-workspace-file-dropzone--compact" : undefined}
      fieldLabel={showFieldLabel}
      fieldRootClassName="mdc-admin-file-dropzone-field"
      fieldLabelClassName="mdc-admin-file-dropzone-field__label"
      footerSlot={footerSlot}
      emptyContent={
        <WorkspaceFileDropzoneEmptyContent
          title={resolvedTitle}
          hint={resolvedHint}
          actionLabel={resolvedAction}
        />
      }
    />
  );
}
