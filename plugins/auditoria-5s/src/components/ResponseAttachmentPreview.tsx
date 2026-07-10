import { useEffect, useState } from "react";

import type { ResponseAttachment } from "../api/audit5sApi";
import { fetchResponseAttachmentPreviewUrl } from "../utils/responseAttachments";

type Props = {
  auditId: string;
  criterionId: string;
  attachment: ResponseAttachment;
  label: string;
};

export function ResponseAttachmentPreview({
  auditId,
  criterionId,
  attachment,
  label,
}: Props) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetchResponseAttachmentPreviewUrl(auditId, criterionId, attachment)
      .then((url) => {
        if (active) setPreviewUrl(url);
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Erro ao carregar imagem.");
        }
      });
    return () => {
      active = false;
    };
  }, [attachment, auditId, criterionId]);

  if (error) {
    return <p className="a5s-nc-evidence__error">{error}</p>;
  }

  if (!previewUrl) {
    return <p className="a5s-nc-evidence__loading">Carregando {label.toLowerCase()}...</p>;
  }

  return (
    <img
      src={previewUrl}
      alt={label}
      className="a5s-nc-evidence__preview"
    />
  );
}
