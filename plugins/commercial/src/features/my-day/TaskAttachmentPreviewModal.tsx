import { FilePreviewModal } from "@delpi/plugin-ui/index";

import { downloadAttachmentBlob } from "../../api/attachmentsApi";

export type TaskAttachmentPreviewTarget =
  | {
      kind: "local";
      file: File;
    }
  | {
      kind: "remote";
      id: string;
      fileName: string;
      contentType?: string | null;
      byteSize?: number;
    }
  | null;

type TaskAttachmentPreviewModalProps = {
  target: TaskAttachmentPreviewTarget;
  open: boolean;
  onClose: () => void;
};

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function TaskAttachmentPreviewModal({
  target,
  open,
  onClose,
}: TaskAttachmentPreviewModalProps) {
  const isLocal = target?.kind === "local";
  const fileName = isLocal ? target.file.name : target?.fileName;
  const mimeType = isLocal ? target.file.type : target?.contentType;
  const byteSize = isLocal ? target.file.size : target?.byteSize;
  const source =
    target == null
      ? null
      : target.kind === "local"
        ? target.file
        : () => downloadAttachmentBlob(target.id);

  return (
    <FilePreviewModal
      open={open && Boolean(target)}
      title={fileName ?? "Pré-visualização"}
      onClose={onClose}
      source={source}
      mimeType={mimeType}
      fileName={fileName}
      portalScopeClassName="dashboard-commercial"
      metaItems={
        target
          ? [
              byteSize != null ? formatBytes(byteSize) : null,
              mimeType?.trim() || "Tipo não informado",
            ]
          : undefined
      }
    />
  );
}
