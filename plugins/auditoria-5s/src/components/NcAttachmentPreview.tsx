import { useEffect, useState } from "react";

import type { NcAttachment } from "../api/audit5sApi";
import { fetchNcAttachmentPreviewUrl } from "../utils/ncAttachments";

type Props = {
  ncId: string;
  attachment: NcAttachment;
  label: string;
};

export function NcAttachmentPreview({ ncId, attachment, label }: Props) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetchNcAttachmentPreviewUrl(ncId, attachment)
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
  }, [attachment, ncId]);

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
