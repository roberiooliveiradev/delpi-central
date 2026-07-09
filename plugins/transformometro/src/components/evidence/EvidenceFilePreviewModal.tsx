import { useCallback, useEffect } from "react";

import {
  FilePreviewView,
  useFilePreviewLoader,
} from "@delpi/plugin-ui";

import { Modal } from "../ui/Modal";

type Props = {
  open: boolean;
  title: string;
  mime?: string | null;
  fetchObjectUrl: () => Promise<string>;
  onClose: () => void;
  onError?: (message: string) => void;
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

  const state = useFilePreviewLoader({
    source,
    mimeType: mime,
    fileName: title,
    enabled: open,
  });

  useEffect(() => {
    if (!open || !state.error || state.error === "empty" || state.error === "unsupported") {
      return;
    }
    onError?.(
      state.error === "load_failed"
        ? "Erro ao carregar pré-visualização do arquivo."
        : state.error,
    );
  }, [open, onError, state.error]);

  return (
    <Modal open={open} title={title} onClose={onClose} className="ds-modal--evidence-preview">
      <div className="tm-evidence-preview-modal">
        <FilePreviewView
          state={state}
          title={title}
          labels={{
            loadFailed: "Erro ao carregar pré-visualização do arquivo.",
          }}
        />
      </div>
    </Modal>
  );
}
