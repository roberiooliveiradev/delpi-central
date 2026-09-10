import { ActionButton, FilePreviewModal } from "@delpi/plugin-ui/index";
import { useState } from "react";

import {
  downloadArtifactBlob,
  downloadAttachmentBlob,
} from "../api/requestsApi";
import { MR_PORTAL_SCOPE } from "../ui/mrUi";

export type RequestFilePreviewTarget =
  | {
      kind: "local";
      file: File;
    }
  | {
      kind: "attachment";
      id: string;
      fileName: string;
      contentType?: string | null;
      byteSize?: number | null;
    }
  | {
      kind: "artifact";
      id: string;
      fileName: string;
      contentType?: string | null;
      byteSize?: number | null;
    }
  | null;

type RequestFilePreviewModalProps = {
  target: RequestFilePreviewTarget;
  open: boolean;
  onClose: () => void;
};

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function triggerBlobDownload(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName || "arquivo";
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

/** Pré-visualização autenticada (blob) + baixar — sem navegar para URL sem JWT. */
export function RequestFilePreviewModal({
  target,
  open,
  onClose,
}: RequestFilePreviewModalProps) {
  const [downloadBusy, setDownloadBusy] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const isLocal = target?.kind === "local";
  const fileName = isLocal ? target.file.name : target?.fileName;
  const mimeType = isLocal ? target.file.type : target?.contentType;
  const byteSize = isLocal ? target.file.size : target?.byteSize ?? undefined;

  const source =
    target == null
      ? null
      : target.kind === "local"
        ? target.file
        : target.kind === "attachment"
          ? () => downloadAttachmentBlob(target.id)
          : () => downloadArtifactBlob(target.id);

  async function onDownload() {
    if (!target || downloadBusy) return;
    setDownloadBusy(true);
    setDownloadError(null);
    try {
      const blob =
        target.kind === "local"
          ? target.file
          : target.kind === "attachment"
            ? await downloadAttachmentBlob(target.id)
            : await downloadArtifactBlob(target.id);
      triggerBlobDownload(blob, fileName || "arquivo");
    } catch (err) {
      setDownloadError(
        err instanceof Error ? err.message : "Não foi possível baixar o arquivo.",
      );
    } finally {
      setDownloadBusy(false);
    }
  }

  return (
    <FilePreviewModal
      open={open && Boolean(target)}
      title={fileName ?? "Pré-visualização"}
      onClose={() => {
        setDownloadError(null);
        onClose();
      }}
      source={source}
      mimeType={mimeType}
      fileName={fileName}
      portalScopeClassName={MR_PORTAL_SCOPE}
      metaItems={
        target
          ? [
              byteSize != null ? formatBytes(byteSize) : null,
              mimeType?.trim() || "Tipo não informado",
              downloadError,
            ]
          : undefined
      }
      headerActions={
        <ActionButton
          type="button"
          variant="ghost"
          disabled={downloadBusy || !target}
          onClick={() => void onDownload()}
        >
          {downloadBusy ? "Baixando…" : "Baixar"}
        </ActionButton>
      }
    />
  );
}
