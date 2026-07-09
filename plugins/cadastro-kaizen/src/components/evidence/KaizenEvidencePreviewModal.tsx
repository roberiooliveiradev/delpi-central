import { useCallback, useMemo } from "react";

import { FilePreviewModal } from "@delpi/plugin-ui";

import { fetchKaizenEvidenceObjectUrl } from "../../api/kaizenApi";
import { formatEvidenceFileSize } from "./kaizenEvidenceUtils";
import {
  evidencePreviewTitle,
  resolveEvidencePreviewMode,
  resolveLocalFilePreviewMode,
  type EvidencePreviewMode,
} from "./kaizenEvidencePreview";

type SavedSource = { kind: "saved"; kaizenId: string; evidence: import("../../types/kaizen").KaizenEvidence };
type LocalSource = { kind: "local"; file: File };
export type EvidencePreviewSource = SavedSource | LocalSource;

type Props = {
  source: EvidencePreviewSource | null;
  onClose: () => void;
};

function sourceTitle(source: EvidencePreviewSource): string {
  return source.kind === "saved" ? evidencePreviewTitle(source.evidence) : source.file.name;
}

function sourceMode(source: EvidencePreviewSource): EvidencePreviewMode {
  return source.kind === "saved"
    ? resolveEvidencePreviewMode(source.evidence)
    : resolveLocalFilePreviewMode(source.file);
}

export function KaizenEvidencePreviewModal({ source, onClose }: Props) {
  const open = source != null;
  const title = source ? sourceTitle(source) : "Pré-visualização";
  const mode = source ? sourceMode(source) : "none";

  const previewSource = useCallback(async () => {
    if (!source || mode === "none") {
      throw new Error("unsupported");
    }
    if (source.kind === "local") {
      return source.file;
    }
    const objectUrl = await fetchKaizenEvidenceObjectUrl(source.kaizenId, source.evidence.id);
    try {
      const response = await fetch(objectUrl);
      return response.blob();
    } finally {
      URL.revokeObjectURL(objectUrl);
    }
  }, [source, mode]);

  const mimeType = source?.kind === "saved" ? source.evidence.mime_type : source?.file.type;
  const fileName = source?.kind === "saved" ? source.evidence.file_name : source?.file.name;
  const declaredType = source?.kind === "saved" ? source.evidence.type : null;

  const metaItems = useMemo(() => {
    if (!source) return undefined;
    if (source.kind === "saved") {
      return [source.evidence.file_name ?? "Arquivo", formatEvidenceFileSize(source.evidence.size_bytes)];
    }
    return [source.file.name, formatEvidenceFileSize(source.file.size)];
  }, [source]);

  return (
    <FilePreviewModal
      open={open}
      title={title}
      onClose={onClose}
      source={previewSource}
      mimeType={mimeType}
      fileName={fileName}
      declaredType={declaredType}
      enabled={mode !== "none"}
      metaItems={metaItems}
    />
  );
}
