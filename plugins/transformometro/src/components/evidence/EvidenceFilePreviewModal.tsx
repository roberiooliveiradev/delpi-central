import { useCallback } from "react";

import { FilePreviewModal } from "@delpi/plugin-ui";

type Props = {
  open: boolean;
  title: string;
  mime?: string | null;
  fetchObjectUrl: () => Promise<string>;
  onClose: () => void;
  onError?: (message: string) => void;
  metaItems?: Array<string | null | undefined>;
};

export function isImageMime(mime: string | null | undefined): boolean {
  return !!mime && mime.startsWith("image/");
}

export function isPdfMime(mime: string | null | undefined): boolean {
  return (mime ?? "").toLowerCase() === "application/pdf";
}

export function EvidenceFilePreviewModal({
  open,
  title,
  mime,
  fetchObjectUrl,
  onClose,
  onError,
  metaItems,
}: Props) {
  const source = useCallback(async () => {
    const objectUrl = await fetchObjectUrl();
    try {
      const response = await fetch(objectUrl);
      return response.blob();
    } finally {
      URL.revokeObjectURL(objectUrl);
    }
  }, [fetchObjectUrl]);

  return (
    <FilePreviewModal
      open={open}
      title={title}
      onClose={onClose}
      source={source}
      mimeType={mime}
      fileName={title}
      metaItems={metaItems}
      labels={{
        loadFailed: "Erro ao carregar pré-visualização do arquivo.",
      }}
      onLoadError={onError}
    />
  );
}
