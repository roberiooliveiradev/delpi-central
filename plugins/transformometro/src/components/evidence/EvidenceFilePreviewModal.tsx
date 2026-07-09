import { useCallback, useEffect, useState } from "react";

import { Modal } from "../ui/Modal";

export function isImageMime(mime: string | null | undefined): boolean {
  return !!mime && mime.startsWith("image/");
}

export function isPdfMime(mime: string | null | undefined): boolean {
  return (mime ?? "").toLowerCase() === "application/pdf";
}

type Props = {
  open: boolean;
  title: string;
  mime?: string | null;
  fetchObjectUrl: () => Promise<string>;
  onClose: () => void;
  onError?: (message: string) => void;
};

export function EvidenceFilePreviewModal({
  open,
  title,
  mime,
  fetchObjectUrl,
  onClose,
  onError,
}: Props) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const revokeObjectUrl = useCallback((url: string | null) => {
    if (url) URL.revokeObjectURL(url);
  }, []);

  useEffect(() => {
    if (!open) return;

    let active = true;
    setLoading(true);
    setError(null);
    setObjectUrl(null);

    fetchObjectUrl()
      .then((url) => {
        if (!active) {
          URL.revokeObjectURL(url);
          return;
        }
        setObjectUrl(url);
      })
      .catch(() => {
        if (!active) return;
        const message = "Erro ao carregar pré-visualização do arquivo.";
        setError(message);
        onError?.(message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [open, fetchObjectUrl, onError]);

  useEffect(() => {
    if (open) return;
    setObjectUrl((current) => {
      revokeObjectUrl(current);
      return null;
    });
    setError(null);
    setLoading(false);
  }, [open, revokeObjectUrl]);

  useEffect(
    () => () => {
      revokeObjectUrl(objectUrl);
    },
    [objectUrl, revokeObjectUrl]
  );

  return (
    <Modal open={open} title={title} onClose={onClose} className="ds-modal--evidence-preview">
      <div className="tm-evidence-preview-modal">
        {loading ? <p className="ds-hint">Carregando…</p> : null}
        {error ? <p className="ds-hint">{error}</p> : null}
        {!loading && !error && objectUrl && isImageMime(mime) ? (
          <img className="tm-evidence-preview-modal__img" src={objectUrl} alt={title} />
        ) : null}
        {!loading && !error && objectUrl && isPdfMime(mime) ? (
          <iframe className="tm-evidence-preview-modal__pdf" src={objectUrl} title={title} />
        ) : null}
        {!loading && !error && objectUrl && !isImageMime(mime) && !isPdfMime(mime) ? (
          <p className="ds-hint">Pré-visualização indisponível para este tipo de arquivo.</p>
        ) : null}
      </div>
    </Modal>
  );
}
