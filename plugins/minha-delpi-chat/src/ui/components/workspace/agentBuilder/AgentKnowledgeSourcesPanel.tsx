import { useCallback, useMemo, useState, type ReactNode } from "react";

import type { ChatWorkspaceSource } from "../../../../data/api/chatTypes";
import {
  workspaceFileAgentIngestLabels,
  workspaceFileIconToneForAttachment,
  workspaceFileKindLabel,
  workspaceFileSourceIndexPresentation,
} from "../../../../content/workspaceFileIngestContent";
import { getSourceContentHash, sha256HexFromFile } from "../../../../utils/fileContentHash";
import {
  buildWorkspaceSourcePreviewTarget,
  useWorkspaceFilePreviewModal,
} from "../../../hooks/useWorkspaceFilePreviewModal";
import { IngestProgressIndicator } from "../../shared/IngestProgressIndicator";
import { WorkspaceFileCard } from "../WorkspaceFileCard";
import { WorkspaceFileDropzone } from "../WorkspaceFileDropzone";
import { WorkspaceFileSourceList, WorkspaceFileSourceListItem } from "../WorkspaceFileSourceList";
import { WorkspaceSourcesPanel } from "../WorkspaceSourcesPanel";

import "./AgentKnowledgeSourcesPanel.css";
import "../workspaceFileIngest.css";

type AgentKnowledgeSourcesPanelProps = {
  sources: ChatWorkspaceSource[];
  isUploading?: boolean;
  uploadPercent?: number | null;
  notice?: string | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onUploadFiles: (files: File[]) => Promise<void>;
  onRemoveSource: (sourceId: string) => Promise<void>;
  onDownloadSource?: (sourceId: string) => Promise<void>;
  onLocalDuplicatesSkipped?: (count: number) => void;
  noteSlot?: ReactNode;
  headerSlot?: ReactNode;
};

function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes || bytes <= 0) {
    return "";
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getSourceLabel(source: ChatWorkspaceSource): string {
  return source.original_filename || source.title || "Arquivo";
}

function getSourceSize(source: ChatWorkspaceSource): string {
  const bytes = source.metadata?.sizeBytes;

  return formatFileSize(typeof bytes === "number" ? bytes : null);
}

export function AgentKnowledgeSourcesPanel({
  sources,
  isUploading = false,
  uploadPercent = null,
  notice,
  getAccessToken,
  onUploadFiles,
  onRemoveSource,
  onDownloadSource,
  onLocalDuplicatesSkipped,
  noteSlot,
  headerSlot,
}: AgentKnowledgeSourcesPanelProps) {
  const ingestLabels = workspaceFileAgentIngestLabels();
  const { openPreview, previewModal } = useWorkspaceFilePreviewModal({ getAccessToken });
  const [isDragActive, setIsDragActive] = useState(false);
  const [pendingHashes, setPendingHashes] = useState<Set<string>>(new Set());

  const knownHashes = useMemo(() => {
    const hashes = new Set<string>();

    for (const source of sources) {
      const hash = getSourceContentHash(source.metadata);

      if (hash) {
        hashes.add(hash);
      }
    }

    return hashes;
  }, [sources]);

  const processFiles = useCallback(
    async (fileList: FileList | File[]) => {
      const files = Array.from(fileList).filter((file) => file.size > 0);

      if (files.length === 0) {
        return;
      }

      const accepted: File[] = [];
      const localHashes = new Set(knownHashes);

      for (const file of files) {
        const hash = await sha256HexFromFile(file);

        if (localHashes.has(hash) || pendingHashes.has(hash)) {
          continue;
        }

        localHashes.add(hash);
        accepted.push(file);
      }

      if (accepted.length === 0) {
        if (files.length > 0) {
          onLocalDuplicatesSkipped?.(files.length);
        }

        return;
      }

      const uploadHashes = await Promise.all(accepted.map((file) => sha256HexFromFile(file)));

      setPendingHashes((current) => {
        const next = new Set(current);
        uploadHashes.forEach((hash) => next.add(hash));
        return next;
      });

      try {
        await onUploadFiles(accepted);
      } finally {
        setPendingHashes((current) => {
          const next = new Set(current);
          uploadHashes.forEach((hash) => next.delete(hash));
          return next;
        });
      }
    },
    [knownHashes, onLocalDuplicatesSkipped, onUploadFiles, pendingHashes],
  );

  return (
    <WorkspaceSourcesPanel className="mdc-agent-knowledge" headerSlot={headerSlot}>
      <WorkspaceFileDropzone
        multiple
        disabled={isUploading}
        isBusy={isUploading}
        isDragActive={isDragActive}
        contentVariant="agent"
        ingestFamily="agent_source"
        getAccessToken={getAccessToken}
        ariaLabel={ingestLabels.ariaAddFiles}
        onDragActiveChange={setIsDragActive}
        onFilesSelected={(files) => {
          void processFiles(files);
        }}
      />

      {notice ? <p className="mdc-agent-knowledge__notice">{notice}</p> : null}

      {isUploading ? (
        <IngestProgressIndicator
          className="mdc-agent-knowledge__status"
          label={ingestLabels.uploadingStatus}
          percent={uploadPercent ?? undefined}
        />
      ) : null}

      {sources.length > 0 ? (
        <WorkspaceFileSourceList ariaLabel={ingestLabels.listAriaLabel}>
          {sources.map((source) => {
            const label = getSourceLabel(source);
            const isDuplicateMarked = source.duplicate === true;
            const indexStatus = workspaceFileSourceIndexPresentation(source);

            return (
              <WorkspaceFileSourceListItem key={source.id}>
                <WorkspaceFileCard
                  variant="row"
                  filename={label}
                  iconTone={workspaceFileIconToneForAttachment(
                    label,
                    "file",
                    indexStatus.statusTone,
                  )}
                  kindLabel={workspaceFileKindLabel(label)}
                  sizeLabel={getSourceSize(source) || undefined}
                  statusLabel={indexStatus.statusLabel}
                  statusTone={indexStatus.statusTone}
                  secondaryLabel={isDuplicateMarked ? ingestLabels.duplicateMarked : undefined}
                  previewKind="file"
                  editable
                  onPreview={() => {
                    openPreview(buildWorkspaceSourcePreviewTarget(source));
                  }}
                  onDownload={
                    onDownloadSource
                      ? () => {
                          void onDownloadSource(source.id);
                        }
                      : undefined
                  }
                  onRemove={() => {
                    void onRemoveSource(source.id);
                  }}
                />
              </WorkspaceFileSourceListItem>
            );
          })}
        </WorkspaceFileSourceList>
      ) : (
        <p className="mdc-chat-ws-empty">{ingestLabels.emptyState}</p>
      )}

      {noteSlot}

      {previewModal}
    </WorkspaceSourcesPanel>
  );
}
