import { FilePreviewModal } from "@delpi/plugin-ui/index";

import { formatEvidenceFileSize } from "./evidenceAttachmentUtils";
import { resolveLocalFilePreviewMode } from "./evidencePreviewUtils";

type Props = {
  file: File | null;
  open: boolean;
  onClose: () => void;
};

export function EvidenceLocalPreviewModal({ file, open, onClose }: Props) {
  const mode = file ? resolveLocalFilePreviewMode(file) : "none";

  return (
    <FilePreviewModal
      open={open}
      title={file?.name ?? "Pré-visualização"}
      onClose={onClose}
      source={file}
      mimeType={file?.type}
      fileName={file?.name}
      enabled={mode !== "none"}
      metaItems={file ? [formatEvidenceFileSize(file.size), file.type || "Tipo não informado"] : undefined}
    />
  );
}
